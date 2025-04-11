import os
import json
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions, Message
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, CallbackQueryHandler, ChatMemberHandler
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

filters_data = {}

def schedule_deletion(message: Message, delay: int = 120):
    asyncio.create_task(delete_after_delay(message, delay))

async def delete_after_delay(message: Message, delay: int):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("Halo! Aku siap membantu menyimpan garapan kamu.")
    schedule_deletion(msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📝 Filters", callback_data="filters")],
        [InlineKeyboardButton("🔇 Mute Member", callback_data="mute")],
        [InlineKeyboardButton("🧹 Hapus Link", callback_data="hapus_link")],
        [InlineKeyboardButton("👋 Welcome Message", callback_data="welcome")],
        [InlineKeyboardButton("❌ Stop Filter", callback_data="stop")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = await update.message.reply_text("Silakan pilih menu:", reply_markup=reply_markup)
    schedule_deletion(msg)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    response_map = {
        "filters": "📝 Filters: Atur kata kunci dan balasan otomatis.",
        "mute": "🔇 Untuk mute member, gunakan perintah /mute <reply pada member>",
        "hapus_link": "🧹 Bot akan otomatis hapus link yang dikirim member.",
        "welcome": "👋 Bot akan mengirim pesan selamat datang setiap ada member baru.",
        "stop": "❌ Untuk hapus filter, gunakan perintah /stop <kata_kunci>"
    }

    if query.data in response_map:
        msg = await query.edit_message_text(response_map[query.data])
        schedule_deletion(msg)

async def filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        msg = await update.message.reply_text("Format: /filter <kata_kunci> <balasan>")
        schedule_deletion(msg)
        return
    keyword = args[0].lower()
    response = update.message.text.split(None, 2)[2]  # Ambil seluruh teks setelah keyword
    filters_data[keyword] = response
    msg = await update.message.reply_text(f"Filter untuk '{keyword}' disimpan!")
    schedule_deletion(msg)

async def stop_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        msg = await update.message.reply_text("Format: /stop <kata_kunci>")
        schedule_deletion(msg)
        return
    keyword = args[0].lower()
    if keyword in filters_data:
        del filters_data[keyword]
        msg = await update.message.reply_text(f"Filter '{keyword}' dihapus!")
    else:
        msg = await update.message.reply_text(f"Filter '{keyword}' tidak ditemukan.")
    schedule_deletion(msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.lower()
    for keyword, response in filters_data.items():
        if keyword in text:
            msg = await update.message.reply_text(response, parse_mode="HTML", disable_web_page_preview=True)
            schedule_deletion(msg)
            break

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.chat_member.new_chat_member.status == "member":
        user_name = update.chat_member.new_chat_member.user.first_name
        message = f"Selamat datang <b>{user_name}</b> di Airdroprs IND, semoga kita bisa jepe bersama!!!"
        msg = await context.bot.send_message(
            chat_id=update.chat_member.chat.id,
            text=message,
            parse_mode="HTML"
        )
        schedule_deletion(msg)

async def mute_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        member = update.message.reply_to_message.from_user
        try:
            await context.bot.restrict_chat_member(
                chat_id=update.effective_chat.id,
                user_id=member.id,
                permissions=ChatPermissions(can_send_messages=False)
            )
            msg = await update.message.reply_text(f"🔇 {member.mention_html()} telah di-mute.", parse_mode="HTML")
        except Exception as e:
            msg = await update.message.reply_text(f"Gagal mute member: {e}")
    else:
        msg = await update.message.reply_text("Balas pesan member yang ingin di-mute dengan /mute")
    schedule_deletion(msg)

async def delete_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and ("http://" in update.message.text or "https://" in update.message.text):
        try:
            await update.message.delete()
        except Exception as e:
            print(f"Gagal menghapus pesan berisi link: {e}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(CommandHandler("filter", filter_command))
    app.add_handler(CommandHandler("stop", stop_filter))
    app.add_handler(CommandHandler("mute", mute_member))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, delete_links))
    app.add_handler(ChatMemberHandler(welcome, ChatMemberHandler.CHAT_MEMBER))

    print("Bot berjalan...")
    app.run_polling()

