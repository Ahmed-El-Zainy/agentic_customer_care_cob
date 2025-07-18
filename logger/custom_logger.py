import logging
import os
import yaml
from datetime import datetime
import sys

# fmt: off
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.append(os.path.dirname(PARENT_DIR))

class CustomLoggerTracker:
    def __init__(self, config_path='logging_config.yaml'):
        """Initialize the custom logger with configuration."""
        self.config = self._load_config(config_path)
        self.loggers = {}
        self.base_log_dir = self.config.get('base_log_dir', 'logs')
        self._setup_base_directory()
        
    def _load_config(self, config_path):
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            # Default configuration if file not found
            return {
                'base_log_dir': 'logs',
                'default_level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'console_output': True,
                'modules': {
                    'main': {'level': 'INFO'},
                    'detection': {'level': 'INFO'},
                    'language_classification': {'level': 'INFO'},
                    'recognition': {'level': 'INFO'},
                    'registration': {'level': 'INFO'},
                    'metadata': {'level': 'INFO'}
                }
            }

    def _setup_base_directory(self):
        """Setup the base directory structure for logs."""
        if not os.path.exists(self.base_log_dir):
            os.makedirs(self.base_log_dir)

    def _get_log_path(self, module_name):
        """Generate the hierarchical path for log files."""
        now = datetime.now()
        year_dir = os.path.join(self.base_log_dir, str(now.year))
        month_dir = os.path.join(year_dir, f"{now.month:02d}")
        day_dir = os.path.join(month_dir, f"{now.day:02d}")
        os.makedirs(day_dir, exist_ok=True)
        return os.path.join(day_dir, f"{module_name}.log")

    def get_logger(self, module_name):
        """Get or create a logger for a specific module."""
        if module_name in self.loggers:
            return self.loggers[module_name]

        # Create new logger & Models Spceific Config
        logger = logging.getLogger(module_name)
        module_config = self.config['modules'].get(module_name, {})
        level = getattr(logging, module_config.get('level', self.config['default_level']))
        logger.setLevel(level)

        # Create formatter
        formatter = logging.Formatter(self.config.get('format'))

        # Create file handler with the hierarchical path
        log_path = self._get_log_path(module_name)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Optionally add console handler
        if self.config.get('console_output', True):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        self.loggers[module_name] = logger
        return logger

    def update_config(self, new_config):
        """Update logger configuration."""
        self.config.update(new_config)
        # Reset all loggers to apply new configuration
        for module_name in self.loggers:
            logger = self.loggers[module_name]
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
        self.loggers = {}
        
if __name__ == "__main__":
    # Create an instance first
    logger_tracker = CustomLoggerTracker()
    
    # Get a logger for the registration module
    logger = logger_tracker.get_logger("registration")
    
    # Test the logger
    logger.info("This is a test message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # Test another module
    detection_logger = logger_tracker.get_logger("detection")
    detection_logger.info("Detection module test message")