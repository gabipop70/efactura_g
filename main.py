import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
from tkinter import messagebox

import messagebox

# Importam modulele locale
from db import get_unitati_text_format, creare_tabele, populate_unitati_default
# AICI IMPORTAM NOUL FISIER DE FUNCTII
import utils

class AplicatieFactura:
    def __init__(self, master):
        # Initializare DB
        creare_tabele()
        populate_unitati_default()
        
        self.master = master
        master.title("🧾 Generator e-Facturi XML + PDF")
        self.master.option_add("*Font", "Arial 10")

        self.produse = [] 
        
        # --- UI SETUP (Layout) ---
        self._setup_ui()

    def _setup_ui(self):
        # Aici punem tot codul care deseneaza Label-uri si Entry-uri
        # (Am simplificat codul pentru claritate, pastreaza structura ta de grid)
        
        # === FURNIZOR ===
        tk.Label(self.master, text="📌 Furnizor", font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=3)
        self.furnizor_cui = self._entry("CUI", 1, 0)
        self.furnizor_nume = self._entry("Denumire", 1, 1)
        self.furnizor_onrc = self._entry("ONRC", 2, 0)
        self.furnizor_adresa = self._entry2("Adresă", 3, 0)
        self.furnizor_localitate = self._entry("Localitate", 2, 1)
        self.furnizor_judet = self._entry1("Judet", 4, 0) 
        self.furnizor_tara = self._entry1("Țara", 4, 1, default="RO")
        self.furnizor_banca = self._entry("Banca 1", 5, 0)
        self.furnizor_iban = self._entry("IBAN 1", 5, 1)
        self.furnizor_banca1 = self._entry("Banca 2", 6, 0)
        self.furnizor_iban1 = self._entry("IBAN 2", 6, 1)  

        # Bind Event FocusOut pentru cautare automata
        self.furnizor_cui.bind("<FocusOut>", lambda e: self.actiune_cauta_entitate("furnizor"))

        # === CLIENT === (Similar layout ca la furnizor)
        tk.Label(self.master, text="👤 Client", font=("Arial", 11, "bold")).grid(row=0, column=3, columnspan=4)
        self.client_cui = self._entry("CUI", 1, 3)
        self.client_nume = self._entry("Denumire", 1, 4)
        self.client_onrc = self._entry("ONRC", 2, 3)
        self.client_adresa = self._entry2("Adresă", 3, 3)
        self.client_localitate = self._entry("Localitate", 2, 4)
        self.client_judet = self._entry1("Judet", 4, 3) 
        self.client_tara = self._entry1("Țara", 4, 4, default="RO")
        self.client_banca = self._entry("Banca 1", 5, 3)
        self.client_iban = self._entry("IBAN 1", 5, 4)
        self.client_banca1 = self._entry("Banca 2", 6, 3)
        self.client_iban1 = self._entry("IBAN 2", 6, 4)

        self.client_cui.bind("<FocusOut>", lambda e: self.actiune_cauta_entitate("client"))

        # === AICI ADAUGĂM GENERAREA AUTOMATĂ A NUMĂRULUI ===

        # === DETALII FACTURA ===
        tk.Label(self.master, text="🧾 Detalii factura", font="bold").grid(row=10, column=2, columnspan=3)
        self.numar_entry = self._entry("Număr", 11, 2)
        self.data_entry = self._entry("Data", 12, 2, default=datetime.now().strftime("%Y-%m-%d"))

        # === PRODUSE ===
        # ... (Codul tau de layout produse ramane la fel) ...
        self.produs_frame = tk.Frame(self.master)
        self.produs_frame.grid(row=15, column=1, columnspan=6)
        tk.Label(self.produs_frame, text="Denumire produs", font=("Arial", 11,"italic")).grid(row=0, column=0)
        tk.Label(self.produs_frame, text="U.M.", font=("Arial", 11, "italic")).grid(row=0, column=1)
        tk.Label(self.produs_frame, text="Cant.", font=("Arial", 11, "italic")).grid(row=0, column=2)
        tk.Label(self.produs_frame, text="Pret unit.", font=("Arial", 11, "italic")).grid(row=0, column=3)
        tk.Label(self.produs_frame, text="TVA(%)", font=("Arial", 11, "italic")).grid(row=0, column=4)
        self.produs_denumire = tk.Entry(self.produs_frame, width=40)
        self.produs_denumire.grid(row=1, column=0)

        # Combobox UM
        self.produs_um = tk.Entry(self.produs_frame, width=10)
        um_vals = get_unitati_text_format()
        self.produs_um = ttk.Combobox(self.produs_frame, values=um_vals, width=10)
        self.produs_um.grid(row=1, column=1)
        if um_vals: self.produs_um.set(um_vals[1])

        self.produs_cant = tk.Entry(self.produs_frame, width=8, justify="right"); self.produs_cant.grid(row=1, column=2)
        self.produs_cant.insert(0, "0.00")
        self.produs_pret = tk.Entry(self.produs_frame, width=10, justify="right"); self.produs_pret.grid(row=1, column=3)
        self.produs_pret.insert(0, "0.00")
        self.produs_tva = tk.Entry(self.produs_frame, width=5, justify="right"); self.produs_tva.grid(row=1, column=4)
        self.produs_tva.insert(0, "0")
        tk.Button(self.produs_frame, text="➕ Adaugă", command=self.actiune_adauga_produs).grid(row=1, column=5)

        
        self.listbox = tk.Listbox(self.master, width=100, height=10, font=("Consolas", 10))
        self.listbox.grid(row=17, column=1, columnspan=6)
        header = f"{'     Produs':<33} | {'Cant.':<5} | {'Preț Unitar':<12} | {'TVA %':<6} | {'Total fara TVA':<12} | {'Total cu TVA': <12}"
        separator = "------------------------------------------------------------------------------------------------------"
        self.listbox.insert(tk.END, header)
        self.listbox.insert(tk.END, separator)
         # Buton stergere
        tk.Button(self.master, text="🗑️ Șterge produs selectat", command=self.sterge_produs).grid(row=18, column=3, columnspan=5)

        tk.Button(self.master, text="GENEREAZĂ FACTURA", bg="green", fg="white", 
                  command=self.actiune_generare).grid(row=19, column=0, columnspan=5, pady=20)

        raspuns = messagebox.askyesno("Generare Factura", "Doresti sa generezi o noua factura?")
        if raspuns:
            # Codul pentru generarea facturii
            self.resetare_campuri()
        else:
            # Poți pune aici alt cod, sau pur și simplu să nu faci nimic
            self.destroy()  # Inchide fereastra

    # --- HELPERS UI ---
    def _entry(self, label, row, col, default=""):
        tk.Label(self.master, text=label).grid(row=row, column=col, sticky="e")
        e = tk.Entry(self.master, width=25)
        e.grid(row=row, column=col+1, sticky="w")
        e.insert(0, default)
        return e
    
    def _entry1(self, label, row, col, default=""):
        tk.Label(self.master, text=label).grid(row=row, column=col, sticky="e")
        e = tk.Entry(self.master, width=5)
        e.grid(row=row, column=col+1, columnspan=4, sticky="w")
        e.insert(0, default)
        return e

    def _entry2(self, label, row, col, default=""):
        tk.Label(self.master, text=label).grid(row=row, column=col, sticky="e")
        e = tk.Entry(self.master, width=51)
        e.grid(row=row, column=col+1, columnspan=2, sticky="w")
        e.insert(0, default)
        return e
    # --- ACTIUNI (Apeleaza functiile din utils.py) ---

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
            totalcutva = total + total*produs_nou.tva_percent/100
            
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
        # Definim maparea intre campurile UI si cheile din dictionarul de date
        if tip == "furnizor":
            cui = self.furnizor_cui.get()
            tabel = "furnizori"
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
        
        # Apelam logica din Utils
        self.master.config(cursor="wait")
        self.master.update()
        
        date_firma = utils.logic_cauta_entitate(cui, tabel)
        
        self.master.config(cursor="")

        # === GENERARE AUTOMATĂ NUMĂR FACTURĂ ===
        if tip == "client" and cui:
            nr_sugerat = utils.sugereaza_urmatorul_numar(cui)
            if nr_sugerat:
                self.numar_entry.delete(0, tk.END)
                self.numar_entry.insert(0, nr_sugerat)
        # ========================================
        
        # Actualizam UI daca avem date
        if date_firma:
            print(f"Firma gasita in: {date_firma.get('sursa')}")
            for key, widget in fields.items():
                val = date_firma.get(key, "")
                widget.delete(0, tk.END)
                if val: widget.insert(0, str(val))
        else:
            print("Firma nu a fost gasita.")

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
            'data': self.data_entry.get()
        }

        try:
            # Apelam functia "Manager" din Utils care face toata treaba
            pdf, xml = utils.generare_fisiere_factura(d_furnizor, d_client, d_factura, self.produse)
            
            messagebox.showinfo("Succes", f"Factura generata!\nPDF: {pdf}\nXML: {xml}")
            
            # Reset
            self.produse = []
            self.listbox.delete(0, tk.END)

            
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
            self.furnizor_cui.focus_set()



if __name__ == "__main__":
    root = tk.Tk()
    app = AplicatieFactura(root)
    root.mainloop()