import threading
import time

class MonitorThread(threading.Thread):
    def __init__(self, controller, monitor, monitor_id, config_frame, update_status_callback):
        super().__init__(daemon=True)
        self.controller = controller
        self.monitor = monitor
        self.monitor_id = monitor_id
        self.config_frame = config_frame
        # self.use_center = use_center
        # self.interval = interval
        self.update_status_callback = update_status_callback
        self._running = True

    def run(self):
        import mss  # Local import for thread safety with mss
        with mss.mss() as sct:
            while self._running:
                try:
                    config = self.config_frame.get_config()
                    self.controller.update_user_config(config)

                    summary = self.controller.process_monitor(
                        monitor=self.monitor,
                        monitor_id=self.monitor_id,
                        use_center=config['use_center']
                    )
                    if self.update_status_callback:
                        status_text = f"Monitor {self.monitor_id}: {int(summary['desired_brightness'])} (auto)"
                        self.update_status_callback(self.monitor_id, status_text)
                except Exception as e:
                    if self.update_status_callback:
                        self.update_status_callback(self.monitor_id, f"Error: {e}")
                time.sleep(config['interval'])

    def stop(self):
        self._running = False
