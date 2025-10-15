"""
CLI Interface Module
Handles all user interface and menu display logic with fixed-width tables
"""

import os
import sys
from typing import List, Dict, Optional, Callable


class Table:
    """Fixed-width table formatter for consistent CLI display"""

    def __init__(self, width: int = 80):
        """
        Initialize table formatter

        Args:
            width: Total width of the table (default: 80)
        """
        self.width = width
        self.padding = 2

    def separator(self, char: str = "=") -> str:
        """Create a separator line"""
        return char * self.width

    def header(self, text: str, char: str = "=") -> str:
        """Create a centered header"""
        return f"{self.separator(char)}\n{text.center(self.width)}\n{self.separator(char)}"

    def section_title(self, text: str, char: str = "-") -> str:
        """Create a section title"""
        return f"{self.separator(char)}\n{text.upper()}\n{self.separator(char)}"

    def row(self, *columns, align: str = "left") -> str:
        """
        Create a formatted row with multiple columns

        Args:
            columns: Column values
            align: Alignment ('left', 'right', 'center')
        """
        if len(columns) == 1:
            # Single column - just pad
            text = str(columns[0])
            if align == "center":
                return text.center(self.width)
            elif align == "right":
                return text.rjust(self.width)
            else:
                return text.ljust(self.width)

        # Multiple columns - distribute evenly
        col_width = (self.width - (len(columns) - 1) * self.padding) // len(columns)
        formatted_cols = []

        for col in columns:
            text = str(col)
            if align == "center":
                formatted_cols.append(text.center(col_width))
            elif align == "right":
                formatted_cols.append(text.rjust(col_width))
            else:
                formatted_cols.append(text.ljust(col_width))

        return (" " * self.padding).join(formatted_cols)

    def key_value(self, key: str, value: str, key_width: int = 30) -> str:
        """Create a key-value row"""
        value_width = self.width - key_width - self.padding
        return f"{str(key).ljust(key_width)}{' ' * self.padding}{str(value).ljust(value_width)}"

    def numbered_item(self, number: int, text: str, description: str = "") -> str:
        """Create a numbered menu item"""
        num_str = f"{number}."
        num_width = 4

        if description:
            # Number + text on one line, description indented below
            main_line = f"{num_str.ljust(num_width)}{text}"
            desc_line = f"{''.ljust(num_width)}  {description}"
            return f"{main_line}\n{desc_line}"
        else:
            return f"{num_str.ljust(num_width)}{text}"

    def wrap_text(self, text: str, indent: int = 0) -> str:
        """Wrap text to fit within table width"""
        max_width = self.width - indent
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > max_width:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)
            else:
                current_line.append(word)
                current_length += word_length

        if current_line:
            lines.append(" ".join(current_line))

        indent_str = " " * indent
        return "\n".join(indent_str + line for line in lines)


class CLIInterface:
    """Main CLI interface for the scraper application"""

    def __init__(self, width: int = 80):
        """
        Initialize CLI interface

        Args:
            width: Fixed width for all displays (default: 80)
        """
        self.width = width
        self.table = Table(width)

    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def pause(self, message: str = "Press Enter to continue..."):
        """Pause and wait for user input"""
        input(f"\n{message}")

    def get_input(self, prompt: str, default: str = "") -> str:
        """Get user input with optional default"""
        if default:
            prompt = f"{prompt} [{default}]"
        value = input(f"{prompt}: ").strip()
        return value if value else default

    def get_choice(self, prompt: str, valid_choices: List[str]) -> str:
        """Get user choice from a list of valid options"""
        while True:
            choice = input(f"\n{prompt}: ").strip()
            if choice in valid_choices:
                return choice
            print(f"✗ Invalid choice. Please select from: {', '.join(valid_choices)}")

    def confirm(self, message: str, default: bool = False) -> bool:
        """Ask for yes/no confirmation"""
        default_str = "Y/n" if default else "y/N"
        response = input(f"\n{message} ({default_str}): ").strip().lower()

        if not response:
            return default

        return response in ['y', 'yes']

    def display_header(self, title: str):
        """Display application header"""
        print("\n" + self.table.header(title))

    def display_section(self, title: str):
        """Display a section title"""
        print("\n" + self.table.section_title(title))

    def display_info(self, key: str, value: str, key_width: int = 30):
        """Display key-value information"""
        print(self.table.key_value(key, value, key_width))

    def display_menu_options(self, options: List[tuple]):
        """
        Display menu options in a fixed-width format

        Args:
            options: List of tuples (number, text, description)
        """
        print()
        for opt in options:
            if len(opt) == 2:
                number, text = opt
                print(self.table.numbered_item(number, text))
            else:
                number, text, description = opt
                print(self.table.numbered_item(number, text, description))

    def display_table_header(self, *headers):
        """Display table column headers"""
        print(self.table.row(*headers, align="left"))
        print(self.table.separator("-"))

    def display_table_row(self, *columns):
        """Display a table row"""
        print(self.table.row(*columns, align="left"))

    def display_error(self, message: str):
        """Display an error message"""
        print(f"\n✗ ERROR: {message}")

    def display_success(self, message: str):
        """Display a success message"""
        print(f"\n✓ SUCCESS: {message}")

    def display_warning(self, message: str):
        """Display a warning message"""
        print(f"\n⚠ WARNING: {message}")

    def display_separator(self, char: str = "-"):
        """Display a separator line"""
        print(self.table.separator(char))


