import tkinter as tk
import db
from tkinter import messagebox
from factura import Factura, Produs
from pdf_generator2 import export_pdf
from xml_generator import export_xml
from datetime import datetime
from factura import Entitate


class AplicatieFactura:
    def __init__(self, master):
        self.master = master
        master.title("Generator de Facturi")
        self.produse = []

        tk.Label(master, text="Număr Factură").grid(row=0, column=0)
        self.numar_entry = tk.Entry(master)
        self.numar_entry.grid(row=0, column=1)

        tk.Label(master, text="Data").grid(row=1, column=0)
        self.data_entry = tk.Entry(master)
        self.data_entry.insert(0, datetime.today().strftime('%d-%m-%Y'))
        self.data_entry.grid(row=1, column=1)

                # Furnizor 
        tk.Label(master, text="Furnizor ").grid(row=2, column=0)     
        tk.Label(master,text="=======================================").grid(row=3, columnspan=2)
        tk.Label(master,text="||").grid(rowspan=2,column=10)
        tk.Label(master, text="CUI").grid(row=5, column=0)
        self.furnizor_cui = tk.Entry(master)
        self.furnizor_cui.grid(row=5, column=1)
        
        tk.Label(master, text="Denumire:").grid(row=4, column=0) 
        self.furnizor_nume = tk.Entry(master)
        self.furnizor_nume.grid(row=4, column=1)

        
        tk.Label(master, text="Adresa").grid(row=6, column=0)
        self.furnizor_adresa = tk.Entry(master, width=40)
        self.furnizor_adresa.grid(row=6, column=1)

        tk.Label(master, text="IBAN").grid(row=7, column=0)
        self.furnizor_iban = tk.Entry(master, width=40)
        self.furnizor_iban.grid(row=7, column=1)

        tk.Label(master, text="ONRC").grid(row=8, column=0)
        self.furnizor_onrc = tk.Entry(master, width=40)
        self.furnizor_onrc.grid(row=8, column=1)

        # Client 
        tk.Label(master, text="Client").grid(row=2, column=3)
        tk.Label(master,text="=========================").grid(row=3, column=3)
        tk.Label(master, text="Denumire:").grid(row=4, column=3) 
        self.client_nume = tk.Entry(master)
        self.client_nume.grid(row=4, column=4)

        tk.Label(master, text="CUI").grid(row=5, column=3)
        self.client_cui = tk.Entry(master)
        self.client_cui.grid(row=5, column=4)
        
        tk.Label(master, text="Adresa").grid(row=6, column=3)
        self.client_adresa = tk.Entry(master, width=40)
        self.client_adresa.grid(row=6, column=4)

        tk.Label(master, text="IBAN").grid(row=7, column=3)
        self.client_iban = tk.Entry(master, width=40)
        self.client_iban.grid(row=7, column=4)

        tk.Label(master, text="ONRC").grid(row=8, column=3)
        self.client_onrc = tk.Entry(master, width=40)
        self.client_onrc.grid(row=8, column=4)

       

        # Produse
        tk.Label(master, text="Produs").grid(row=12, column=0, sticky='E')
        self.produs_entry = tk.Entry(master)
        self.produs_entry.grid(row=12, column=1, sticky='W')

        tk.Label(master, text="Cantitate").grid(row=13, column=0,)
        self.cantitate_entry = tk.Entry(master)
        self.cantitate_entry.grid(row=13, column=1)

        tk.Label(master, text="Preț unitar").grid(row=14, column=0)
        self.pret_entry = tk.Entry(master)
        self.pret_entry.grid(row=14, column=1)
        
        tk.Label(master, text="TVA").grid(row=15, column=1)
        self.tva_entry = tk.Entry(master)
        self.tva_entry.grid(row=15, column=1)

        tk.Button(master, text="Adaugă produs", command=self.adauga_produs).grid(row=16, column=0, columnspan=2, pady=5)

        tk.Button(master, text="Generează Factura", command=self.genereaza_factura).grid(row=17, column=0, columnspan=2, pady=10)
      
    def adauga_produs(self):
        try:
            produs = Produs(
                self.produs_entry.get(),
                float(self.cantitate_entry.get()),
                float(self.pret_entry.get()),
                float(self.tva_entry.get())
            )
            self.produse.append(produs)
            messagebox.showinfo("Produs Adăugat", f"Produsul {produs.denumire} a fost adăugat.")
        except Exception as e:
            messagebox.showerror("Eroare", str(e))

    def genereaza_factura(self):
        if not self.produse:
            messagebox.showerror("Eroare", "Nu ai adăugat produse.")
        return

        factura = Factura(
            furnizor = Entitate(
                nume=self.furnizor_nume.get(),
                cui=self.furnizor_cui.get(),
                onrc=self.furnizor_onrc.get(),
                adresa=self.furnizor_adresa.get(),
                iban=self.furnizor_iban.get()
            ),

            client = Entitate(
                nume=self.client_nume.get(),
                cui=self.client_cui.get(),
                onrc=self.client_onrc.get(),
                adresa=self.client_adresa.get(),
                iban=self.client_iban.get()
            ),

            factura = Factura(
                self.numar_entry.get(),
                self.data_entry.get(),
                furnizor,
                client,
                self.produse
            )
                   
        )
        # 1. Salvează în PDF și XML
        export_pdf(factura, filename=f"Factura_{factura.numar}.pdf")
        export_xml(factura, filename=f"Factura_{factura.numar}.xml")

        # 2. Salvează în baza de date 🗃️
        db.salveaza_factura(factura)

        # 3. Gata!
        messagebox.showinfo("Succes", f"Factura {factura.numar} a fost generată și salvată.")
    
if __name__ == "__main__":
    root = tk.Tk()
    app = AplicatieFactura(root)
    root.mainloop()