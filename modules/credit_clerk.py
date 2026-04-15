from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.db import get_conn
from utils.groq_client import ask
from .prompts import CREDIT_CLERK
from datetime import date


def register(app):

    async def owe(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if len(ctx.args) < 2:
            await update.message.reply_text("Usage: /owe <person> <amount> [description] [due_date]\nExample: /owe Bilguun 50000 lunch 2026-04-20")
            return
        person, amount_str = ctx.args[0], ctx.args[1]
        desc = ctx.args[2] if len(ctx.args) > 2 else ""
        due = ctx.args[3] if len(ctx.args) > 3 else None
        try:
            amount = float(amount_str.replace(",", ""))
        except ValueError:
            await update.message.reply_text("Invalid amount.")
            return
        uid = str(update.effective_user.id)
        conn = get_conn()
        conn.execute(
            "INSERT INTO ledger (user_id, counterparty, amount, direction, description, due_date) VALUES (?,?,?,?,?,?)",
            (uid, person, amount, "owe", desc, due)
        )
        conn.commit()
        conn.close()
        await update.message.reply_text(f"Logged: You owe *{person}* `{amount:,.2f}`", parse_mode="Markdown")

    async def owed(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if len(ctx.args) < 2:
            await update.message.reply_text("Usage: /owed <person> <amount> [description] [due_date]")
            return
        person, amount_str = ctx.args[0], ctx.args[1]
        desc = ctx.args[2] if len(ctx.args) > 2 else ""
        due = ctx.args[3] if len(ctx.args) > 3 else None
        try:
            amount = float(amount_str.replace(",", ""))
        except ValueError:
            await update.message.reply_text("Invalid amount.")
            return
        uid = str(update.effective_user.id)
        conn = get_conn()
        conn.execute(
            "INSERT INTO ledger (user_id, counterparty, amount, direction, description, due_date) VALUES (?,?,?,?,?,?)",
            (uid, person, amount, "owed", desc, due)
        )
        conn.commit()
        conn.close()
        await update.message.reply_text(f"Logged: *{person}* owes you `{amount:,.2f}`", parse_mode="Markdown")

    async def settle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not ctx.args:
            await update.message.reply_text("Usage: /settle <person>")
            return
        person = ctx.args[0]
        uid = str(update.effective_user.id)
        conn = get_conn()
        conn.execute("UPDATE ledger SET settled=1 WHERE user_id=? AND counterparty=? AND settled=0", (uid, person))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"Settled all entries with *{person}*.", parse_mode="Markdown")

    async def ledger(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = str(update.effective_user.id)
        conn = get_conn()
        rows = conn.execute(
            "SELECT counterparty, direction, amount, description, due_date FROM ledger "
            "WHERE user_id=? AND settled=0 ORDER BY direction, counterparty", (uid,)
        ).fetchall()
        conn.close()

        if not rows:
            await update.message.reply_text("Ledger is clear. No outstanding amounts.")
            return

        you_owe = [r for r in rows if r["direction"] == "owe"]
        owed_to_you = [r for r in rows if r["direction"] == "owed"]
        lines = []
        if you_owe:
            lines.append("YOU OWE:")
            for r in you_owe:
                lines.append(f"  → {r['counterparty']}: {r['amount']:,.2f}" + (f" ({r['description']})" if r["description"] else "") + (f" due {r['due_date']}" if r["due_date"] else ""))
        if owed_to_you:
            lines.append("OWED TO YOU:")
            for r in owed_to_you:
                lines.append(f"  ← {r['counterparty']}: {r['amount']:,.2f}" + (f" ({r['description']})" if r["description"] else "") + (f" due {r['due_date']}" if r["due_date"] else ""))

        context = "\n".join(lines)
        summary = ask(CREDIT_CLERK, "Summarize ledger. Flag overdue items.", context)
        await update.message.reply_text(f"📒 *Ledger*\n```\n{context}\n```\n\n{summary}", parse_mode="Markdown")

    app.add_handler(CommandHandler("owe", owe))
    app.add_handler(CommandHandler("owed", owed))
    app.add_handler(CommandHandler("settle", settle))
    app.add_handler(CommandHandler("ledger", ledger))
