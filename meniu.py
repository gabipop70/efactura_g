import tkinter as tk
from tkcalendar import DateEntry
from datetime import datetime
from tkinter import ttk, messagebox

import db
from db import get_unitati_text_format, creare_tabele, populate_unitati_default, cauta_facturi_dupa_cui, cauta_in_tabel, \
    cauta_clienti, cauta_furnizori, get_explicatii_furnizor

import utils
from factura import AutoCompleteEntry
from utils import centreaza_fereastra, sugereaza_nr_chitanta, validare_cui, validare_cnp


class AplicatieFacturi:
    def __init__(self, master):
        self.explicatii_combo = None
        self.pagina_generare = master
        creare_tabele()
        populate_unitati_default()

        centreaza_fereastra(master, 1100, 800)
        master.title("🧾 Sistem Gestiune e-Facturi")
        master.configure(bg="#e0f7fa")

        # --- CONFIGURARE MENIU ---
        self.creeaza_meniu()

        # --- CONTAINERUL PENTRU PAGINI ---
        self.container = tk.Frame(master, bg="#e0f7fa")
        self.container.pack(side="top", fill="both", expand=True)

        # Dicționar pentru a păstra referințele către ecrane
        self.pagini = {}

        # Creăm cadrele (Frames) pentru fiecare secțiune
        self.pagina_start = tk.Frame(self.container, bg="#e0f7fa")
        self.pagina_generare = tk.Frame(self.container, bg="#e0f7fa")
        self.pagina_cautare = tk.Frame(self.container, bg="#e0f7fa")

        for p in (self.pagina_start, self.pagina_generare, self.pagina_cautare):
            p.grid(row=0, column=0, sticky="nsew")

        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Populăm paginile
        self._setup_ui_start()
        self._setup_ui_generare()
        self._setup_ui_cautare()

        # Afișăm prima pagină
        self.arata_pagina(self.pagina_start)

    def creeaza_meniu(self):
        menubar = tk.Menu(self.pagina_generare)
        self.pagina_generare.config(menu=menubar)

        menu_optiuni = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Meniu", menu=menu_optiuni)

        menu_optiuni.add_command(label="🏠 Acasă (Info)", command=lambda: self.arata_pagina(self.pagina_start))
        menu_optiuni.add_separator()
        menu_optiuni.add_command(label="Factură Nouă", command=lambda: self.arata_pagina(self.pagina_generare))
        menu_optiuni.add_command(label="Istoric / Căutare", command=lambda: self.arata_pagina(self.pagina_cautare))
        menu_optiuni.add_separator()
        menu_optiuni.add_command(label="Ieșire", command=self.pagina_generare.quit)

    def arata_pagina(self, pagina):
        pagina.tkraise()
        if pagina == self.pagina_generare:
            self.furnizor_cui.focus_set()
        elif pagina == self.pagina_cautare:
            if hasattr(self, 'cui_entry'):
                self.cui_entry.focus_set()

    def _setup_ui_start(self):
        p = self.pagina_start
        tk.Label(p, text="📊 Sistem Gestiune Facturi", font=("Arial", 20, "bold"),
                 bg="#e0f7fa", fg="#006064").pack(pady=(50, 20))

        info_text = (
            "Bine ați venit în aplicația de generare e-Factura!\n\n"
            "• Folosiți meniul de sus pentru navigare.\n"
            "• 'Factură Nouă' - Generare fișiere PDF și XML (RO e-Factura).\n"
            "• 'Istoric' - Căutare și re-listare facturi emise anterior.\n"
            "• CUI-urile sunt salvate automat pentru utilizări viitoare."
        )

        tk.Label(p, text=info_text, font=("Arial", 12), bg="#e0f7fa",
                 justify="left", padx=20).pack(pady=20)

        btn_frame = tk.Frame(p, bg="#e0f7fa")
        btn_frame.pack(pady=30)

        tk.Button(btn_frame, text="📄 Emite Factură Nouă", font=("Arial", 11), width=20,
                  command=lambda: self.arata_pagina(self.pagina_generare)).grid(row=0, column=0, padx=10)

        tk.Button(btn_frame, text="🔍 Consultă Istoric", font=("Arial", 11), width=20,
                  command=lambda: self.arata_pagina(self.pagina_cautare)).grid(row=0, column=1, padx=10)

        tk.Label(p, text="Versiune: 2026.1.0 | Status DB: Conectat", font=("Arial", 8),
                 bg="#e0f7fa", fg="gray").pack(side="bottom", pady=10)

    def _setup_ui_generare(self):
        self.produse = []
        self._setup_ui()

    def _setup_ui(self):
        p = self.pagina_generare

        # === FURNIZOR ===
        tk.Label(self.pagina_generare, text="📌 Furnizor", bg="#e0f7fa", font=("Arial", 11, "bold")).grid(row=0,
                                                                                                         column=0,
                                                                                                         columnspan=3)
        self.furnizor_cui = self._entry(p, "CUI", 1, 0)
        self.furnizor_nume = self._entry(p, "Denumire", 1, 1)
        self.autocomplete_furnizor = AutoCompleteEntry(
            entry=self.furnizor_nume,
            search_callback=cauta_furnizori,
            select_callback=self.completeaza_furnizor
        )
        self.furnizor_onrc = self._entry(p, "ONRC", 2, 0)
        self.furnizor_adresa = self._entry2(p, "Adresă", 3, 0)
        self.furnizor_localitate = self._entry(p, "Localitate", 2, 1)
        self.furnizor_judet = self._entry1(p, "Judet", 4, 0)
        self.furnizor_tara = self._entry1(p, "Țara", 4, 1, default="RO")
        self.furnizor_banca = self._entry(p, "Banca 1", 5, 0)
        self.furnizor_iban = self._entry(p, "IBAN 1", 5, 1)
        self.furnizor_banca1 = self._entry(p, "Banca 2", 6, 0)
        self.furnizor_iban1 = self._entry(p, "IBAN 2", 6, 1)

        self.furnizor_cui.bind("<FocusIn>", lambda e: self.resetare_campuri())
        self.furnizor_cui.bind("<FocusOut>", lambda e: self.actiune_cauta_entitate("furnizor"))

        # === CLIENT ===
        tk.Label(self.pagina_generare, text="👤 Client", bg="#e0f7fa", font=("Arial", 11, "bold")).grid(row=0, column=3,
                                                                                                       columnspan=4)
        self.client_cui = self._entry(p, "CUI", 1, 3)
        self.client_nume = self._entry(p, "Denumire", 1, 4)
        self.autocomplete_client = AutoCompleteEntry(
            entry=self.client_nume,
            search_callback=cauta_clienti,
            select_callback=self.completeaza_client
        )
        self.client_onrc = self._entry(p, "ONRC", 2, 3)
        self.client_adresa = self._entry2(p, "Adresă", 3, 3)
        self.client_localitate = self._entry(p, "Localitate", 2, 4)
        self.client_judet = self._entry1(p, "Judet", 4, 3)
        self.client_tara = self._entry1(p, "Țara", 4, 4, default="RO")
        self.client_banca = self._entry(p, "Banca 1", 5, 3)
        self.client_iban = self._entry(p, "IBAN 1", 5, 4)
        self.client_banca1 = self._entry(p, "Banca 2", 6, 3)
        self.client_iban1 = self._entry(p, "IBAN 2", 6, 4)

        self.client_cui.bind("<FocusOut>", lambda e: self.actiune_cauta_entitate("client"))

        # === DETALII FACTURA ===
        tk.Label(self.pagina_generare, text="🧾 Detalii factura", font="bold", bg="#e0f7fa").grid(row=10, column=2,
                                                                                                 columnspan=3)
        self.ser_fac_entry = self._entry(p, "Serie factura", 11, 1)
        self.numar_entry = self._entry(p, "Număr factura", 11, 2)
        self.data_entry = self._entry(p, "Data", 12, 2, default=datetime.now().strftime("%Y-%m-%d"))

        # === PRODUSE ===
        self.produs_frame = tk.Frame(self.pagina_generare)
        self.produs_frame.grid(row=15, column=1, columnspan=6, pady=5)
        tk.Label(self.produs_frame, text="Denumire produs", font=("Arial", 11, "italic"), bg="#e0f7fa").grid(row=0,
                                                                                                             column=0)
        # --- AICI ADĂUGĂM COMBOBOX-UL DE EXPLICAȚII ---
        tk.Label(self.produs_frame, text="Explicații:", bg="#e0f7fa").grid(row=1, column=0, sticky="e", padx=2, pady=5)
        self.explicatii_combo = ttk.Combobox(self.produs_frame, width=40)
        self.explicatii_combo.grid(row=1, column=0,  sticky="w", padx=2, pady=5)


        tk.Label(self.produs_frame, text="U.M.", bg="#e0f7fa", font=("Arial", 11, "italic")).grid(row=0, column=1)
        tk.Label(self.produs_frame, text="Cant.", bg="#e0f7fa", font=("Arial", 11, "italic")).grid(row=0, column=2)
        tk.Label(self.produs_frame, text="Pret unit.", bg="#e0f7fa", font=("Arial", 11, "italic")).grid(row=0, column=3)
        tk.Label(self.produs_frame, text="TVA(%)", bg="#e0f7fa", font=("Arial", 11, "italic")).grid(row=0, column=4)

 #       self.produs_denumire = tk.Entry(self.produs_frame, width=40)
 #       self.produs_denumire.grid(row=1, column=0)

        self.produs_um = tk.Entry(self.produs_frame, width=10)
        um_vals = get_unitati_text_format()
        self.produs_um = ttk.Combobox(self.produs_frame, values=um_vals, width=10)
        self.produs_um.grid(row=1, column=1)
        if um_vals: self.produs_um.set(um_vals[1])

        self.produs_cant = tk.Entry(self.produs_frame, width=8, justify="right")
        self.produs_cant.grid(row=1, column=2)
        self.produs_cant.insert(0, "0.00")
        self.produs_pret = tk.Entry(self.produs_frame, width=10, justify="right")
        self.produs_pret.grid(row=1, column=3)
        self.produs_pret.insert(0, "0.00")
        self.produs_tva = tk.Entry(self.produs_frame, width=5, justify="right")
        self.produs_tva.grid(row=1, column=4)
        self.produs_tva.insert(0, "0")
        tk.Button(self.produs_frame, text="➕ Adaugă", command=self.actiune_adauga_produs).grid(row=1, column=5, padx=5)

        self.listbox = tk.Listbox(self.pagina_generare, width=100, height=10, font=("Consolas", 10))
        self.listbox.grid(row=17, column=1, columnspan=6, pady=5)
        header = f"{'     Produs':<40} | {'Cant.':<5} | {'Preț Unitar':<12} | {'TVA %':<6} | {'Total fara TVA':<12} | {'Total cu TVA': <12}"
        separator = "------------------------------------------------------------------------------------------------------"
        self.listbox.insert(tk.END, header)
        self.listbox.insert(tk.END, separator)

        tk.Button(self.pagina_generare, text="🗑️ Șterge produs selectat", command=self.sterge_produs).grid(row=18,
                                                                                                           column=3,
                                                                                                           columnspan=5,
                                                                                                           pady=2)

        # === ZONA CHITANȚĂ ===
        self.vrea_chitanta_var = tk.BooleanVar(value=False)
        self.chk_chitanta = tk.Checkbutton(
            self.pagina_generare, text="Chitanta.", bg="#e0f7fa",
            variable=self.vrea_chitanta_var, command=self.toggle_chitanta_ui
        )
        self.chk_chitanta.grid(row=19, column=0, columnspan=2, sticky="we", padx=5, pady=2)

        tk.Label(self.pagina_generare, text="Nr. Chitanță:", bg="#e0f7fa").grid(row=20, column=0, sticky="e", padx=5,
                                                                                pady=2)
        self.entry_nr_chitanta = tk.Entry(self.pagina_generare, state="disabled")
        self.entry_nr_chitanta.grid(row=20, column=1, sticky="w", padx=5, pady=2)

        tk.Button(self.pagina_generare, text="GENEREAZĂ FACTURA", bg="green", fg="white", font=("Arial", 11, "bold"),
                  command=self.actiune_generare).grid(row=22, column=0, columnspan=5, pady=20)

    def toggle_chitanta_ui(self):
        if self.vrea_chitanta_var.get():
            self.entry_nr_chitanta.config(state="normal")
            cui = self.furnizor_cui.get()
            nr_sugerat = sugereaza_nr_chitanta(cui)
            if nr_sugerat:
                self.entry_nr_chitanta.delete(0, tk.END)
                self.entry_nr_chitanta.insert(0, nr_sugerat)
        else:
            self.entry_nr_chitanta.delete(0, tk.END)
            self.entry_nr_chitanta.config(state="disabled")

    def _entry(self, parent, label, row, col, default=""):
        tk.Label(parent, text=label, bg=parent.cget("bg")).grid(row=row, column=col, sticky="e", padx=2, pady=2)
        e = tk.Entry(parent, width=25)
        e.grid(row=row, column=col + 1, sticky="w", padx=2, pady=2)
        e.insert(0, default)
        return e

    def _entry1(self, parent, label, row, col, default=""):
        tk.Label(parent, text=label, bg=parent.cget("bg")).grid(row=row, column=col, sticky="e", padx=2, pady=2)
        e = tk.Entry(parent, width=5)
        e.grid(row=row, column=col + 1, sticky="w", padx=2, pady=2)
        e.insert(0, default)
        return e

    def _entry2(self, parent, label, row, col, default=""):
        tk.Label(parent, text=label, bg=parent.cget("bg")).grid(row=row, column=col, sticky="e", padx=2, pady=2)
        e = tk.Entry(parent, width=51)
        e.grid(row=row, column=col + 1, columnspan=2, sticky="w", padx=2, pady=2)
        e.insert(0, default)
        return e

    def actiune_adauga_produs(self):
        raw_data = {
            'denumire': self.explicatii_combo.get(),
            'cant_str': self.produs_cant.get(),
            'pret_str': self.produs_pret.get(),
            'tva_str': self.produs_tva.get(),
            'um': self.produs_um.get()
        }
        try:
            produs_nou = utils.validare_produs_input(**raw_data)
            self.produse.append(produs_nou)

            total = produs_nou.cantitate * produs_nou.pret_unitar
            totalcutva = total + total * produs_nou.tva_percent / 100

            row_text = f"{produs_nou.denumire[:20]:<33} | {produs_nou.cantitate:=5} | {produs_nou.pret_unitar:>12} | {produs_nou.tva_percent:<6} | {total:>14} | {totalcutva:>12}"
            self.listbox.insert(tk.END, row_text)

            self.explicatii_combo.delete(0, tk.END)
            self.produs_cant.delete(0, tk.END)
            self.produs_cant.insert(0, "0.00")
            self.produs_pret.delete(0, tk.END)
            self.produs_pret.insert(0, "0.00")
        except ValueError as ex:
            messagebox.showerror("Eroare Validare", str(ex))

    def sterge_produs(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Selectare", "Selectează un produs de șters.")
            return

        index = sel[0]
        if index < 2:
            messagebox.showwarning("Atenție", "Nu poți șterge capul de tabel!")
            return

        data_index = index - 2
        try:
            if 0 <= data_index < len(self.produse):
                self.produse.pop(data_index)
                self.listbox.delete(index)
                messagebox.showinfo("Șters", "Produsul a fost șters din factură.")
        except IndexError:
            messagebox.showerror("Eroare", "Index invalid.")

    def actiune_cauta_entitate(self, tip):
        if tip == "furnizor":
            cui = self.furnizor_cui.get()
            tabel = "furnizori"
            fields = {
                'nume': self.furnizor_nume, 'onrc': self.furnizor_onrc, 'adresa': self.furnizor_adresa,
                'localitate': self.furnizor_localitate, 'judet': self.furnizor_judet, 'tara': self.furnizor_tara,
                'banca': self.furnizor_banca, 'iban': self.furnizor_iban,
                'banca1': self.furnizor_banca1, 'iban1': self.furnizor_iban1, 'serie': self.ser_fac_entry
            }


        else:
            cui = self.client_cui.get()
            tabel = "clienti"
            fields = {
                'nume': self.client_nume, 'onrc': self.client_onrc, 'adresa': self.client_adresa,
                'localitate': self.client_localitate, 'judet': self.client_judet, 'tara': self.client_tara,
                'banca': self.client_banca, 'iban': self.client_iban,
                'banca1': self.client_banca1, 'iban1': self.client_iban1
            }

        if not cui: return

        valid, mesaj = validare_cui(cui)
        if not valid:
            messagebox.showerror("Eroare CUI", mesaj)
            if tip == "furnizor":
                self.furnizor_cui.focus_set()
            else:
                self.client_cui.focus_set()
            return

        self.pagina_generare.config(cursor="wait")
        self.pagina_generare.update()

        try:
            date_firma = utils.logic_cauta_entitate(cui, tabel)
            if date_firma:
                for key, widget in fields.items():
                    val = date_firma.get(key, "")
                    widget.delete(0, "end")
                    if val: widget.insert(0, str(val))

                if tip == "furnizor":
                    nr_sugerat = utils.sugereaza_urmatorul_numar(cui)
                    if nr_sugerat:
                        self.numar_entry.delete(0, "end")
                        self.numar_entry.insert(0, nr_sugerat)
                        if 'ser_fac' in date_firma:
                            self.ser_fac_entry.delete(0, "end")
                            self.ser_fac_entry.insert(0, date_firma['ser_fac'])

                    explicatii_firma = db.get_explicatii_furnizor(cui)
                    if hasattr(self, 'explicatii_combo') and self.explicatii_combo is not None:
                        self.explicatii_combo['values'] = explicatii_firma
                        if explicatii_firma:
                            self.explicatii_combo.set(explicatii_firma[0])
                        else:
                            self.explicatii_combo.set("")

        finally:
            self.pagina_generare.config(cursor="")

    def actiune_generare(self):
        if not self.produse:
            messagebox.showwarning("Atentie", "Nu ai adaugat produse!")
            return

    # 2. Extragere CUI Furnizor și Explicație din UI
        cui_f = self.furnizor_cui.get().strip()
        text_explicatie = ""
        if hasattr(self, 'explicatii_combo') and self.explicatii_combo is not None:
                text_explicatie = self.explicatii_combo.get().strip()

                # 3. Salvare explicație nouă în efactura.db pentru furnizorul curent
        if cui_f and text_explicatie:
            db.salveaza_explicatie_furnizor(cui_f, text_explicatie)
            optiuni_noi = db.get_explicatii_furnizor(cui_f)

            if hasattr(self, 'explicatii_combo') and self.explicatii_combo is not None:
                self.explicatii_combo['values'] = optiuni_noi
                self.explicatii_combo.set(text_explicatie)


        d_furnizor = {
            'nume': self.furnizor_nume.get(), 'cui': self.furnizor_cui.get(), 'onrc': self.furnizor_onrc.get(),
            'adresa': self.furnizor_adresa.get(), 'localitate': self.furnizor_localitate.get(),
            'judet': self.furnizor_judet.get(), 'tara': self.furnizor_tara.get(),
            'banca': self.furnizor_banca.get(), 'iban': self.furnizor_iban.get(),
            'banca1': self.furnizor_banca1.get(), 'iban1': self.furnizor_iban1.get(),
            'ser_fac': self.ser_fac_entry.get(),
        }

        d_client = {
            'nume': self.client_nume.get(), 'cui': self.client_cui.get(), 'onrc': self.client_onrc.get(),
            'adresa': self.client_adresa.get(), 'localitate': self.client_localitate.get(),
            'judet': self.client_judet.get(), 'tara': self.client_tara.get(),
            'banca': self.client_banca.get(), 'iban': self.client_iban.get(),
            'banca1': self.client_banca1.get(), 'iban1': self.client_iban1.get()
        }

        d_factura = {
            'numar': self.numar_entry.get(),
            'data': self.data_entry.get(),
            'nr_chit': self.entry_nr_chitanta.get(),
            'vrea_chitanta': self.vrea_chitanta_var.get(),
            'explicatii': text_explicatie

        }

        try:
            pdf, xml = utils.generare_fisiere_factura(d_furnizor, d_client, d_factura, self.produse)
            messagebox.showinfo("Succes", f"Factura generata!\nPDF: {pdf}\nXML: {xml}")

            self.produse = []
            self.listbox.delete(0, tk.END)

            raspuns = messagebox.askyesno("Generare Factura", "Doresti sa generezi o noua factura?")
            if raspuns:
                self.resetare_campuri()
            else:
                self.arata_pagina(self.pagina_start)
        except Exception as e:
            messagebox.showerror("Eroare Generare", f"Ceva nu a mers bine:\n{str(e)}")

    def resetare_campuri(self):
        for entry in [
            self.furnizor_nume, self.furnizor_cui, self.furnizor_onrc, self.furnizor_adresa,
            self.furnizor_localitate, self.furnizor_judet,
            self.furnizor_banca, self.furnizor_iban, self.furnizor_banca1, self.furnizor_iban1,
            self.client_nume, self.client_cui, self.client_onrc, self.client_adresa,
            self.client_localitate, self.client_judet,
            self.client_banca, self.client_iban, self.client_banca1, self.client_iban1,
            self.ser_fac_entry, self.numar_entry, self.data_entry
        ]:
            entry.delete(0, tk.END)
            entry.config(state='normal')

        self.data_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.produs_cant.delete(0, tk.END)
        self.produs_cant.insert(0, "0.00")
        self.produs_pret.delete(0, tk.END)
        self.produs_pret.insert(0, "0.00")
        self.produs_tva.delete(0, tk.END)
        self.produs_tva.insert(0, "0")

        self.listbox.delete(0, tk.END)
        header = f"{'     Produs':<33} | {'Cant.':<5} | {'Preț Unitar':<12} | {'TVA %':<6} | {'Total fara TVA':<12} | {'Total cu TVA': <12}"
        separator = "------------------------------------------------------------------------------------------------------"
        self.listbox.insert(tk.END, header)
        self.listbox.insert(tk.END, separator)

        self.vrea_chitanta_var.set(False)
        self.entry_nr_chitanta.delete(0, tk.END)
        self.entry_nr_chitanta.config(state="disabled")
        self.furnizor_cui.focus_set()

    def _setup_ui_cautare(self):
        frame = self.pagina_cautare

        # Titlu ecran
        tk.Label(frame, text="🔍 Căutare Istoric Facturi", font=("Arial", 14, "bold"), bg="#e0f7fa").pack(pady=10)

        # Container principal filtre
        search_subframe = tk.Frame(frame, bg="#e0f7fa")
        search_subframe.pack(pady=10, padx=20)

        # --- RÂND 0: FRAME COMPACT FURNIZOR ---
        rand_furnizor_frame = tk.Frame(search_subframe, bg="#e0f7fa")
        rand_furnizor_frame.grid(row=0, column=0, columnspan=2, sticky="w", pady=5)

        tk.Label(rand_furnizor_frame, text="Denumire furnizor:", bg="#e0f7fa").pack(side="left", padx=(0, 2))
        self.furnizor_nume_cautare = tk.Entry(rand_furnizor_frame, width=25)
        self.furnizor_nume_cautare.pack(side="left", padx=(0, 5))

        tk.Label(rand_furnizor_frame, text="CUI furnizor:", bg="#e0f7fa").pack(side="left", padx=(5, 2))
        self.cui_entry = tk.Entry(rand_furnizor_frame, width=15)
        self.cui_entry.pack(side="left", padx=(0, 20))


        def completeaza_furnizor_istoric(row):
            self.cui_entry.delete(0, tk.END)
            self.cui_entry.insert(0, row[0])
            self.furnizor_nume_cautare.delete(0, tk.END)
            self.furnizor_nume_cautare.insert(0, row[1])

        self.autocomplete_furnizor_istoric = AutoCompleteEntry(
            entry=self.furnizor_nume_cautare,
            search_callback=cauta_furnizori,
            select_callback=completeaza_furnizor_istoric
        )

        # --- RÂND 1: CUI CLIENT ---
        # tk.Label(search_subframe, text="CUI client:", bg="#e0f7fa").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        # cui_entryc = tk.Entry(search_subframe, width=25)
        # cui_entryc.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        rand_client_frame = tk.Frame(search_subframe, bg="#e0f7fa")
        rand_client_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=5)

        tk.Label(rand_client_frame, text="Denumire client:", bg="#e0f7fa").pack(side="left", padx=(0, 2))
        self.client_nume_cautare = tk.Entry(rand_client_frame, width=25)
        self.client_nume_cautare.pack(side="left", padx=(0, 5))

        tk.Label(rand_client_frame, text="CUI client:", bg="#e0f7fa").pack(side="left", padx=(5, 2))
        self.cui_entryc = tk.Entry(rand_client_frame, width=15)
        self.cui_entryc.pack(side="left", padx=(0, 20))

        def completeaza_client_istoric(row):
            self.cui_entryc.delete(0, tk.END)
            self.cui_entryc.insert(0, row[0])
            self.client_nume_cautare.delete(0, tk.END)
            self.client_nume_cautare.insert(0, row[1])

        self.autocomplete_furnizor_istoric = AutoCompleteEntry(
            entry=self.client_nume_cautare,
            search_callback=cauta_clienti,
            select_callback=completeaza_client_istoric
        )

        # --- RÂND 2: ETICHETE DATE ---
        tk.Label(search_subframe, text="Data început (AAAA-LL-ZZ):", bg="#e0f7fa", font=("Arial", 9, "italic")).grid(
            row=2, column=0, sticky="s", padx=5, pady=(10, 0))
        tk.Label(search_subframe, text="Data sfârșit (AAAA-LL-ZZ):", bg="#e0f7fa", font=("Arial", 9, "italic")).grid(
            row=2, column=1, sticky="s", padx=5, pady=(10, 0))

        # --- RÂND 3: CÂMPURI DATE ---
        datai_entryc = tk.Entry(search_subframe, width=20, justify="center")
        datai_entryc.grid(row=3, column=0, padx=5, pady=2)
        datai_entryc.insert(0, "2026-01-01")

        datas_entryc = tk.Entry(search_subframe, width=20, justify="center")
        datas_entryc.grid(row=3, column=1, padx=5, pady=2)
        datas_entryc.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # --- RÂND 4: BUTON CĂUTARE ---
        listbox_cautare = tk.Listbox(search_subframe, width=110, height=15, font=("Courier", 10))

        def executa_cautare():
            cui = self.cui_entry.get().strip()
            cui_c = self.cui_entryc.get().strip()
            data_i = datai_entryc.get().strip()
            data_s = datas_entryc.get().strip()

            if cui_c == "": cui_c = None
            if data_i == "": data_i = None
            if data_s == "": data_s = None

            rezultate = cauta_facturi_dupa_cui(cui, cui_c, data_i, data_s)
            listbox_cautare.delete(0, tk.END)

            if rezultate:
                suma_totala = sum(factura['total_general'] for factura in rezultate)
                header = f"{'Număr':<10} | {'Data':<15} | {'Client':<40} | {'Total':>10}"
                listbox_cautare.insert(tk.END, header)
                listbox_cautare.insert(tk.END, "-" * 85)
                for factura in rezultate:
                    listbox_cautare.insert(
                        tk.END,
                        f"{factura['numar']:<10} | {factura['data']:<15} | {factura['nume_client']:<40} | {factura['total_general']:>10.2f}"
                    )
                listbox_cautare.insert(tk.END, "-" * 85)
                listbox_cautare.insert(tk.END, f"{'TOTAL GENERAL:':<69} | {suma_totala:>10.2f} RON")
            else:
                listbox_cautare.insert(tk.END, "Nu s-au găsit facturi.")

        tk.Button(search_subframe, text="🔍 Caută Facturi", bg="#00897b", fg="white", font=("Arial", 10, "bold"),
                  width=30, command=executa_cautare).grid(row=4, column=0, columnspan=2, pady=15)

        # --- RÂND 5: LISTBOX ISTORIC ---
        listbox_cautare.grid(row=5, column=0, columnspan=2, pady=10)

        def action_listeaza():
            try:
                selection = listbox_cautare.curselection()
                if not selection:
                    messagebox.showwarning("Atenție", "Te rugăm să selectezi o factură din listă!")
                    return

                index = selection[0]
                if index < 2: return  # Sărim peste header-e

                text_linie = listbox_cautare.get(index)
                if "TOTAL GENERAL:" in text_linie or "-------" in text_linie: return

                nr_factura = text_linie.split('|')[0].strip()
                utils.genereaza_pdf_din_db(nr_factura)
            except Exception as e:
                print(f"Eroare la listare: {e}")

        # --- RÂND 6: BUTON LISTARE ---
        tk.Button(search_subframe, text="📄 Listează factura selectată (PDF)", bg="#2196f3", fg="white",
                  font=("Arial", 10, "bold"), command=action_listeaza).grid(row=6, column=0, columnspan=2, pady=5)

        # --- RÂND 7: BUTON resetare cautare ---
        def resetare_cautare():
            # Curățăm câmpurile text din ecranul de căutare
            for entry in [
                self.furnizor_nume_cautare,
                self.cui_entry,
                self.client_nume_cautare,
                self.cui_entryc  # CORECTAT: numele corect al widget-ului
            ]:
                entry.delete(0, tk.END)
                entry.config(state='normal')

            # Resetăm și datele la valorile inițiale
            datai_entryc.delete(0, tk.END)
            datai_entryc.insert(0, "2026-01-01")
            datas_entryc.delete(0, tk.END)
            datas_entryc.insert(0, datetime.now().strftime("%Y-%m-%d"))

            # Ștergem și rezultatele anterioare din listbox-ul de istoric
            listbox_cautare.delete(0, tk.END)

        # Adăugăm butonul în grid (Atenție: i-am dat row=7, deci butonul de listare de sub listbox va trebui mutat la row=8)
        tk.Button(search_subframe, text="♻️ Resetare Căutare", bg="#757575", fg="white",
                  font=("Arial", 10, "bold"), width=30, command=resetare_cautare).grid(row=7, column=0, columnspan=2, pady=5)

    def completeaza_client(self, row):
        self.client_cui.delete(0, tk.END)
        self.client_cui.insert(0, row[0])
        self.client_nume.delete(0, tk.END)
        self.client_nume.insert(0, row[1])
        self.client_onrc.delete(0, tk.END)
        self.client_onrc.insert(0, row[2])
        self.client_localitate.delete(0, tk.END)
        self.client_localitate.insert(0, row[3])
        self.client_adresa.delete(0, tk.END)
        self.client_adresa.insert(0, row[4])
        self.client_judet.delete(0, tk.END)
        self.client_judet.insert(0, row[5])
        self.client_tara.delete(0, tk.END)
        self.client_tara.insert(0, row[6])
        self.client_banca.delete(0, tk.END)
        self.client_banca.insert(0, row[7])
        self.client_iban.delete(0, tk.END)
        self.client_iban.insert(0, row[8])
        self.client_banca1.delete(0, tk.END)
        self.client_banca1.insert(0, row[9])
        self.client_iban1.delete(0, tk.END)
        self.client_iban1.insert(0, row[10])

    def completeaza_furnizor(self, row):
        self.furnizor_cui.delete(0, tk.END)
        self.furnizor_cui.insert(0, row[0])
        self.furnizor_nume.delete(0, tk.END)
        self.furnizor_nume.insert(0, row[1])
        self.furnizor_onrc.delete(0, tk.END)
        self.furnizor_onrc.insert(0, row[2])
        self.furnizor_localitate.delete(0, tk.END)
        self.furnizor_localitate.insert(0, row[3])
        self.furnizor_adresa.delete(0, tk.END)
        self.furnizor_adresa.insert(0, row[4])
        self.furnizor_judet.delete(0, tk.END)
        self.furnizor_judet.insert(0, row[5])
        self.furnizor_tara.delete(0, tk.END)
        self.furnizor_tara.insert(0, row[6])
        self.furnizor_banca.delete(0, tk.END)
        self.furnizor_banca.insert(0, row[7])
        self.furnizor_iban.delete(0, tk.END)
        self.furnizor_iban.insert(0, row[8])
        self.furnizor_banca1.delete(0, tk.END)
        self.furnizor_banca1.insert(0, row[9])
        self.furnizor_iban1.delete(0, tk.END)
        self.furnizor_iban1.insert(0, row[10])

        cui = self.furnizor_cui.get()
        nr_sugerat = utils.sugereaza_urmatorul_numar(cui)
        tabel = "furnizori"
        date_firma = utils.logic_cauta_entitate(cui, tabel)
        if nr_sugerat:
            self.numar_entry.delete(0, "end")
            self.numar_entry.insert(0, nr_sugerat)
            if date_firma and 'ser_fac' in date_firma:
                self.ser_fac_entry.delete(0, "end")
                self.ser_fac_entry.insert(0, date_firma['ser_fac'])

        cui_furnizor = self.furnizor_cui.get()
        explicatii_firma = db.get_explicatii_furnizor(cui_furnizor)
        self.explicatii_combo['values'] = explicatii_firma

        if explicatii_firma:
            self.explicatii_combo.set(explicatii_firma[0])
        else:
            self.explicatii_combo.set("")

    def destroy(self):
        self.arata_pagina(self.pagina_start)