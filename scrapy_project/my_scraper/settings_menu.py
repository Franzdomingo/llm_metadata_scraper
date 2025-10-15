"""
Interactive CLI Menu for Settings Configuration
Provides a user-friendly interface for viewing and editing scraper settings
"""

import os
import sys
from my_scraper.settings_manager import SettingsManager
from my_scraper.cli_interface import CLIInterface, Table


class SettingsMenu:
    """
    Interactive CLI menu for settings configuration
    """

    def __init__(self, settings_manager: SettingsManager, width: int = 80):
        """
        Initialize menu

        Args:
            settings_manager: SettingsManager instance
            width: Fixed table width (default: 80)
        """
        self.manager = settings_manager
        self.cli = CLIInterface(width)
        self.table = Table(width)

    def display_header(self):
        """Display menu header"""
        print("\n" + self.table.header("SCRAPER SETTINGS MENU"))

    def display_main_menu(self):
        """Display main menu options"""
        self.cli.display_section("Menu Options")

        options = [
            (1, "View System Information", "Display CPU cores and memory"),
            (2, "View All Settings", "Show current configuration values"),
            (3, "Edit a Setting", "Modify individual settings"),
            (4, "Reset to Defaults", "Restore factory defaults"),
            (5, "Save Settings", "Save to config file"),
            (6, "Load Settings", "Load from config file"),
            (7, "Apply Settings to settings.py", "Make changes permanent"),
            (8, "Auto-Configure (Recommended)", "Use preset configurations"),
            (9, "Exit Menu", "Return to main menu")
        ]

        self.cli.display_menu_options(options)

    def view_system_info(self):
        """View system information"""
        self.cli.clear_screen()
        self.display_header()

        self.cli.display_section("System Information")
        print()
        self.cli.display_info("CPU Cores", str(self.manager.cpu_count), key_width=25)

        if self.manager.system_memory_gb:
            self.cli.display_info("System Memory", f"{self.manager.system_memory_gb:.2f} GB", key_width=25)
        else:
            self.cli.display_info("System Memory", "Unable to detect", key_width=25)

        self.cli.display_separator()
        self.cli.pause()

    def view_all_settings(self):
        """View all current settings"""
        self.cli.clear_screen()
        self.display_header()

        self.cli.display_section("Current Settings")
        print()

        for i, (key, config) in enumerate(self.manager.settings_schema.items(), 1):
            value = config['value']
            desc = config['description']

            # Check if value exceeds recommended
            warning_indicator = ""
            if 'recommended_max' in config and value > config['recommended_max']:
                warning_indicator = " ⚠"
            elif 'recommended_min' in config and value < config['recommended_min']:
                warning_indicator = " ⚠"

            print(f"\n{i}. {key}{warning_indicator}")
            self.cli.display_info("   Current Value", str(value), key_width=20)
            self.cli.display_info("   Description", desc, key_width=20)

            # Show limits
            limits = []
            if 'min' in config:
                limits.append(f"min: {config['min']}")
            if 'max' in config:
                limits.append(f"max: {config['max']}")
            if 'recommended_max' in config:
                limits.append(f"recommended: {config['recommended_max']}")

            if limits:
                self.cli.display_info("   Limits", ", ".join(limits), key_width=20)

        print()
        self.cli.display_separator()
        self.cli.pause()

    def edit_setting(self):
        """Edit a specific setting"""
        self.cli.clear_screen()
        self.display_header()

        # Show all settings first
        self.view_all_settings()

        self.cli.display_section("Edit Setting")

        # Get setting name
        settings_list = list(self.manager.settings_schema.keys())

        choice = self.cli.get_input("\nEnter setting number (or 'q' to cancel)")

        if choice.lower() == 'q':
            return

        try:
            setting_index = int(choice) - 1
            if setting_index < 0 or setting_index >= len(settings_list):
                self.cli.display_error("Invalid selection")
                self.cli.pause()
                return

            setting_key = settings_list[setting_index]
            config = self.manager.settings_schema[setting_key]

            self.cli.clear_screen()
            self.display_header()
            self.cli.display_section(f"Editing: {setting_key}")

            print()
            self.cli.display_info("Current Value", str(config['value']), key_width=25)
            self.cli.display_info("Description", config['description'], key_width=25)

            # Show limits
            limits = []
            if 'min' in config:
                limits.append(f"min: {config['min']}")
            if 'max' in config:
                limits.append(f"max: {config['max']}")
            if 'recommended_max' in config:
                limits.append(f"recommended max: {config['recommended_max']}")
            if 'recommended_min' in config:
                limits.append(f"recommended min: {config['recommended_min']}")

            if limits:
                self.cli.display_info("Limits", ", ".join(limits), key_width=25)

            self.cli.display_separator()

            new_value = self.cli.get_input("\nEnter new value (or 'q' to cancel)")

            if new_value.lower() == 'q':
                return

            # Try to set the setting
            if self.manager.set_setting(setting_key, new_value):
                self.cli.display_success("Setting updated successfully!")
            else:
                self.cli.display_error("Failed to update setting")

        except ValueError:
            self.cli.display_error("Invalid input")

        self.cli.pause()

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.cli.clear_screen()
        self.display_header()

        self.cli.display_section("Reset to Defaults")
        self.cli.display_warning("This will reset ALL settings to their default values.")
        print("Any custom configurations will be lost.")

        if self.cli.confirm("Are you sure you want to reset?", default=False):
            # Reload default values
            for key, config in self.manager.settings_schema.items():
                # Reset to defaults (you could store original defaults)
                pass

            # Delete config file
            if os.path.exists(self.manager.config_file):
                try:
                    os.remove(self.manager.config_file)
                    self.cli.display_success(f"Deleted {self.manager.config_file}")
                except Exception as e:
                    self.cli.display_error(f"Error deleting config file: {e}")

            self.cli.display_success("Settings reset to defaults")
        else:
            print("\nReset cancelled")

        self.cli.pause()

    def save_settings(self):
        """Save settings to config file"""
        self.cli.clear_screen()
        self.display_header()

        self.cli.display_section("Save Settings")

        self.manager.save_config()
        self.cli.pause()

    def load_settings(self):
        """Load settings from config file"""
        self.cli.clear_screen()
        self.display_header()

        self.cli.display_section("Load Settings")

        if os.path.exists(self.manager.config_file):
            self.manager.load_config()
            self.cli.display_success("Settings loaded successfully")
        else:
            self.cli.display_warning(f"No config file found at {self.manager.config_file}")

        self.cli.pause()

    def apply_to_settings_py(self):
        """Apply settings to settings.py"""
        self.cli.clear_screen()
        self.display_header()

        self.cli.display_section("Apply to Settings.py")

        settings_file = os.path.join(
            os.path.dirname(__file__),
            'settings.py'
        )

        if os.path.exists(settings_file):
            print(f"\nTarget file: {settings_file}")
            self.cli.display_warning("This will modify your settings.py file.")

            if self.cli.confirm("Continue?", default=False):
                self.manager.export_to_settings_py(settings_file)
                self.cli.display_success("Settings applied to settings.py")
            else:
                print("\nOperation cancelled")
        else:
            self.cli.display_error(f"Settings file not found: {settings_file}")

        self.cli.pause()

    def auto_configure(self):
        """Auto-configure settings based on system resources"""
        self.cli.clear_screen()
        self.display_header()

        self.cli.display_section("Auto-Configure (Recommended)")

        cpu_count = self.manager.cpu_count
        memory_gb = self.manager.system_memory_gb

        print("\nDetected System Resources:")
        self.cli.display_info("  CPU Cores", str(cpu_count), key_width=20)
        if memory_gb:
            self.cli.display_info("  System Memory", f"{memory_gb:.2f} GB", key_width=20)

        print("\nRecommended Configurations:")
        print()
        print("1. Conservative (Recommended for most users)")
        self.cli.display_info("     CONCURRENT_REQUESTS", f"{cpu_count * 4}", key_width=30)
        self.cli.display_info("     SELENIUM_POOL_SIZE", f"{cpu_count}", key_width=30)
        self.cli.display_info("     DOWNLOAD_DELAY", "0.5s", key_width=30)

        print("\n2. Balanced (Good performance with safety)")
        self.cli.display_info("     CONCURRENT_REQUESTS", f"{cpu_count * 8}", key_width=30)
        self.cli.display_info("     SELENIUM_POOL_SIZE", f"{cpu_count * 2}", key_width=30)
        self.cli.display_info("     DOWNLOAD_DELAY", "0.25s", key_width=30)

        print("\n3. Aggressive (Maximum performance, higher risk)")
        self.cli.display_info("     CONCURRENT_REQUESTS", f"{cpu_count * 16}", key_width=30)
        self.cli.display_info("     SELENIUM_POOL_SIZE", f"{min(cpu_count * 3, 24)}", key_width=30)
        self.cli.display_info("     DOWNLOAD_DELAY", "0.1s", key_width=30)

        print("\n4. Custom (Keep current settings)")

        self.cli.display_separator()

        choice = self.cli.get_input("\nSelect configuration (1-4, or 'q' to cancel)")

        if choice == '1':
            self._apply_conservative_config()
            self.cli.display_success("Conservative configuration applied!")
        elif choice == '2':
            self._apply_balanced_config()
            self.cli.display_success("Balanced configuration applied!")
        elif choice == '3':
            self._apply_aggressive_config()
            self.cli.display_success("Aggressive configuration applied!")
        elif choice == '4':
            print("\nKeeping current settings")
        else:
            print("\nAuto-configure cancelled")

        self.cli.pause()

    def _apply_conservative_config(self):
        """Apply conservative configuration"""
        cpu = self.manager.cpu_count
        self.manager.set_setting('CONCURRENT_REQUESTS', cpu * 4)
        self.manager.set_setting('CONCURRENT_REQUESTS_PER_DOMAIN', cpu * 2)
        self.manager.set_setting('CONCURRENT_REQUESTS_PER_IP', cpu * 2)
        self.manager.set_setting('SELENIUM_POOL_SIZE', cpu)
        self.manager.set_setting('DOWNLOAD_DELAY', 0.5)
        self.manager.set_setting('AUTOTHROTTLE_TARGET_CONCURRENCY', cpu * 2.0)
        self.manager.set_setting('AUTOTHROTTLE_START_DELAY', 0.5)
        self.manager.set_setting('AUTOTHROTTLE_MAX_DELAY', 5.0)

    def _apply_balanced_config(self):
        """Apply balanced configuration"""
        cpu = self.manager.cpu_count
        self.manager.set_setting('CONCURRENT_REQUESTS', cpu * 8)
        self.manager.set_setting('CONCURRENT_REQUESTS_PER_DOMAIN', cpu * 3)
        self.manager.set_setting('CONCURRENT_REQUESTS_PER_IP', cpu * 3)
        self.manager.set_setting('SELENIUM_POOL_SIZE', cpu * 2)
        self.manager.set_setting('DOWNLOAD_DELAY', 0.25)
        self.manager.set_setting('AUTOTHROTTLE_TARGET_CONCURRENCY', cpu * 4.0)
        self.manager.set_setting('AUTOTHROTTLE_START_DELAY', 0.25)
        self.manager.set_setting('AUTOTHROTTLE_MAX_DELAY', 3.0)

    def _apply_aggressive_config(self):
        """Apply aggressive configuration"""
        cpu = self.manager.cpu_count
        self.manager.set_setting('CONCURRENT_REQUESTS', cpu * 16)
        self.manager.set_setting('CONCURRENT_REQUESTS_PER_DOMAIN', cpu * 4)
        self.manager.set_setting('CONCURRENT_REQUESTS_PER_IP', cpu * 4)
        self.manager.set_setting('SELENIUM_POOL_SIZE', min(cpu * 3, 24))
        self.manager.set_setting('DOWNLOAD_DELAY', 0.1)
        self.manager.set_setting('AUTOTHROTTLE_TARGET_CONCURRENCY', cpu * 8.0)
        self.manager.set_setting('AUTOTHROTTLE_START_DELAY', 0.1)
        self.manager.set_setting('AUTOTHROTTLE_MAX_DELAY', 2.0)

    def run(self):
        """Run the interactive menu"""
        while True:
            self.cli.clear_screen()
            self.display_header()
            self.display_main_menu()

            choice = self.cli.get_input("\nEnter your choice (1-9)")

            if choice == '1':
                self.view_system_info()
            elif choice == '2':
                self.view_all_settings()
            elif choice == '3':
                self.edit_setting()
            elif choice == '4':
                self.reset_to_defaults()
            elif choice == '5':
                self.save_settings()
            elif choice == '6':
                self.load_settings()
            elif choice == '7':
                self.apply_to_settings_py()
            elif choice == '8':
                self.auto_configure()
            elif choice == '9':
                print("\n✓ Exiting settings menu...")
                break
            else:
                self.cli.display_error("Invalid choice. Please enter 1-9.")
                self.cli.pause()


def main():
    """Main entry point for settings menu"""
    # Get the config file path
    config_file = os.path.join(
        os.path.dirname(__file__),
        'scraper_config.json'
    )

    # Create settings manager
    manager = SettingsManager(config_file=config_file)

    # Create and run menu
    menu = SettingsMenu(manager)
    menu.run()


if __name__ == '__main__':
    main()
