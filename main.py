import tkinter as tk
from tkinter import END, messagebox, ttk
from factura import Factura, Entitate, Produs
# FIX: Corectarea importurilor pentru a se potrivi cu numele fișierelor de export
from pdf_generator2 import export_pdf 
from ubl_generator import export_xml_lxml
from db import  get_unitati_text_format, creare_tabele, populate_unitati_default, get_entitate_dupa_cui, salveaza_factura_completa, format_data_ro
from datetime import datetime
import os

class AplicatieFactura:
    def __init__(self, master):
        creare_tabele() # Comentat
        populate_unitati_default()
        
        self.master = master
        master.title("🧾 Generator e-Facturi XML + PDF")

        self.produse = [] # Lista internă de obiecte Produs
        
        
        # Setează un stil uniform
        self.master.option_add("*Font", "Arial 10")
        data_gen=format_data_ro(datetime.today())

        # === Furnizor ===
        tk.Label(master, text="📌 Furnizor", font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=2, pady=(10, 0))

        # Câmpurile Furnizor
        self.furnizor_cui = self._entry(master, "CUI", 1, 0)
        self.furnizor_nume = self._entry(master, "Denumire", 1, 1)
        self.furnizor_onrc = self._entry(master, "ONRC", 2,0)
        self.furnizor_adresa = self._entry(master, "Adresă", 2, 1)
        self.furnizor_localitate = self._entry(master, "Localitate", 3, 0)
        self.furnizor_judet = self._entry1(master, "Judet", 3,1) 
        self.furnizor_tara = self._entry1(master, "Țara", 3, 2, default="RO")
        self.furnizor_banca = self._entry(master, "Banca 1", 4, 0)
        self.furnizor_iban = self._entry(master, "IBAN 1", 4, 1)
        self.furnizor_banca1 = self._entry(master, "Banca 2", 5, 0)
        self.furnizor_iban1 = self._entry(master, "IBAN 2", 5, 1)      
        
        # Spacer
        tk.Label(master, text=" " * 20).grid(row=1, column=2, rowspan=11)
    
        # === Client ===
        tk.Label(master, text="👤 Client", font=("Arial", 11, "bold")).grid(row=0, column=3, columnspan=2, pady=(10, 0))

        # Câmpurile Client
        self.client_cui = self._entry(master, "CUI", 1, 3)
        self.client_nume = self._entry(master, "Denumire", 1, 4)
        self.client_onrc = self._entry(master, "ONRC", 2, 3)
        self.client_adresa = self._entry(master, "Adresă", 2,4)
        self.client_localitate = self._entry(master, "Localitate",3, 3)
        self.client_judet = self._entry1(master, "Judet", 3, 4) 
        self.client_tara = self._entry1(master, "Țara", 3, 5, default="RO")
        self.client_banca = self._entry(master, "Banca 1", 4, 3)
        self.client_iban = self._entry(master, "IBAN 1", 4, 4)
        self.client_banca1 = self._entry(master, "Banca 2", 5, 3)
        self.client_iban1 = self._entry(master, "IBAN 2", 5, 4)

        # Adaugă bind-urile pentru căutare CUI (dacă db ar fi activ)
        self.furnizor_cui.bind("<FocusOut>", lambda e: self.cauta_furnizor_dupa_cui()) 
        self.client_cui.bind("<FocusOut>", lambda e: self.cauta_client_dupa_cui())

        # === Factura Detalii ===
        ROW_START_FACTURA = 10
        tk.Label(master, text="🧾 Detalii Factură", font=("Arial", 11, "bold")).grid(row=ROW_START_FACTURA, column=2, columnspan=2, pady=(10, 5))

        self.numar_entry = self._entry(master, "Număr factură", ROW_START_FACTURA + 1, 2)
        self.data_entry = self._entry(master, "Data (ZZ.LL.AAAA)", ROW_START_FACTURA + 2, 2, default=datetime.today().strftime("%Y-%m-%d"))

        # === Produse Input ===
        ROW_START_PRODUS = ROW_START_FACTURA + 4
        tk.Label(master, text="📦 Adaugă produs în factură", font=("Arial", 12, "bold")).grid(row=ROW_START_PRODUS, column=0, columnspan=5, pady=(10, 5))

        # Etichete
        labels = ["Denumire", "UM (ex: H87)", "Cantitate", "Preț unitar", "TVA (%)"]
        for i, label in enumerate(labels):
            tk.Label(master, text=label).grid(row=ROW_START_PRODUS + 1, column=i)
        
        

        # Entry-uri (FIX: Rândul a fost corectat)
        self.produs_denumire = tk.Entry(master, width=20)
        #Lista unitati masura
        um_lista = get_unitati_text_format()
        self.produs_um = ttk.Combobox(master, values=um_lista, width=10)
        self.produs_um.grid(row=ROW_START_PRODUS+2, column=1, padx=5, pady=5)
        self.produs_um.set(um_lista[1])  # default: C62 - Bucată
        # self.produs_um = tk.Entry(master, width=10)
        self.produs_cant = tk.Entry(master, width=8)
        self.produs_pret = tk.Entry(master, width=10)
        self.produs_tva = tk.Entry(master, width=6)

        entries = [self.produs_denumire, self.produs_um, self.produs_cant, self.produs_pret, self.produs_tva]
        for i, entry in enumerate(entries):
            entry.grid(row=ROW_START_PRODUS + 2, column=i, padx=5, pady=5) 

        self.produs_tva.insert(0, "0") 

        # Buton adaugare
        tk.Button(master, text="➕ Adaugă produs", command=self.adauga_produs).grid(row=ROW_START_PRODUS + 3, column=0, columnspan=5, pady=(5, 10))

        # Listbox (Afișarea produselor)
        self.listbox = tk.Listbox(master, width=90, height=6)
        self.listbox.grid(row=ROW_START_PRODUS + 4, column=0, columnspan=5, padx=10)

        # Buton stergere
        tk.Button(master, text="🗑️ Șterge produs selectat", command=self.sterge_produs).grid(row=ROW_START_PRODUS + 5, column=0, columnspan=5, pady=10)

        # Buton Generare Factură
        tk.Button(master, text="🖨️ Generează Factură (XML + PDF)", bg="#047857", fg="white", 
                  font=("Arial", 11, "bold"), command=self.genereaza_factura).grid(row=ROW_START_PRODUS + 6, column=0, columnspan=5, pady=(15, 20), ipadx=10, ipady=5)

    def _entry(self, master, label, row, col=0, default=""):
        # Metodă helper pentru a crea etichete și câmpuri de intrare
        tk.Label(master, text=label).grid(row=row, column=col, sticky="e", padx=5, pady=2)
        entry = tk.Entry(master, width=30)
        entry.grid(row=row, column=col + 1, sticky="w", padx=5, pady=2)
        entry.insert(0, default)
        return entry
    
    def _entry1(self, master, label, row, col=0, default=""):
        # Metodă helper pentru a crea etichete și câmpuri de intrare
        tk.Label(master, text=label).grid(row=row, column=col, sticky="e", padx=5, pady=2)
        entry = tk.Entry(master, width=4)
        entry.grid(row=row, column=col + 1, sticky="w", padx=5, pady=2)
        entry.insert(0, default)
        return entry

    def adauga_produs(self):
        try:
            # Preluare și validare date
            denumire = self.produs_denumire.get().strip()
            um = self.produs_um.get()
            cantitate = float(self.produs_cant.get())
            pret_unitar = float(self.produs_pret.get())
            tva_percent = float(self.produs_tva.get())

            if not denumire or not um:
                 messagebox.showerror("Eroare", "Denumirea și UM sunt obligatorii.")
                 return

            produs = Produs(
                denumire=denumire,
                cantitate=cantitate,
                um=um,
                pret_unitar=pret_unitar,
                tva_percent=tva_percent
            )

            # Adaugă la lista internă self.produse
            self.produse.append(produs)
            
            # Adaugă în listbox
            total_linie = produs.total()
            # Formatare pentru listbox
            linie_afisare = f'{produs.denumire[:25]:<25} | UM: {produs.um:<5} | Qty: {produs.cantitate:>7.2f} | PU: {produs.pret_unitar:>8.2f} | TVA: {produs.tva_percent:>3.0f}% | Total: {total_linie:>10.2f}'
            self.listbox.insert(tk.END, linie_afisare)

            # Reset câmpuri
            self._clear_product_fields()

        except ValueError:
            messagebox.showerror("Eroare", "Introdu corect valorile numerice pentru cantitate, preț și TVA!")
        except Exception as e:
            messagebox.showerror("Eroare necunoscută", f"Eroare la adăugare produs: {e}")

    def sterge_produs(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Selectare", "Selectează un produs de șters.")
            return
        
        index = sel[0]
        try:
            # Șterge din lista internă self.produse și din listbox
            self.produse.pop(index)
            self.listbox.delete(index)
            messagebox.showinfo("Șters", "Produsul a fost șters din factură.")
        except IndexError:
             messagebox.showerror("Eroare", "Index invalid.")

    def _clear_product_fields(self):
        # Resetează câmpurile de intrare pentru produse
        self.produs_denumire.delete(0, tk.END)
        self.produs_um.delete(0, tk.END)
        self.produs_cant.delete(0, tk.END)
        self.produs_pret.delete(0, tk.END)
        self.produs_tva.delete(0, tk.END)
        self.produs_tva.insert(0, "0")

    def genereaza_factura(self):
        if not self.produse:
            messagebox.showerror("Eroare", "Adaugă cel puțin un produs.")
            return

        # Creează folderul "facturi" dacă nu există
        output_dir = "facturi"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        try:
            # Preluare date entități
            furnizor = Entitate(
                self.furnizor_nume.get(), self.furnizor_cui.get(), self.furnizor_onrc.get(), 
                self.furnizor_adresa.get(), self.furnizor_localitate.get(), self.furnizor_judet.get(), 
                self.furnizor_tara.get(), self.furnizor_banca.get(), self.furnizor_iban.get(), 
                self.furnizor_banca1.get(), self.furnizor_iban1.get()
            )
            client = Entitate(
                self.client_nume.get(), self.client_cui.get(), self.client_onrc.get(), 
                self.client_adresa.get(), self.client_localitate.get(), self.client_judet.get(), 
                self.client_tara.get(), self.client_banca.get(), self.client_iban.get(), 
                self.client_banca1.get(), self.client_iban1.get()
            )
            
            if not furnizor.cui or not client.cui or not self.numar_entry.get():
                messagebox.showerror("Eroare", "CUI-urile și Numărul facturii sunt obligatorii.")
                return

            # Creare obiect Factura
            factura = Factura(
                numar=self.numar_entry.get(),
                data=self.data_entry.get(),
                furnizor=furnizor,
                client=client,
                produse=self.produse
            )

            # Salvare factură în DB (Comentată)
            salveaza_factura_completa(furnizor, client, factura)

            # Generare fișiere
            nume_fisier = f"{output_dir}/Factura_{factura.numar}"
            export_pdf(factura, f"{nume_fisier}.pdf")
            export_xml_lxml(factura, f"{nume_fisier}.xml")

            messagebox.showinfo("Succes", f"Factura {factura.numar} a fost generată cu succes în directorul '{output_dir}'!")
            
            # Reset UI
            self.produse.clear()
            self.listbox.delete(0, tk.END)

        except Exception as e:
            messagebox.showerror("Eroare", f"Eroare la generare factură: {e}")

    # FIX: Metodele cauta_furnizor_dupa_cui și cauta_client_dupa_cui sunt comentate 
    # pentru că nu este disponibil modulul db.py.
    def cauta_furnizor_dupa_cui(self):
        cui = self.furnizor_cui.get().strip()
        if not cui:
            return
        
        ent = get_entitate_dupa_cui("furnizori", cui)
        print('$' * 50)
        print(ent)
        if ent:
            self.furnizor_nume.delete(0, tk.END)
            self.furnizor_nume.insert(0, ent["nume"])
            self.furnizor_onrc.delete(0, tk.END)
            self.furnizor_onrc.insert(0, ent["onrc"])
            self.furnizor_adresa.delete(0, tk.END)
            self.furnizor_adresa.insert(0, ent["adresa"])
            self.furnizor_localitate.delete(0, tk.END)
            self.furnizor_localitate.insert(0, ent["localitate"])
            self.furnizor_judet.delete(0, tk.END)
            self.furnizor_judet.insert(0, ent["judet"])
            self.furnizor_tara.delete(0, tk.END)
            self.furnizor_tara.insert(0, ent["tara"])
            self.furnizor_banca.delete(0, tk.END)
            self.furnizor_banca.insert(0, ent["banca"])
            self.furnizor_iban.delete(0, tk.END)
            self.furnizor_iban.insert(0, ent["iban"])
            self.furnizor_banca1.delete(0, tk.END)
            self.furnizor_banca1.insert(0, ent["banca1"])
            self.furnizor_iban1.delete(0, tk.END)
            self.furnizor_iban1.insert(0, ent["iban1"])
            print("✔ Furnizor încărcat din baza de date.")

        
        # Aici ar trebui să fie logica de căutare DB
        # if ent:
        #     ... populați câmpurile ...
        # print("Căutare furnizor (funcționalitate DB comentată).") 
            
    def cauta_client_dupa_cui(self):
        cui = self.client_cui.get().strip()
        if not cui:
            return
        
        ent = get_entitate_dupa_cui("clienti", cui)
        if ent:
            self.client_nume.delete(0, tk.END)
            self.client_nume.insert(0, ent["nume"])
            self.client_onrc.delete(0, tk.END)
            self.client_onrc.insert(0, ent["onrc"])
            self.client_adresa.delete(0, tk.END)
            self.client_adresa.insert(0, ent["adresa"])            
            self.client_localitate.delete(0, tk.END)
            self.client_localitate.insert(0, ent["localitate"])
            self.client_judet.delete(0, tk.END)
            self.client_judet.insert(0, ent["judet"])
            self.client_tara.delete(0, tk.END)
            self.client_tara.insert(0, ent["tara"])
            self.client_banca.delete(0, tk.END)
            self.client_banca.insert(0, ent["banca"])
            self.client_iban.delete(0, tk.END)
            self.client_iban.insert(0, ent["iban"])
            self.client_banca1.delete(0, tk.END)
            self.client_banca1.insert(0, ent["banca1"])
            self.client_iban1.delete(0, tk.END)
            self.client_iban1.insert(0, ent["iban1"])
            print("✔ Client încărcat din baza de date.")  

        # Aici ar trebui să fie logica de căutare DB
        # print("Căutare client (funcționalitate DB comentată).") 
    
   
            
            
if __name__ == "__main__":
    root = tk.Tk()
    app = AplicatieFactura(root)
    root.mainloop()