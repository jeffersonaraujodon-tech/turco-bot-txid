import re
import os

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

# Aceita TXID tipo ETH/BSC (0x + 64 hex) OU TRON (alfa-num longo)
TXID_REGEX = re.compile(r"^(0x[a-fA-F0-9]{64}|[A-Za-z0-9]{60,100})$")


START_TEXT = (
    "Hoş geldiniz. 🇹🇷\n\n"
    "1) Ödemeyi yapın\n"
    "2) TXID'yi buraya gönderin\n\n"
    "TXID gönderildiğinde yöneticiye iletilecektir."
)

ASK_CONTACT_TEXT = (
    "✅ TXID alındı.\n\n"
    "📌 VIP grubuna eklenebilmeniz için **zorunlu** olarak:\n"
    "• Telegram kullanıcı adınızı (@username) yazın\n"
    "veya\n"
    "• Aşağıdaki butondan telefon numaranızı gönderin.\n\n"
    "⚠️ Bu bilgi olmadan VIP erişimi verilmeyecektir."
)

CONFIRM_INFO_TEXT = "✅ Bilgiler alındı. Yönetici kontrol edip sizi gruba ekleyecek."


def phone_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📞 Telefon numaramı gönder", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


async def post_init(app: Application):
    # Mata qualquer webhook antigo (evita “bot mudo” em alguns casos)
    await app.bot.delete_webhook(drop_pending_updates=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(START_TEXT)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (update.message.text or "").strip()
    user = update.effective_user
    user_id = user.id

    # 1) Recebe TXID
    if TXID_REGEX.match(msg):
        # Guarda o TXID para usar quando o usuário mandar contato/username
        context.user_data["txid"] = msg

        username_display = f"@{user.username}" if user.username else "yok (username yok)"
        text_to_admin = (
            "💰 YENİ TXID GELDİ\n\n"
            f"Ad: {user.full_name}\n"
            f"Username: {username_display}\n"
            f"ID: {user_id}\n\n"
            f"TXID:\n{msg}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=text_to_admin)

        # Agora exige username/telefone
        await update.message.reply_text(
            ASK_CONTACT_TEXT,
            reply_markup=phone_keyboard()
        )
        return

    # 2) Se o usuário mandou @username manualmente (texto começando com @)
    # (Só faz sentido se já tiver TXID guardado)
    if msg.startswith("@") and len(msg) >= 3 and context.user_data.get("txid"):
        txid = context.user_data.get("txid")

        text_to_admin = (
            "✅ KULLANICI BİLGİSİ (USERNAME) GELDİ\n\n"
            f"Ad: {user.full_name}\n"
            f"ID: {user_id}\n"
            f"Username (yazdı): {msg}\n\n"
            f"TXID:\n{txid}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=text_to_admin)

        # Limpa dados e remove teclado
        context.user_data.pop("txid", None)
        await update.message.reply_text(CONFIRM_INFO_TEXT, reply_markup=ReplyKeyboardRemove())
        return

    # 3) Qualquer outra coisa
    if context.user_data.get("txid"):
        # Já mandou TXID, agora a gente pede username/telefone
        await update.message.reply_text(
            "⚠️ Lütfen @username yazın veya aşağıdaki butondan telefon numaranızı gönderin.",
            reply_markup=phone_keyboard()
        )
    else:
        # Ainda não mandou TXID
        await update.message.reply_text("❌ Lütfen sadece TXID gönderin (başka mesaj yazmayın).")


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    contact = update.message.contact

    txid = context.user_data.get("txid")

    if not txid:
        await update.message.reply_text(
            "⚠️ Önce TXID gönderin, sonra telefon numaranızı gönderin.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    username_display = f"@{user.username}" if user.username else "yok (username yok)"

    text_to_admin = (
        "📞 TELEFON BİLGİSİ GELDİ\n\n"
        f"Ad: {user.full_name}\n"
        f"Username: {username_display}\n"
        f"ID: {user_id}\n"
        f"Telefon: {contact.phone_number}\n\n"
        f"TXID:\n{txid}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=text_to_admin)

    # Limpa dados e remove teclado
    context.user_data.pop("txid", None)
    await update.message.reply_text(CONFIRM_INFO_TEXT, reply_markup=ReplyKeyboardRemove())


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN não definido nas Environment Variables.")
    app = Application.builder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
