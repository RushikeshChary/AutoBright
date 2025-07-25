import tkinter as tk
from tkinter import ttk
import threading
import time
import mss
import argparse
# Assume your logic and controller class is imported as BrightnessController
# from brightness_module import BrightnessController, ConfigLoader
import BrightnessController as BNC
import ConfigLoader as CFL

# Helper class to handle configuration input
# This class will be used to dynamically update the configuration based on user input
class ConfigInputFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        # Interval
        ttk.Label(self, text='Interval (seconds)').grid(row=0, column=0, sticky='w')
        self.interval_var = tk.IntVar(value=5)
        ttk.Entry(self, textvariable=self.interval_var, width=10).grid(row=0, column=1)

        # Min brightness
        ttk.Label(self, text='Min Brightness (0-100)').grid(row=1, column=0, sticky='w')
        self.min_brightness_var = tk.IntVar(value=10)
        ttk.Entry(self, textvariable=self.min_brightness_var, width=10).grid(row=1, column=1)

        # Max brightness
        ttk.Label(self, text='Max Brightness (0-100)').grid(row=2, column=0, sticky='w')
        self.max_brightness_var = tk.IntVar(value=90)
        ttk.Entry(self, textvariable=self.max_brightness_var, width=10).grid(row=2, column=1)

        # Threshold
        ttk.Label(self, text='Threshold').grid(row=3, column=0, sticky='w')
        self.threshold_var = tk.IntVar(value=8)
        ttk.Entry(self, textvariable=self.threshold_var, width=10).grid(row=3, column=1)

        # Use center region
        self.use_center_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self, text='Use center region', variable=self.use_center_var).grid(row=4, columnspan=2, sticky='w')

        # Monitor indices
        ttk.Label(self, text='Monitors (comma-separated)').grid(row=5, column=0, sticky='w')
        self.monitors_var = tk.StringVar(value='0,2')
        ttk.Entry(self, textvariable=self.monitors_var, width=10).grid(row=5, column=1)

        # Pack/present all in the frame
        self.pack(pady=10, padx=10, anchor='w')

    def get_config(self):
        # Safely parse monitors as list of ints
        monitors = [int(idx.strip()) for idx in self.monitors_var.get().split(',') if idx.strip().isdigit()]
        return {
            'interval': self.interval_var.get(),
            'min_brightness': self.min_brightness_var.get(),
            'max_brightness': self.max_brightness_var.get(),
            'threshold': self.threshold_var.get(),
            'use_center': self.use_center_var.get(),
            'monitors': monitors
        }

# Main application class
# This class will create the GUI and handle user interactions
class BrightnessApp(tk.Tk):
    def __init__(self, controller, config):
        super().__init__()
        self.title("Brightness Controller")
        self.geometry("500x340")
        self.controller = controller
        self.config = config
        self.is_running = False
        self.worker_thread = None

        # Configuration input frame
        self.config_frame = ConfigInputFrame(self)
        self.config_frame.pack(pady=10, padx=10, fill='x')

        # Status labels
        self.status_label = ttk.Label(self, text="Status: Idle")
        self.status_label.pack(pady=8)

        # Manual brightness slider
        self.brightness_slider = ttk.Scale(self, from_=0, to=100, orient='horizontal', command=self.manual_brightness)
        self.brightness_slider.set(50)  # Default value
        ttk.Label(self, text='Manual Brightness').pack()
        self.brightness_slider.pack(padx=20, pady=8, fill='x')

        # Start/stop buttons
        self.start_btn = ttk.Button(self, text="Start Auto", command=self.start)
        self.start_btn.pack(side='left', padx=10, pady=15)

        self.stop_btn = ttk.Button(self, text="Stop Auto", command=self.stop, state='disabled')
        self.stop_btn.pack(side='left', padx=10, pady=15)

        # Clean exit
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def manual_brightness(self, value):
        if not self.is_running:
            # Only allow manual when auto is off
            self.controller.adjust_brightness_direct(int(float(value)))
            self.status_label.config(text=f"Status: Manual brightness set to {int(float(value))}")
    
    def start(self):
        self.is_running = True
        # Load configuration from the input frame
        new_config = self.config_frame.get_config()
        self.config.update(new_config)
        self.controller.update_user_config(new_config)

        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.brightness_slider.config(state='disabled')  # Disable the slider
        self.status_label.config(text="Status: Running auto adjustment")
        self.worker_thread = threading.Thread(target=self.auto_loop, daemon=True)
        self.worker_thread.start()

    def stop(self):
        self.is_running = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.brightness_slider.config(state='normal')  # Enable the slider
        self.status_label.config(text="Status: Auto adjustment stopped")
    
    def auto_loop(self):
        with mss.mss() as sct:
            while self.is_running:
                # for monitor_id, monitor in enumerate(self.controller.monitors):
                for monitor_id, monitor in enumerate(sct.monitors[1:], start=1):
                    summary = self.controller.process_monitor(
                        monitor=monitor,
                        monitor_id=monitor_id-1,
                        use_center=self.config.get("use_center")
                    )
                    self.status_label.config(
                        text=f"Monitor {monitor_id}: {int(summary['desired_brightness'])} (auto)"
                    )
                time.sleep(self.config.get("interval"))

    def on_closing(self):
        # print("Exiting application...")
        self.stop()
        self.destroy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to default config file")
    parser.add_argument("--user-config", help="Path to user config file")
    args = parser.parse_args()

    # print("Default config file:", args.config)
    # print("User config file:", args.user_config)

    config_loader = CFL.ConfigLoader(args.config, args.user_config)

    controller = BNC.BrightnessController(
        min_brightness=config_loader.get('min_brightness', 0),
        max_brightness=config_loader.get('max_brightness', 100),
        threshold=config_loader.get('threshold', 10)
    )
    app = BrightnessApp(controller, config_loader)
    app.mainloop()
