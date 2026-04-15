from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.groq_client import ask
from .prompts import LOAN_OFFICER


def calc_loan(principal, annual_rate, months):
    r = annual_rate / 100 / 12
    if r == 0:
        monthly = principal / months
    else:
        monthly = principal * r * (1 + r) ** months / ((1 + r) ** months - 1)
    total = monthly * months
    interest = total - principal
    return monthly, total, interest


def register(app):

    async def loan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if len(ctx.args) < 3:
            await update.message.reply_text(
                "Usage: /loan <principal> <annual_rate%> <years>\n"
                "Example: /loan 10000000 12 5"
            )
            return
        try:
            principal = float(ctx.args[0].replace(",", ""))
            rate = float(ctx.args[1])
            years = int(ctx.args[2])
        except ValueError:
            await update.message.reply_text("Invalid values.")
            return
        monthly, total, interest = calc_loan(principal, rate, years * 12)
        context = (
            f"Principal: {principal:,.2f} | Rate: {rate}% | Term: {years} years\n"
            f"Monthly: {monthly:,.2f} | Total: {total:,.2f} | Interest: {interest:,.2f}"
        )
        advice = ask(LOAN_OFFICER, "Give advice on this loan. Good deal? Watch out for?", context)
        await update.message.reply_text(
            f"🏦 *Loan Analysis*\n"
            f"Monthly: `{monthly:,.2f}`\n"
            f"Total Cost: `{total:,.2f}`\n"
            f"Total Interest: `{interest:,.2f}`\n\n{advice}",
            parse_mode="Markdown"
        )

    async def compare_loans(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if len(ctx.args) < 6:
            await update.message.reply_text(
                "Usage: /compareloans <p1> <r1> <y1> <p2> <r2> <y2>\n"
                "Example: /compareloans 10000000 12 5 10000000 10 7"
            )
            return
        try:
            p1, r1, y1 = float(ctx.args[0]), float(ctx.args[1]), int(ctx.args[2])
            p2, r2, y2 = float(ctx.args[3]), float(ctx.args[4]), int(ctx.args[5])
        except ValueError:
            await update.message.reply_text("Invalid values.")
            return
        m1, t1, i1 = calc_loan(p1, r1, y1 * 12)
        m2, t2, i2 = calc_loan(p2, r2, y2 * 12)
        context = (
            f"Loan A: {p1:,.0f} @ {r1}% {y1}y → monthly={m1:,.2f}, total={t1:,.2f}, interest={i1:,.2f}\n"
            f"Loan B: {p2:,.0f} @ {r2}% {y2}y → monthly={m2:,.2f}, total={t2:,.2f}, interest={i2:,.2f}"
        )
        advice = ask(LOAN_OFFICER, "Compare these two loans. Which is better and why?", context)
        await update.message.reply_text(
            f"⚖️ *Loan Comparison*\n"
            f"Loan A: `{m1:,.2f}/mo` | Total `{t1:,.2f}`\n"
            f"Loan B: `{m2:,.2f}/mo` | Total `{t2:,.2f}`\n\n{advice}",
            parse_mode="Markdown"
        )

    app.add_handler(CommandHandler("loan", loan))
    app.add_handler(CommandHandler("compareloans", compare_loans))
