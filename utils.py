# utils.py
# -*- coding: utf-8 -*-
import os
import unicodedata
import re
from datetime import datetime

from pyexpat.errors import messages
from tqdm import tk


from factura import Factura, Entitate, Produs
# Import�m modulele tale existente pentru logic�
from db import get_entitate_dupa_cui, cauta_firma_anaf, salveaza_factura_completa, cauta_firma_openapi
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
    Logica unificată de căutare:
    1. Caută în DB local.
    2. Dacă nu găsește, caută în OpenAPI și salvează în DB.
    """
    if not cui:
        return None

    # 1. Căutare în baza de date locală
    entitate = get_entitate_dupa_cui(tip_entitate, cui)

    # 2. Dacă NU există în DB, interogăm OpenAPI
    if not entitate:
        try:
            # NOTĂ: În producție, mută cheia într-un fișier .env sau variabilă de mediu
            CHEIA_MEA = "45sp3XcMzLGasV53Lvc5fjsWizucXLXkJRzvmmfpHC1dzAxhFw"

            rezultat = cauta_firma_openapi(cui, CHEIA_MEA)

            if rezultat:
                # IMPORTANT: 'rezultat' este deja un dicționar.
                # Trebuie să mapăm câmpurile de la OpenAPI pe structura ta din DB.
                adresa_reala = rezultat.get('adresa')
                print('Adresa reala', adresa_reala)
                adresa_fara_localitate, loc = proceseaza_adresa_si_localitate(adresa_reala)

                print('Judet',rezultat.get('judet'))

                # Preluare județ brut (ex: 'BISTRIŢA-NĂSĂUD')
                judet_raw = rezultat.get('judet', '')

                # Formatare: 'Bistrița-Năsăud'
                judet_nume = judet_raw.title() if judet_raw else 'N/A'

                # Obținere abreviere: 'BN'
                judet_abrev = get_abreviere_judet(judet_raw)

                #rest_adresa_lista = adresa_reala[:-1]

                # 3. Unim restul elementelor într-un text curat
                # Rezultat: "STR. PRINCIPALA, 307, -"
               # adresa_fara_localitate = ", ".join(rest_adresa_lista).strip().upper()

                # Dacă la final a rămas o virgulă sau un cratimă izolată, o putem curăța
                #adresa_fara_localitate = adresa_fara_localitate.rstrip(', -')

                print('Adresa', adresa_fara_localitate,'Localitate ',loc)
                entitate = {
                    'cui': rezultat.get('cif'),
                    'nume': str(rezultat.get('denumire')).upper(),
                    'adresa': str(adresa_fara_localitate).upper(),
                    'localitate': str(loc).upper(),
                    'judet':str(judet_abrev).upper(),
                    'platitor_tva': rezultat.get('vat_status'),
                    'onrc': rezultat.get('numar_reg_com'),
                    'stare': rezultat.get('state'),
                    'tara': 'RO',
                    'sursa': 'OpenAPI'
                }

                # OPTIONAL: Salvează entitatea nou găsită în DB locală pentru viitor
                # save_entitate_in_db(tip_entitate, entitate)
                print(f"Firma {entitate['nume']} a fost adusă din OpenAPI.")
            else:
                print(f"CUI-ul {cui} nu a fost găsit în nicio sursă.")
                return None

        except Exception as e:
            print(f"Eroare la căutarea OpenAPI: {e}")
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
    safe_numef = "".join([c for c in furnizor.nume if c.isalnum()])[:4]
    safe_numec = "".join([c for c in client.nume if c.isalnum()])[:4]
    nume_fisier_base = f"{output_dir}/Fac_{factura.numar}_{safe_numef}_{safe_numec}_{factura.data.replace('.','')}"

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
    # clasele Factura, Furnizor, Client sunt importate

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
        data_curata = str(row['data']).strip().replace(":", "-")

        output_dir = "facturi"
        nr_curat = str(row['numar']).strip().replace("/", "-")
        data_curata = str(row['data']).strip().replace(":", "-")

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Construim numele fișierului folosind variabilele curățate
        nume_pdf = f"Factura_{nr_curat}_{data_curata}.pdf"

        # UTILIZĂM os.path.join pentru a evita eroarea de tip operand
        cale_pdf = os.path.join(output_dir, nume_pdf)

        print(f"DEBUG: Calea generată este: {cale_pdf}")  # Vez
        # 4. Apelăm funcția ta de export
        export_pdf(factura_obj, f"{output_dir}/Factura_{nr_curat}_{data_curata}.pdf")
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

def validare_cui(cui):
	"""
       Verifică dacă un CUI este valid și returnează (True/False, mesaj).
       """
	cui = cui.strip().upper()
	if cui.startswith("RO"):
		cui = cui[2:]
	if not cui.isdigit():
		return False, "CUI-ul trebuie să conțină doar cifre (sau prefix RO)."
	if not (2 <= len(cui) <= 10):
		return False, "CUI-ul trebuie să aibă între 2 și 10 cifre."
	# Algoritmul de control CUI
	key = "753217532"
	cui = cui.zfill(10)
	suma = sum(int(cui[i]) * int(key[i]) for i in range(9))
	rest = suma * 10 % 11
	if rest == 10:
		rest = 0
	if rest != int(cui[-1]):
		return False, "CUI-ul este eronat algoritmic (posibil introdus greșit)."
	return True, "CUI valid."

def validare_cnp(cnp):
    """
    Verifică dacă un CNP este valid (inclusiv cifra de control).
    """
    cnp = cnp.strip()
    if not (cnp.isdigit() and len(cnp) == 13):
        return False

    control = "279146358279"
    suma = sum(int(cnp[i]) * int(control[i]) for i in range(12))
    rest = suma % 11
    cifra = 1 if rest == 10 else rest
    return cifra == int(cnp[-1])


def extrage_localitate(text_adresa):
    if not text_adresa:
        return ""
    # adresa_curata = text_adresa.strip().replace('\n', ', ')
    # # Împărțim după virgulă
    parti = text_adresa.split(',')
    a = parti[-1]
    print('Test', parti,'  ', a)
    # Luăm ultimul element și eliminăm spațiile albe
    localitate = parti[-1]
    #localitate = str(parti).split(',')[-1]

    return localitate


def proceseaza_adresa_si_localitate(date_input):
    # 1. Dacă date_input este String, îl tăiem după virgulă să facem o listă
    if isinstance(date_input, str):
        # Transformăm "Strada X, Nr 1, Rebrisoara" -> ["Strada X", "Nr 1", "Rebrisoara"]
        lista = [item.strip() for item in date_input.split(',')]
    elif isinstance(date_input, list):
        lista = date_input
    else:
        return "", ""

    if not lista:
        return "", ""

    # 2. Extragem localitatea (ultimul element)
    localitate = str(lista[-1]).strip().upper()

    # 3. Luăm restul elementelor (totul până la penultimul)
    rest_elemente = [str(item).strip().upper() for item in lista[:-1]]

    # 4. Filtrăm elementele care sunt doar cratime sau goale
    elemente_valide = [e for e in rest_elemente if e and e != '-']

    # 5. Unim restul pentru a forma adresa curată
    adresa_fara_localitate = ", ".join(elemente_valide)

    return adresa_fara_localitate, localitate

# Mapare între denumirea județului și abrevierea de 2 litere
MAP_ABREVIERI = {
    "ALBA": "AB", "ARAD": "AR", "ARGES": "AG", "BACAU": "BC", "BIHOR": "BH",
    "BISTRITA-NASAUD": "BN", "BOTOSANI": "BT", "BRASOV": "BV", "BRAILA": "BR",
    "BUCURESTI": "B", "BUZAU": "BZ", "CARAS-SEVERIN": "CS", "CALARASI": "CL",
    "CLUJ": "CJ", "CONSTANTA": "CT", "COVASNA": "CV", "DAMBOVITA": "DB",
    "DOLJ": "DJ", "GALATI": "GL", "GIURGIU": "GR", "GORJ": "GJ",
    "HARGHITA": "HR", "HUNEDOARA": "HD", "IALOMITA": "IL", "IASI": "IS",
    "ILFOV": "IF", "MARAMURES": "MM", "MEHEDINTI": "MH", "MURES": "MS",
    "NEAMT": "NT", "OLT": "OT", "PRAHOVA": "PH", "SATU MARE": "SM",
    "SALAJ": "SJ", "SIBIU": "SB", "SUCEAVA": "SV", "TELEORMAN": "TR",
    "TIMIS": "TM", "TULCEA": "TL", "VASLUI": "VS", "VALCEA": "VL",
    "VRANCEA": "VN"
}

def get_abreviere_judet(nume_judet):
    if not nume_judet:
        return "N/A"
    # Curățăm diacriticele și uniformizăm (ex: BISTRIŢA-NĂSĂUD -> BISTRITA-NASAUD)
    nfd = unicodedata.normalize('NFD', str(nume_judet).upper())
    fara_diacritice = ''.join(c for c in nfd if unicodedata.category(c) != 'Mn').replace('Ţ', 'T').replace('Ş', 'S')
    return MAP_ABREVIERI.get(fara_diacritice, "N/A")