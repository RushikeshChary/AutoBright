"""
BrightnessApp.py

A GUI tool for adaptive screen brightness control across multiple monitors.

Features:
- Manual and automatic brightness adjustment.
- Per-monitor configuration and status display.
- Uses screen content analysis to reduce eye strain.
- Supports user-configurable intervals, thresholds, and regions.

Dependencies:
- tkinter (for GUI)
- mss (for screen capture)
- numpy (for image processing, assumed in logic)
- BrightnessController, ConfigLoader, MonitorThread (local modules)

Usage:
    python BrightnessApp.py [--config CONFIG_PATH] [--user-config USER_CONFIG_PATH]

Author: [Your Name]
Date: [Date]
"""

import tkinter as tk
from tkinter import ttk
import argparse
from tkinter import messagebox
import mss
import BrightnessController as BNC
import ConfigLoader as CFL
import MonitorThread as MT

# ----------------- Helper Classes -----------------

class ConfigInputFrame(ttk.Frame):
    """
    Frame for user configuration input.

    Allows the user to set:
    - Interval (seconds between checks)
    - Min/Max brightness
    - Brightness threshold
    - Whether to use only the center region of the screen
    - Which monitors to control
    """
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
        """
        Returns the current configuration as a dictionary.
        """
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

# ----------------- Main Application -----------------

class BrightnessApp(tk.Tk):
    """
    Main application window for adaptive brightness control.

    Attributes:
        controller: BrightnessController instance for hardware interaction.
        config: Current configuration dictionary.
        is_running: Whether auto mode is active.
        monitor_threads: List of running MonitorThread objects.
        status_labels: Dict of status labels per monitor.
    """
    def __init__(self, controller, config):
        """
        Initialize the GUI, widgets, and state.
        """
        super().__init__()
        self.title("Brightness Controller")
        self.geometry("500x340")
        self.controller = controller
        self.config = config
        self.is_running = False
        self.monitor_threads = []
        self.status_labels = {}

        # --- GUI Layout ---
        # Configuration input
        self.config_frame = ConfigInputFrame(self)
        self.config_frame.pack(pady=10, padx=10, fill='x')

        # Status area for per-monitor feedback
        self.status_area = ttk.Frame(self)
        self.status_area.pack(pady=4)

        # Manual brightness slider
        self.brightness_slider = ttk.Scale(self, from_=0, to=100, orient='horizontal', command=self.manual_brightness)
        # self.brightness_slider.set(50)
        ttk.Label(self, text='Manual Brightness').pack()
        self.brightness_slider.pack(padx=20, pady=8, fill='x')

        # Start/Stop buttons
        self.start_btn = ttk.Button(self, text="Start Auto", command=self.start)
        self.start_btn.pack(side='left', padx=10, pady=15)
        self.stop_btn = ttk.Button(self, text="Stop Auto", command=self.stop, state='disabled')
        self.stop_btn.pack(side='left', padx=10, pady=15)

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_status(self, monitor_id, message):
        """
        Update the status label for a specific monitor.
        """
        if monitor_id not in self.status_labels:
            label = ttk.Label(self.status_area, text=message)
            label.pack()
            self.status_labels[monitor_id] = label
        else:
            self.status_labels[monitor_id].config(text=message)

    def manual_brightness(self, value):
        """
        Set brightness manually for all selected monitors.
        Only works when auto mode is not running.
        """
        if not self.is_running:
            for mid in self.controller.monitors:
                self.controller.adjust_brightness_direct(int(float(value)), monitor_id=mid)
            # You may update a general info label here if you wish

    def start(self):
        """
        Start automatic brightness adjustment threads for each monitor.
        """
        self.is_running = True
        new_config = self.config_frame.get_config()
        self.config.update(new_config)
        self.controller.update_user_config(new_config)
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.brightness_slider.config(state='disabled')

        # Clear old threads and status labels
        self.monitor_threads = []
        for label in self.status_labels.values():
            label.destroy()
        self.status_labels = {}


        invalid_indices = []
        with mss.mss() as sct:
            monitor_ids = self.controller.monitors
            available = len(sct.monitors) - 1  # mss uses 1-based indexing
            for mid in monitor_ids:
                if mid < 0 or mid >= available:
                   invalid_indices.append(mid)
                   continue
                try:
                    monitor = sct.monitors[mid + 1]  # mss uses 1-based indexing
                except IndexError:
                    continue
                t = MT.MonitorThread(
                    self.controller,
                    monitor,
                    mid,
                    new_config['use_center'],
                    new_config['interval'],
                    self.update_status
                )
                t.start()
                self.monitor_threads.append(t)
        if invalid_indices:
            messagebox.showwarning(
                "Invalid Monitor Index",
                f"The following monitor indices are invalid and will be ignored: {invalid_indices}\n"
                f"Available monitors: 0 to {available-1}"
            )

    def stop(self):
        """
        Stop all monitor threads and re-enable manual controls.
        """
        self.is_running = False
        for thread in self.monitor_threads:
            thread.stop()
        for thread in self.monitor_threads:
            thread.join(timeout=1)
        self.monitor_threads = []
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.brightness_slider.config(state='normal')

    def on_closing(self):
        """
        Handle application close event.
        """
        self.stop()
        self.destroy()

# ----------------- Main Entry Point -----------------

if __name__ == "__main__":
    """
    Parse command-line arguments, load configuration, and launch the app.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to default config file")
    parser.add_argument("--user-config", help="Path to user config file")
    args = parser.parse_args()

    config_loader = CFL.ConfigLoader(args.config, args.user_config)

    controller = BNC.BrightnessController(
        min_brightness=config_loader.get('min_brightness', 0),
        max_brightness=config_loader.get('max_brightness', 100),
        threshold=config_loader.get('threshold', 10)
    )
    app = BrightnessApp(controller, config_loader)
    app.mainloop()
