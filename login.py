import tkinter as tk
from tkinter import messagebox
from db import creare_tabele_utilizatori, verifica_parola, sqlite3

class FereastraLogin:
    def __init__(self, master, on_login_success):
        self.master = master
        self.on_login_success = on_login_success
        self.master.title("🔐 Autentificare - e-Factura")
        self.master.geometry("400x320")
        self.master.configure(bg="#e0f7fa")
        self.master.resizable(False, False)

        # Centrare fereastră login
        self.master.update_idletasks()
        x = (self.master.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.master.winfo_screenheight() // 2) - (320 // 2)
        self.master.geometry(f"400x320+{x}+{y}")

        # UI Elements
        tk.Label(
            master, text="🔑 Autentificare Sistem", font=("Arial", 14, "bold"),
            bg="#e0f7fa", fg="#006064"
        ).pack(pady=(25, 15))

        frame_form = tk.Frame(master, bg="#e0f7fa")
        frame_form.pack(pady=10, padx=30, fill="x")

        # User
        tk.Label(frame_form, text="Utilizator:", font=("Arial", 10, "bold"), bg="#e0f7fa").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_user = tk.Entry(frame_form, font=("Arial", 10))
        self.entry_user.grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        self.entry_user.focus_set()

        # Parolă
        tk.Label(frame_form, text="Parolă:", font=("Arial", 10, "bold"), bg="#e0f7fa").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_pass = tk.Entry(frame_form, font=("Arial", 10), show="*")
        self.entry_pass.grid(row=1, column=1, sticky="ew", pady=5, padx=5)

        frame_form.columnconfigure(1, weight=1)

        # Bind tasta Enter pentru autentificare rapidă
        self.entry_pass.bind("<Return>", lambda e: self.autentifica())
        self.entry_user.bind("<Return>", lambda e: self.entry_pass.focus_set())

        # Buton Login
        btn_login = tk.Button(
            master, text="Autentificare", font=("Arial", 10, "bold"),
            bg="#00897b", fg="white", activebackground="#006064", activeforeground="white",
            command=self.autentifica, cursor="hand2", padx=15, pady=5
        )
        btn_login.pack(pady=20)

    def autentifica(self):
        user = self.entry_user.get().strip()
        parola = self.entry_pass.get().strip()

        if not user or not parola:
            messagebox.showwarning("Atenție", "Introduceți utilizatorul și parola!")
            return

        with sqlite3.connect("efactura.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash, salt, nume_complet FROM utilizatori WHERE username = ?", (user,))
            row = cursor.fetchone()

            if row:
                hash_salvat, salt_salvat, nume_complet = row
                if verifica_parola(parola, hash_salvat, salt_salvat):
                    # Autentificare cu succes
                    self.on_login_success(user, nume_complet)
                    return

        messagebox.showerror("Eroare Autentificare", "Utilizator sau parolă incorectă!")
        self.entry_pass.delete(0, tk.END)