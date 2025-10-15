#!/usr/bin/env python3
"""
Main entry point for LLM Metadata Scraper
Automatically detects and runs available Scrapy spiders

Usage:
    python main.py                      # Interactive menu
    python main.py --list               # List all spiders
    python main.py --spider <name>      # Run specific spider
    python main.py --all                # Run all spiders in sequence
"""

import argparse
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from my_scraper.spider_manager import SpiderManager
from my_scraper.cli_interface import CLIInterface, SpiderMenuInterface
from my_scraper.settings_manager import SettingsManager
from my_scraper.settings_menu import SettingsMenu


class ScraperApplication:
    """Main application controller"""

    def __init__(self):
        """Initialize the scraper application"""
        self.project_dir = Path(__file__).parent
        self.spider_manager = SpiderManager(self.project_dir)
        self.cli = CLIInterface(width=80)
        self.menu = SpiderMenuInterface(self.cli)

    def list_spiders(self):
        """Display all detected spiders in a formatted table"""
        spiders = self.spider_manager.get_all_spiders()

        if not spiders:
            self.cli.display_error("No spiders detected!")
            return

        self.cli.display_header("AVAILABLE SPIDERS")
        print()

        # Display in table format
        for i, spider in enumerate(spiders, 1):
            print(f"{i}. {spider['name']}")
            self.cli.display_info("   Description", spider['description'], key_width=18)

            if spider['parameters']:
                self.cli.display_info("   Parameters", "", key_width=18)
                for param_name, param_type, default in spider['parameters']:
                    default_str = f"(default: {default})" if default != "None" else "(required)"
                    print(f"      - {param_name} ({param_type}) {default_str}")

            self.cli.display_info("   Module", f"{spider['module']}.py", key_width=18)
            print()

        self.cli.display_separator("=")

    def run_spider(self, spider_name: str, spider_args: dict = None):
        """
        Run a specific spider

        Args:
            spider_name: Name of the spider to run
            spider_args: Optional spider arguments
        """
        spider_info = self.spider_manager.get_spider_by_name(spider_name)

        if not spider_info:
            self.cli.display_error(f"Spider '{spider_name}' not found!")
            self.list_spiders()
            return False

        self.menu.display_execution_header(spider_name)

        success = self.spider_manager.run_spider(spider_name, spider_args)

        if success:
            self.cli.display_success(f"Spider '{spider_name}' completed!")
        else:
            self.cli.display_error(f"Spider '{spider_name}' failed!")

        return success

    def run_all_spiders(self):
        """Run all spiders in sequence"""
        spiders = self.spider_manager.get_all_spiders()

        if not spiders:
            self.cli.display_error("No spiders detected!")
            return

        self.cli.display_header("RUNNING ALL SPIDERS")
        print("\nExecuting spiders with intelligent chaining...\n")
        self.cli.display_separator()

        results = self.spider_manager.run_all_spiders()

        # Display summary
        self.menu.display_summary(results)

    def open_settings_menu(self):
        """Open the settings configuration menu"""
        try:
            # Get config file path
            config_file = self.project_dir / 'my_scraper' / 'scraper_config.json'

            # Create settings manager and menu
            manager = SettingsManager(config_file=str(config_file))
            settings_menu = SettingsMenu(manager)

            # Run the settings menu
            settings_menu.run()

        except ImportError as e:
            self.cli.display_error(f"Settings menu module not found: {e}")
            print("[!] Make sure settings_manager.py and settings_menu.py are in my_scraper/")
        except Exception as e:
            self.cli.display_error(f"Error opening settings menu: {e}")
            import traceback
            traceback.print_exc()

    def interactive_menu(self):
        """Display interactive menu for spider selection"""
        while True:
            spiders = self.spider_manager.get_all_spiders()

            # Prepare extra options
            num_spiders = len(spiders)
            extra_options = [
                (num_spiders + 1, "Run ALL Spiders", "Execute all spiders in sequence"),
                (num_spiders + 2, "Settings Menu", "Configure scraper performance settings"),
                (0, "Exit", "Quit the application")
            ]

            # Display menu
            self.menu.display_main_menu(spiders, extra_options)

            # Get user choice
            try:
                choice = self.menu.get_spider_choice(num_spiders, len(extra_options))

                if choice == '0':
                    print("\n✓ Goodbye!\n")
                    break

                choice_num = int(choice)

                if choice_num == num_spiders + 1:
                    # Run all spiders
                    self.run_all_spiders()
                    self.cli.pause()
                    break  # Exit after running all

                elif choice_num == num_spiders + 2:
                    # Open settings menu
                    self.open_settings_menu()
                    continue  # Return to main menu after settings

                elif 1 <= choice_num <= num_spiders:
                    # Run selected spider
                    spider = self.spider_manager.get_spider_by_index(choice_num - 1)

                    if spider:
                        # Show spider details
                        self.menu.display_spider_details(spider)

                        # Get parameters if needed
                        spider_args = self.menu.get_spider_parameters(spider)

                        # Confirm execution
                        if self.cli.confirm("Run this spider?", default=True):
                            self.run_spider(spider['name'], spider_args)
                            self.cli.pause()
                            break  # Exit after running

                else:
                    self.cli.display_error(f"Invalid choice! Please select 0-{num_spiders + len(extra_options)}")
                    self.cli.pause()

            except ValueError:
                self.cli.display_error("Invalid input! Please enter a number.")
                self.cli.pause()
            except KeyboardInterrupt:
                print("\n\n✓ Interrupted. Goodbye!\n")
                break
            except Exception as e:
                self.cli.display_error(f"Unexpected error: {e}")
                import traceback
                traceback.print_exc()
                self.cli.pause()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='LLM Metadata Scraper - Automatically detect and run spiders',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                    # Interactive menu
  python main.py --list                             # List all spiders
  python main.py --spider kaggle_links              # Run specific spider
  python main.py --spider kaggle_links --args max_pages=10
  python main.py --spider kaggle_metadata --args input_file=output/file.csv
  python main.py --all                              # Run all spiders
        """
    )

    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List all available spiders'
    )

    parser.add_argument(
        '--spider', '-s',
        type=str,
        help='Run specific spider by name'
    )

    parser.add_argument(
        '--args', '-a',
        type=str,
        help='Spider arguments in format: key1=value1,key2=value2'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all spiders in sequence'
    )

    args = parser.parse_args()

    # Initialize application
    app = ScraperApplication()

    # Handle different modes
    if args.list:
        app.list_spiders()

    elif args.spider:
        # Parse spider arguments
        spider_args = {}
        if args.args:
            for arg in args.args.split(','):
                if '=' in arg:
                    key, value = arg.split('=', 1)
                    spider_args[key.strip()] = value.strip()

        app.run_spider(args.spider, spider_args)

    elif args.all:
        app.run_all_spiders()

    else:
        # Interactive menu
        app.interactive_menu()


if __name__ == '__main__':
    main()
