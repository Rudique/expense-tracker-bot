from decimal import Decimal


def stats_text(period_label: str, rows: list) -> str:
    if not rows:
        return (
            f"📊 <b>Spending for {period_label}</b>\n\n"
            "No transactions found for this period."
        )

    total = sum(row.total for row in rows)
    lines = [f"📊 <b>Spending for {period_label}</b>\n"]
    for row in rows:
        lines.append(f"{row.emoji} {row.name}  —  <b>{row.total}</b>  ({row.count} tx)")
    lines.append(f"\n💰 <b>Total: {total}</b>")
    return "\n".join(lines)


def month_picker_prompt() -> str:
    return "🗓 <b>Select a month:</b>"
