from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.db import get_conn
from utils.groq_client import ask
from utils.charts import pie_chart
from .prompts import ACCOUNTANT


def register(app):

    async def audit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = str(update.effective_user.id)
        await update.message.reply_text("Running audit...")
        conn = get_conn()
        rows = conn.execute(
            "SELECT date, type, category, amount, description FROM transactions "
            "WHERE user_id=? AND date >= date('now','start of month') ORDER BY date", (uid,)
        ).fetchall()
        conn.close()

        if not rows:
            await update.message.reply_text("No transactions to audit this month.")
            return

        lines = "\n".join(
            f"{r['date']} | {r['type']:7} | {r['category']:12} | {r['amount']:>10.2f} | {r['description']}"
            for r in rows
        )
        analysis = ask(ACCOUNTANT, "Audit transactions. Produce P&L summary. Flag anomalies.", lines)

        expense_cats = {}
        for r in rows:
            if r["type"] == "expense":
                expense_cats[r["category"]] = expense_cats.get(r["category"], 0) + r["amount"]

        text = f"🔍 *Audit Report*\n\n{analysis}"
        if expense_cats:
            chart = pie_chart(list(expense_cats.keys()), list(expense_cats.values()), "Expense Breakdown")
            await update.message.reply_photo(photo=chart, caption=text, parse_mode="Markdown")
        else:
            await update.message.reply_text(text, parse_mode="Markdown")

    async def import_csv(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        # /importcsv date,type,category,amount,description
        if not ctx.args:
            await update.message.reply_text(
                "Usage: /importcsv <csv rows>\n"
                "Format: date,type,category,amount,description\n"
                "Example: /importcsv 2026-04-01,expense,food,15000,lunch"
            )
            return
        uid = str(update.effective_user.id)
        raw = " ".join(ctx.args)
        lines = raw.split("|")
        imported, errors = 0, []
        conn = get_conn()
        for i, line in enumerate(lines, 1):
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 4:
                errors.append(f"Row {i}: too few columns")
                continue
            date_str, tx_type, category, amount_str = parts[0], parts[1], parts[2], parts[3]
            desc = parts[4] if len(parts) > 4 else ""
            if tx_type not in ("income", "expense"):
                errors.append(f"Row {i}: invalid type")
                continue
            try:
                amount = float(amount_str.replace(",", ""))
                conn.execute(
                    "INSERT INTO transactions (user_id, date, amount, category, description, type) VALUES (?,?,?,?,?,?)",
                    (uid, date_str, amount, category.lower(), desc, tx_type)
                )
                imported += 1
            except ValueError:
                errors.append(f"Row {i}: invalid amount")
        conn.commit()
        conn.close()
        msg = f"Imported *{imported}* transactions."
        if errors:
            msg += "\nErrors:\n" + "\n".join(errors)
        await update.message.reply_text(msg, parse_mode="Markdown")

    app.add_handler(CommandHandler("audit", audit))
    app.add_handler(CommandHandler("importcsv", import_csv))
