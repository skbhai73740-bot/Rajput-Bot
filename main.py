import os
import re
import json
import base64
import urllib.parse
import logging
import requests
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8743272736:AAEQEPf_afFQyeVuH1VudpHZ3I9z4R8RvXk"
CHANNEL_LINK = "https://t.me/+UemRGWr-B2wzMmFl"
CHANNEL_ID = -1002345678901  # Apne channel ka numeric ID yahan set karein

OWNER_CREDIT = "👑 Owner: Rajput bhai\n⚡ Powered by: CRACK RAJPUT BHAI"
USERS_FILE = "users.json"

# ==================== FLASK SERVER (For 24/7 Render Hosting) ====================
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "Bot is running 24/7 Flash Fast! - CRACK RAJPUT BHAI"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

# ==================== USER MANAGEMENT ====================
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_users(users_set):
    with open(USERS_FILE, 'w') as f:
        json.dump(list(users_set), f)

users_db = load_users()

def add_user(user_id):
    if user_id not in users_db:
        users_db.add(user_id)
        save_users(users_db)

# ==================== DECRYPTION LOGIC ====================
def caesar_decode(text, shift):
    result = ''
    for ch in text:
        c = ord(ch)
        if 32 <= c <= 126:
            c = ((c - 32 - shift) % 95) + 32
        result += chr(c)
    return result

def decode_multi_layer(encoded_data):
    try:
        s = urllib.parse.unquote(encoded_data)
        s = base64.b64decode(s).decode('utf-8')
        shifts = [15, 9, 9, 6, 3, 18, 18, 15, 5, 5, 2, 1, 5, 17, 13]
        for shift in shifts:
            s = caesar_decode(s, shift)
        return s
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        return None

def extract_payload(decoded_json):
    try:
        data = json.loads(decoded_json)
        html_content = data.get('html') or data.get('logic') or ""
        css_content = data.get('css', "")
        js_content = data.get('js') or data.get('javascript') or data.get('script') or ""
        
        if not html_content:
            for k, v in data.items():
                if isinstance(v, str) and len(v) > 50 and '<' in v and '>' in v:
                    html_content = v
                    break

        if html_content:
            if css_content and '<style>' not in html_content:
                if '<head>' in html_content:
                    html_content = html_content.replace('<head>', f'<head>\n<style>\n{css_content}\n</style>')
            if js_content and '<script>' not in html_content:
                if '</body>' in html_content:
                    html_content = html_content.replace('</body>', f'<script>\n{js_content}\n</script>\n</body>')
            return html_content
        return decoded_json
    except json.JSONDecodeError:
        return decoded_json

def extract_passwords_and_keys(content):
    found_info = []
    
    firebase_matches = re.findall(r'apiKey["\']?\s*:\s*["\']([^"\']+)["\']', content, re.IGNORECASE)
    if firebase_matches:
        found_info.append(f"🔥 Firebase API Key: `{firebase_matches[0]}`")

    pass_matches = re.findall(r'(?:password|pass|key|secret|token)\s*[:=]\s*["\']([^"\']+)["\']', content, re.IGNORECASE)
    if pass_matches:
        for idx, p in enumerate(set(pass_matches[:5]), 1):
            found_info.append(f"🔑 Secret/Password #{idx}: `{p}`")
            
    json_pass = re.findall(r'"password"\s*:\s*"([^"]+)"', content)
    if json_pass:
        found_info.append(f"🔓 Extracted Password: `{json_pass[0]}`")

    if not found_info:
        return "⚠️ Koi Password ya Firebase Key nahi mili!"
    return "\n".join(found_info)

