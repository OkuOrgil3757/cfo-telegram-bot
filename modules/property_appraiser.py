from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.groq_client import ask
from .prompts import PROPERTY_APPRAISER


def register(app):

    async def appraise(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if len(ctx.args) < 2:
            await update.message.reply_text(
                "Usage: /appraise <type> <description>\n"
                "Types: real_estate, business, vehicle, other\n"
                "Example: /appraise real_estate 2BR apartment Ulaanbaatar 80sqm built 2015"
            )
            return
        asset_type = ctx.args[0]
        description = " ".join(ctx.args[1:])
        analysis = ask(
            PROPERTY_APPRAISER,
            "Estimate value. Give low/mid/high range. State assumptions.",
            f"Asset: {asset_type}\nDescription: {description}"
        )
        await update.message.reply_text(f"🏠 *Appraisal: {asset_type}*\n\n{analysis}", parse_mode="Markdown")

    app.add_handler(CommandHandler("appraise", appraise))
