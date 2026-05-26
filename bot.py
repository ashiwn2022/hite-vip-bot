from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

import sqlite3
import os

# ================= CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
AFFILIATE_LINK = os.getenv("AFFILIATE_LINK")
VIP_LINK = os.getenv("VIP_LINK")

# ================= DATABASE =================

db = sqlite3.connect(
    "users.db",
    check_same_thread=False
)

c = db.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users(
telegram_id INTEGER PRIMARY KEY,
username TEXT,
uid TEXT,
status TEXT
)
""")

db.commit()

# ================= START =================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    kb = [
        [
            InlineKeyboardButton(
                "🚀 Register Now",
                url=AFFILIATE_LINK
            )
        ],

        [
            InlineKeyboardButton(
                "✅ Verify Account",
                callback_data="verify"
            )
        ]
    ]

    await update.message.reply_text(
"""
🎯 Welcome To VIP Access 🎯

Follow these steps:

1️⃣ Register using our link

2️⃣ Deposit minimum 💵 $30+

3️⃣ Click Verify

4️⃣ Submit your Pocket Option UID

🔥 Unlock:

🤖 Premium Trading Bot
📈 VIP Signals
💎 Exclusive Content

👇 Start below
""",
reply_markup=InlineKeyboardMarkup(kb)
)

# ================= BUTTONS =================

async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    q = update.callback_query
    await q.answer()

    # VERIFY

    if q.data == "verify":

        context.user_data["await_uid"] = True

        await q.message.reply_text(
"""
📝 Send your Pocket Option UID

Example:

123456789
"""
)

    # APPROVE

    elif q.data.startswith("approve_"):

        uid = q.data.split("_")[1]

        c.execute(
            "UPDATE users SET status='approved' WHERE telegram_id=?",
            (uid,)
        )

        db.commit()

        await context.bot.send_message(
uid,
f"""
🎉🔥 CONGRATULATIONS 🔥🎉

✅ Verification Approved

Welcome to VIP Access 🚀

You now unlocked:

🤖 Trading Bot
📈 VIP Signals
💎 Exclusive Content

👇 Join below:

{VIP_LINK}

Good luck 🚀💰
"""
)

        await q.message.reply_text(
            "✅ User approved"
        )

    # DEPOSIT ISSUE

    elif q.data.startswith("deposit_"):

        uid = q.data.split("_")[1]

        kb = [[
            InlineKeyboardButton(
                "🔄 Verify Again",
                callback_data="verify"
            )
        ]]

        await context.bot.send_message(
uid,
"""
💰 Registration Complete 🎉

We found your account successfully ✅

⚠️ Final step remaining:

Deposit minimum:

💵 $30

After completing the deposit:

Click below and submit your UID again.

🚀 You're one step away.
""",
reply_markup=InlineKeyboardMarkup(kb)
)

        await q.message.reply_text(
            "💰 Deposit reminder sent"
        )

    # REJECT

    elif q.data.startswith("reject_"):

        uid = q.data.split("_")[1]

        c.execute(
            "UPDATE users SET status='rejected' WHERE telegram_id=?",
            (uid,)
        )

        db.commit()

        kb = [[
            InlineKeyboardButton(
                "🔄 Verify Again",
                callback_data="verify"
            )
        ]]

        await context.bot.send_message(
uid,
"""
❌ Verification Failed

We couldn't find your account in our system.

📌 Please register using our official link.

Then click Verify Again and submit UID.
""",
reply_markup=InlineKeyboardMarkup(kb)
)

        await q.message.reply_text(
            "❌ User rejected"
        )

# ================= RECEIVE UID =================

async def receive_uid(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if context.user_data.get(
        "await_uid"
    ):

        uid = update.message.text

        user = update.effective_user

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

        kb = [[

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

        username = user.username

        if username is None:
            username = "No username"

        await context.bot.send_message(
ADMIN_ID,
f"""
🔥 NEW VERIFICATION REQUEST

👤 Username:
@{username}

🆔 Telegram ID:
{user.id}

💹 Pocket UID:
{uid}
""",
reply_markup=InlineKeyboardMarkup(kb)
)

        await update.message.reply_text(
"""
⏳ Verification submitted

Admin will review your account shortly 🚀
"""
)

        context.user_data[
            "await_uid"
        ] = False

# ================= PENDING =================

async def pending(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_user.id != ADMIN_ID:
        return

    rows = c.execute(
        """
        SELECT username,uid
        FROM users
        WHERE status='pending'
        """
    ).fetchall()

    msg = "\n".join(
        [
            f"👤 @{r[0]} | UID: {r[1]}"
            for r in rows
        ]
    )

    if msg == "":
        msg = "No pending users"

    await update.message.reply_text(
        msg
    )

# ================= RUN =================

app = Application.builder().token(
    BOT_TOKEN
).build()

app.add_handler(
    CommandHandler(
        "start",
        start
    )
)

app.add_handler(
    CommandHandler(
        "pending",
        pending
    )
)

app.add_handler(
    CallbackQueryHandler(
        buttons
    )
)

app.add_handler(
    MessageHandler(
        filters.TEXT &
        ~filters.COMMAND,
        receive_uid
    )
)

app.run_polling()
