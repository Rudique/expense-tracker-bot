from typing import Optional

from app.models.transaction import Transaction


def amount_prompt() -> str:
    return "💰 <b>How much did you spend?</b>\n\nEnter the amount:"


def amount_invalid() -> str:
    return "⚠️ Please enter a valid positive number.\n\nExample: <b>1500</b> or <b>9.99</b>"


def category_prompt(amount: str) -> str:
    return f"💰 Amount: <b>{amount}</b>\n\n📂 <b>Select a category:</b>"


def comment_prompt(amount: str, category_label: str) -> str:
    return (
        f"💰 Amount: <b>{amount}</b>\n"
        f"📂 Category: <b>{category_label}</b>\n\n"
        "💬 <b>Add a comment:</b>"
    )


def confirm_text(amount: str, category_label: str, comment: Optional[str]) -> str:
    lines = [
        f"💰 Amount: <b>{amount}</b>",
        f"📂 Category: <b>{category_label}</b>",
    ]
    if comment:
        lines.append(f"💬 Comment: <b>{comment}</b>")
    lines.append("\nReady to save?")
    return "\n".join(lines)


def success_text(transaction: Transaction, category_label: str) -> str:
    comment_line = f"\n💬 {transaction.comment}" if transaction.comment else ""
    return (
        f"✅ <b>Transaction saved!</b>\n\n"
        f"💰 Amount: <b>{transaction.amount}</b>\n"
        f"📂 Category: <b>{category_label}</b>"
        f"{comment_line}"
    )


def cancelled_text() -> str:
    return "❌ <b>Transaction cancelled.</b>"


def no_categories_text() -> str:
    return "📭 You have no categories yet.\n\nAdd one first with /add_category"
