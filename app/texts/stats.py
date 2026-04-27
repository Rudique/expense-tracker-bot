from datetime import datetime
from decimal import Decimal


def _date_range_label(date_from: datetime, date_to: datetime) -> str:
    fmt_full = "%-d %b %Y"
    if date_from.date() == date_to.date():
        return date_from.strftime(fmt_full)
    if date_from.year == date_to.year:
        if date_from.month == date_to.month:
            return f"{date_from.strftime('%-d')}–{date_to.strftime('%-d %b %Y')}"
        return f"{date_from.strftime('%-d %b')} – {date_to.strftime('%-d %b %Y')}"
    return f"{date_from.strftime(fmt_full)} – {date_to.strftime(fmt_full)}"


def _category_line(emoji: str, name: str, total: Decimal, count: int, grand_total: Decimal) -> str:
    pct = float(total / grand_total * 100)
    return f"{emoji} {name} — <b>{total}</b> · {pct:.0f}% · {count} tx"


def stats_text(period_label: str, rows: list, date_from: datetime, date_to: datetime) -> str:
    date_str = _date_range_label(date_from, date_to)
    header = f"📊 <b>Spending for {period_label}</b>\n📅 {date_str}"

    if not rows:
        return f"{header}\n\nNo transactions found for this period."

    personal = [r for r in rows if not r.is_shared]
    common   = [r for r in rows if r.is_shared]

    personal_total = sum(r.total for r in personal)
    common_total   = sum(r.total for r in common)
    grand_total    = personal_total + common_total

    lines = [header, ""]

    if personal:
        lines.append("👤 <b>Personal</b>")
        for r in personal:
            lines.append(_category_line(r.emoji, r.name, r.total, r.count, grand_total))
        lines.append(f"\n<i>Subtotal: {personal_total}</i>")

    if personal and common:
        lines.append("")

    if common:
        lines.append("👥 <b>Common</b>")
        for r in common:
            lines.append(_category_line(r.emoji, r.name, r.total, r.count, grand_total))
        lines.append(f"\n<i>Subtotal: {common_total}</i>")

    lines.append(f"\n💰 <b>Total: {grand_total}</b>")
    return "\n".join(lines)


def group_stats_text(period_label: str, rows: list, date_from: datetime, date_to: datetime) -> str:
    date_str = _date_range_label(date_from, date_to)
    header = f"👥 <b>Group spending for {period_label}</b>\n📅 {date_str}"

    if not rows:
        return f"{header}\n\nNo transactions found for this period."

    grand_total = sum(r.total for r in rows)

    shared_rows  = [r for r in rows if r.is_shared]
    personal_rows = [r for r in rows if not r.is_shared]

    lines = [header, ""]

    # ── Shared section (aggregate by category across all users) ────────────────
    if shared_rows:
        # Merge same-category rows that came from different users
        merged: dict[tuple, dict] = {}
        for r in shared_rows:
            key = (r.emoji, r.name)
            if key not in merged:
                merged[key] = {"emoji": r.emoji, "name": r.name,
                               "total": r.total, "count": r.count}
            else:
                merged[key]["total"] += r.total
                merged[key]["count"] += r.count

        shared_cats = sorted(merged.values(), key=lambda x: x["total"], reverse=True)
        shared_total = sum(c["total"] for c in shared_cats)

        lines.append("🏠 <b>Shared</b>")
        for c in shared_cats:
            lines.append(_category_line(c["emoji"], c["name"], c["total"], c["count"], grand_total))
        lines.append(f"\n<i>Subtotal: {shared_total}</i>")

    # ── Personal section (per user) ────────────────────────────────────────────
    if personal_rows:
        if shared_rows:
            lines.append("")

        by_user: dict[int, list] = {}
        for r in personal_rows:
            by_user.setdefault(r.user_id, []).append(r)

        for user_rows in by_user.values():
            first = user_rows[0]
            display = f"@{first.username}" if first.username else (first.first_name or f"User {first.user_id}")
            user_total = sum(r.total for r in user_rows)

            lines.append(f"👤 <b>{display}</b>")
            for r in user_rows:
                lines.append(_category_line(r.emoji, r.name, r.total, r.count, grand_total))
            lines.append(f"\n<i>Subtotal: {user_total}</i>")
            lines.append("")

    lines.append(f"💰 <b>Total: {grand_total}</b>")
    return "\n".join(lines)
