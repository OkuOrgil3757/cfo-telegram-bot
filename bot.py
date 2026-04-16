from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
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
)

load_dotenv()


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *CFO Bot — Your Financial Expert*\n\n"
        "📊 *Financial Manager*\n"
        "  /snapshot — monthly health report\n"
        "  /log — log income or expense\n"
        "  /history — recent transactions\n"
        "  /decide — is this decision sound?\n\n"
        "🔍 *Accountant*\n"
        "  /audit — P&L + anomaly check\n"
        "  /importcsv — bulk import transactions\n\n"
        "📉 *Budget Analyst*\n"
        "  /setbudget — set category limit\n"
        "  /budget — actuals vs budget\n\n"
        "📈 *Investment Analyst*\n"
        "  /invest — stock research report\n"
        "  /compare — compare two stocks\n"
        "  /portfolioadd — add position\n\n"
        "⚠️ *Risk Specialist*\n"
        "  /risk — portfolio risk analysis\n\n"
        "🏦 *Credit & Loans*\n"
        "  /creditcheck — creditworthiness\n"
        "  /loan — payment & amortization\n"
        "  /compareloans — compare two loans\n\n"
        "🎯 *Financial Advisor*\n"
        "  /advise — holistic advice\n"
        "  /ontrack — savings rate check\n\n"
        "🏠 *Other*\n"
        "  /appraise — asset valuation\n"
        "  /owe /owed /settle /ledger — debt ledger\n\n"
        "💡 *Brainstorm*\n"
        "  /brainstorm <topic> — generate financial ideas\n"
        "  /income\\_ideas — new income streams\n"
        "  /costcuts — spending cuts\n"
        "  /goals — 3/6/12-month roadmap",
        parse_mode="Markdown"
    )


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

    # free-text AI chat — catches any plain message that isn't a command
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("CFO Telegram Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
