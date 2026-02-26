import tkinter as tk
from meniu import AplicatieFacturi


if __name__ == "__main__":
    root = tk.Tk()
    app = AplicatieFacturi(root)
    root.mainloop()