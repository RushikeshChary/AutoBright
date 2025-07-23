#!/bin/bash

# Name of the Python file
SCRIPT="BrightnessApp.py"
# Other variables
DEFAULT_CONFIG="default_config.yaml"
USER_CONFIG="user_config.yaml"

# Optional: Activate a virtual environment (if you use one)
# source venv/bin/activate

# Check if the script exists
if [ ! -f "$SCRIPT" ]; then
  echo "❌ Python script '$SCRIPT' not found!"
  exit 1
fi

# Check if required config files exist
if [ ! -f "$DEFAULT_CONFIG" ]; then
  echo "❌ Missing '$DEFAULT_CONFIG'."
  exit 1
fi

if [ ! -f "$USER_CONFIG" ]; then
  echo "⚠️  '$USER_CONFIG' not found. Using built-in defaults only."
fi

# Optional: Create a log file
# LOG_FILE="brightness_tool.log"
# echo "🟢 Starting Brightness Tool..."
# echo "Logging to $LOG_FILE"

# Just Run the script
echo "🟢 Starting Brightness Tool..."
echo "📜 Running '$SCRIPT'..."
python3 "$SCRIPT" --config "$DEFAULT_CONFIG" --user-config "$USER_CONFIG"
# Run the script and save output
# python "$SCRIPT" | tee "$LOG_FILE"

# Done
echo "✅ Script finished."
