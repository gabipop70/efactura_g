import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

import tr_anaf

DB_NAME = "efactura.db"


class EFacturaNotebook(ttk.Notebook):

    def __init__(self, parent, get_cui_furnizor_gen_callback=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.get_cui_furnizor_gen_callback = get_cui_furnizor_gen_callback

        # Creare Tab-uri
        self.tab_netransmise = ttk.Frame(self)
        self.tab_trimise = ttk.Frame(self)

        self.add(
            self.tab_netransmise, text=" 📤 Transmitere Facturi Netransmise "
        )
        self.add(
            self.tab_trimise, text=" 🔄 Stare ANAF / Preluare ID Descărcare "
        )

        # Construire interfețe vizuale
        self._setup_tab_netransmise()
        self._setup_tab_trimise()

        # Încărcare date la pornire
        self.incarca_tabel_netransmise()
        self.incarca_tabel_trimise()

    # ==========================================
    # TAB 1: TRANSMITERE FACTURI NETRANSMISE (DESIGN-UL INIȚIAL)
    # ==========================================
    def _setup_tab_netransmise(self):
        p = self.tab_netransmise

        # --- FRAME SUS: AUTENTIFICARE, FILTRARE CUI ȘI BUTOANE ACȚIUNI ---
        top_frame = ttk.LabelFrame(
            p, text=" Conectare, Filtrare & Control ", padding=10
        )
        top_frame.pack(fill="x", padx=10, pady=5)

        # 1. Buton Token ANAF
        tk.Button(
            top_frame,
            text="🔑 Actualizare Token ANAF (90 zile)",
            bg="#1976D2",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.actiune_actualizare_token,
        ).pack(side="left", padx=(5, 15))

        # 2. Câmp Filtrare CUI Furnizor
        tk.Label(
            top_frame, text="Filtru CUI Furnizor:", font=("Arial", 10, "bold")
        ).pack(side="left", padx=(5, 2))
        self.cui_filter_entry = tk.Entry(
            top_frame, width=14, font=("Arial", 10)
        )
        self.cui_filter_entry.pack(side="left", padx=(0, 10))

        # 3. Buton Reîmprospătare/Filtrare
        tk.Button(
            top_frame,
            text="🔍 Filtrează Facturi",
            bg="#009688",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.incarca_tabel_netransmise,
        ).pack(side="left", padx=5)

        # 4. Buton Transmitere Selectate
        tk.Button(
            top_frame,
            text="🚀 Transmite Facturile Selectate",
            bg="#2E7D32",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.transmite_facturi_selectate,
        ).pack(side="right", padx=5)

        # --- FRAME MIJLOC: TABELUL CU FACTURILE NETRANSMISE ---
        frame_tabel = ttk.LabelFrame(
            p, text=" Selectează Facturile pentru Transmitere ", padding=10
        )
        frame_tabel.pack(fill="both", expand=True, padx=10, pady=5)

        coloane = ("id", "numar", "data", "client", "total", "cui_f")
        self.tree_netransmise = ttk.Treeview(
            frame_tabel, columns=coloane, show="headings", selectmode="extended"
        )

        self.tree_netransmise.heading("id", text="ID DB")
        self.tree_netransmise.heading("numar", text="Nr. Factură")
        self.tree_netransmise.heading("data", text="Data Emiterii")
        self.tree_netransmise.heading("client", text="Client")
        self.tree_netransmise.heading("total", text="Total RON")
        self.tree_netransmise.heading("cui_f", text="CUI Furnizor")

        self.tree_netransmise.column("id", width=60, anchor="center")
        self.tree_netransmise.column("numar", width=80, anchor="center")
        self.tree_netransmise.column("data", width=90, anchor="center")
        self.tree_netransmise.column("client", width=300, anchor="w")
        self.tree_netransmise.column("total", width=90, anchor="e")
        self.tree_netransmise.column("cui_f", width=100, anchor="center")

        scrollbar_y = ttk.Scrollbar(
            frame_tabel, orient="vertical", command=self.tree_netransmise.yview
        )
        self.tree_netransmise.configure(yscrollcommand=scrollbar_y.set)

        self.tree_netransmise.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")

        # --- FRAME JOS: OPȚIUNI RAPIDE DE SELECTARE ---
        ctrl_frame = tk.Frame(p)
        ctrl_frame.pack(fill="x", padx=10, pady=(0, 10))

        tk.Button(
            ctrl_frame,
            text="✅ Selectează Toate",
            command=self.selecteaza_toate_facturile,
        ).pack(side="left", padx=5)
        tk.Button(
            ctrl_frame,
            text="❌ Deselectează Toate",
            command=self.deselecteaza_toate_facturile,
        ).pack(side="left", padx=5)

        tk.Label(
            ctrl_frame,
            text="💡 Lăsați câmpul 'Filtru CUI Furnizor' gol pentru a afișa facturile tuturor furnizorilor.",
            font=("Arial", 9, "italic"),
            fg="#555",
        ).pack(side="right", padx=10)

    # ==========================================
    # TAB 2: FACTURI TRIMISE & VERIFICARE STARE ANAF
    # ==========================================
    def _setup_tab_trimise(self):
        p = self.tab_trimise

        top_frame = ttk.LabelFrame(
            p, text=" Verificare Stare & Preluare ID Descărcare ", padding=10
        )
        top_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(
            top_frame,
            text="🔄 Verificare Stare / Preluare ID Descărcare",
            command=self.actiune_verificare_stare,
        ).pack(side="left", padx=5)

        ttk.Button(
            top_frame,
            text="🔄 Reîmprospătează Tabel",
            command=self.incarca_tabel_trimise,
        ).pack(side="left", padx=5)

        # Tabel Trimise
        frame_tabel = ttk.LabelFrame(
            p, text=" Facturi Încărcate la ANAF ", padding=10
        )
        frame_tabel.pack(fill="both", expand=True, padx=10, pady=5)

        coloane = ("id", "numar", "data", "client", "total", "nr1", "nr2")
        self.tree_trimise = ttk.Treeview(
            frame_tabel, columns=coloane, show="headings"
        )

        self.tree_trimise.heading("id", text="ID DB")
        self.tree_trimise.heading("numar", text="Nr. Factură")
        self.tree_trimise.heading("data", text="Data Emiterii")
        self.tree_trimise.heading("client", text="Client")
        self.tree_trimise.heading("total", text="Total RON")
        self.tree_trimise.heading("nr1", text="Index Încărcare (nr1)")
        self.tree_trimise.heading("nr2", text="Index Descărcare / Stare (nr2)")

        self.tree_trimise.column("id", width=50, anchor="center")
        self.tree_trimise.column("numar", width=80, anchor="center")
        self.tree_trimise.column("data", width=90, anchor="center")
        self.tree_trimise.column("client", width=250)
        self.tree_trimise.column("total", width=80, anchor="e")
        self.tree_trimise.column("nr1", width=140, anchor="center")
        self.tree_trimise.column("nr2", width=220)

        scrollbar_y = ttk.Scrollbar(
            frame_tabel, orient="vertical", command=self.tree_trimise.yview
        )
        self.tree_trimise.configure(yscrollcommand=scrollbar_y.set)

        self.tree_trimise.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")

    # ==========================================
    # LOGICĂ TAB 1: POPULARE, SELECȚIE, TOKEN, TRANSMITERE
    # ==========================================
    def actiune_actualizare_token(self):
        messagebox.showinfo(
            "Autorizare ANAF",
            "S-a deschis browserul.\nIntroduceți PIN-ul semnăturii electronice și aprobați cererea de acces.",
        )
        try:
            thread_server = tr_anaf.autorizeaza_anaf_pas_1()
            succes, mesaj = tr_anaf.finalizeaza_autorizare_pas_2(thread_server)
            if succes:
                messagebox.showinfo("Succes", mesaj)
            else:
                messagebox.showerror("Eroare", mesaj)
        except Exception as e:
            messagebox.showerror("Eroare Autentificare", str(e))

    def incarca_tabel_netransmise(self):
        for item in self.tree_netransmise.get_children():
            self.tree_netransmise.delete(item)

        cui_filtru = self.cui_filter_entry.get().strip()

        # Preluare CUI din ecranul de generare dacă câmpul e gol
        if not cui_filtru and self.get_cui_furnizor_gen_callback:
            val_gen = self.get_cui_furnizor_gen_callback()
            if val_gen:
                self.cui_filter_entry.delete(0, tk.END)
                self.cui_filter_entry.insert(0, val_gen)
                cui_filtru = val_gen

        try:
            facturi = tr_anaf.preia_facturi_netransmise(
                cui_furnizor=cui_filtru if cui_filtru else None
            )
            if not facturi:
                return

            for f in facturi:
                id_db, nr, data, client, total, cui_f = f[:6]
                total_str = f"{total:.2f}" if total is not None else "0.00"
                self.tree_netransmise.insert(
                    "",
                    "end",
                    iid=str(id_db),
                    values=(id_db, nr, data, client, total_str, cui_f),
                )
        except Exception as e:
            print(f"Eroare la încărcarea tabelului netransmise: {e}")

    def selecteaza_toate_facturile(self):
        all_items = self.tree_netransmise.get_children()
        self.tree_netransmise.selection_set(all_items)

    def deselecteaza_toate_facturile(self):
        self.tree_netransmise.selection_remove(
            self.tree_netransmise.selection()
        )

    def transmite_facturi_selectate(self):
        selected_items = self.tree_netransmise.selection()
        if not selected_items:
            messagebox.showwarning(
                "Atenție", "Te rugăm să selectezi cel puțin o factură din tabel!"
            )
            return

        lista_ids = [int(item_id) for item_id in selected_items]

        confirm = messagebox.askyesno(
            "Confirmare Transmitere",
            f"Sigur dorești să transmiți cele {len(lista_ids)} facturi selectate la ANAF?",
        )
        if not confirm:
            return

        try:
            rezultat = tr_anaf.proceseaza_trimitere_facturi_selectate(lista_ids)
            messagebox.showinfo("Rezultat Transmitere", rezultat)

            # Reîmprospătăm ambele tab-uri
            self.incarca_tabel_netransmise()
            self.incarca_tabel_trimise()
        except Exception as e:
            messagebox.showerror("Eroare Transmitere", str(e))

    # ==========================================
    # LOGICĂ TAB 2: POPULARE & VERIFICARE STARE
    # ==========================================
    def incarca_tabel_trimise(self):
        for item in self.tree_trimise.get_children():
            self.tree_trimise.delete(item)

        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT f.id, f.numar, f.data, COALESCE(c.nume, 'Client necunoscut'), f.total_general, f.nr1, f.nr2
                FROM facturi f
                LEFT JOIN clienti c ON f.client_id = c.id
                WHERE f.tr_efact = 1
                ORDER BY f.data DESC
            """
            )
            facturi = cursor.fetchall()
            conn.close()

            for f in facturi:
                id_db, nr, data, client, total, nr1, nr2 = f
                total_str = f"{total:.2f}" if total is not None else "0.00"
                stare_desc = (
                    nr2 if nr2 else "În așteptare descărcare / neprocesat"
                )
                self.tree_trimise.insert(
                    "",
                    "end",
                    iid=str(id_db),
                    values=(
                        id_db,
                        nr,
                        data,
                        client,
                        total_str,
                        nr1,
                        stare_desc,
                    ),
                )
        except Exception as e:
            print(f"Eroare la încărcarea tabelului trimise: {e}")

    def actiune_verificare_stare(self):
        rezultat = tr_anaf.actualizeaza_stare_facturi_pending()
        messagebox.showinfo("Rezultat Verificare ANAF", rezultat)
        self.incarca_tabel_trimise()