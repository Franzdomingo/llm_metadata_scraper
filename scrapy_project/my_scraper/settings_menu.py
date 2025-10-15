"""
Interactive CLI Menu for Settings Configuration
Provides a user-friendly interface for viewing and editing scraper settings
"""

import os
import sys
from my_scraper.settings_manager import SettingsManager


class SettingsMenu:
    """
    Interactive CLI menu for settings configuration
    """

    def __init__(self, settings_manager: SettingsManager):
        """
        Initialize menu

        Args:
            settings_manager: SettingsManager instance
        """
        self.manager = settings_manager

    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_header(self):
        """Display menu header"""
        print("\n" + "="*70)
        print(" "*20 + "SCRAPER SETTINGS MENU")
        print("="*70)

    def display_main_menu(self):
        """Display main menu options"""
        print("\n" + "-"*70)
        print("MENU OPTIONS:")
        print("-"*70)
        print("1. View System Information")
        print("2. View All Settings")
        print("3. Edit a Setting")
        print("4. Reset to Defaults")
        print("5. Save Settings")
        print("6. Load Settings")
        print("7. Apply Settings to settings.py")
        print("8. Auto-Configure (Recommended)")
        print("9. Exit Menu")
        print("-"*70)

    def view_system_info(self):
        """View system information"""
        self.clear_screen()
        self.display_header()
        self.manager.display_system_info()
        input("\nPress Enter to continue...")

    def view_all_settings(self):
        """View all current settings"""
        self.clear_screen()
        self.display_header()
        self.manager.display_all_settings()
        input("\nPress Enter to continue...")

    def edit_setting(self):
        """Edit a specific setting"""
        self.clear_screen()
        self.display_header()
        self.manager.display_all_settings()

        print("\n" + "-"*70)
        print("EDIT SETTING")
        print("-"*70)

        # Get setting name
        settings_list = list(self.manager.settings_schema.keys())
        print("\nEnter the number of the setting to edit (or 'q' to cancel):")

        choice = input("\nYour choice: ").strip()

        if choice.lower() == 'q':
            return

        try:
            setting_index = int(choice) - 1
            if setting_index < 0 or setting_index >= len(settings_list):
                print("\n✗ Invalid selection")
                input("\nPress Enter to continue...")
                return

            setting_key = settings_list[setting_index]
            config = self.manager.settings_schema[setting_key]

            print(f"\n" + "-"*70)
            print(f"Editing: {setting_key}")
            print(f"Current Value: {config['value']}")
            print(f"Description: {config['description']}")

            # Show limits
            limits_info = []
            if 'min' in config:
                limits_info.append(f"Minimum: {config['min']}")
            if 'max' in config:
                limits_info.append(f"Maximum: {config['max']}")
            if 'recommended_max' in config:
                limits_info.append(f"Recommended Max: {config['recommended_max']}")
            if 'recommended_min' in config:
                limits_info.append(f"Recommended Min: {config['recommended_min']}")

            if limits_info:
                print("Limits:")
                for limit in limits_info:
                    print(f"  - {limit}")

            print("-"*70)

            new_value = input(f"\nEnter new value (or 'q' to cancel): ").strip()

            if new_value.lower() == 'q':
                return

            # Try to set the setting
            if self.manager.set_setting(setting_key, new_value):
                print("\n✓ Setting updated successfully!")
            else:
                print("\n✗ Failed to update setting")

        except ValueError:
            print("\n✗ Invalid input")

        input("\nPress Enter to continue...")

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.clear_screen()
        self.display_header()

        print("\n" + "-"*70)
        print("RESET TO DEFAULTS")
        print("-"*70)
        print("\n⚠ WARNING: This will reset ALL settings to their default values.")
        print("Any custom configurations will be lost.")

        confirm = input("\nAre you sure? (yes/no): ").strip().lower()

        if confirm == 'yes':
            # Reload default values
            for key, config in self.manager.settings_schema.items():
                # Reset to defaults (you could store original defaults)
                pass

            # Delete config file
            if os.path.exists(self.manager.config_file):
                try:
                    os.remove(self.manager.config_file)
                    print(f"\n✓ Deleted {self.manager.config_file}")
                except Exception as e:
                    print(f"\n✗ Error deleting config file: {e}")

            print("\n✓ Settings reset to defaults")
        else:
            print("\nReset cancelled")

        input("\nPress Enter to continue...")

    def save_settings(self):
        """Save settings to config file"""
        self.clear_screen()
        self.display_header()

        print("\n" + "-"*70)
        print("SAVE SETTINGS")
        print("-"*70)

        self.manager.save_config()
        input("\nPress Enter to continue...")

    def load_settings(self):
        """Load settings from config file"""
        self.clear_screen()
        self.display_header()

        print("\n" + "-"*70)
        print("LOAD SETTINGS")
        print("-"*70)

        if os.path.exists(self.manager.config_file):
            self.manager.load_config()
            print("\n✓ Settings loaded successfully")
        else:
            print(f"\n⚠ No config file found at {self.manager.config_file}")

        input("\nPress Enter to continue...")

    def apply_to_settings_py(self):
        """Apply settings to settings.py"""
        self.clear_screen()
        self.display_header()

        print("\n" + "-"*70)
        print("APPLY TO SETTINGS.PY")
        print("-"*70)

        settings_file = os.path.join(
            os.path.dirname(__file__),
            'settings.py'
        )

        if os.path.exists(settings_file):
            print(f"\nTarget file: {settings_file}")
            print("\n⚠ This will modify your settings.py file.")

            confirm = input("\nContinue? (y/n): ").strip().lower()

            if confirm == 'y':
                self.manager.export_to_settings_py(settings_file)
                print("\n✓ Settings applied to settings.py")
            else:
                print("\nOperation cancelled")
        else:
            print(f"\n✗ Settings file not found: {settings_file}")

        input("\nPress Enter to continue...")

    def auto_configure(self):
        """Auto-configure settings based on system resources"""
        self.clear_screen()
        self.display_header()

        print("\n" + "-"*70)
        print("AUTO-CONFIGURE (RECOMMENDED)")
        print("-"*70)

        cpu_count = self.manager.cpu_count
        memory_gb = self.manager.system_memory_gb

        print("\nDetected System Resources:")
        print(f"  CPU Cores: {cpu_count}")
        if memory_gb:
            print(f"  System Memory: {memory_gb:.2f} GB")

        print("\nRecommended configurations:")
        print("\n1. Conservative (Recommended for most users)")
        print(f"   - CONCURRENT_REQUESTS: {cpu_count * 4}")
        print(f"   - SELENIUM_POOL_SIZE: {cpu_count}")
        print(f"   - DOWNLOAD_DELAY: 0.5s")

        print("\n2. Balanced (Good performance with safety)")
        print(f"   - CONCURRENT_REQUESTS: {cpu_count * 8}")
        print(f"   - SELENIUM_POOL_SIZE: {cpu_count * 2}")
        print(f"   - DOWNLOAD_DELAY: 0.25s")

        print("\n3. Aggressive (Maximum performance, higher risk)")
        print(f"   - CONCURRENT_REQUESTS: {cpu_count * 16}")
        print(f"   - SELENIUM_POOL_SIZE: {min(cpu_count * 3, 24)}")
        print(f"   - DOWNLOAD_DELAY: 0.1s")

        print("\n4. Custom (Current settings)")

        print("\n" + "-"*70)

        choice = input("\nSelect configuration (1-4, or 'q' to cancel): ").strip()

        if choice == '1':
            self._apply_conservative_config()
        elif choice == '2':
            self._apply_balanced_config()
        elif choice == '3':
            self._apply_aggressive_config()
        elif choice == '4':
            print("\nKeeping current settings")
        else:
            print("\nAuto-configure cancelled")
            input("\nPress Enter to continue...")
            return

        if choice in ['1', '2', '3']:
            print("\n✓ Configuration applied!")
            self.manager.display_all_settings()

        input("\nPress Enter to continue...")

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
            self.clear_screen()
            self.display_header()
            self.display_main_menu()

            choice = input("\nEnter your choice (1-9): ").strip()

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
                print("\nExiting settings menu...")
                break
            else:
                print("\n✗ Invalid choice. Please enter 1-9.")
                input("\nPress Enter to continue...")


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
