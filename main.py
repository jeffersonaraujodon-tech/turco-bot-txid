import re
import os

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

# Aceita praticamente qualquer TXID/hash (sem espaços), e evita confundir com @username, telefone e comandos
TXID_REGEX = re.compile(r"^(?!@)(?!\+?\d)(?!/)[A-Za-z0-9:_\-]{20,200}$")

# Telefone digitado (8 a 16 dígitos, pode ter +, espaço e hífen)
PHONE_REGEX = re.compile(r"^\+?\d[\d\s\-]{7,15}$")

START_TEXT = (
    "Hoş geldiniz. 🇹🇷\n\n"
    "1) Ödemeyi yapın\n"
    "2) TXID'yi buraya gönderin\n\n"
    "TXID gönderildikten sonra sizden iletişim bilgisi istenecektir."
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
    # Evita conflito com webhook antigo
    await app.bot.delete_webhook(drop_pending_updates=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(START_TEXT)


def _username_display(user) -> str:
    return f"@{user.username}" if user.username else "yok (username yok)"


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (update.message.text or "").strip()
    user = update.effective_user
    user_id = user.id

    # 1) Recebe TXID -> guarda e pede contato (NÃO fala com admin aqui)
    if TXID_REGEX.match(msg):
        context.user_data["txid"] = msg
        await update.message.reply_text(ASK_CONTACT_TEXT, reply_markup=phone_keyboard())
        return

    # Se já tem TXID guardado, agora aceitamos username OU telefone digitado
    txid = context.user_data.get("txid")

    # 2) Username manual (@algo)
    if txid and msg.startswith("@") and len(msg) >= 3:
        text_to_admin = (
            "✅ YENİ ÖDEME BİLGİSİ (USERNAME)\n\n"
            f"Ad: {user.full_name}\n"
            f"ID: {user_id}\n"
            f"Telegram Username (yazdı): {msg}\n"
            f"Profil Username: {_username_display(user)}\n\n"
            f"TXID:\n{txid}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=text_to_admin)

        context.user_data.pop("txid", None)
        await update.message.reply_text(CONFIRM_INFO_TEXT, reply_markup=ReplyKeyboardRemove())
        return

    # 3) Telefone digitado (+90..., +55..., etc.)
    if txid and PHONE_REGEX.match(msg):
        phone_clean = re.sub(r"[\s\-]", "", msg)

        text_to_admin = (
            "✅ YENİ ÖDEME BİLGİSİ (TELEFON)\n\n"
            f"Ad: {user.full_name}\n"
            f"ID: {user_id}\n"
            f"Telefon (yazdı): {phone_clean}\n"
            f"Profil Username: {_username_display(user)}\n\n"
            f"TXID:\n{txid}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=text_to_admin)

        context.user_data.pop("txid", None)
        await update.message.reply_text(CONFIRM_INFO_TEXT, reply_markup=ReplyKeyboardRemove())
        return

    # 4) Qualquer outra coisa
    if txid:
        await update.message.reply_text(
            "⚠️ Lütfen @username yazın veya aşağıdaki butondan telefon numaranızı gönderin.",
            reply_markup=phone_keyboard()
        )
    else:
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

    text_to_admin = (
        "✅ YENİ ÖDEME BİLGİSİ (KONTакт)\n\n"
        f"Ad: {user.full_name}\n"
        f"ID: {user_id}\n"
        f"Username: {_username_display(user)}\n"
        f"Telefon (buton): {contact.phone_number}\n\n"
        f"TXID:\n{txid}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=text_to_admin)

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
