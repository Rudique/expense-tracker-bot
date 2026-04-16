from datetime import datetime
from decimal import Decimal

_BAR_WIDTH = 8
_FILLED = "█"
_EMPTY = "░"


def _date_range_label(date_from: datetime, date_to: datetime) -> str:
    fmt_full = "%-d %b %Y"
    if date_from.date() == date_to.date():
        return date_from.strftime(fmt_full)
    if date_from.year == date_to.year:
        if date_from.month == date_to.month:
            return f"{date_from.strftime('%-d')}–{date_to.strftime('%-d %b %Y')}"
        return f"{date_from.strftime('%-d %b')} – {date_to.strftime('%-d %b %Y')}"
    return f"{date_from.strftime(fmt_full)} – {date_to.strftime(fmt_full)}"


def _bar(pct: float) -> str:
    filled = round(pct / 100 * _BAR_WIDTH)
    return _FILLED * filled + _EMPTY * (_BAR_WIDTH - filled)


def _section(rows: list, grand_total: Decimal) -> list[str]:
    lines = []
    for row in rows:
        pct = float(row.total / grand_total * 100)
        lines.append(
            f"{row.emoji} {row.name} — <b>{row.total}</b>\n"
            f"<code>{_bar(pct)}</code> {pct:.0f}%  ·  {row.count} tx\n"
        )
    return lines


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
        lines.extend(_section(personal, grand_total))
        lines.append(f"<i>Subtotal: {personal_total}</i>\n")

    if common:
        lines.append("👥 <b>Common</b>")
        lines.extend(_section(common, grand_total))
        lines.append(f"<i>Subtotal: {common_total}</i>\n")

    lines.append(f"💰 <b>Total: {grand_total}</b>")
    return "\n".join(lines)
