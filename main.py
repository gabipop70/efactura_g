import sys
import os

# Adaugă calea din executabilul PyInstaller la sys.path
if getattr(sys, 'frozen', False):
    sys.path.append(sys._MEIPASS)
else:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
import meniu
from meniu import AplicatieFacturi


if __name__ == "__main__":
    root = tk.Tk()
    app = AplicatieFacturi(root)
    root.mainloop()