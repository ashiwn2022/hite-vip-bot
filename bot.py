from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
import sqlite3
import os

# ===== VARIABLES =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
AFFILIATE_LINK = os.getenv("AFFILIATE_LINK")
VIP_LINK = os.getenv("VIP_LINK")

# YOUR IMAGE URL
WELCOME_IMAGE="https://raw.githubusercontent.com/ashiwn2022/hite-vip-bot/main/YOUR%20UID.png"

# ===== DATABASE =====
db=sqlite3.connect("users.db", check_same_thread=False)
c=db.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users(
telegram_id INTEGER PRIMARY KEY,
username TEXT,
uid TEXT,
status TEXT
)
""")

db.commit()

# ===== BUTTON MENU =====
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Register",url=AFFILIATE_LINK)],
        [InlineKeyboardButton("✅ Verify",callback_data="verify")],
        [InlineKeyboardButton("💬 Contact Support",url="https://t.me/bitxtrading_official")]
    ])

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_photo(
        photo=WELCOME_IMAGE,

caption="""
🔥 WELCOME TO VIP ACCESS 🔥

Follow these steps carefully:

1️⃣ Register using our affiliate link

2️⃣ Deposit minimum 💵 $30

3️⃣ Click Verify

4️⃣ Send your Pocket Option UID

━━━━━━━━━━━━━━━

🎁 WHAT YOU GET:

🤖 Premium Trading Robot
📈 VIP Signals
💎 Exclusive Access
🚀 Special Content

━━━━━━━━━━━━━━━

Need help?

💬 @bitxtrading_official
""",
reply_markup=main_menu()
)

# ===== BUTTONS =====
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    # VERIFY BUTTON
    if q.data=="verify":

        context.user_data["await_uid"]=True

        await q.message.reply_text(
            "📝 Send your Pocket Option UID"
        )

    # APPROVE
    elif q.data.startswith("approve_"):

        uid=q.data.split("_")[1]

        c.execute(
            "UPDATE users SET status='approved' WHERE telegram_id=?",
            (uid,)
        )

        db.commit()

        await context.bot.send_message(
            uid,
            f"""
🎉 CONGRATULATIONS 🎉

Your account has been approved ✅

Welcome to our VIP community 🚀

🎁 Access below:

{VIP_LINK}

Good luck and happy trading 📈🔥
"""
        )

        await q.message.reply_text(
            "✅ User approved"
        )

    # REJECT
    elif q.data.startswith("reject_"):

        uid=q.data.split("_")[1]

        c.execute(
            "UPDATE users SET status='rejected' WHERE telegram_id=?",
            (uid,)
        )

        db.commit()

        kb=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🚀 Done Registering",
                callback_data="verify"
            )]
        ])

        await context.bot.send_message(
            uid,
            """
❌ Verification Failed

We couldn't find your account in our system.

Please register using our affiliate link and try again.

Need help?

💬 @bitxtrading_official
""",
reply_markup=kb
        )

        await q.message.reply_text(
            "❌ User rejected"
        )

    # DEPOSIT ISSUE
    elif q.data.startswith("deposit_"):

        uid=q.data.split("_")[1]

        kb=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "✅ Done",
                callback_data="verify"
            )]
        ])

        await context.bot.send_message(
            uid,
            """
💰 Registration Completed

We found your account ✅

Deposit minimum $30 to unlock VIP access 🚀

After depositing click DONE and verify again.

Need help?

💬 @bitxtrading_official
""",
reply_markup=kb
        )

        await q.message.reply_text(
            "💰 Deposit issue sent"
        )

# ===== RECEIVE UID =====
async def receive_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if context.user_data.get("await_uid"):

        uid=update.message.text

        user=update.effective_user

        c.execute(
            "INSERT OR REPLACE INTO users VALUES(?,?,?,?)",
            (
                user.id,
                user.username,
                uid,
                "pending"
            )
        )

        db.commit()

        kb=[

            [
            InlineKeyboardButton(
                "✅ Approve",
                callback_data=f"approve_{user.id}"
            ),

            InlineKeyboardButton(
                "❌ Reject",
                callback_data=f"reject_{user.id}"
            )
            ],

            [
            InlineKeyboardButton(
                "💰 Deposit Issue",
                callback_data=f"deposit_{user.id}"
            )
            ]

        ]

        await context.bot.send_message(

            ADMIN_ID,

            f"""
🔥 New Verification Request

👤 User:
@{user.username}

🆔 Telegram:
{user.id}

💳 Pocket UID:
{uid}
""",

reply_markup=InlineKeyboardMarkup(kb)

)

        await update.message.reply_text(
            """
⏳ Verification submitted

Our team will review your account shortly 🚀
"""
        )

        context.user_data["await_uid"]=False

# ===== PENDING =====
async def pending(update:Update,context:ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id!=ADMIN_ID:
        return

    rows=c.execute(
        "SELECT username,uid FROM users WHERE status='pending'"
    ).fetchall()

    msg="\n".join(
        [f"@{r[0]} | {r[1]}" for r in rows]
    )

    if not msg:
        msg="No pending users"

    await update.message.reply_text(msg)

# ===== APP =====
app=Application.builder().token(BOT_TOKEN).build()

app.add_handler(
    CommandHandler("start",start)
)

app.add_handler(
    CommandHandler("pending",pending)
)

app.add_handler(
    CallbackQueryHandler(buttons)
)

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        receive_uid
    )
)

print("Bot running...")

app.run_polling()
