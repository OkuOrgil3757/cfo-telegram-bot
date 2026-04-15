from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.db import get_conn
from utils.groq_client import ask
from .prompts import BRAINSTORMER


def register(app):

    async def brainstorm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        """
        /brainstorm <topic>
        Topic can be: income, savings, investments, business, cuts, goals, or any free text
        """
        topic = " ".join(ctx.args) if ctx.args else ""
        if not topic:
            await update.message.reply_text(
                "💡 *Brainstorm — Financial Ideas Generator*\n\n"
                "Usage: `/brainstorm <topic>`\n\n"
                "*Quick topics:*\n"
                "  `/brainstorm income` — new income stream ideas\n"
                "  `/brainstorm cuts` — where to cut spending\n"
                "  `/brainstorm invest` — investment opportunities\n"
                "  `/brainstorm business` — side business ideas\n"
                "  `/brainstorm savings` — ways to save more\n"
                "  `/brainstorm goals` — financial goal roadmap\n\n"
                "Or ask anything: `/brainstorm how to pay off debt faster`",
                parse_mode="Markdown"
            )
            return

        uid = str(update.effective_user.id)
        await update.message.chat.send_action("typing")

        # Pull user's financial context to personalise the ideas
        conn = get_conn()
        tx_rows = conn.execute(
            "SELECT type, category, SUM(amount) as total FROM transactions "
            "WHERE user_id=? AND date >= date('now','-30 days') GROUP BY type, category",
            (uid,)
        ).fetchall()
        budgets = conn.execute(
            "SELECT category, monthly_limit FROM budgets WHERE user_id=?", (uid,)
        ).fetchall()
        portfolio = conn.execute(
            "SELECT ticker, shares, avg_cost FROM portfolio WHERE user_id=?", (uid,)
        ).fetchall()
        conn.close()

        # Build context string
        context_parts = []
        if tx_rows:
            income = sum(r["total"] for r in tx_rows if r["type"] == "income")
            expenses = sum(r["total"] for r in tx_rows if r["type"] == "expense")
            context_parts.append(f"Last 30 days: income={income:,.0f}, expenses={expenses:,.0f}, net={income-expenses:,.0f}")
            expense_cats = ", ".join(
                f"{r['category']}={r['total']:,.0f}"
                for r in tx_rows if r["type"] == "expense"
            )
            if expense_cats:
                context_parts.append(f"Spending categories: {expense_cats}")
        if budgets:
            budget_str = ", ".join(f"{b['category']}={b['monthly_limit']:,.0f}" for b in budgets)
            context_parts.append(f"Monthly budgets: {budget_str}")
        if portfolio:
            port_str = ", ".join(f"{p['ticker']} ({p['shares']} shares)" for p in portfolio)
            context_parts.append(f"Portfolio: {port_str}")

        financial_context = "\n".join(context_parts) if context_parts else "No financial data on file yet."
        full_context = f"{financial_context}\n\nBrainstorm topic: {topic}"

        ideas = ask(BRAINSTORMER, topic, full_context)
        await update.message.reply_text(
            f"💡 *Brainstorm: {topic.title()}*\n\n{ideas}",
            parse_mode="Markdown"
        )

    async def brainstorm_income(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        """Shortcut: /income_ideas"""
        ctx.args = ["new income streams and side hustles"]
        await brainstorm(update, ctx)

    async def brainstorm_cuts(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        """Shortcut: /costcuts"""
        ctx.args = ["cuts — ways to reduce spending without hurting quality of life"]
        await brainstorm(update, ctx)

    async def brainstorm_goals(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        """Shortcut: /goals"""
        ctx.args = ["financial goals — a 3/6/12-month roadmap based on current finances"]
        await brainstorm(update, ctx)

    app.add_handler(CommandHandler("brainstorm", brainstorm))
    app.add_handler(CommandHandler("income_ideas", brainstorm_income))
    app.add_handler(CommandHandler("costcuts", brainstorm_cuts))
    app.add_handler(CommandHandler("goals", brainstorm_goals))
