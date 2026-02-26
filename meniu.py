import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox
from db import get_unitati_text_format, creare_tabele, populate_unitati_default, cauta_facturi_dupa_cui
import utils
from utils import centreaza_fereastra, sugereaza_nr_chitanta

class AplicatieFacturi:
    def __init__(self, master):
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
        self._setup_ui_generare()  # Mutăm codul tău de UI aici
        self._setup_ui_cautare()  # Mutăm codul de căutare aici

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

        # Titlu mare
        tk.Label(p, text="📊 Sistem Gestiune Facturi", font=("Arial", 20, "bold"),
                 bg="#e0f7fa", fg="#006064").pack(pady=(50, 20))

        # Text informativ
        info_text = (
            "Bine ați venit în aplicația de generare e-Factura!\n\n"
            "• Folosiți meniul de sus pentru navigare.\n"
            "• 'Factură Nouă' - Generare fișiere PDF și XML (RO e-Factura).\n"
            "• 'Istoric' - Căutare și re-listare facturi emise anterior.\n"
            "• CUI-urile sunt salvate automat pentru utilizări viitoare."
        )

        tk.Label(p, text=info_text, font=("Arial", 12), bg="#e0f7fa",
                 justify="left", padx=20).pack(pady=20)

        # Butoane rapide (Quick Actions)
        btn_frame = tk.Frame(p, bg="#e0f7fa")
        btn_frame.pack(pady=30)

        tk.Button(btn_frame, text="📄 Emite Factură Nouă", font=("Arial", 11), width=20,
                  command=lambda: self.arata_pagina(self.pagina_generare)).grid(row=0, column=0, padx=10)

        tk.Button(btn_frame, text="🔍 Consultă Istoric", font=("Arial", 11), width=20,
                  command=lambda: self.arata_pagina(self.pagina_cautare)).grid(row=0, column=1, padx=10)

        # Footer cu versiunea
        tk.Label(p, text="Versiune: 2026.1.0 | Status DB: Conectat", font=("Arial", 8),
                 bg="#e0f7fa", fg="gray").pack(side="bottom", pady=10)

    def _setup_ui_generare(self):
        self.produse = []

        # --- UI SETUP (Layout) ---
        self._setup_ui()

    def _setup_ui(self):
        # Aici punem tot codul care deseneaza Label-uri si Entry-uri
        p = self.pagina_generare  # Referință scurtă către pagina de factură
        # === FURNIZOR ===
        tk.Label(self.pagina_generare, text="📌 Furnizor", bg="#e0f7fa", font=("Arial", 11, "bold")).grid(row=0, column=0,
                                                                                                         columnspan=3)
        self.furnizor_cui = self._entry(p,"CUI", 1, 0)
        self.furnizor_nume = self._entry(p,"Denumire", 1, 1)
        self.furnizor_onrc = self._entry(p,"ONRC", 2, 0)
        self.furnizor_adresa = self._entry2(p,"Adresă", 3, 0)
        self.furnizor_localitate = self._entry(p,"Localitate", 2, 1)
        self.furnizor_judet = self._entry1(p,"Judet", 4, 0)
        self.furnizor_tara = self._entry1(p,"Țara", 4, 1, default="RO")
        self.furnizor_banca = self._entry(p,"Banca 1", 5, 0)
        self.furnizor_iban = self._entry(p,"IBAN 1", 5, 1)
        self.furnizor_banca1 = self._entry(p,"Banca 2", 6, 0)
        self.furnizor_iban1 = self._entry(p,"IBAN 2", 6, 1)

        # Bind Event FocusOut pentru cautare automata
        self.furnizor_cui.bind("<FocusOut>", lambda e: self.actiune_cauta_entitate("furnizor"))

        # === CLIENT === (Similar layout ca la furnizor)
        tk.Label(self.pagina_generare, text="👤 Client", bg="#e0f7fa", font=("Arial", 11, "bold")).grid(row=0, column=3, columnspan=4)
        self.client_cui = self._entry(p,"CUI", 1, 3)
        self.client_nume = self._entry(p,"Denumire", 1, 4)
        self.client_onrc = self._entry(p,"ONRC", 2, 3)
        self.client_adresa = self._entry2(p,"Adresă", 3, 3)
        self.client_localitate = self._entry(p,"Localitate", 2, 4)
        self.client_judet = self._entry1(p,"Judet", 4, 3)
        self.client_tara = self._entry1(p,"Țara", 4, 4, default="RO")
        self.client_banca = self._entry(p,"Banca 1", 5, 3)
        self.client_iban = self._entry(p,"IBAN 1", 5, 4)
        self.client_banca1 = self._entry(p,"Banca 2", 6, 3)
        self.client_iban1 = self._entry(p,"IBAN 2", 6, 4)

        self.client_cui.bind("<FocusOut>", lambda e: self.actiune_cauta_entitate("client"))

        # === AICI ADAUGĂM GENERAREA AUTOMATĂ A NUMĂRULUI ===

        # === DETALII FACTURA ===
        tk.Label(self.pagina_generare, text="🧾 Detalii factura", font="bold", bg="#e0f7fa").grid(row=10, column=2, columnspan=3)
        self.numar_entry = self._entry(p,"Număr", 11, 2)
        self.data_entry = self._entry(p,"Data", 12, 2, default=datetime.now().strftime("%Y-%m-%d"))

        # === PRODUSE ===
        # ... (Codul tau de layout produse ramane la fel) ...
        self.produs_frame = tk.Frame(self.pagina_generare)
        self.produs_frame.grid(row=15, column=1, columnspan=6)
        tk.Label(self.produs_frame, text="Denumire produs", font=("Arial", 11, "italic"), bg="#e0f7fa").grid(row=0, column=0)
        tk.Label(self.produs_frame, text="U.M.", bg="#e0f7fa", font=("Arial", 11, "italic")).grid(row=0, column=1)
        tk.Label(self.produs_frame, text="Cant.",  bg="#e0f7fa", font=("Arial", 11, "italic")).grid(row=0, column=2)
        tk.Label(self.produs_frame, text="Pret unit.",  bg="#e0f7fa", font=("Arial", 11, "italic")).grid(row=0, column=3)
        tk.Label(self.produs_frame, text="TVA(%)",  bg="#e0f7fa", font=("Arial", 11, "italic")).grid(row=0, column=4)
        self.produs_denumire = tk.Entry(self.produs_frame, width=40)
        self.produs_denumire.grid(row=1, column=0)

        # Combobox UM
        self.produs_um = tk.Entry(self.produs_frame, width=10)
        um_vals = get_unitati_text_format()
        self.produs_um = ttk.Combobox(self.produs_frame, values=um_vals, width=10)
        self.produs_um.grid(row=1, column=1)
        if um_vals: self.produs_um.set(um_vals[1])

        self.produs_cant = tk.Entry(self.produs_frame, width=8, justify="right");
        self.produs_cant.grid(row=1, column=2)
        self.produs_cant.insert(0, "0.00")
        self.produs_pret = tk.Entry(self.produs_frame, width=10, justify="right");
        self.produs_pret.grid(row=1, column=3)
        self.produs_pret.insert(0, "0.00")
        self.produs_tva = tk.Entry(self.produs_frame, width=5, justify="right");
        self.produs_tva.grid(row=1, column=4)
        self.produs_tva.insert(0, "0")
        tk.Button(self.produs_frame, text="➕ Adaugă", command=self.actiune_adauga_produs).grid(row=1, column=5)

        self.listbox = tk.Listbox(self.pagina_generare, width=100, height=10, font=("Consolas", 10))
        self.listbox.grid(row=17, column=1, columnspan=6)
        header = f"{'     Produs':<33} | {'Cant.':<5} | {'Preț Unitar':<12} | {'TVA %':<6} | {'Total fara TVA':<12} | {'Total cu TVA': <12}"
        separator = "------------------------------------------------------------------------------------------------------"
        self.listbox.insert(tk.END, header)
        self.listbox.insert(tk.END, separator)
        # Buton stergere
        tk.Button(self.pagina_generare, text="🗑️ Șterge produs selectat", command=self.sterge_produs).grid(row=18, column=3,
                                                                                                           columnspan=5)
        tk.Button(self.pagina_generare, text="🔍 Caută facturi după CUI", command=self._setup_ui_cautare).grid(row=21,
                                                                                                                     column=0,
                                                                                                                     columnspan=5,
                                                                                                                     padx=15)

        # Check box chitanta

        # === ZONA CHITANȚĂ ===
        self.vrea_chitanta_var = tk.BooleanVar(value=False)

        # Checkbox-ul (Coloana 0)
        self.chk_chitanta = tk.Checkbutton(
            self.pagina_generare,
            text="Chitanta.",
            bg="#e0f7fa",
            variable=self.vrea_chitanta_var,
            command=self.toggle_chitanta_ui  # Am adăugat legătura cu funcția
        )
        self.chk_chitanta.grid(row=19, column=0, columnspan=2, sticky="we", padx=5, pady=5)

        # Etichetă (Coloana 1)
        tk.Label(self.pagina_generare, text="Nr. Chitanță:", bg="#e0f7fa").grid(row=20, column=0, sticky="e", padx=5, pady=5)
        vrea_chitanta = self.vrea_chitanta_var.get()
        # Câmpul de intrare (Coloana 2)
        self.entry_nr_chitanta = tk.Entry(self.pagina_generare, state="disabled")  # Pornim dezactivat (pentru că bifa e False)
        self.entry_nr_chitanta.grid(row=20, column=1, sticky="w", padx=5, pady=5)

        tk.Button(self.pagina_generare, text="GENEREAZĂ FACTURA", bg="green", fg="white",
                  command=self.actiune_generare).grid(row=22, column=0, columnspan=5, pady=20)

        # --- HELPERS UI ---

    def toggle_chitanta_ui(self):
        if self.vrea_chitanta_var.get():
            self.entry_nr_chitanta.config(state="normal")
            # Sugerăm automat un număr de chitanță când se bifează
            nr_sugerat = sugereaza_nr_chitanta()
            if nr_sugerat:
                self.entry_nr_chitanta.delete(0, tk.END)
                self.entry_nr_chitanta.insert(0, nr_sugerat)
        else:
            self.entry_nr_chitanta.delete(0, tk.END)
            self.entry_nr_chitanta.config(state="disabled")

    # --- HELPERE ENTRY MODIFICATE ---
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
        # 1. Colectam datele brute din UI
        raw_data = {
            'denumire': self.produs_denumire.get(),
            'cant_str': self.produs_cant.get(),
            'pret_str': self.produs_pret.get(),
            'tva_str': self.produs_tva.get(),
            'um': self.produs_um.get()
        }

        try:
            # 2. Trimitem la validare in UTILS
            produs_nou = utils.validare_produs_input(**raw_data)

            # 3. Daca e ok, actualizam starea aplicatiei (UI + Lista interna)
            self.produse.append(produs_nou)

            # Calculam totalul doar pentru afisare (logica simpla poate ramane aici sau mutata in modelul Produs)
            total = produs_nou.cantitate * produs_nou.pret_unitar
            totalcutva = total + total * produs_nou.tva_percent / 100

            row_text = f"{produs_nou.denumire[:20]:<33} | {produs_nou.cantitate:=5} | {produs_nou.pret_unitar:>12} | {produs_nou.tva_percent:<6} | {total:>14} | {totalcutva:>12}"
            self.listbox.insert(tk.END, row_text)

            # Curatare campuri
            self.produs_denumire.delete(0, tk.END)
            self.produs_cant.delete(0, tk.END)
            self.produs_pret.delete(0, tk.END)



        except ValueError as ex:
            messagebox.showerror("Eroare Validare", str(ex))

    def sterge_produs(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Selectare", "Selectează un produs de șters.")
            return

        index = sel[0]

        # Protect the headers
        if index < 2:
            messagebox.showwarning("Atenție", "Nu poți șterge capul de tabel!")
            return

        # Calculate index for the data list
        data_index = index - 2

        try:
            # 1. Remove from the internal data list using data_index
            if 0 <= data_index < len(self.produse):
                self.produse.pop(data_index)  # Use data_index here!

                # 2. Remove from the Listbox UI using the UI index
                self.listbox.delete(index)

                messagebox.showinfo("Șters", "Produsul a fost șters din factură.")

            # 3. Optional: Recalculate totals here
            # self.actualizeaza_totaluri()

        except IndexError:
            messagebox.showerror("Eroare", "Index invalid.")

    def actiune_cauta_entitate(self, tip):
        # 1. Configurare dinamică în funcție de tip
        if tip == "furnizor":
            cui = self.furnizor_cui.get()
            tabel = "furnizori"
            # Folosim prefixul pentru a construi referințele la atribute dinamic sau manual
            fields = {
                'nume': self.furnizor_nume, 'onrc': self.furnizor_onrc, 'adresa': self.furnizor_adresa,
                'localitate': self.furnizor_localitate, 'judet': self.furnizor_judet, 'tara': self.furnizor_tara,
                'banca': self.furnizor_banca, 'iban': self.furnizor_iban,
                'banca1': self.furnizor_banca1, 'iban1': self.furnizor_iban1
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

        # 2. Validare minimă
        if not cui:
            print("Introduceți un CUI pentru căutare.")
            return

        # 3. Execuție căutare (Mutată în afara blocului else)
        self.pagina_generare.config(cursor="wait")
        self.pagina_generare.update()

        try:
            date_firma = utils.logic_cauta_entitate(cui, tabel)

            # 4. Actualizare UI dacă avem date
            if date_firma:
                print(f"Firma găsită în: {date_firma.get('sursa')}")
                for key, widget in fields.items():
                    val = date_firma.get(key, "")
                    widget.delete(0, "end")
                    if val:
                        widget.insert(0, str(val))

                # 5. Logică specifică pentru client (Număr Factură)
                if tip == "client":
                    nr_sugerat = utils.sugereaza_urmatorul_numar(cui)
                    if nr_sugerat:
                        self.numar_entry.delete(0, "end")
                        self.numar_entry.insert(0, nr_sugerat)
            else:
                print("Firma nu a fost găsită.")

        finally:
            # Revenire cursor la normal chiar dacă apare o eroare
            self.pagina_generare.config(cursor="")

    def actiune_generare(self):
        if not self.produse:
            messagebox.showwarning("Atentie", "Nu ai adaugat produse!")
            return

        # Colectam datele din UI intr-un format curat (dictionare)
        d_furnizor = {
            'nume': self.furnizor_nume.get(), 'cui': self.furnizor_cui.get(), 'onrc': self.furnizor_onrc.get(),
            'adresa': self.furnizor_adresa.get(), 'localitate': self.furnizor_localitate.get(),
            'judet': self.furnizor_judet.get(), 'tara': self.furnizor_tara.get(),
            'banca': self.furnizor_banca.get(), 'iban': self.furnizor_iban.get(),
            'banca1': self.furnizor_banca1.get(), 'iban1': self.furnizor_iban1.get()
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
            'vrea_chitanta': self.vrea_chitanta_var.get()
        }

        try:
            # Apelam functia "Manager" din Utils care face toata treaba
            pdf, xml = utils.generare_fisiere_factura(d_furnizor, d_client, d_factura, self.produse)

            messagebox.showinfo("Succes", f"Factura generata!\nPDF: {pdf}\nXML: {xml}")

            # Reset
            self.produse = []
            self.listbox.delete(0, tk.END)

            raspuns = messagebox.askyesno("Generare Factura", "Doresti sa generezi o noua factura?")
            if raspuns:
                # Codul pentru generarea facturii
                self.resetare_campuri()
            else:
                # Poți pune aici alt cod, sau pur și simplu să nu faci nimic
                self.destroy()  # Inchide fereastra

        except Exception as e:
            messagebox.showerror("Eroare Generare", f"Ceva nu a mers bine:\n{str(e)}")
        return

    def resetare_campuri(self):
        for entry in [
            self.furnizor_nume, self.furnizor_cui, self.furnizor_onrc, self.furnizor_adresa,
            self.furnizor_localitate, self.furnizor_judet,
            self.furnizor_banca, self.furnizor_iban, self.furnizor_banca1, self.furnizor_iban1,
            self.client_nume, self.client_cui, self.client_onrc, self.client_adresa,
            self.client_localitate, self.client_judet,
            self.client_banca, self.client_iban, self.client_banca1, self.client_iban1,
            self.numar_entry, self.data_entry
        ]:
            entry.delete(0, tk.END)
            entry.config(state='normal')

        self.data_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))  # Data facturii = azi
        self.produs_cant.delete(0, tk.END)
        self.produs_cant.insert(0, "0.00")
        self.produs_pret.delete(0, tk.END)
        self.produs_pret.insert(0, "0.00")
        self.produs_tva.delete(0, tk.END)
        self.produs_tva.insert(0, "0")

        header = f"{'     Produs':<33} | {'Cant.':<5} | {'Preț Unitar':<12} | {'TVA %':<6} | {'Total fara TVA':<12} | {'Total cu TVA': <12}"
        separator = "------------------------------------------------------------------------------------------------------"
        self.listbox.insert(tk.END, header)
        self.listbox.insert(tk.END, separator)

        # Resetare checkbox chitanță
        self.vrea_chitanta_var.set(False)  # debifează checkbox-ul
        self.entry_nr_chitanta.delete(0, tk.END)
        self.entry_nr_chitanta.config(state="disabled")

        self.furnizor_cui.focus_set()


    def _setup_ui_cautare(self):
        frame = self.pagina_cautare
        tk.Label(frame, text="🔍 Căutare Istoric Facturi", font=("Arial", 14, "bold"), bg="#e0f7fa").pack(pady=10)

        search_subframe = tk.Frame(frame, bg="#e0f7fa")
        search_subframe.pack(pady=5)

        # UI Setup
        tk.Label(search_subframe, text="CUI furnizor:").grid(row=0, column=0)
        self.cui_entry = tk.Entry(search_subframe)
        self.cui_entry.grid(row=0, column=1)

        tk.Label(search_subframe, text="CUI client:").grid(row=1, column=0)
        cui_entryc = tk.Entry(search_subframe)
        cui_entryc.grid(row=1, column=1)

        # Listbox - Folosim font Monospace pentru a păstra coloanele aliniate
        listbox = tk.Listbox(search_subframe, width=100, font=("Courier", 10))
        listbox.grid(row=3, column=0, columnspan=2, pady=10)

        def executa_cautare():
            cui = self.cui_entry.get().strip()
            cui_c = cui_entryc.get().strip()
            if cui_c == "":
                cui_c = None

            rezultate = cauta_facturi_dupa_cui(cui, cui_c)
            listbox.delete(0, tk.END)

            if rezultate:
                header = f"{'Număr':<10} | {'Data':<15} | {'Client':<40} | {'Total':<15}"
                listbox.insert(tk.END, header)
                listbox.insert(tk.END, "-" * 80)
                for factura in rezultate:
                    listbox.insert(
                        tk.END,
                        f"{factura['numar']:<10} | {factura['data']:<15} | {factura['nume_client']:<40} | {factura['total_general']:<15}"
                    )
            else:
                listbox.insert(tk.END, "Nu s-au găsit facturi.")

        def action_listeaza():
            """Extrage selecția din listbox și generează PDF"""
            try:
                selection = listbox.curselection()
                if not selection:
                    messagebox.showwarning("Te rugăm să selectezi o factură din listă!")
                    return

                index = selection[0]
                if index < 2:  # Ignorăm header-ul și linia de separare
                    return

                text_linie = listbox.get(index)
                # Extragem primul element (numărul facturii) înainte de separatorul |
                nr_factura = text_linie.split('|')[0].strip()

                # Apelăm generarea din modulul utils
                utils.genereaza_pdf_din_db(nr_factura)

            except Exception as e:
                print(f"Eroare la listare: {e}")

        # Butoanele sunt la același nivel cu definițiile funcțiilor de mai sus
        tk.Button(search_subframe, text="Caută", command=executa_cautare).grid(row=2, column=0, columnspan=2, pady=5)
        tk.Button(search_subframe, text="Listează factura", command=action_listeaza).grid(row=4, column=0, columnspan=2, pady=5)
        
    