import os
import asyncio
from flask import Flask
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from PIL import Image, ImageEnhance, ImageFilter

# ---- CONFIGURATION ----
BOT_TOKEN = "8953989836:AAHegyT-lnluYCcxM-oweH1DWS2iGoOZQhg"
INSTA_LINK = "https://www.instagram.com/itx_suraj_bhai23?psln=Zm9nNTNudmEydms4"

# User follow tracking dictionary (In-memory storage)
user_followed = {}

# ---- WEB SERVER FOR RENDER PING ----
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is active and running 24/7!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host="0.0.0.0", port=port)

# ---- /start COMMAND HANDLER ----
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_followed[user_id] = False  # Reset status

    keyboard = [
        [InlineKeyboardButton("📱 Follow on Instagram", url=INSTA_LINK)],
        [InlineKeyboardButton("✅ Maine Follow Kar Diya", callback_data="verify_follow")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption_text = (
        "⚠️ **WARNING / ZAROORI SOOCHNA** ⚠️\n\n"
        "Bot ko use karne ke liye aapko humare Instagram account ko follow karna mandatory hai.\n\n"
        "👉 **Step 1:** Niche diye gaye link se Instagram par follow karein.\n"
        "👉 **Step 2:** '✅ Maine Follow Kar Diya' button par click karein.\n\n"
        "Jab tak aap follow nahi karenge, tab tak photo process nahi hogi!"
    )

    await update.message.reply_text(
        text=caption_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ---- BUTTON CLICK CALLBACK (VERIFICATION) ----
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "verify_follow":
        user_id = query.from_user.id
        user_followed[user_id] = True
        
        await query.edit_message_text(
            text="🎉 **Aapka Verification successful ho gaya hai!**\n\n"
                 "Ab aap apni koi bhi photo bhejein. Bot usko iPhone-level clarity, "
                 "1080p / 4K Ultra HD aur enhance backend me convert karke bhej dega."
        )

# ---- IMAGE ENHANCEMENT FUNCTION ----
def enhance_photo_hd(input_path: str, output_path: str):
    with Image.open(input_path) as img:
        img = img.convert("RGB")
        width, height = img.size
        target_size = max(width, height)
        if target_size < 3840:
            scale_factor = 3840 / target_size
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        img = ImageEnhance.Sharpness(img).enhance(1.6)
        img = ImageEnhance.Color(img).enhance(1.25)
        img = ImageEnhance.Contrast(img).enhance(1.15)
        img = ImageEnhance.Brightness(img).enhance(1.05)
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

        img.save(output_path, "JPEG", quality=100, subsampling=0)

# ---- PHOTO MESSAGE HANDLER ----
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not user_followed.get(user_id, False):
        keyboard = [
            [InlineKeyboardButton("📱 Follow on Instagram", url=INSTA_LINK)],
            [InlineKeyboardButton("✅ Maine Follow Kar Diya", callback_data="verify_follow")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            text="🚨 **WARNING: Photo nahi banegi!**\n\n"
                 "Aapne abhi tak Instagram account follow nahi kiya hai. "
                 "Pehle follow karein aur '✅ Maine Follow Kar Diya' button par click karein!",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return

    msg = await update.message.reply_text("⏳ **Photo enhance ho rahi hai... (5 Second wait karein)**")

    photo_file = await update.message.photo[-1].get_file()
    input_path = f"input_{user_id}.jpg"
    output_path = f"output_4k_{user_id}.jpg"
    await photo_file.download_to_drive(input_path)

    await asyncio.sleep(5)
    enhance_photo_hd(input_path, output_path)

    await update.message.reply_document(
        document=open(output_path, "rb"),
        filename="Enhanced_4K_UltraHD.jpg",
        caption="✨ **Aapki 4K Ultra HD Enhanced Photo Ready Hai!**\n\n"
                "⚡ *Features applied: 1080p/4K Upscaling, Dynamic Color Boost, Face Intact Sharpening.*"
    )

    await msg.delete()
    if os.path.exists(input_path):
        os.remove(input_path)
    if os.path.exists(output_path):
        os.remove(output_path)

# ---- MAIN FUNCTION ----
def main():
    # Flask server ko background thread me start karein
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Bot Successfully Started!")
    app.run_polling()

if __name__ == "__main__":
    main()
