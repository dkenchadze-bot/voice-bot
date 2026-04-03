"""
ქართული Voice-to-Text Telegram ბოტი
=====================================
ქართულ ვოისს აგზავნი — ქართულ ტექსტს გიბრუნებს.

Environment Variables:
  TELEGRAM_BOT_TOKEN  — @BotFather-დან
  OPENAI_API_KEY      — Whisper-ისთვის
"""

import os, io, logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import openai

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
openai_client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("voice_bot")


def transcribe(ogg_bytes: bytes) -> str:
    """Whisper: ქართული ვოისი → ქართული ტექსტი"""
    f = io.BytesIO(ogg_bytes)
    f.name = "voice.ogg"
    resp = openai_client.audio.transcriptions.create(
        model="whisper-1",
        file=f,
        language="ka",
    )
    return resp.text


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎙 გამომიგზავნე ხმოვანი შეტყობინება ქართულად — "
        "ტექსტს დაგიბრუნებ."
    )


async def handle_voice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    voice = msg.voice or msg.audio
    if not voice:
        return

    processing = await msg.reply_text("⏳")

    try:
        file = await ctx.bot.get_file(voice.file_id)
        ogg = await file.download_as_bytearray()
        text = transcribe(bytes(ogg))
        log.info(f"Transcribed: {text[:80]}...")
        await processing.edit_text(text)
    except Exception as e:
        log.error(f"Error: {e}", exc_info=True)
        await processing.edit_text(f"❌ შეცდომა: {e}")


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    print("🟢 ბოტი გაეშვა")
    app.run_polling()


if __name__ == "__main__":
    main()
