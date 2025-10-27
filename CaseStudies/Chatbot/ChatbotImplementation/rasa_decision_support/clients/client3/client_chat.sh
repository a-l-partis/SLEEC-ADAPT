#!/bin/bash

# === Activate virtualenv ===
source "$HOME/virtualenvs/rasa_env/bin/activate"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLIENT_NAME="$(basename "$SCRIPT_DIR")"
ROOT_DIR="$SCRIPT_DIR/../.."
ADAPT_DIR="$ROOT_DIR/sleec-adapt"
FINAL_OUTPUT="$ADAPT_DIR/active.workflowspec"

# Set terminal title
echo -ne "\033]0;Chat - $CLIENT_NAME\007"

# === Ensure base workflow exists ===
if [ ! -f "$ADAPT_DIR/Chatbot.workflowspec" ]; then
  echo "❌ Base workflow not found in sleec-adapt. Is the server running?"
  exit 1
fi

# === Delete ONLY previous user rules for this client ===
find "$ADAPT_DIR" -maxdepth 1 -type f -name "client*_*.sleec" -delete

# === Copy client user rules safely ===
find "$SCRIPT_DIR" -maxdepth 1 -name "*.sleec" | sort | while read -r RULE; do
  BASENAME="$(basename "$RULE")"
  cp "$RULE" "$ADAPT_DIR/${CLIENT_NAME}_${BASENAME}"
done

# === Let the server know who's connecting ===
echo "$CLIENT_NAME" > "$ADAPT_DIR/client.info"

# === Slightly touch the workflow to trigger hash change ===
echo "" >> "$FINAL_OUTPUT"

# === Start chat ===
echo "💬 Starting chat for $CLIENT_NAME..."
echo "----------------------------------------"
cd "$ROOT_DIR"

# Try virtualenv first
if [ -x "$HOME/virtualenvs/rasa_env/bin/rasa" ]; then
  RASA_CMD="$HOME/virtualenvs/rasa_env/bin/rasa"
else
  RASA_CMD="$(command -v rasa)"
fi

if [ -z "$RASA_CMD" ]; then
  echo "❌ Rasa executable not found. Please ensure it is installed."
  exit 1
fi

PYTHONWARNINGS="ignore" RASA_LOG_LEVEL=ERROR "$RASA_CMD" shell --quiet 2>/dev/null