import yaml

class ConfigLoader:
    def __init__(self, default_config_path=None, user_config_path=None):
        self.default_config_path = default_config_path
        self.user_config_path = user_config_path
        self.config = self.load_and_merge_configs()
        self.interval = self.get('interval')
        self.use_center = self.get('use_center')
        print(f"Using interval: {self.interval}, use_center: {self.use_center}")
        self.monitors = self.get('monitors')

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
