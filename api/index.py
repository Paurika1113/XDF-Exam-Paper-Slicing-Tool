"""XDFclier — Vercel entry point"""
import sys, os

_cli_dir = os.path.join(os.path.dirname(__file__), "..", "cli")
_cli_dir = os.path.normpath(_cli_dir)
if _cli_dir not in sys.path:
    sys.path.insert(0, _cli_dir)

from main import app
