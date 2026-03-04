# utils.py
# -*- coding: utf-8 -*-
import os
import re
from datetime import datetime

from tqdm import tk


from factura import Factura, Entitate, Produs
# Import�m modulele tale existente pentru logic�
from db import get_entitate_dupa_cui, cauta_firma_anaf, salveaza_factura_completa
from pdf_generator2 import export_pdf
from ubl_generator import export_xml_lxml
from db import get_ultimul_numar_factura_furnizor
from db import get_ultimul_nr_chitanta

def procesare_valoare_numerica(valoare_str):
	"""
	Transform� un string (ex: "10,5") �n float (10.5).
	Returneaz� float sau ridic� ValueError.
	"""
	if not valoare_str:
		return 0.0
	# �nlocuim virgula cu punctul
	clean_str = valoare_str.replace(',', '.')
	return float(clean_str)

def validare_produs_input(denumire, cant_str, pret_str, tva_str, um):
	"""
	Valideaz� datele introduse pentru un produs.
	Returneaz� un obiect Produs sau ridic� o eroare cu mesaj.
	"""
	if not denumire or not um:
		raise ValueError("Denumirea ?i Unitatea de M�sur� (UM) sunt obligatorii.")

	try:
		cantitate = procesare_valoare_numerica(cant_str)
		pret = procesare_valoare_numerica(pret_str)
		tva = procesare_valoare_numerica(tva_str)
	except ValueError:
		raise ValueError("Cantitatea, Pre?ul ?i TVA trebuie s� fie numere valide.")

	return Produs(
		denumire=denumire,
		cantitate=cantitate,
		um=um,
		pret_unitar=pret,
		tva_percent=tva
	)

def logic_cauta_entitate(cui, tip_entitate="furnizori"):
	"""
	Logica unificat� de c�utare:
	1. Caut� �n DB local.
	2. Dac� nu g�se?te, caut� �n ANAF.
	Returneaz� un dic?ionar cu datele firmei sau None.
	"""
	if not cui:
		return None

	# 1. Cautare DB
	entitate = get_entitate_dupa_cui(tip_entitate, cui)

	# 2. Cautare ANAF (daca nu e in DB)
	if not entitate:
		try:
			entitate = cauta_firma_anaf(cui)
			if entitate:
				entitate['sursa'] = 'ANAF'
		except Exception as e:
			print(f"Eroare la c�utarea ANAF: {e}")
			return None
	else:
		entitate['sursa'] = 'DB Local'

	return entitate

def generare_fisiere_factura(date_furnizor, date_client, date_factura, lista_produse):
	"""
	Coordoneaz� crearea obiectelor, salvarea �n DB ?i generarea PDF/XML.
	"""

	# 1. Creare directoare
	output_dir = "facturi"
	if not os.path.exists(output_dir):
		os.makedirs(output_dir)

	# 2. Instantiere obiecte (Validare date obligatorii)
	if not date_furnizor['cui'] or not date_client['cui'] or not date_factura['numar']:
		raise ValueError("Lipsesc date obligatorii (CUI Furnizor, CUI Client sau Numar Factura).")

	furnizor = Entitate(**date_furnizor)
	client = Entitate(**date_client)


	factura = Factura(
		numar=date_factura['numar'],
		data=date_factura['data'],
		furnizor=furnizor,
		client=client,
		produse=lista_produse,
		nr_chit=date_factura['nr_chit'],
		cu_chitanta=date_factura['vrea_chitanta']
	)

	# 3. Salvare DB
	salveaza_factura_completa(furnizor, client, factura)

	# 4. Generare nume fi?ier
	# Cur�?�m numele pentru a fi valid �n sistemul de fi?iere
	safe_nume = "".join([c for c in furnizor.nume if c.isalnum()])[:10]
	nume_fisier_base = f"{output_dir}/Factura_{factura.numar}_{safe_nume}_{factura.data.replace('.','')}"

	# 5. Export
	path_pdf = f"{nume_fisier_base}.pdf"
	path_xml = f"{nume_fisier_base}.xml"


	export_pdf(factura, path_pdf)
	export_xml_lxml(factura, path_xml)

	return path_pdf, path_xml

def sugereaza_urmatorul_numar(furnizori_cui):
	if not furnizori_cui:
		return ""
	ultimul_nr = get_ultimul_numar_factura_furnizor(furnizori_cui)
	if ultimul_nr is not None:
		return str(ultimul_nr + 1)
	else:
		return "1"

