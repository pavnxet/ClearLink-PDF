import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pdf_processor import (
    remove_hyperlinks, compress_pdf, extract_text, extract_images,
    merge_pdfs, split_pdf, rotate_pdf, encrypt_pdf, decrypt_pdf, 
    add_watermark, pdf_to_images
)

# === CONFIGURATION ===
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# For handling files > 20MB, you need to use a Local Bot API Server.
# See: https://core.telegram.org/bots/api#using-a-local-bot-api-server
USE_LOCAL_API_SERVER = False
LOCAL_API_URL = "http://localhost:8081/bot{0}/{1}"

if USE_LOCAL_API_SERVER:
    telebot.apihelper.API_URL = LOCAL_API_URL
    # Increase timeout for large files
    telebot.apihelper.SESSION_TIME_TO_LIVE = 5 * 60

bot = telebot.TeleBot(BOT_TOKEN)

# Ensure temp directory exists
# On Vercel, the only writable directory is /tmp
if os.environ.get('VERCEL'):
    TEMP_DIR = '/tmp/bot_temp'
else:
    TEMP_DIR = 'bot_temp'
os.makedirs(TEMP_DIR, exist_ok=True)

# State variable for merging
user_merge_sessions = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    help_text = (
        "Welcome to ClearLink-PDF Bot! 🚀\n\n"
        "Send me any PDF file and choose an action to perform on it:\n"
        "🧹 Remove Links\n"
        "🗜 Compress\n"
        "📄 Extract Text\n"
        "🖼 Extract Images\n"
        "✂️ Split\n"
        "🔄 Rotate\n"
        "🔒 Encrypt\n"
        "🔓 Decrypt\n"
        "💧 Watermark\n"
        "📸 Convert to Images\n\n"
        "To merge PDFs, use the /merge command to start a session."
    )
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['merge'])
def start_merge(message):
    chat_id = message.chat.id
    user_merge_sessions[chat_id] = []
    bot.reply_to(message, "Merge session started! Send me the PDF files you want to merge one by one. When you are done, send /donemerge.")

@bot.message_handler(commands=['donemerge'])
def done_merge(message):
    chat_id = message.chat.id
    if chat_id not in user_merge_sessions or len(user_merge_sessions[chat_id]) < 2:
        bot.reply_to(message, "You need to send at least 2 PDFs before merging. Send /merge to restart.")
        return
        
    msg = bot.reply_to(message, "Merging PDFs... Please wait.")
    output_path = os.path.join(TEMP_DIR, f"merged_{chat_id}.pdf")
    
    success, res = merge_pdfs(user_merge_sessions[chat_id], output_path)
    if success:
        with open(output_path, 'rb') as f:
            bot.send_document(chat_id, f)
        bot.edit_message_text("Merged successfully!", chat_id=chat_id, message_id=msg.message_id)
    else:
        bot.edit_message_text(f"Error merging: {res}", chat_id=chat_id, message_id=msg.message_id)
        
    # Clear session
    user_merge_sessions.pop(chat_id, None)

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if not message.document.mime_type == 'application/pdf':
        bot.reply_to(message, "Please upload a valid PDF document.")
        return
        
    chat_id = message.chat.id
    
    # Check if in merge session
    if chat_id in user_merge_sessions:
        file_path = download_file(message)
        if file_path:
            user_merge_sessions[chat_id].append(file_path)
            bot.reply_to(message, f"Added to merge session! ({len(user_merge_sessions[chat_id])} files). Send more or /donemerge.")
        return

    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🧹 Remove Links", callback_data=f"remove_links|{message.message_id}"))
    markup.row(InlineKeyboardButton("🗜 Compress", callback_data=f"compress|{message.message_id}"))
    markup.row(InlineKeyboardButton("📄 Extract Text", callback_data=f"extract_text|{message.message_id}"),
               InlineKeyboardButton("🖼 Extract Images", callback_data=f"extract_images|{message.message_id}"))
    markup.row(InlineKeyboardButton("✂️ Split", callback_data=f"split|{message.message_id}"),
               InlineKeyboardButton("🔄 Rotate", callback_data=f"rotate_prompt|{message.message_id}"))
    markup.row(InlineKeyboardButton("🔒 Encrypt", callback_data=f"encrypt_prompt|{message.message_id}"),
               InlineKeyboardButton("🔓 Decrypt", callback_data=f"decrypt_prompt|{message.message_id}"))
    markup.row(InlineKeyboardButton("💧 Watermark", callback_data=f"watermark_prompt|{message.message_id}"))
    markup.row(InlineKeyboardButton("📸 Convert to Images", callback_data=f"to_images|{message.message_id}"))

    bot.reply_to(message, "Document received! Choose an action:", reply_markup=markup)

