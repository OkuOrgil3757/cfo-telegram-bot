from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.db import get_conn
from utils.groq_client import ask
from utils.charts import line_chart
from .prompts import INVESTMENT_ANALYST
import yfinance as yf


def register(app):

    async def invest(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not ctx.args:
            await update.message.reply_text("Usage: /invest <TICKER>\nExample: /invest AAPL")
            return
        ticker = ctx.args[0].upper()
        await update.message.reply_text(f"Researching {ticker}...")
        try:
            t = yf.Ticker(ticker)
            info = t.info
            hist = t.history(period="3mo")
        except Exception as e:
            await update.message.reply_text(f"Could not fetch {ticker}: {e}")
            return

        price = info.get("currentPrice") or info.get("regularMarketPrice", "N/A")
        pe = info.get("trailingPE", "N/A")
        mktcap = info.get("marketCap", 0)
        name = info.get("longName", ticker)
        week52_high = info.get("fiftyTwoWeekHigh", "N/A")
        week52_low = info.get("fiftyTwoWeekLow", "N/A")

        context = (
            f"Ticker: {ticker} | Name: {name}\n"
            f"Price: {price} | P/E: {pe} | Mkt Cap: {mktcap:,}\n"
            f"52W High: {week52_high} | 52W Low: {week52_low}"
        )
        analysis = ask(INVESTMENT_ANALYST, "Write mini research report: valuation, growth, risks, verdict.", context)
        text = f"📈 *{name} ({ticker})*\nPrice: `{price}` | P/E: `{pe}`\n\n{analysis}"

        if not hist.empty:
            dates = [str(d.date()) for d in hist.index[-30:]]
            closes = list(hist["Close"].values[-30:])
            chart = line_chart(dates, closes, f"{ticker} — 30 Day Price", "Date", "Price")
            await update.message.reply_photo(photo=chart, caption=text, parse_mode="Markdown")
        else:
            await update.message.reply_text(text, parse_mode="Markdown")

    async def compare(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if len(ctx.args) < 2:
            await update.message.reply_text("Usage: /compare <TICKER1> <TICKER2>\nExample: /compare AAPL MSFT")
            return
        t1, t2 = ctx.args[0].upper(), ctx.args[1].upper()
        await update.message.reply_text(f"Comparing {t1} vs {t2}...")
        results = []
        for tk in [t1, t2]:
            try:
                info = yf.Ticker(tk).info
                results.append(
                    f"{tk}: Price={info.get('currentPrice','N/A')} P/E={info.get('trailingPE','N/A')} "
                    f"Sector={info.get('sector','N/A')}"
                )
            except Exception:
                results.append(f"{tk}: fetch failed")
        context = "\n".join(results)
        analysis = ask(INVESTMENT_ANALYST, "Compare these two. Which is better and why?", context)
        await update.message.reply_text(f"⚖️ *{t1} vs {t2}*\n\n{analysis}", parse_mode="Markdown")

    async def portfolio_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if len(ctx.args) < 3:
            await update.message.reply_text("Usage: /portfolioadd <TICKER> <shares> <avg_cost>\nExample: /portfolioadd AAPL 10 150.00")
            return
        ticker, shares_str, cost_str = ctx.args[0].upper(), ctx.args[1], ctx.args[2]
        try:
            shares, avg_cost = float(shares_str), float(cost_str)
        except ValueError:
            await update.message.reply_text("Invalid shares or cost.")
            return
        uid = str(update.effective_user.id)
        conn = get_conn()
        conn.execute(
            "INSERT INTO portfolio (user_id, ticker, shares, avg_cost) VALUES (?,?,?,?) "
            "ON CONFLICT(user_id, ticker) DO UPDATE SET shares=excluded.shares, avg_cost=excluded.avg_cost",
            (uid, ticker, shares, avg_cost)
        )
        conn.commit()
        conn.close()
        await update.message.reply_text(f"Portfolio updated: *{ticker}* — {shares} shares @ `{avg_cost:,.2f}`", parse_mode="Markdown")

    app.add_handler(CommandHandler("invest", invest))
    app.add_handler(CommandHandler("compare", compare))
    app.add_handler(CommandHandler("portfolioadd", portfolio_add))
