from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.groq_client import ask
from .prompts import CREDIT_ANALYST


def register(app):

    async def credit_check(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if len(ctx.args) < 4:
            await update.message.reply_text(
                "Usage: /creditcheck <monthly_income> <monthly_debt> <loan_amount> <purpose>\n"
                "Example: /creditcheck 3000000 500000 10000000 car"
            )
            return
        try:
            income = float(ctx.args[0].replace(",", ""))
            debt = float(ctx.args[1].replace(",", ""))
            loan = float(ctx.args[2].replace(",", ""))
        except ValueError:
            await update.message.reply_text("Invalid numbers.")
            return
        purpose = " ".join(ctx.args[3:])
        dti = (debt / income * 100) if income else 0
        context = (
            f"Monthly Income: {income:,.2f}\nExisting Debt: {debt:,.2f}\n"
            f"DTI: {dti:.1f}%\nLoan Amount: {loan:,.2f}\nPurpose: {purpose}"
        )
        analysis = ask(CREDIT_ANALYST, "Assess creditworthiness. Calculate ratios. Give verdict.", context)
        emoji = "🔴" if dti > 43 else ("🟡" if dti > 36 else "🟢")
        await update.message.reply_text(
            f"{emoji} *Credit Analysis*\nDTI: `{dti:.1f}%`\n\n{analysis}", parse_mode="Markdown"
        )

    app.add_handler(CommandHandler("creditcheck", credit_check))
