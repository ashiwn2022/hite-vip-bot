from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
import sqlite3
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
AFFILIATE_LINK = os.getenv("AFFILIATE_LINK")
VIP_LINK = os.getenv("VIP_LINK")

db=sqlite3.connect("users.db", check_same_thread=False)
c=db.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS users(
telegram_id INTEGER PRIMARY KEY,
username TEXT,
uid TEXT,
status TEXT
)""")
db.commit()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    kb=[
        [InlineKeyboardButton("🚀 Register Now", url=AFFILIATE_LINK)],
        [InlineKeyboardButton("✅ Verify Account", callback_data="verify")]
    ]

    await update.message.reply_text(
"""
🎯 Welcome To Premium VIP Access 🎯

Follow these simple steps:

1️⃣ Register using our affiliate link

2️⃣ Deposit minimum 💵 $30+

3️⃣ Click Verify and submit your UID

🔥 Complete the steps to unlock VIP access and your trading bot.

👇 Start below
""",
reply_markup=InlineKeyboardMarkup(kb)
)


async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    if q.data=="verify":

        context.user_data["await_uid"]=True

        await q.message.reply_text(
"""
📝 Send your Pocket Option UID below

Example:
123456789
"""
)

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
🎉🔥 CONGRATULATIONS 🔥🎉

✅ Verification Approved Successfully

🚀 Welcome to our VIP members area

You now have access to:

💎 Premium Signals
🤖 VIP Trading Bot
📈 Exclusive Content

👇 Access below:

{VIP_LINK}

Good luck and happy trading 🚀
"""
        )

        await q.message.reply_text(
            "✅ User Approved"
        )


    elif q.data.startswith("deposit_"):

        uid=q.data.split("_")[1]

        await context.bot.send_message(
uid,
"""
💰 Registration Completed Successfully 🎉

We found your account in our system ✅

⚠️ Final step remaining:

Deposit minimum 💵 $30

After depositing click Verify again and submit your UID.

Good luck 🚀
"""
        )

        await q.message.reply_text(
            "💰 Deposit reminder sent"
        )


    elif q.data.startswith("reject_"):

        uid=q.data.split("_")[1]

        c.execute(
            "UPDATE users SET status='rejected' WHERE telegram_id=?",
            (uid,)
        )
        db.commit()

        kb=[
            [
                InlineKeyboardButton(
                    "🔄 Verify Again",
                    callback_data="verify"
                )
            ]
        ]

        await context.bot.send_message(
uid,
"""
❌ Verification Failed

We couldn't find your account in our system.

📌 Please register using our official affiliate link to gain access.

After registering, click below and submit your UID again.
""",
reply_markup=InlineKeyboardMarkup(kb)
        )

        await q.message.reply_text(
            "❌ User Rejected"
        )


async def receive_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if context.user_data.get("await_uid"):

        uid=update.message.text
        user=update.effective_user

        c.execute(
            "INSERT OR REPLACE INTO users VALUES(?,?,?,?)",
            (user.id,user.username,uid,"pending")
        )

        db.commit()

        kb=[[
            InlineKeyboardButton(
                "✅ Approve",
                callback_data=f"approve_{user.id}"
            ),

            InlineKeyboardButton(
                "💰 Deposit Issue",
                callback_data=f"deposit_{user.id}"
            ),

            InlineKeyboardButton(
                "❌ Reject",
                callback_data=f"reject_{user.id}"
            )
        ]]

        await context.bot.send_message(
ADMIN_ID,
f"""
🔥 New Verification Request

👤 Username: @{user.username}

🆔 Telegram ID:
{user.id}

💹 Pocket UID:
{uid}
""",
reply_markup=InlineKeyboardMarkup(kb)
        )

        await update.message.reply_text(
"""
⏳ Verification request submitted successfully.

Our team will review your account shortly 🚀
"""
        )

        context.user_data["await_uid"]=False


async def pending(update:Update, context:ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id!=ADMIN_ID:
        return

    rows=c.execute(
        "SELECT username,uid FROM users WHERE status='pending'"
    ).fetchall()

    msg="\n".join(
        [f"👤 @{r[0]} | UID: {r[1]}" for r in rows]
    ) or "No pending requests"

    await update.message.reply_text(msg)


app=Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("pending",pending))

app.add_handler(
    CallbackQueryHandler(buttons)
)

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        receive_uid
    )
)

app.run_polling()
