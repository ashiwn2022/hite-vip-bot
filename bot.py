from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
import sqlite3

BOT_TOKEN="8902339331:AAH_hgZTGV4HpdJagumzc_ZCM0FrFz9_Coc"
ADMIN_ID=2044820129
AFFILIATE_LINK="https://p.finance/en/register/?utm_campaign=45216&utm_source=affiliate&utm_medium=sr&a=8jZdQ2jXqwr5sG&al=1764115&ac=2026alphabravo26&cid=956645&code=YRP176"
VIP_LINK="https://t.me/+gYb1GUI1KGM3Y2Q0"

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
        [InlineKeyboardButton("Register", url=AFFILIATE_LINK)],
        [InlineKeyboardButton("Verify", callback_data="verify")]
    ]
    await update.message.reply_text(
        "Welcome 🎉\n\n1.Register using affiliate link\n2.Deposit $30+\n3.Click Verify",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    await q.answer()

    if q.data=="verify":
        context.user_data["await_uid"]=True
        await q.message.reply_text("Send your Pocket Option UID")

    elif q.data.startswith("approve_"):
        uid=q.data.split("_")[1]
        c.execute("UPDATE users SET status='approved' WHERE telegram_id=?",(uid,))
        db.commit()
        await context.bot.send_message(uid, f"✅ Approved!\nVIP access:\n{VIP_LINK}")
        await q.message.reply_text("Approved")

    elif q.data.startswith("reject_"):
        uid=q.data.split("_")[1]
        c.execute("UPDATE users SET status='rejected' WHERE telegram_id=?",(uid,))
        db.commit()
        await context.bot.send_message(uid, "❌ Verification rejected")
        await q.message.reply_text("Rejected")

async def receive_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("await_uid"):
        uid=update.message.text
        user=update.effective_user

        c.execute("INSERT OR REPLACE INTO users VALUES(?,?,?,?)",
                  (user.id,user.username,uid,"pending"))
        db.commit()

        kb=[[
            InlineKeyboardButton("✅ Approve",callback_data=f"approve_{user.id}"),
            InlineKeyboardButton("❌ Reject",callback_data=f"reject_{user.id}")
        ]]

        await context.bot.send_message(
            ADMIN_ID,
            f"New verification\n@{user.username}\nTG:{user.id}\nPocket UID:{uid}",
            reply_markup=InlineKeyboardMarkup(kb)
        )

        await update.message.reply_text("Verification sent to admin.")
        context.user_data["await_uid"]=False

async def pending(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID:return
    rows=c.execute("SELECT username,uid FROM users WHERE status='pending'").fetchall()
    msg="\n".join([f"@{r[0]} | {r[1]}" for r in rows]) or "No pending"
    await update.message.reply_text(msg)

app=Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("pending",pending))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,receive_uid))

app.run_polling()