def sugereaza_nr_chitanta(furnizori_cui):
	if not furnizori_cui:
		return ""
	ultimul_nr_chit = get_ultimul_nr_chitanta(furnizori_cui)
	if ultimul_nr_chit is not None:
		return str(ultimul_nr_chit + 1)
	else:
		return "0"


def genereaza_pdf_din_db(numar_factura):
	import sqlite3
	# Presupunem că clasele Factura, Furnizor, Client sunt importate

	with sqlite3.connect('efactura.db') as conn:
		conn.row_factory = sqlite3.Row
		c = conn.cursor()

		# Luăm datele facturii, furnizorului și clientului într-un singur JOIN
		c.execute("""
				  SELECT f.*,
						 fr.nume       as fr_nume,
						 fr.cui        as fr_cui,
						 fr.onrc       as fr_onrc,
						 fr.adresa     as fr_adr,
						 fr.localitate as fr_loc,
						 fr.judet      as fr_jud,
						 fr.tara	   as fr_tara,
						 fr.banca      as fr_bnc,
						 fr.iban       as fr_iban,
						 fr.banca1	   as fr_banc1,
						 fr.iban1      as fr_iban1,
						 fr.ser_fac		as fr_ser_fac,
						 cl.nume       as cl_nume,
						 cl.cui        as cl_cui,
						 cl.onrc       as cl_onrc,
						 cl.adresa     as cl_adr,
						 cl.localitate as cl_loc,
						 cl.judet      as cl_jud,
						 cl.tara	   as cl_tara,
						 cl.banca      as cl_bnc,
						 cl.iban       as cl_iban,
						 cl.banca1	   as cl_banc1,
						 cl.iban1      as cl_iban1
				  FROM facturi f
						   JOIN furnizori fr ON f.furnizor_id = fr.id
						   JOIN clienti cl ON f.client_id = cl.id
				  WHERE f.numar = ?
				  """, (numar_factura,))

		row = c.fetchone()
		if not row:
			print("Factura nu a fost găsită în baza de date.")
			return

		# 2. Construim obiectele pentru funcția export_pdf
		from factura import Factura, Entitate, Produs  # Exemplu structură

		furnizori = Entitate(nume=row['fr_nume'], cui=row['fr_cui'], onrc=row['fr_onrc'],
							adresa=row['fr_adr'], localitate=row['fr_loc'],
							judet=row['fr_jud'], tara=row['fr_tara'], banca=row['fr_bnc'], iban=row['fr_iban'],
							 banca1=row['fr_banc1'], iban1=row['fr_iban1'], ser_fac=row['fr_ser_fac'],)

		clienti = Entitate(nume=row['cl_nume'], cui=row['cl_cui'], onrc=row['cl_onrc'],
						adresa=row['cl_adr'], localitate=row['cl_loc'],
						judet=row['cl_jud'], tara=row['cl_tara'], banca=row['cl_bnc'], iban=row['cl_iban'],
						   banca1=row['cl_banc1'], iban1=row['cl_iban1'])
		factura_obj = Factura(numar=row['numar'], data=row['data'], nr_chit=row['nr_chit'],
								  furnizor=furnizori, client=clienti)


		# 3. Adăugăm produsele (trebuie să ai un tabel 'produse_factura' sau similar)
		c.execute("SELECT * FROM produse_facturi WHERE factura_id = ?", (row['id'],))
		for p in c.fetchall():
			factura_obj.adauga_produs(Produs(denumire=p['denumire'], um=p['um'],
											 cantitate=p['cantitate'], pret_unitar=p['pret_unitar'],
											 tva_percent=p['tva_percent']))
		output_dir = "facturi"
		# 4. Apelăm funcția ta de export
		export_pdf(factura_obj, f"{output_dir}/Factura_{row['numar']}_{row['data']}.pdf")
		nume_fis = f"{output_dir}\Factura_{row['numar']}_{row['data']}.pdf"
		os.startfile(nume_fis)

# Functie centrare fereastra
def centreaza_fereastra(fereastra, latime, inaltime):
	fereastra.update_idletasks()  # Asigură că dimensiunile sunt calculate corect

	ecran_w = fereastra.winfo_screenwidth()
	ecran_h = fereastra.winfo_screenheight()

	x = (ecran_w // 2) - (latime // 2)
	y = (ecran_h // 2) - (inaltime // 2)

	fereastra.geometry(f"{latime}x{inaltime}+{x}+{y}")
