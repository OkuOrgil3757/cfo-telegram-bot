from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.db import get_conn
from utils.groq_client import ask
from .prompts import FINANCIAL_ADVISOR


def register(app):

    async def advise(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        question = " ".join(ctx.args)
        if not question:
            await update.message.reply_text("Usage: /advise <your question>\nExample: /advise should I invest in index funds or save in cash?")
            return
        uid = str(update.effective_user.id)
        conn = get_conn()
        rows = conn.execute(
            "SELECT type, SUM(amount) as total FROM transactions WHERE user_id=? "
            "AND date >= date('now','-30 days') GROUP BY type", (uid,)
        ).fetchall()
        conn.close()
        context = "\n".join(f"{r['type']}: {r['total']:.2f}" for r in rows) if rows else "No transaction history."
        analysis = ask(FINANCIAL_ADVISOR, question, context)
        await update.message.reply_text(f"🎯 *Financial Advisor*\n\n{analysis}", parse_mode="Markdown")

    async def on_track(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if len(ctx.args) < 3:
            await update.message.reply_text(
                "Usage: /ontrack <monthly_income> <savings_goal_%> <retirement_age>\n"
                "Example: /ontrack 3000000 20 60"
            )
            return
        try:
            income = float(ctx.args[0].replace(",", ""))
            goal_pct = float(ctx.args[1])
            retire_age = int(ctx.args[2])
        except ValueError:
            await update.message.reply_text("Invalid values.")
            return
        uid = str(update.effective_user.id)
        conn = get_conn()
        row = conn.execute(
            "SELECT SUM(amount) as total FROM transactions WHERE user_id=? AND type='expense' "
            "AND date >= date('now','start of month')", (uid,)
        ).fetchone()
        conn.close()
        expenses = row["total"] or 0
        savings = income - expenses
        actual_rate = (savings / income * 100) if income else 0
        target = income * goal_pct / 100
        context = (
            f"Income: {income:,.2f} | Expenses: {expenses:,.2f} | Savings: {savings:,.2f} ({actual_rate:.1f}%)\n"
            f"Target savings rate: {goal_pct}% = {target:,.2f}/month | Retirement age: {retire_age}"
        )
        analysis = ask(FINANCIAL_ADVISOR, "Am I on track? What adjustments needed?", context)
        emoji = "✅" if actual_rate >= goal_pct else "❌"
        await update.message.reply_text(
            f"{emoji} *On Track Check*\nSavings rate: `{actual_rate:.1f}%` (target: {goal_pct}%)\n\n{analysis}",
            parse_mode="Markdown"
        )

    app.add_handler(CommandHandler("advise", advise))
    app.add_handler(CommandHandler("ontrack", on_track))
