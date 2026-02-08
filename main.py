import re
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

# Aceita TXID tipo ETH/BSC (0x + 64 hex) OU TRON (alfa-num longo)
TXID_REGEX = re.compile(r"^(0x[a-fA-F0-9]{64}|[A-Za-z0-9]{60,100})$")

START_TEXT = (
    "Hoş geldiniz.\n\n"
    "1) Ödemeyi yapın\n"
    "2) TXID'yi buraya gönderin\n\n"
    "TXID gönderildiğinde, yöneticiye iletilecektir."
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(START_TEXT)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (update.message.text or "").strip()
    user = update.effective_user

    if TXID_REGEX.match(msg):
        text = (
            "💰 NOVO TXID RECEBIDO\n\n"
            f"Nome: {user.full_name}\n"
            f"Username: @{user.username if user.username else 'sem'}\n"
            f"ID: {user.id}\n\n"
            f"TXID:\n{msg}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=text)
        await update.message.reply_text("✅ TXID recebido. Aguarde a verificação.")
    else:
        await update.message.reply_text("❌ Envie apenas o TXID (sem texto extra).")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
