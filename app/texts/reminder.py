from datetime import datetime

_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def schedule_label(schedule_type: str, schedule_value: str | None) -> str:
    if schedule_type == "daily":
        return "Every day"
    if schedule_type == "weekly":
        return f"Every {_WEEKDAYS[int(schedule_value)]}"
    if schedule_type == "monthly":
        n = int(schedule_value)
        suffix = "th" if 11 <= n <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"Every month on {n}{suffix}"
    if schedule_type == "once":
        dt = datetime.strptime(schedule_value, "%Y-%m-%d")
        return dt.strftime("%-d %B %Y")
    return schedule_type


def title_prompt() -> str:
    return "🔔 <b>New reminder</b>\n\nEnter a title:"


def schedule_type_prompt(title: str) -> str:
    return f"🔔 <b>New reminder</b>\n\n📌 {title}\n\nHow often?"


def weekly_day_prompt(title: str) -> str:
    return f"🔔 <b>New reminder</b>\n\n📌 {title}\n\nWhich day of the week?"


def monthly_day_prompt(title: str) -> str:
    return f"🔔 <b>New reminder</b>\n\n📌 {title}\n\nWhich day of the month?"


def once_date_prompt(title: str) -> str:
    return (
        f"🔔 <b>New reminder</b>\n\n📌 {title}\n\n"
        "Enter date:\n<i>e.g. 15.06.2026</i>"
    )


def once_date_invalid(title: str) -> str:
    return (
        f"🔔 <b>New reminder</b>\n\n📌 {title}\n\n"
        "⚠️ Couldn't parse date. Use format <b>DD.MM.YYYY</b>:"
    )


def time_prompt(title: str, sched: str) -> str:
    return f"🔔 <b>New reminder</b>\n\n📌 {title}\n📅 {sched}\n\n⏰ At what time?"


def time_custom_prompt(title: str, sched: str) -> str:
    return f"🔔 <b>New reminder</b>\n\n📌 {title}\n📅 {sched}\n\n⏰ Enter time <i>(HH:MM)</i>:"


def time_invalid(title: str, sched: str) -> str:
    return (
        f"🔔 <b>New reminder</b>\n\n📌 {title}\n📅 {sched}\n\n"
        "⚠️ Couldn't parse time. Use format <b>HH:MM</b>:"
    )


def target_prompt(title: str, sched: str, send_time: str) -> str:
    return (
        f"🔔 <b>New reminder</b>\n\n"
        f"📌 {title}\n📅 {sched}\n⏰ {send_time}\n\n"
        "📨 Where to send?"
    )


def confirm_text(title: str, sched: str, send_time: str, target_label: str) -> str:
    return (
        f"🔔 <b>New reminder</b>\n\n"
        f"📌 {title}\n"
        f"📅 {sched}\n"
        f"⏰ {send_time}\n"
        f"📨 {target_label}\n\n"
        "Ready to save?"
    )


def success_text(title: str, sched: str, send_time: str, target_label: str) -> str:
    return (
        f"✅ <b>Reminder saved!</b>\n\n"
        f"🔔 {title}\n"
        f"📅 {sched}\n"
        f"⏰ {send_time}\n"
        f"📨 {target_label}"
    )


def cancelled_text() -> str:
    return "❌ <b>Cancelled.</b>"
