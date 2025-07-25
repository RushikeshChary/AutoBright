import mss
import numpy as np
import screen_brightness_control as sbc
import argparse
import yaml
import time
import sys

class ConfigLoader:
    def __init__(self, default_config_path=None, user_config_path=None):
        self.default_config_path = default_config_path
        self.user_config_path = user_config_path
        self.config = self.load_and_merge_configs()

    def load_yaml(self, filename):
        """Load YAML from a file gracefully, returning empty dict if file not found or empty."""
        try:
            with open(filename, 'r') as f:
                content = yaml.safe_load(f)
                return content if content is not None else {}
        except FileNotFoundError:
            return {}

    def load_and_merge_configs(self):
        """Merge user config over default config with fallback for missing keys."""
        default_config = self.load_yaml(self.default_config_path)
        user_config = self.load_yaml(self.user_config_path)
        # Merge: user values override default values
        merged_config = {**default_config, **user_config}
        return merged_config

    def get(self, key, default=None):
        """Safe getter for configuration values."""
        return self.config.get(key, default)


class BrightnessController:
    def __init__(self, min_brightness=0, max_brightness=100, threshold=10):
        self.threshold = threshold
        self.min_brightness = min_brightness
        self.max_brightness = max_brightness
        self.monitors = sbc.list_monitors()

    def getMonitor(self, monitor_id):
        """Fetches the monitor object by ID."""
        if monitor_id < len(self.monitors):
            return self.monitors[monitor_id]
        print(f"Monitor {monitor_id} not found.")
        return None

    def default_brightness(self):
        """Returns the default brightness value."""
        return (self.min_brightness + self.max_brightness) // 2
    
    def scale_brightness(self, value, min_value=0, max_value=255):
        """Scale the value from 0-255 to min_brightness-max_brightness range."""
        scaled = (value - min_value) / (max_value - min_value)
        return int(scaled * (self.max_brightness - self.min_brightness) + self.min_brightness)

    def get_current_brightness(self, monitor_id):
        """Fetches the current brightness setting."""
        try:
            return sbc.get_brightness()[monitor_id]
        except ValueError:
            print(f"Monitor {monitor_id} not found or brightness control not supported.")
            return self.default_brightness()
        
    def adjust_brightness_(self, value, monitor_id=0, attemptCount=0):
        """Adjusts system brightness with fading."""
        try:
            sbc.fade_brightness(value, interval=0.01, increment=1, display=self.getMonitor(monitor_id))
            attemptCount += 1
        except ValueError:
            if(attemptCount < 3):
                print(f"Failed to set brightness to {value}. Retrying...")
                self.adjust_brightness_(value, monitor_id, attemptCount)
            else:
                print(f"Failed to set brightness to {value}.")
                sys.exit(1)

    def adjust_brightness_with_hysterisis(self, current, target, threshold = 10):
        """Adjusts brightness with hysteresis to avoid flickering."""
        if(abs(current - target) > threshold):
            self.adjust_brightness_(target)

    def get_avg_brightness(self, img):
        """Calculates the mean brightness across the screenshot."""
        gray_img = np.mean(img, axis=2)  # Simple grayscale approximation
        return np.mean(gray_img)

    def get_center_brightness(self, img):
        """Calculates mean brightness in the center region of the screenshot."""
        h, w = img.shape[:2]
        center = img[h//4:3*h//4, w//4:3*w//4, :3]
        gray_center = np.mean(center, axis=2)
        return np.mean(gray_center)

    def process_monitor(self, monitor, monitor_id, use_center=False):
        """Handles the workflow for a single monitor."""
        screenshot = np.array(mss.mss().grab(monitor))
        if use_center:
            Screen_background = self.get_center_brightness(screenshot)
        else:
            Screen_background = self.get_avg_brightness(screenshot)
        scaled = self.scale_brightness(Screen_background)
        current_brightness = self.get_current_brightness(monitor_id)
        desired_brightness = self.max_brightness - scaled  # Inversion logic
        self.adjust_brightness_with_hysterisis(current_brightness, desired_brightness, self.threshold)
        return {
            "Screen_background": Screen_background,
            "scaled": scaled,
            "current_brightness": current_brightness,
            "desired_brightness": desired_brightness
        }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to default config file")
    parser.add_argument("--user-config", help="Path to user config file")
    args = parser.parse_args()

    print("Default config file:", args.config)
    print("User config file:", args.user_config)

    config_loader = ConfigLoader(args.config, args.user_config)

    controller = BrightnessController(
        min_brightness=config_loader.get('min_brightness', 0),
        max_brightness=config_loader.get('max_brightness', 100),
        threshold=config_loader.get('threshold', 10)
    )

    interval = config_loader.get('interval')
    use_center = config_loader.get('use_center')
    monitors = config_loader.get('monitors')

    with mss.mss() as sct:
        try:
            while True:
            # for monitor_id in monitors:
                for monitor_id, monitor in enumerate(sct.monitors[1:], start=1):
                    summary = controller.process_monitor(monitor, monitor_id - 1, use_center)
                    print(f"Monitor {monitor_id} - Screen background: {summary['Screen_background']:.2f} "
                            f"(Scaled: {summary['scaled']})")
                    print(f"Current Brightness: {summary['current_brightness']}")
                    print(f"Brightness adjusted to: {summary['desired_brightness']}")

                time.sleep(interval)
        except KeyboardInterrupt:
            print("Exiting brightness adjustment loop.")


if __name__ == "__main__":
   main()
