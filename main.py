import sys
import os
import tkinter as tk

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import creare_tabele, creare_tabele_utilizatori
from login import FereastraLogin
from meniu import AplicatieFacturi


def lansare_aplicatie():
    # 1. Inițializăm tabelele în baza de date
    creare_tabele()
    creare_tabele_utilizatori()

    root = tk.Tk()

    def pe_login_succes(username, nume_complet):
        # Distrugem widget-urile de login și lansăm interfața principală
        for widget in root.winfo_children():
            widget.destroy()
        root.withdraw()
        root.update_idletasks()
        # Pornim aplicația principală
        app = AplicatieFacturi(root)
        root.title(
            f"🧾 Sistem Gestiune e-Facturi | Utilizator: {nume_complet}"
        )
        root.deiconify()
    # Lansăm mai întâi modulul de Login
    FereastraLogin(root, on_login_success=pe_login_succes)

    root.mainloop()


if __name__ == "__main__":
    lansare_aplicatie()