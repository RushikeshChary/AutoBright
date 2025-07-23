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

class BrightnessApp(tk.Tk):
    def __init__(self, controller, config):
        super().__init__()
        self.title("Brightness Controller")
        self.geometry("400x240")
        self.controller = controller
        self.config = config
        self.is_running = False
        self.worker_thread = None

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
                        use_center=self.config.use_center
                    )
                    self.status_label.config(
                        text=f"Monitor {monitor_id}: {int(summary['desired_brightness'])} (auto)"
                    )
                time.sleep(self.config.interval)

    def on_closing(self):
        print("Exiting application...")
        self.stop()
        self.destroy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to default config file")
    parser.add_argument("--user-config", help="Path to user config file")
    args = parser.parse_args()

    print("Default config file:", args.config)
    print("User config file:", args.user_config)

    config_loader = CFL.ConfigLoader(args.config, args.user_config)

    controller = BNC.BrightnessController(
        min_brightness=config_loader.get('min_brightness', 0),
        max_brightness=config_loader.get('max_brightness', 100),
        threshold=config_loader.get('threshold', 10)
    )
    app = BrightnessApp(controller, config_loader)
    app.mainloop()
