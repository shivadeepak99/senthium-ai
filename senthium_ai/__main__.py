"""
Entry point for running Senthium AI as a module.
Usage: python -m senthium_ai [options]
"""
import sys
from pathlib import Path
import importlib.util

if __name__ == '__main__':
    # Import from the main script
    spec = importlib.util.spec_from_file_location("senthium_ai_main", 
                                                   Path(__file__).parent.parent / "senthium_ai.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.exit(module.main())