# ==================== CHANNEL CHECKER ====================
async def is_user_joined(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception:
        return True

def get_join_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel First", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ Verify / Check Joined", callback_data="verify_join")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_main_menu():
    keyboard = [
        [
            InlineKeyboardButton("🔓 HTML Decrypt", callback_data="btn_html_decrypt"),
            InlineKeyboardButton("🌐 URL to HTML", callback_data="btn_url_to_html")
        ],
        [
            InlineKeyboardButton("🔑 HTML Password", callback_data="btn_html_pass"),
            InlineKeyboardButton("🔐 URL Password", callback_data="btn_url_pass")
        ],
        [InlineKeyboardButton("📊 Total Users", callback_data="btn_total_users")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== HANDLERS ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id)
    
    joined = await is_user_joined(context.bot, user.id)
    if not joined:
        await update.message.reply_text(
            "⚠️ **WARNING: Access Denied!**\n\n"
            "Aapne abhi tak channel join nahi kiya hai. Pehle join karke verify karein!",
            parse_mode="Markdown",
            reply_markup=get_join_keyboard()
        )
        return

    await update.message.reply_text(
        f"🔥 **WELCOME TO ULTIMATE HTML TOOL BOT** 🔥\n\n"
        f"Choose an option below:\n\n{OWNER_CREDIT}",
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "verify_join":
        joined = await is_user_joined(context.bot, user_id)
        if joined:
            await query.edit_message_text(
                f"✅ **Verification Successful!**\n\nChoose an option:\n\n{OWNER_CREDIT}",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
        else:
            await query.edit_message_text(
                "❌ **Warning:** Aapne join nahi kiya! Pehle join karein.",
                parse_mode="Markdown",
                reply_markup=get_join_keyboard()
            )
        return

    joined = await is_user_joined(context.bot, user_id)
    if not joined:
        await query.message.reply_text("⚠️ Channel join karein!", reply_markup=get_join_keyboard())
        return

    action = query.data
    context.user_data['action'] = action

    if action == "btn_html_decrypt":
        await query.message.reply_text("📥 `.html` file bhejo decrypt karne ke liye.")
    elif action == "btn_url_to_html":
        await query.message.reply_text("🌐 Web **URL/Link** bhejo HTML me convert karne ke liye.")
    elif action == "btn_html_pass":
        await query.message.reply_text("🔑 `.html` file bhejo hidden password/keys nikalne ke liye.")
    elif action == "btn_url_pass":
        await query.message.reply_text("🔐 Web **URL/Link** bhejo password/keys extract karne ke liye.")
    elif action == "btn_total_users":
        await query.message.reply_text(
            f"👥 **Total Bot Users:** `{len(users_db)}` Users\n\n{OWNER_CREDIT}",
            parse_mode="Markdown"
        )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_user_joined(context.bot, user_id):
        await update.message.reply_text("⚠️ Pehle channel join karein!", reply_markup=get_join_keyboard())
        return

    doc = update.message.document
    if not doc.file_name.endswith(('.html', '.txt')):
        await update.message.reply_text("❌ Sirf `.html` file support hai!")
        return

    action = context.user_data.get('action', 'btn_html_decrypt')
    msg = await update.message.reply_text("⚡ Processing in 1 second...")
    
    file = await context.bot.get_file(doc.file_id)
    file_bytes = await file.download_as_bytearray()
    content = file_bytes.decode('utf-8', errors='ignore')

    if action == "btn_html_pass":
        keys_info = extract_passwords_and_keys(content)
        await msg.edit_text(f"🔓 **Extracted Info:**\n\n{keys_info}\n\n{OWNER_CREDIT}", parse_mode="Markdown")
    else:
        match = re.search(r'var d="([^"]+)"', content)
        if match:
            enc_data = match.group(1)
            decoded = decode_multi_layer(enc_data)
            final_html = extract_payload(decoded) if decoded else content
        else:
            final_html = content

        out_path = "decrypted_CRACK_RAJPUT_BHAI.html"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"<!-- {OWNER_CREDIT} -->\n" + final_html)

        await update.message.reply_document(
            document=open(out_path, "rb"),
            filename="decrypted_CRACK_RAJPUT_BHAI.html",
            caption=f"✅ **HTML Decrypted!**\n\n{OWNER_CREDIT}",
            parse_mode="Markdown"
        )
        if os.path.exists(out_path):
            os.remove(out_path)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_user_joined(context.bot, user_id):
        await update.message.reply_text("⚠️ Pehle channel join karein!", reply_markup=get_join_keyboard())
        return

    text = update.message.text.strip()
    action = context.user_data.get('action')

    if text.startswith("http://") or text.startswith("https://"):
        msg = await update.message.reply_text("⚡ Fetching URL data...")
        try:
            resp = requests.get(text, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            html_text = resp.text

            if action == "btn_url_pass":
                keys_info = extract_passwords_and_keys(html_text)
                await msg.edit_text(f"🔐 **URL Passwords & Keys:**\n\n{keys_info}\n\n{OWNER_CREDIT}", parse_mode="Markdown")
            else:
                out_path = "converted_CRACK_RAJPUT_BHAI.html"
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(f"<!-- {OWNER_CREDIT} -->\n" + html_text)

                await update.message.reply_document(
                    document=open(out_path, "rb"),
                    filename="converted_CRACK_RAJPUT_BHAI.html",
                    caption=f"✅ **URL Converted to HTML!**\n\n{OWNER_CREDIT}",
                    parse_mode="Markdown"
                )
                if os.path.exists(out_path):
                    os.remove(out_path)
        except Exception as e:
            await msg.edit_text(f"❌ Error: {e}")
    else:
        await update.message.reply_text("Valid URL ya File bhejo!")

# ==================== MAIN ====================
def main():
    Thread(target=run_flask).start()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🤖 Bot started on Render...")
    app.run_polling()

if __name__ == '__main__':
    main()
