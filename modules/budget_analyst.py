from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.db import get_conn
from utils.groq_client import ask
from utils.charts import grouped_bar_chart
from .prompts import BUDGET_ANALYST


def register(app):

    async def set_budget(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if len(ctx.args) < 2:
            await update.message.reply_text("Usage: /setbudget <category> <monthly_limit>\nExample: /setbudget food 200000")
            return
        category, limit_str = ctx.args[0], ctx.args[1]
        try:
            limit = float(limit_str.replace(",", ""))
        except ValueError:
            await update.message.reply_text("Invalid amount.")
            return
        uid = str(update.effective_user.id)
        conn = get_conn()
        conn.execute(
            "INSERT INTO budgets (user_id, category, monthly_limit) VALUES (?,?,?) "
            "ON CONFLICT(user_id, category) DO UPDATE SET monthly_limit=excluded.monthly_limit",
            (uid, category.lower(), limit)
        )
        conn.commit()
        conn.close()
        await update.message.reply_text(f"Budget set: *{category}* = `{limit:,.2f}/month`", parse_mode="Markdown")

    async def budget(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = str(update.effective_user.id)
        await update.message.reply_text("Generating budget report...")
        conn = get_conn()
        budgets = {r["category"]: r["monthly_limit"] for r in
                   conn.execute("SELECT category, monthly_limit FROM budgets WHERE user_id=?", (uid,)).fetchall()}
        actuals_rows = conn.execute(
            "SELECT category, SUM(amount) as total FROM transactions "
            "WHERE user_id=? AND type='expense' AND date >= date('now','start of month') GROUP BY category", (uid,)
        ).fetchall()
        conn.close()

        if not budgets:
            await update.message.reply_text("No budgets set. Use /setbudget food 200000")
            return

        actuals = {r["category"]: r["total"] for r in actuals_rows}
        lines, cats, budget_vals, actual_vals = [], [], [], []

        for cat, limit in budgets.items():
            actual = actuals.get(cat, 0)
            pct = (actual / limit * 100) if limit else 0
            status = "OVER" if actual > limit else "OK"
            lines.append(f"{cat}: {actual:,.0f}/{limit:,.0f} ({pct:.0f}%) [{status}]")
            cats.append(cat)
            budget_vals.append(limit)
            actual_vals.append(actual)

        context = "\n".join(lines)
        analysis = ask(BUDGET_ANALYST, "Analyze budget vs actuals. Variance report and forecast.", context)
        text = f"📊 *Budget Report*\n```\n{context}\n```\n\n{analysis}"
        chart = grouped_bar_chart(cats, budget_vals, actual_vals, "Budget", "Actual", "Budget vs Actuals")
        await update.message.reply_photo(photo=chart, caption=text, parse_mode="Markdown")

    app.add_handler(CommandHandler("setbudget", set_budget))
    app.add_handler(CommandHandler("budget", budget))
