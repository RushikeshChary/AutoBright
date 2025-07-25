**Adaptive Screen Brightness Controller** is a Python-powered desktop app that automatically adjusts your monitor brightness based on what's displayed onscreen. It provides a simple GUI, supports multiple monitors, and lets users fine-tune settings (interval, brightness limits, region, threshold) in real time. The app can work both automatically or manually, ensuring more comfortable viewing and reduced eye strain—all with just a few clicks.

## Installation

1. Make sure you have Python 3.7+ installed on your system.
2. Install all required Python dependencies at once using the provided `utils.txt` file. In your project directory, run:
   ```bash
   pip install -r utils.txt
   ```

## How to Launch

**Option 1: Manual Command-Line**

Run this command from your app directory, specifying the configuration files if needed:
```bash
python BrightnessApp.py --config default_config.yaml --user-config user_config.yaml
```
- This method lets you select or override config files as you launch.

**Option 2: Using the Bash Script**

Simply run the included script for a quick start:
```bash
./run_brightness_tool.sh
```
- Make sure to make it executable first with:
  ```bash
  chmod +x run_brightness_tool.sh
  ```
- The script takes care of paths and logging automatically.

With either method, the GUI will open, and you’re ready to use adaptive brightness controls on your monitors!
