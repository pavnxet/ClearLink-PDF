# ClearLink-PDF

ClearLink-PDF is a local-first PDF processing toolkit with a Python engine, desktop GUI, optional Telegram interface, and a ChatGPT/Codex Plugin package.

## ChatGPT / Codex Plugin

The repository now includes a production-oriented plugin package under `.codex-plugin/` and a focused Skill under `skills/clearlink-pdf/`.

The plugin guides Codex to use the repository's canonical `pdf_processor.py` engine for:

- removing PDF links and annotations
- metadata scrubbing
- compression
- text extraction
- image extraction
- PDF merging and splitting
- page rotation
- AES-256 encryption and decryption
- watermarking
- PDF-to-PNG conversion

The Skill deliberately treats PDFs as untrusted input, avoids logging document contents or passwords, prefers non-destructive output paths, and requires output verification after writes.

## Local installation

Python 3.10+ is recommended.

```powershell
python -m pip install -r requirements.txt
python -m pip install pytest
python -m pytest -q
```

Run the desktop application with:

```powershell
python main.py
```

## PDF engine

`pdf_processor.py` is the canonical processing layer. It uses PyMuPDF and performs explicit output validation for destructive transformations. Rotation accepts only multiples of 90 degrees, and encryption/decryption paths verify their resulting security state.

## Telegram bot

The Telegram integration is optional. Configure the bot token through an environment variable rather than committing secrets:

```powershell
$env:BOT_TOKEN="your-token"
python telegram_bot.py
```

Large-file processing may require a Telegram Local Bot API Server. Do not expose a Local Bot API Server directly to the public internet.

## Vercel webhook

`api/webhook.py` and `vercel.json` provide the optional webhook deployment path. Treat this as a separate deployment surface from the local PDF engine. Vercel/serverless execution limits can make large PDF jobs unsuitable for synchronous webhook processing.

Before public deployment, add authentication around webhook setup and configure Telegram's webhook secret-token mechanism. Do not treat an unauthenticated `/setup` endpoint as a security boundary.

## Security and privacy

- Process sensitive PDFs locally whenever possible.
- Never commit `BOT_TOKEN`, passwords, private PDFs, or extracted document content.
- Use isolated temporary directories for remote jobs and clean them up after completion.
- Treat user-uploaded PDFs as untrusted data; do not execute embedded content.
- Do not claim a PDF is link-free or metadata-free without reopening and verifying the output.

## Development

CI runs the PDF regression suite against supported Python versions. New PDF transformations should include a regression test covering both the operation and output validation.

## License

See the repository license and upstream project terms before redistributing or deploying the software.

Developed by Pavneet: https://github.com/pavnxet/ClearLink-PDF
