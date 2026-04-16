from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
from dotenv import load_dotenv
from utils.groq_client import ask, ask_with_history
from utils.db import get_conn
import os

from utils.db import init_db
from modules import (
    financial_manager,
    accountant,
    budget_analyst,
    investment_analyst,
    risk_specialist,
    credit_analyst,
    financial_advisor,
    loan_officer,
    property_appraiser,
    credit_clerk,
    brainstormer,
    extras,
)

load_dotenv()


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📊 Snapshot", callback_data="cmd_snapshot"),
            InlineKeyboardButton("📋 History", callback_data="cmd_history"),
        ],
        [
            InlineKeyboardButton("📉 Budget", callback_data="cmd_budget"),
            InlineKeyboardButton("🔍 Audit", callback_data="cmd_audit"),
        ],
        [
            InlineKeyboardButton("📈 Invest", callback_data="cmd_invest"),
            InlineKeyboardButton("⚠️ Risk", callback_data="cmd_risk"),
        ],
        [
            InlineKeyboardButton("💱 FX Convert", callback_data="cmd_fx"),
            InlineKeyboardButton("🍽️ Bill Split", callback_data="cmd_split"),
        ],
        [
            InlineKeyboardButton("🎯 Goals", callback_data="cmd_goalstatus"),
            InlineKeyboardButton("💡 Brainstorm", callback_data="cmd_brainstorm"),
        ],
        [
            InlineKeyboardButton("📒 Ledger", callback_data="cmd_ledger"),
            InlineKeyboardButton("🏦 Loan Calc", callback_data="cmd_loan"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 *CFO Bot — Your Personal Financial Expert*\n\n"
        "I have 11 financial expert roles and 30+ commands.\n"
        "Tap a button below or just type any financial question.\n\n"
        "📊 /snapshot  📋 /history  /log  /decide\n"
        "🔍 /audit  /importcsv\n"
        "📉 /setbudget  /budget\n"
        "📈 /invest  /compare  /portfolioadd\n"
        "⚠️ /risk\n"
        "🏦 /creditcheck  /loan  /compareloans\n"
        "🎯 /advise  /ontrack\n"
        "🏠 /appraise\n"
        "📒 /owe  /owed  /settle  /ledger\n"
        "💡 /brainstorm  /income\\_ideas  /costcuts  /goals\n"
        "🆕 /split  /fx  /setgoal  /saveto  /goalstatus",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button taps — show usage hint for each command."""
    query = update.callback_query
    await query.answer()
    hints = {
        "cmd_snapshot": "📊 Send /snapshot to see your monthly financial health report.",
        "cmd_history":  "📋 Send /history or /history 20 to see your last transactions.",
        "cmd_budget":   "📉 Send /budget to see actuals vs budget.\nSet limits with /setbudget food 200000",
        "cmd_audit":    "🔍 Send /audit to run a full P&L audit with anomaly detection.",
        "cmd_invest":   "📈 Send /invest AAPL (or any ticker) for a research report.",
        "cmd_risk":     "⚠️ Send /risk to analyse your portfolio risk.\nOptional: /risk market crash 30%",
        "cmd_fx":       "💱 Send /fx 100 USD MNT to convert currencies.\nUses live exchange rates.",
        "cmd_split":    "🍽️ Send /split 90000 Alice Bob Charlie to split a bill.\nOr /split 90000 3 for equal split.",
        "cmd_goalstatus": "🎯 Send /goalstatus to see all savings goals.\nCreate one: /setgoal MacBook 3000000",
        "cmd_brainstorm": "💡 Send /brainstorm income or /brainstorm cuts for personalised ideas.",
        "cmd_ledger":   "📒 Send /ledger to see who owes you and who you owe.\n/owe Bob 50000  |  /owed Alice 20000",
        "cmd_loan":     "🏦 Send /loan 10000000 12 5 (principal rate years) for payment breakdown.",
    }
    text = hints.get(query.data, "Use the command directly in chat.")
    await query.edit_message_reply_markup(reply_markup=None)
    await query.message.reply_text(text)


SYSTEM_PROMPT = """You are a personal CFO bot — a financial expert with 10 roles:
Financial Manager, Accountant, Budget Analyst, Investment Analyst, Risk Specialist,
Credit Analyst, Financial Advisor, Loan Officer, Property Appraiser, Credit Clerk.

The user may send you raw data, questions, numbers, or financial situations in plain text.
Automatically detect what they need and respond as the right expert.
Be concise, use bullet points, give specific numbers and verdicts. No fluff."""

# per-user chat history (in memory, resets on restart)
chat_histories: dict[str, list] = {}


async def chat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    user_text = update.message.text

    # attach user's financial context from DB
    conn = get_conn()
    rows = conn.execute(
        "SELECT type, category, SUM(amount) as total FROM transactions "
        "WHERE user_id=? AND date >= date('now','-30 days') GROUP BY type, category", (uid,)
    ).fetchall()
    budgets = conn.execute("SELECT category, monthly_limit FROM budgets WHERE user_id=?", (uid,)).fetchall()
    conn.close()

    db_context = ""
    if rows:
        db_context += "User's last 30 days transactions:\n"
        db_context += "\n".join(f"  {r['type']} | {r['category']}: {r['total']:.2f}" for r in rows)
    if budgets:
        db_context += "\nUser's budgets:\n"
        db_context += "\n".join(f"  {b['category']}: {b['monthly_limit']:.2f}/month" for b in budgets)

    # maintain last 10 messages of history
    if uid not in chat_histories:
        chat_histories[uid] = []
    chat_histories[uid].append({"role": "user", "content": user_text})
    if len(chat_histories[uid]) > 20:
        chat_histories[uid] = chat_histories[uid][-20:]

    await update.message.chat.send_action("typing")

    system = SYSTEM_PROMPT + (f"\n\n{db_context}" if db_context else "")
    reply = ask_with_history(system, chat_histories[uid])
    chat_histories[uid].append({"role": "assistant", "content": reply})

    await update.message.reply_text(reply)


def main():
    init_db()
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_TOKEN environment variable is not set")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))

    financial_manager.register(app)
    accountant.register(app)
    budget_analyst.register(app)
    investment_analyst.register(app)
    risk_specialist.register(app)
    credit_analyst.register(app)
    financial_advisor.register(app)
    loan_officer.register(app)
    property_appraiser.register(app)
    credit_clerk.register(app)
    brainstormer.register(app)
    extras.register(app)

    # inline keyboard button taps
    app.add_handler(CallbackQueryHandler(button_handler))

    # free-text AI chat — catches any plain message that isn't a command
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("CFO Telegram Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