class SpiderMenuInterface:
    """CLI interface for spider selection and management"""

    def __init__(self, cli: CLIInterface):
        """
        Initialize spider menu interface

        Args:
            cli: CLIInterface instance
        """
        self.cli = cli

    def display_main_menu(self, spiders: List[Dict], extra_options: List[tuple] = None):
        """
        Display main spider selection menu

        Args:
            spiders: List of spider info dictionaries
            extra_options: Additional menu options [(number, text), ...]
        """
        self.cli.clear_screen()
        self.cli.display_header("LLM METADATA SCRAPER")

        if not spiders:
            self.cli.display_error("No spiders detected!")
            return

        self.cli.display_section("Available Spiders")

        # Display spiders in a table format
        options = []
        for i, spider in enumerate(spiders, 1):
            name = spider['name']
            desc = spider.get('description', 'No description')
            # Truncate description if too long
            if len(desc) > 50:
                desc = desc[:47] + "..."
            options.append((i, name, desc))

        self.cli.display_menu_options(options)

        # Display extra options
        if extra_options:
            print()
            self.cli.display_separator()
            self.cli.display_menu_options(extra_options)

        self.cli.display_separator()

    def display_spider_details(self, spider: Dict):
        """Display detailed information about a spider"""
        self.cli.clear_screen()
        self.cli.display_header(f"SPIDER: {spider['name'].upper()}")

        print()
        self.cli.display_info("Name", spider['name'])
        self.cli.display_info("Description", spider.get('description', 'N/A'))
        self.cli.display_info("Module", spider.get('module', 'N/A'))

        if spider.get('parameters'):
            self.cli.display_section("Parameters")
            for param_name, param_type, default in spider['parameters']:
                default_str = f"(default: {default})" if default != "None" else "(required)"
                self.cli.display_info(f"  {param_name} ({param_type})", default_str, key_width=40)

    def get_spider_choice(self, num_spiders: int, num_extra_options: int = 0) -> str:
        """Get user's spider choice"""
        max_choice = num_spiders + num_extra_options
        prompt = f"Select option (0 to exit, 1-{max_choice})"
        return self.cli.get_input(prompt)

    def get_spider_parameters(self, spider: Dict) -> Dict:
        """
        Get parameters for running a spider

        Args:
            spider: Spider info dictionary

        Returns:
            Dictionary of parameter values
        """
        params = {}

        if not spider.get('parameters'):
            return params

        self.cli.display_section("Spider Parameters")
        print("Press Enter to use default values\n")

        for param_name, param_type, default in spider['parameters']:
            default_display = default if default != "None" else ""
            value = self.cli.get_input(f"{param_name} ({param_type})", default_display)

            if value:
                # Convert to appropriate type
                try:
                    if param_type == 'int':
                        params[param_name] = int(value)
                    elif param_type == 'float':
                        params[param_name] = float(value)
                    elif param_type == 'bool':
                        params[param_name] = value.lower() in ['true', 'yes', '1', 'y']
                    else:
                        params[param_name] = value
                except ValueError:
                    self.cli.display_warning(f"Invalid value for {param_name}, using default")

        return params

    def display_execution_header(self, spider_name: str):
        """Display header when executing a spider"""
        self.cli.clear_screen()
        self.cli.display_header(f"RUNNING: {spider_name.upper()}")
        print()

    def display_summary(self, results: List[tuple]):
        """
        Display summary of spider executions

        Args:
            results: List of (spider_name, success) tuples
        """
        self.cli.display_section("Execution Summary")

        print()
        for spider_name, success in results:
            status = "✓ SUCCESS" if success else "✗ FAILED"
            self.cli.display_info(spider_name, status, key_width=40)

        print()
        self.cli.display_separator("=")


class SystemInfoInterface:
    """Interface for displaying system information"""

    def __init__(self, cli: CLIInterface):
        """
        Initialize system info interface

        Args:
            cli: CLIInterface instance
        """
        self.cli = cli

    def display_system_info(self, cpu_count: int, memory_gb: Optional[float] = None):
        """Display system information"""
        self.cli.display_section("System Information")

        print()
        self.cli.display_info("CPU Cores", str(cpu_count))

        if memory_gb:
            self.cli.display_info("System Memory", f"{memory_gb:.2f} GB")
        else:
            self.cli.display_info("System Memory", "Unable to detect")

        self.cli.display_separator()
