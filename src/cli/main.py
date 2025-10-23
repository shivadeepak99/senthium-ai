"""
Main CLI entry point for Senthium.

This module serves as the primary command-line interface,
routing commands to the appropriate handlers (wrapper, daemon control, etc.).
"""

import sys
from cli.wrapper import main as wrapper_main

# For now, route everything to the wrapper
# In the future, we'll add daemon control (start/stop/restart) here
def main() -> int:
    """Main entry point for senthium command"""
    return wrapper_main()


if __name__ == "__main__":
    sys.exit(main())
