import os
import zipfile
import requests
import sqlite3
from lxml import etree

URL_MESAJE = "https://api.anaf.ro/prod/FCTEL/rest/listaMesajeFactura"
URL_DESCARCARE = "https://api.anaf.ro/prod/FCTEL/rest/descarcare"


def sincronizeaza_facturi_primite(cui, token_anaf, zile=60):
    cif_curat = _curata_cif(cui)
    if not cif_curat:
        print("CUI/CIF invalid pentru sincronizare.")
        return 0

    headers = {"Authorization": f"Bearer {token_anaf}"}
    params = {"zile": zile, "cif": cui}

    try:
        # raspuns = requests.get(URL_MESAJE, params=params, headers=headers)
        # if raspuns.status_code != 200:
        #     print(f"Eroare ANAF: {raspuns.text}")
        #     return 0
        # Verificare
        print(f"DEBUG URL: {URL_MESAJE}")
        print(f"DEBUG CUI trimis: {cui}")
        print(
            f"DEBUG Token folosit (primele 20 caractere):"
            f" {token_anaf[:20] if token_anaf else 'ESTE NUL!'}"
        )

        raspuns = requests.get(URL_MESAJE, params=params, headers=headers)
        print(f"DEBUG Status: {raspuns.status_code}")
        print(f"DEBUG Body raspuns: {raspuns.text}")

        mesaje = raspuns.json().get("mesaje", [])
        facturi_noi = 0

        with sqlite3.connect("efactura.db") as conn:
            cursor = conn.cursor()

            for msg in mesaje:
                id_msg = str(msg.get("id"))
                tip_mesaj = msg.get("tip")

                if "PRIMITA" not in str(tip_mesaj).upper():
                    continue

                # Verificăm dacă o avem deja în baza de date
                cursor.execute("SELECT id_descarcare FROM facturi_primite WHERE id_descarcare = ?", (id_msg,))
                if cursor.fetchone():
                    continue

                # --- DESCĂRCARE ȘI SALVARE ÎN /primite/[cui] ---
                facturi_noi += descarca_si_proceseaza_factura(id_msg, cui, headers, cursor)
                conn.commit()

        return facturi_noi

    except Exception as e:
        print(f"Eroare la sincronizare: {e}")
        return 0


def descarca_si_proceseaza_factura(id_msg, cui_propriu, headers, db_cursor):
    try:
        raspuns = requests.get(f"{URL_DESCARCARE}?id={id_msg}", headers=headers)
        if raspuns.status_code != 200:
            return 0

        # --- STRUCTURĂ DINAMICĂ FOLDER: primite/[cui] ---
        dir_primite = os.path.join("primite", str(cui_propriu).strip())
        os.makedirs(dir_primite, exist_ok=True)

        zip_path = os.path.join(dir_primite, f"{id_msg}.zip")
        with open(zip_path, "wb") as f:
            f.write(raspuns.content)

        xml_extras_path = ""
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_name in zip_ref.namelist():
                if file_name.endswith('.xml') and "semnatura" not in file_name.lower():
                    # Extragem direct în folderul specific CUI-ului
                    zip_ref.extract(file_name, dir_primite)
                    xml_extras_path = os.path.join(dir_primite, file_name)
                    break

        os.remove(zip_path)  # Ștergem arhiva ZIP

        if not xml_extras_path:
            return 0

        return parsare_si_salvare_xml(id_msg, xml_extras_path, db_cursor, cui_beneficiar=cui_propriu)

    except Exception as e:
        print(f"Eroare descărcare mesaj {id_msg}: {e}")
        return 0


def parsare_si_salvare_xml(id_msg, xml_path, cursor, cui_beneficiar=""):
    try:
        ns = {
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'
        }

        tree = etree.parse(xml_path)
        root = tree.getroot()

        numar_factura = root.findtext('.//cbc:ID', namespaces=ns, default='N/A')
        data_factura = root.findtext('.//cbc:IssueDate', namespaces=ns, default='N/A')
        total = root.findtext('.//cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount', namespaces=ns, default='0')

        cif_ben = _curata_cif(cui_beneficiar)
        if not cif_ben:
            raw_ben = root.findtext(
                ".//cac:AccountingCustomerParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID",
                namespaces=ns,
                default="",
            )
            cif_ben = _curata_cif(raw_ben)

        cui_furnizor = root.findtext('.//cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID',
                                     namespaces=ns, default='N/A')
        # cui_curat = cui_furniz.strip().upper()
        # if cui_curat.startswith("RO"):
        #     cui_curat = cui_curat[2:].strip()
        #
        # # Păstrăm doar cifrele dacă este cazul (ex. eliminăm cratime sau spații accidentale)
        # cifre = "".join(ch for ch in cui_curat if ch.isdigit())
        # cui_furnizor = cifre if cifre else ("N/A" if cui_furniz == "N/A" else cui_curat)

        # --- CĂUTARE ROBUSTĂ PENTRU NUMELE FURNIZORULUI ---
        nume_furnizor = 'N/A'

        # 1. Încercăm calea standard UBL
        nume_furnizor = root.findtext('.//cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name', namespaces=ns,
                                      default='')

        # 2. Dacă e gol, încercăm din LegalEntity
        if not nume_furnizor or nume_furnizor.strip() == 'N/A' or nume_furnizor.strip() == '':
            nume_furnizor = root.findtext(
                './/cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName', namespaces=ns,
                default='')

        # 3. Dacă tot nu l-am găsit, căutăm fără namespaces stricte (cazuri particulare)
        if not nume_furnizor or nume_furnizor.strip() == '':
            for elem in root.iter():
                if elem.tag.endswith('PartyName') or elem.tag.endswith('RegistrationName'):
                    if elem.text and elem.text.strip():
                        nume_furnizor = elem.text.strip()
                        break

        if not nume_furnizor:
            nume_furnizor = "Necunoscut"

        cursor.execute("""
            INSERT INTO facturi_primite (id_descarcare, cui_beneficiar, cui_furnizor, nume_furnizor, numar_factura, data_factura, total, cale_xml)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (id_msg, cif_ben, cui_furnizor, nume_furnizor, numar_factura, data_factura, float(total), xml_path))

        return 1
    except Exception as e:
        print(f"Eroare parsare XML {xml_path}: {e}")
        return 0

def _curata_cif(valoare):
    if not valoare:
        return ""
    s = str(valoare).strip().upper()
    if s.startswith("RO"):
        s = s[2:].strip()
    cifre = "".join(ch for ch in s if ch.isdigit())
    return cifre if cifre else s