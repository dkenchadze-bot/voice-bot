import os, io, logging, subprocess, tempfile
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import speech_recognition as sr

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
recognizer = sr.Recognizer()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("voice_bot")


def transcribe(ogg_bytes):
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as ogg_f:
        ogg_f.write(ogg_bytes)
        ogg_path = ogg_f.name

    wav_path = ogg_path.replace(".ogg", ".wav")
    subprocess.run(
        ["ffmpeg", "-y", "-i", ogg_path, "-ar", "16000", "-ac", "1", wav_path],
        capture_output=True,
    )

    with sr.AudioFile(wav_path) as source:
        audio = recognizer.record(source)

    os.unlink(ogg_path)
    os.unlink(wav_path)

    text = recognizer.recognize_google(audio, language="ka-GE")
    return text


async def cmd_start(update, ctx):
    await update.message.reply_text(
        "გამომიგზავნე ხმოვანი შეტყობინება ქართულად — ტექსტს დაგიბრუნებ."
    )


async def handle_voice(update, ctx):
    msg = update.message
    voice = msg.voice or msg.audio
    if not voice:
        return

    processing = await msg.reply_text("...")

    try:
        file = await ctx.bot.get_file(voice.file_id)
        ogg = await file.download_as_bytearray()
        text = transcribe(bytes(ogg))
        await processing.edit_text(text)
    except sr.UnknownValueError:
        await processing.edit_text("ვერ გავიგე, სცადე თავიდან.")
    except Exception as e:
        log.error(f"Error: {e}", exc_info=True)
        await processing.edit_text(f"შეცდომა: {e}")


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    print("bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
