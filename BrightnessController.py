import mss
import numpy as np
import screen_brightness_control as sbc
import sys

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

    def adjust_brightness_direct(self, value, monitor_id=0):
        """Directly adjusts brightness without fading."""
        try:
            sbc.set_brightness(value, display=self.getMonitor(monitor_id))
        except ValueError:
            print(f"Failed to set brightness to {value} on monitor {monitor_id}.")
            sys.exit(1)

    def adjust_brightness_with_hysterisis(self, current, target):
        """Adjusts brightness with hysteresis to avoid flickering."""
        if(abs(current - target) > self.threshold):
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

    def process_monitor(self, monitor, monitor_id, use_center=True):
        """Handles the workflow for a single monitor."""
        screenshot = np.array(mss.mss().grab(monitor))
        if use_center:
            Screen_background = self.get_center_brightness(screenshot)
        else:
            Screen_background = self.get_avg_brightness(screenshot)
        scaled = self.scale_brightness(Screen_background)
        current_brightness = self.get_current_brightness(monitor_id)
        desired_brightness = self.max_brightness - scaled  # Inversion logic
        self.adjust_brightness_with_hysterisis(current_brightness, desired_brightness)
        return {
            "Screen_background": Screen_background,
            "scaled": scaled,
            "current_brightness": current_brightness,
            "desired_brightness": desired_brightness
        }
    
    # IMP: update user input configs dynamically
    def update_user_config(self, new_config):
        self.min_brightness = new_config.get('min_brightness', self.min_brightness)
        self.max_brightness = new_config.get('max_brightness', self.max_brightness)
        self.threshold = new_config.get('threshold', self.threshold)
        self.monitors = new_config.get('monitors', self.monitors)