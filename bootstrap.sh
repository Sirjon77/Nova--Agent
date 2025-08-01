
#!/usr/bin/env bash
# Bootstrap script for Nova Agent development
set -e
echo "🔧  Creating virtualenv..."
python -m venv .venv
source .venv/bin/activate
echo "⬆️  Upgrading pip & installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt
echo "💻  Installing Playwright chromium driver..."
playwright install chromium
echo "✅  Bootstrap complete. Duplicate .env.example → .env and add your secrets."
