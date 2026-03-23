# 🚀 ClearLink-PDF: Advanced PDF Toolset & Telegram Bot

ClearLink-PDF is a premium, high-performance utility designed for advanced PDF manipulation. Originally a specialized tool to strip hyperlinks, it has been expanded into a comprehensive PDF processing engine with a modern GUI and a powerful Telegram Bot interface.

---

## ✨ Key Features

### 💎 Premium GUI
- **Glassmorphic Design**: A sleek, dark-mode aesthetic with translucent elements.
- **Interactive Drag-and-Drop**: Drag PDFs in for processing and drag results out directly.
- **Batch Processing**: Handle multiple files simultaneously with real-time progress.
- **Instant Preview**: Open cleaned PDFs directly from the app after processing.

### 🤖 Telegram Bot Interface
A fully integrated Telegram Bot (`telegram_bot.py`) that brings all PDF features to your chat:
- **Large File Support**: Configurable for Local Bot API Server to handle files up to **2GB**.
- **Interactive Commands**: Use simple buttons to trigger complex PDF operations.
- **Merge Sessions**: Send multiple files and merge them with a single command.
- **Secure Processing**: Temporary files are handled in isolated workspace directories.

### 🧠 "Perfect Logic" PDF Engine
Our engine performs 12+ advanced operations with 100% reliability:
1.  **🧹 Link Removal**: Triple-sweep cleaning of visible and invisible clickables.
2.  **🗜 Deep Compression**: Object optimization and zlib deflation for minimal file size.
3.  **📄 Text Extraction**: Fast and accurate text recovery from any document.
4.  **🖼 Image Extraction**: Securely pulls all embedded images into a local folder.
5.  **🔗 PDF Merging**: Combine multiple documents into one seamless file.
6.  **✂️ PDF Splitting**: Break down documents into individual high-quality pages.
7.  **🔄 Page Rotation**: Change orientation (90/180/270°) across the entire file.
8.  **🔒 AES-256 Encryption**: Secure your documents with owner and user passwords.
9.  **🔓 PDF Decryption**: Remove protection from encrypted files instantly.
10. **💧 Custom Watermarking**: Add dynamic text overlays to every page.
11. **📸 Image Conversion**: Turn PDF pages into high-resolution PNG images.
12. **🛡 Metadata Scrubbing**: Removes Authors, Producers, and sensitive timestamps.

---

## 🛠️ Installation & Setup

### 1. Requirements
- **Python 3.8+**
- **Windows OS** (Optimized for DirectWrite fonts)

### 2. Dependencies
Install the required high-performance libraries:
```powershell
pip install PySide6 pymupdf pyTelegramBotAPI
```

### 3. Running the GUI
```powershell
python main.py
```

### 4. Running the Telegram Bot
1. Replace `YOUR_BOT_TOKEN_HERE` in `telegram_bot.py` or set it in your environment:
   ```powershell
   set BOT_TOKEN=your_token_here
   ```
2. Launch the bot:
   ```powershell
   python telegram_bot.py
   ```

---

## 🌐 Huge File Processing (>20MB)
Standard Telegram Bots are limited to 20MB downloads. To process massive PDFs (up to 2GB):
1. Setup a [Local Bot API Server](https://core.telegram.org/bots/api#using-a-local-bot-api-server).
2. Set `USE_LOCAL_API_SERVER = True` in `telegram_bot.py`.

---

## 🚀 Easy Vercel Deployment
You can seamlessly deploy this bot to Vercel for free 24/7 hosting. Using Serverless Functions, it will automatically run your bot via Webhooks without needing a computer turned on!

> **Note on Free-Tier Limits:** Vercel limits Serverless Function execution times to 10 seconds. Extremely large PDFs may fail to process due to this timeout.

### Deployment Steps:
1. **Push your code to GitHub** (Make sure your repository has `vercel.json`, `requirements.txt`, and the `api/` folder).
2. Go to [Vercel](https://vercel.com/) and create a **New Project**.
3. Import your GitHub repository.
4. **Important**: Before deploying, go to **Environment Variables** and add:
   - Key: `BOT_TOKEN` | Value: `Your Telegram Bot Token`
5. Click **Deploy**.
6. Once deployed, open your browser and go to your Vercel URL directly followed by `/setup` to initialize the Webhook (e.g., `https://your-bot-project.vercel.app/setup`).
7. Your bot is now live and waiting for messages!

---

## 📂 Privacy & Safety
- **No Residual Data**: The GUI preserves your output while the Bot uses isolated temp folders.
- **Local-Only**: All processing happens on your machine. No data is ever sent to third-party processing APIs.
- **Pointer-Based Logic**: Our code uses pointer-referenced traversal to ensure 100% of links are removed, even in complex nested structures.

---

*Developed with ❤️ by [Pavneet](https://github.com/pavnxet/ClearLink-PDF)*
