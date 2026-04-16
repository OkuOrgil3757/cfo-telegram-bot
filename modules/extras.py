import urllib.request
import json
from datetime import date
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.db import get_conn


# ── /split ────────────────────────────────────────────────────────────────────

async def split(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    /split <total> <person1> <person2> ...
    /split <total> <N>          ← split equally among N people
    Examples:
      /split 90000 alice bob charlie
      /split 120000 4
    """
    if len(ctx.args) < 2:
        await update.message.reply_text(
            "Usage:\n"
            "  `/split <total> <person1> <person2> ...`\n"
            "  `/split <total> <N>`\n\n"
            "Examples:\n"
            "  `/split 90000 Alice Bob Charlie`\n"
            "  `/split 120000 4`",
            parse_mode="Markdown"
        )
        return

    try:
        total = float(ctx.args[0].replace(",", ""))
    except ValueError:
        await update.message.reply_text("Invalid total amount.")
        return

    rest = ctx.args[1:]

    # If single number → split N ways
    if len(rest) == 1 and rest[0].isdigit():
        n = int(rest[0])
        if n < 2:
            await update.message.reply_text("Need at least 2 people.")
            return
        per_person = total / n
        lines = [f"  Person {i+1}: `{per_person:,.0f}`" for i in range(n)]
        names_label = f"{n} people"
    else:
        names = rest
        per_person = total / len(names)
        lines = [f"  {name.capitalize()}: `{per_person:,.0f}`" for name in names]
        names_label = ", ".join(n.capitalize() for n in names)

    await update.message.reply_text(
        f"🍽️ *Bill Split*\n"
        f"Total: `{total:,.0f}` ÷ {len(lines)}\n\n"
        + "\n".join(lines) +
        f"\n\nEach person pays: *{per_person:,.0f}*",
        parse_mode="Markdown"
    )


# ── /fx ───────────────────────────────────────────────────────────────────────

async def fx(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    /fx <amount> <FROM> <TO>
    Example: /fx 100 USD MNT
    """
    if len(ctx.args) < 3:
        await update.message.reply_text(
            "Usage: `/fx <amount> <FROM> <TO>`\n"
            "Example: `/fx 100 USD MNT`",
            parse_mode="Markdown"
        )
        return

    try:
        amount = float(ctx.args[0].replace(",", ""))
    except ValueError:
        await update.message.reply_text("Invalid amount.")
        return

    from_cur = ctx.args[1].upper()
    to_cur = ctx.args[2].upper()

    await update.message.chat.send_action("typing")
    try:
        url = f"https://open.er-api.com/v6/latest/{from_cur}"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())

        if data.get("result") != "success":
            await update.message.reply_text(f"Unknown currency: {from_cur}")
            return

        rates = data["rates"]
        if to_cur not in rates:
            await update.message.reply_text(f"Unknown currency: {to_cur}")
            return

        rate = rates[to_cur]
        converted = amount * rate

        await update.message.reply_text(
            f"💱 *Currency Converter*\n\n"
            f"`{amount:,.2f} {from_cur}` = *{converted:,.2f} {to_cur}*\n\n"
            f"Rate: 1 {from_cur} = {rate:,.4f} {to_cur}",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"Could not fetch exchange rate: {e}")


# ── /setgoal & /goalstatus ────────────────────────────────────────────────────

def _progress_bar(current, target, width=20):
    pct = min(current / target, 1.0) if target else 0
    filled = int(width * pct)
    bar = "█" * filled + "░" * (width - filled)
    return bar, pct * 100


async def setgoal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    /setgoal <name> <target_amount>
    Example: /setgoal MacBook 3000000
    """
    if len(ctx.args) < 2:
        await update.message.reply_text(
            "Usage: `/setgoal <name> <target_amount>`\n"
            "Example: `/setgoal MacBook 3000000`",
            parse_mode="Markdown"
        )
        return
    name = ctx.args[0]
    try:
        target = float(ctx.args[1].replace(",", ""))
    except ValueError:
        await update.message.reply_text("Invalid amount.")
        return

    uid = str(update.effective_user.id)
    conn = get_conn()
    conn.execute(
        "INSERT INTO goals (user_id, name, target, saved, created_date) VALUES (?,?,?,0,?) "
        "ON CONFLICT(user_id, name) DO UPDATE SET target=excluded.target",
        (uid, name, target, date.today().isoformat())
    )
    conn.commit()
    conn.close()
    await update.message.reply_text(
        f"🎯 Goal set: *{name}* — target `{target:,.0f}`\n"
        f"Use `/saveto {name} <amount>` to log progress.",
        parse_mode="Markdown"
    )


async def saveto(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    /saveto <goal_name> <amount>
    Example: /saveto MacBook 200000
    """
    if len(ctx.args) < 2:
        await update.message.reply_text(
            "Usage: `/saveto <goal_name> <amount>`\n"
            "Example: `/saveto MacBook 200000`",
            parse_mode="Markdown"
        )
        return
    name = ctx.args[0]
    try:
        amount = float(ctx.args[1].replace(",", ""))
    except ValueError:
        await update.message.reply_text("Invalid amount.")
        return

    uid = str(update.effective_user.id)
    conn = get_conn()
    row = conn.execute(
        "SELECT id, saved, target FROM goals WHERE user_id=? AND name=?", (uid, name)
    ).fetchone()
    if not row:
        await update.message.reply_text(f"Goal '{name}' not found. Create it with /setgoal.")
        conn.close()
        return
    new_saved = row["saved"] + amount
    conn.execute("UPDATE goals SET saved=? WHERE id=?", (new_saved, row["id"]))
    conn.commit()
    conn.close()

    bar, pct = _progress_bar(new_saved, row["target"])
    done = " — *GOAL REACHED!* 🎉" if new_saved >= row["target"] else ""
    await update.message.reply_text(
        f"💰 Saved *+{amount:,.0f}* toward *{name}*\n\n"
        f"`{bar}` {pct:.1f}%\n"
        f"{new_saved:,.0f} / {row['target']:,.0f}{done}",
        parse_mode="Markdown"
    )


async def goalstatus(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    /goalstatus — show all active savings goals with progress bars
    """
    uid = str(update.effective_user.id)
    conn = get_conn()
    rows = conn.execute(
        "SELECT name, target, saved, created_date FROM goals WHERE user_id=? ORDER BY created_date",
        (uid,)
    ).fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text(
            "No goals yet. Use `/setgoal <name> <amount>` to create one.",
            parse_mode="Markdown"
        )
        return

    lines = []
    for r in rows:
        bar, pct = _progress_bar(r["saved"], r["target"])
        remaining = max(r["target"] - r["saved"], 0)
        status = "✅" if r["saved"] >= r["target"] else "🎯"
        lines.append(
            f"{status} *{r['name']}*\n"
            f"`{bar}` {pct:.1f}%\n"
            f"{r['saved']:,.0f} / {r['target']:,.0f}  (need {remaining:,.0f} more)"
        )

    await update.message.reply_text(
        "🎯 *Savings Goals*\n\n" + "\n\n".join(lines),
        parse_mode="Markdown"
    )


# ── register ──────────────────────────────────────────────────────────────────

def register(app):
    app.add_handler(CommandHandler("split", split))
    app.add_handler(CommandHandler("fx", fx))
    app.add_handler(CommandHandler("setgoal", setgoal))
    app.add_handler(CommandHandler("saveto", saveto))
    app.add_handler(CommandHandler("goalstatus", goalstatus))
