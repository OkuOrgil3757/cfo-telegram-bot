from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters
from utils.db import get_conn
from utils.groq_client import ask
from utils.charts import bar_chart
from .prompts import FINANCIAL_MANAGER
from datetime import date

WAITING_LOG = 1


def register(app):

    async def snapshot(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = str(update.effective_user.id)
        await update.message.reply_text("Analyzing your finances...")
        conn = get_conn()
        rows = conn.execute(
            "SELECT type, category, SUM(amount) as total FROM transactions "
            "WHERE user_id=? AND date >= date('now','start of month') GROUP BY type, category",
            (uid,)
        ).fetchall()
        conn.close()

        if not rows:
            await update.message.reply_text("No transactions yet.\nUse: /log expense food 15000 lunch")
            return

        income = sum(r["total"] for r in rows if r["type"] == "income")
        expenses = sum(r["total"] for r in rows if r["type"] == "expense")
        net = income - expenses

        context = f"Income={income:.2f}, Expenses={expenses:.2f}, Net={net:.2f}\n"
        context += "\n".join(f"{r['type']} | {r['category']}: {r['total']:.2f}" for r in rows)
        analysis = ask(FINANCIAL_MANAGER, "Give financial health snapshot and warnings.", context)

        text = (
            f"📊 *Financial Snapshot*\n"
            f"Income:   `{income:,.2f}`\n"
            f"Expenses: `{expenses:,.2f}`\n"
            f"Net:      `{net:,.2f}`\n\n"
            f"{analysis}"
        )

        cats = [r["category"] for r in rows if r["type"] == "expense"]
        vals = [r["total"] for r in rows if r["type"] == "expense"]
        if cats:
            chart = bar_chart(cats, vals, "This Month's Expenses")
            await update.message.reply_photo(photo=chart, caption=text, parse_mode="Markdown")
        else:
            await update.message.reply_text(text, parse_mode="Markdown")

    async def log_tx(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        # /log expense food 15000 lunch
        args = ctx.args
        if len(args) < 3:
            await update.message.reply_text(
                "Usage: /log <income|expense> <category> <amount> [description]\n"
                "Example: /log expense food 15000 lunch"
            )
            return
        tx_type, category, amount_str = args[0], args[1], args[2]
        description = " ".join(args[3:]) if len(args) > 3 else ""
        if tx_type not in ("income", "expense"):
            await update.message.reply_text("Type must be income or expense.")
            return
        try:
            amount = float(amount_str.replace(",", ""))
        except ValueError:
            await update.message.reply_text("Invalid amount.")
            return
        uid = str(update.effective_user.id)
        conn = get_conn()
        conn.execute(
            "INSERT INTO transactions (user_id, date, amount, category, description, type) VALUES (?,?,?,?,?,?)",
            (uid, date.today().isoformat(), amount, category.lower(), description, tx_type)
        )
        conn.commit()
        conn.close()
        await update.message.reply_text(
            f"Logged: *{tx_type}* `{amount:,.2f}` — {category}" + (f" ({description})" if description else ""),
            parse_mode="Markdown"
        )

    async def decide(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        question = " ".join(ctx.args)
        if not question:
            await update.message.reply_text("Usage: /decide <your financial question>")
            return
        uid = str(update.effective_user.id)
        conn = get_conn()
        rows = conn.execute(
            "SELECT type, SUM(amount) as total FROM transactions WHERE user_id=? "
            "AND date >= date('now','-30 days') GROUP BY type", (uid,)
        ).fetchall()
        conn.close()
        context = "\n".join(f"{r['type']}: {r['total']:.2f}" for r in rows) if rows else "No financial data."
        analysis = ask(FINANCIAL_MANAGER, question, context)
        await update.message.reply_text(f"💼 *CFO Analysis*\n\n{analysis}", parse_mode="Markdown")

    app.add_handler(CommandHandler("snapshot", snapshot))
    app.add_handler(CommandHandler("log", log_tx))
    app.add_handler(CommandHandler("decide", decide))
