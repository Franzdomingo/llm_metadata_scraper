"""
Interactive Settings Manager for Scrapy Spider
Allows users to view, edit, and validate scraper settings with safety caps
"""

import os
import json
import multiprocessing
from typing import Dict, Any, Optional


class SettingsManager:
    """
    Manages scraper settings with validation, caps, and persistence
    """

    def __init__(self, config_file='scraper_config.json'):
        """
        Initialize settings manager

        Args:
            config_file: Path to JSON config file for persistence
        """
        self.config_file = config_file
        self.cpu_count = multiprocessing.cpu_count()

        # Try to detect system memory
        try:
            if hasattr(os, 'sysconf'):
                self.system_memory_gb = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024.**3)
            else:
                # Fallback for Windows
                import psutil
                self.system_memory_gb = psutil.virtual_memory().total / (1024.**3)
        except:
            self.system_memory_gb = None

        # Default settings with validation rules
        self.settings_schema = {
            'CONCURRENT_REQUESTS': {
                'value': 64,
                'min': 1,
                'max': 256,
                'recommended_max': self.cpu_count * 8,
                'type': int,
                'description': 'Maximum concurrent requests',
                'warning': 'High values may overwhelm your CPU and network'
            },
            'CONCURRENT_REQUESTS_PER_DOMAIN': {
                'value': 24,
                'min': 1,
                'max': 128,
                'recommended_max': self.cpu_count * 4,
                'type': int,
                'description': 'Concurrent requests per domain',
                'warning': 'Too high may get you blocked by the target site'
            },
            'CONCURRENT_REQUESTS_PER_IP': {
                'value': 24,
                'min': 1,
                'max': 128,
                'recommended_max': self.cpu_count * 4,
                'type': int,
                'description': 'Concurrent requests per IP',
                'warning': 'Too high may get you blocked by the target site'
            },
            'DOWNLOAD_DELAY': {
                'value': 0.25,
                'min': 0.0,
                'max': 10.0,
                'recommended_min': 0.1,
                'type': float,
                'description': 'Delay between requests (seconds)',
                'warning': 'Very low delays may get you blocked; 0 delay is aggressive'
            },
            'AUTOTHROTTLE_TARGET_CONCURRENCY': {
                'value': 16.0,
                'min': 1.0,
                'max': 100.0,
                'recommended_max': self.cpu_count * 2.0,
                'type': float,
                'description': 'AutoThrottle target concurrency',
                'warning': 'Should generally be lower than CONCURRENT_REQUESTS'
            },
            'SELENIUM_POOL_SIZE': {
                'value': 16,
                'min': 1,
                'max': self.cpu_count * 4,
                'recommended_max': self.cpu_count * 2,
                'type': int,
                'description': 'Number of concurrent Selenium drivers',
                'warning': 'Each driver uses significant memory (~100-200MB). High values may exhaust system memory'
            },
            'AUTOTHROTTLE_START_DELAY': {
                'value': 0.25,
                'min': 0.0,
                'max': 10.0,
                'recommended_min': 0.1,
                'type': float,
                'description': 'Initial AutoThrottle delay (seconds)',
                'warning': 'Very low values may cause rate limiting'
            },
            'AUTOTHROTTLE_MAX_DELAY': {
                'value': 3.0,
                'min': 0.5,
                'max': 60.0,
                'recommended_max': 10.0,
                'type': float,
                'description': 'Maximum AutoThrottle delay (seconds)',
                'warning': 'High values will slow down scraping significantly'
            },
        }

        # Load saved config if exists
        self.load_config()

    def load_config(self) -> None:
        """Load settings from config file if it exists"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    saved_settings = json.load(f)

                # Update values from saved config
                for key, value in saved_settings.items():
                    if key in self.settings_schema:
                        self.settings_schema[key]['value'] = value

                print(f"✓ Loaded settings from {self.config_file}")
            except Exception as e:
                print(f"⚠ Warning: Could not load config file: {e}")

    def save_config(self) -> None:
        """Save current settings to config file"""
        try:
            settings_to_save = {
                key: config['value']
                for key, config in self.settings_schema.items()
            }

            with open(self.config_file, 'w') as f:
                json.dump(settings_to_save, indent=2, fp=f)

            print(f"✓ Settings saved to {self.config_file}")
        except Exception as e:
            print(f"✗ Error saving settings: {e}")

    def get_setting(self, key: str) -> Any:
        """Get a setting value"""
        if key in self.settings_schema:
            return self.settings_schema[key]['value']
        return None

    def validate_setting(self, key: str, value: Any) -> tuple[bool, Optional[str]]:
        """
        Validate a setting value

        Args:
            key: Setting name
            value: Value to validate

        Returns:
            Tuple of (is_valid, warning_message)
        """
        if key not in self.settings_schema:
            return False, f"Unknown setting: {key}"

        config = self.settings_schema[key]
        warnings = []

        # Type checking
        try:
            if config['type'] == int:
                value = int(value)
            elif config['type'] == float:
                value = float(value)
        except ValueError:
            return False, f"Invalid type. Expected {config['type'].__name__}"

        # Range validation
        if 'min' in config and value < config['min']:
            return False, f"Value too low. Minimum is {config['min']}"

        if 'max' in config and value > config['max']:
            return False, f"Value too high. Maximum is {config['max']}"

        # Recommended range warnings
        if 'recommended_min' in config and value < config['recommended_min']:
            warnings.append(f"⚠ WARNING: Below recommended minimum of {config['recommended_min']}")

        if 'recommended_max' in config and value > config['recommended_max']:
            warnings.append(f"⚠ WARNING: Above recommended maximum of {config['recommended_max']}")

        # Setting-specific warnings
        if 'warning' in config and warnings:
            warnings.append(f"⚠ {config['warning']}")

        # Special validations
        if key == 'SELENIUM_POOL_SIZE' and self.system_memory_gb:
            estimated_memory_gb = value * 0.15  # ~150MB per driver
            if estimated_memory_gb > self.system_memory_gb * 0.7:
                warnings.append(
                    f"⚠ WARNING: {value} drivers may use ~{estimated_memory_gb:.1f}GB RAM "
                    f"(you have {self.system_memory_gb:.1f}GB total)"
                )

        warning_msg = "\n".join(warnings) if warnings else None
        return True, warning_msg

    def set_setting(self, key: str, value: Any) -> bool:
        """
        Set a setting value with validation

        Args:
            key: Setting name
            value: New value

        Returns:
            True if successful, False otherwise
        """
        is_valid, warning = self.validate_setting(key, value)

        if not is_valid:
            print(f"\n✗ Invalid value: {warning}")
            return False

        # Convert to proper type
        config = self.settings_schema[key]
        if config['type'] == int:
            value = int(value)
        elif config['type'] == float:
            value = float(value)

        if warning:
            print(f"\n{warning}")
            response = input("\nDo you want to continue anyway? (y/n): ").strip().lower()
            if response != 'y':
                print("Setting not changed.")
                return False

        self.settings_schema[key]['value'] = value
        print(f"✓ {key} set to {value}")
        return True

    def display_system_info(self) -> None:
        """Display system information"""
        print("\n" + "="*70)
        print("SYSTEM INFORMATION")
        print("="*70)
        print(f"CPU Cores: {self.cpu_count}")
        if self.system_memory_gb:
            print(f"System Memory: {self.system_memory_gb:.2f} GB")
        else:
            print("System Memory: Unable to detect")
        print("="*70)

    def display_all_settings(self) -> None:
        """Display all settings in a formatted table"""
        print("\n" + "="*70)
        print("CURRENT SETTINGS")
        print("="*70)

        for i, (key, config) in enumerate(self.settings_schema.items(), 1):
            value = config['value']
            desc = config['description']

            # Check if value exceeds recommended
            warning_indicator = ""
            if 'recommended_max' in config and value > config['recommended_max']:
                warning_indicator = " ⚠"
            elif 'recommended_min' in config and value < config['recommended_min']:
                warning_indicator = " ⚠"

            print(f"\n{i}. {key}{warning_indicator}")
            print(f"   Current: {value}")
            print(f"   Description: {desc}")

            # Show limits
            limits = []
            if 'min' in config:
                limits.append(f"min: {config['min']}")
            if 'max' in config:
                limits.append(f"max: {config['max']}")
            if 'recommended_max' in config:
                limits.append(f"recommended max: {config['recommended_max']}")
            if limits:
                print(f"   Limits: {', '.join(limits)}")

        print("\n" + "="*70)

    def get_settings_dict(self) -> Dict[str, Any]:
        """Get all settings as a dictionary"""
        return {
            key: config['value']
            for key, config in self.settings_schema.items()
        }

    def export_to_settings_py(self, settings_file: str) -> None:
        """
        Update settings.py file with current values

        Args:
            settings_file: Path to settings.py file
        """
        try:
            # Read the current settings.py
            with open(settings_file, 'r') as f:
                lines = f.readlines()

            # Update values
            updated_lines = []
            for line in lines:
                updated = False
                for key, config in self.settings_schema.items():
                    if line.strip().startswith(f"{key} ="):
                        value = config['value']
                        updated_lines.append(f"{key} = {value}\n")
                        updated = True
                        break
                if not updated:
                    updated_lines.append(line)

            # Write back
            with open(settings_file, 'w') as f:
                f.writelines(updated_lines)

            print(f"✓ Updated {settings_file}")
        except Exception as e:
            print(f"✗ Error updating settings.py: {e}")
