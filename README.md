# Teletext PDF Generator

A Python script that fetches the latest news from Czech Television (CT2) teletext, creates a custom information dashboard, generates a PDF, and sends it directly to your email.

## Features

- **Teletext Download**: Automatically downloads and processes teletext pages (100–170) from CT2.
- **Custom Dashboard**: Generates a first page containing:
  - 3-day weather forecast for Prague (via OpenMeteo)
  - Czech namesdays for the next 3 days (via SvatkyAPI.cz)
  - Market data (BTC/USD, EUNL/EUR) with 3-day trends
  - Current exchange rates (EUR/CZK, PLN/CZK via CNB)
- **PDF Generation**: Compiles the dashboard and processed teletext images into a single PDF.
- **Email Delivery**: Sends the generated PDF to a specified recipient.
- **Automated Workflows**: Includes GitHub Actions for scheduled generation (e.g., Mon, Wed, Fri mornings).

## Requirements

- Python >= 3.13
- [uv](https://docs.astral.sh/uv/) for dependency management

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/JaroslavKodousek/Teletext.git
   cd Teletext
   ```

2. Install dependencies using `uv`:
   ```bash
   uv sync
   ```

3. Set up environment variables:
   Copy `.env.example` to `.env` and configure your email credentials:
   ```bash
   cp .env.example .env
   ```
   **`.env` contents:**
   ```env
   SENDER_EMAIL=your_email@example.com
   SENDER_PASSWORD=your_app_password
   RECIPIENT_EMAIL=recipient@example.com
   # Optional: set to "true" to run without sending emails
   # DRY_RUN=false
   ```

## Usage

Run the script directly using `uv`:
```bash
uv run teletext
```
*(Alternatively, you can run `uv run python -m src.main`)*

If `DRY_RUN=true` is set, the script will generate the PDF in the `data/` folder without attempting to send an email.

## Automation

This repository includes a GitHub Actions workflow (`.github/workflows/main.yml`) that automatically runs the script on specific days (Monday, Wednesday, Friday at 5:15 CEST). To enable it, add `SENDER_EMAIL`, `SENDER_PASSWORD`, and `RECIPIENT_EMAIL` to your repository's Actions Secrets.

## License

MIT License
