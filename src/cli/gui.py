"""
Senthium AI - GUI Launcher
Launches the Streamlit web interface
"""
import sys
import subprocess
from pathlib import Path


def launch_gui():
    """Launch the Streamlit web interface"""
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    app_file = project_root / "streamlit_app.py"
    
    if not app_file.exists():
        print(f"❌ Error: Could not find streamlit_app.py at {app_file}")
        sys.exit(1)
    
    print("🚀 Launching Senthium AI Web Interface...")
    print(f"📂 Project root: {project_root}")
    print(f"🌐 Streamlit will open in your browser...")
    print()
    
    try:
        # Launch streamlit
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(app_file)],
            cwd=str(project_root),
            check=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down Senthium AI...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error launching GUI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    launch_gui()
