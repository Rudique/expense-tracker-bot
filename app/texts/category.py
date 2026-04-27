def input_prompt() -> str:
    return (
        "📂 <b>New category</b>\n\n"
        "Send emoji and name separated by a space:\n"
        "<i>e.g. 🍕 Fast Food</i>"
    )


def input_invalid() -> str:
    return (
        "📂 <b>New category</b>\n\n"
        "⚠️ Please send emoji and name separated by a space:\n"
        "<i>e.g. 🍕 Fast Food</i>"
    )


def confirm_text(emoji: str, name: str) -> str:
    return (
        f"📂 Category: <b>{emoji} {name}</b>\n\n"
        "Ready to save?"
    )


def success_text(emoji: str, name: str) -> str:
    return f"✅ <b>Category saved!</b>\n\n📂 Category: <b>{emoji} {name}</b>"


def cancelled_text() -> str:
    return "❌ <b>Cancelled.</b>"
