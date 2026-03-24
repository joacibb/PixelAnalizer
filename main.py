"""
main.py
-------
Entry point for PixelAnalizer.
Initialises logging, then launches the Tkinter application.
"""

import sys
import tkinter as tk

from src.utils.logger import setup_logging
from src.ui.app import PixelAnalizerApp


def main() -> None:
    setup_logging()

    root = tk.Tk()
    _app = PixelAnalizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
