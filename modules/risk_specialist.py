from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.db import get_conn
from utils.groq_client import ask
from .prompts import RISK_SPECIALIST
import yfinance as yf


def register(app):

    async def risk(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = str(update.effective_user.id)
        scenario = " ".join(ctx.args) if ctx.args else ""
        await update.message.reply_text("Analyzing portfolio risk...")
        conn = get_conn()
        positions = conn.execute(
            "SELECT ticker, shares, avg_cost FROM portfolio WHERE user_id=?", (uid,)
        ).fetchall()
        conn.close()

        if not positions:
            await update.message.reply_text("No portfolio. Use /portfolioadd AAPL 10 150")
            return

        lines = []
        total_value = 0
        for p in positions:
            try:
                info = yf.Ticker(p["ticker"]).info
                price = info.get("currentPrice") or p["avg_cost"]
                value = price * p["shares"]
                pnl = (price - p["avg_cost"]) * p["shares"]
                total_value += value
                lines.append(f"{p['ticker']}: {p['shares']} @ {price:.2f} = {value:,.2f} (P&L: {pnl:+,.2f})")
            except Exception:
                lines.append(f"{p['ticker']}: fetch failed")

        context = f"Portfolio (total ~{total_value:,.2f}):\n" + "\n".join(lines)
        if scenario:
            context += f"\nStress test: {scenario}"
        analysis = ask(RISK_SPECIALIST, "Analyze portfolio risk. Identify concentration, liquidity, market risks.", context)
        await update.message.reply_text(f"⚠️ *Risk Analysis*\nTotal: `{total_value:,.2f}`\n\n{analysis}", parse_mode="Markdown")

    app.add_handler(CommandHandler("risk", risk))