def download_file(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        input_path = os.path.join(TEMP_DIR, f"{message.message_id}.pdf")
        with open(input_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        return input_path
    except Exception as e:
        bot.reply_to(message, f"Failed to download file: {e}. If file >20MB, a Local API server is required.")
        return None

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    action, msg_id = call.data.split('|')
    msg_id = int(msg_id)
    
    bot.answer_callback_query(call.id, "Processing...")
    
    original_msg = call.message.reply_to_message
    if not original_msg or not original_msg.document:
        bot.send_message(call.message.chat.id, "Error: Could not locate the original document.")
        return
        
    chat_id = call.message.chat.id
    input_path = download_file(original_msg)
    if not input_path:
        return
        
    output_path = os.path.join(TEMP_DIR, f"out_{msg_id}.pdf")
    output_dir = os.path.join(TEMP_DIR, f"out_dir_{msg_id}")
    
    bot.edit_message_text(f"Action '{action}' started. Please wait...", chat_id=chat_id, message_id=call.message.message_id)

    try:
        if action == "remove_links":
            success, res = remove_hyperlinks(input_path, output_path, remove_all_annots=True)
            if success:
                bot.send_document(chat_id, open(output_path, 'rb'))
            else:
                bot.send_message(chat_id, f"Error: {res}")
                
        elif action == "compress":
            success, res = compress_pdf(input_path, output_path)
            if success:
                bot.send_document(chat_id, open(output_path, 'rb'))
            else:
                bot.send_message(chat_id, f"Error: {res}")
                
        elif action == "extract_text":
            success, res = extract_text(input_path)
            if success:
                if len(res) > 4000:
                    text_path = os.path.join(TEMP_DIR, f"text_{msg_id}.txt")
                    with open(text_path, 'w', encoding='utf-8') as f:
                        f.write(res)
                    bot.send_document(chat_id, open(text_path, 'rb'))
                else:
                    bot.send_message(chat_id, res if res.strip() else "No text found.")
            else:
                bot.send_message(chat_id, f"Error: {res}")
                
        elif action == "extract_images":
            success, res = extract_images(input_path, output_dir)
            if success:
                images = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(('.png', '.jpeg', '.jpg'))]
                for img in images:
                    with open(img, 'rb') as f:
                        bot.send_photo(chat_id, f)
                bot.send_message(chat_id, f"Extracted {len(images)} images.")
            else:
                bot.send_message(chat_id, f"Error: {res}")
                
        elif action == "split":
            success, res = split_pdf(input_path, output_dir)
            if success:
                pdfs = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith('.pdf')]
                for pdf in pdfs:
                    with open(pdf, 'rb') as f:
                        bot.send_document(chat_id, f)
                bot.send_message(chat_id, f"Split into {len(pdfs)} pages.")
            else:
                bot.send_message(chat_id, f"Error: {res}")
                
        elif action == "to_images":
            success, res = pdf_to_images(input_path, output_dir)
            if success:
                images = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith('.png')]
                for img in images:
                    with open(img, 'rb') as f:
                        bot.send_document(chat_id, f)
                bot.send_message(chat_id, f"Converted {len(images)} pages.")
            else:
                bot.send_message(chat_id, f"Error: {res}")
                
        # Actions requiring prompts
        elif "prompt" in action:
            action_raw = action.replace('_prompt', '')
            bot.send_message(chat_id, f"Please reply with the parameter for {action_raw} (e.g. angle for rotate, password for encrypt/decrypt, text for watermark):")
            bot.register_next_step_handler(call.message, handle_parameter, action_raw, input_path, output_path)
            return

        bot.edit_message_text("Process completed.", chat_id=chat_id, message_id=call.message.message_id)

    except Exception as e:
        bot.send_message(chat_id, f"Unexpected error: {str(e)}")

def handle_parameter(message, action, input_path, output_path):
    param = message.text
    chat_id = message.chat.id
    
    msg = bot.send_message(chat_id, "Processing...")
    
    if action == "rotate":
        try:
            angle = int(param)
            success, res = rotate_pdf(input_path, output_path, angle)
            if success:
                bot.send_document(chat_id, open(output_path, 'rb'))
            else:
                bot.send_message(chat_id, f"Error: {res}")
        except ValueError:
            bot.send_message(chat_id, "Invalid angle. Must be a number.")
            
    elif action == "encrypt":
        success, res = encrypt_pdf(input_path, output_path, param)
        if success:
            bot.send_document(chat_id, open(output_path, 'rb'))
        else:
            bot.send_message(chat_id, f"Error: {res}")
            
    elif action == "decrypt":
        success, res = decrypt_pdf(input_path, output_path, param)
        if success:
            bot.send_document(chat_id, open(output_path, 'rb'))
        else:
            bot.send_message(chat_id, f"Error: {res}")
            
    elif action == "watermark":
        success, res = add_watermark(input_path, output_path, param)
        if success:
            bot.send_document(chat_id, open(output_path, 'rb'))
        else:
            bot.send_message(chat_id, f"Error: {res}")
            
    bot.edit_message_text("Process completed.", chat_id=chat_id, message_id=msg.message_id)

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
