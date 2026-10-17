import os
import logging
import cv2
import numpy as np
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# ---------- CONFIG ----------
TOKEN = "8861322216:AAGngjWZB2czJrzswL_xW89bEv_6WXV6RAc"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- FLASK SERVER (For 24/7 Render Active Status) ----------
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "Bot is running 24/7 Flash Fast!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

# ---------- IMAGE ENHANCEMENT FUNCTION ----------
def enhance_image(input_path, output_path):
    img = cv2.imread(input_path)
    if img is None:
        return False
    denoised = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(denoised, -1, kernel)
    enhanced = cv2.convertScaleAbs(sharpened, alpha=1.2, beta=15)
    cv2.imwrite(output_path, enhanced)
    return True

# ---------- VIDEO ENHANCEMENT FUNCTION ----------
def enhance_video(input_path, output_path):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        return False
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0 or fps is None:
        fps = 25.0

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        enhanced_frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=10)
        out.write(enhanced_frame)

    cap.release()
    out.release()
    return True

# ---------- BOT COMMANDS ----------
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "✨ **HD PHOTO & VIDEO ENHANCER BOT** ✨\n\n"
        "📸 Mujhe koi bhi **Photo** bhejo — sharp aur clear kar dunga.\n"
        "🎥 Mujhe koi bhi **Video** bhejo — quality enhance kar dunga!\n\n"
        "🚀 24/7 Active on Render.",
        parse_mode="Markdown"
    )

async def handle_photo(update: Update, context: CallbackContext):
    msg = await update.message.reply_text("⏳ Photo enhance ki ja rahi hai...")
    photo = update.message.photo[-1]
    file = await photo.get_file()
    
    input_file = "input_img.jpg"
    output_file = "output_img.jpg"
    
    await file.download_to_drive(input_file)
    success = enhance_image(input_file, output_file)
    
    if success:
        await update.message.reply_photo(photo=open(output_file, "rb"), caption="✅ **Photo Enhanced Successfully!**")
    else:
        await update.message.reply_text("❌ Error processing photo.")
        
    await msg.delete()
    if os.path.exists(input_file): os.remove(input_file)
    if os.path.exists(output_file): os.remove(output_file)

async def handle_video(update: Update, context: CallbackContext):
    msg = await update.message.reply_text("⏳ Video process ho rahi hai, thoda waqt lag sakta hai...")
    video = update.message.video or update.message.document
    file = await video.get_file()
    
    input_file = "input_vid.mp4"
    output_file = "output_vid.mp4"
    
    await file.download_to_drive(input_file)
    success = enhance_video(input_file, output_file)
    
    if success:
        await update.message.reply_video(video=open(output_file, "rb"), caption="✅ **Video Enhanced Successfully!**")
    else:
        await update.message.reply_text("❌ Error processing video.")
        
    await msg.delete()
    if os.path.exists(input_file): os.remove(input_file)
    if os.path.exists(output_file): os.remove(output_file)

# ---------- MAIN ----------
def main():
    Thread(target=run_flask).start()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))
    
    logger.info("🤖 Enhancer Bot running on Render 24/7...")
    app.run_polling()

if __name__ == "__main__":
    main()
