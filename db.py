from datetime import datetime
import sqlite3
from wsgiref import headers

from tqdm import tk

from factura import Entitate, Factura, Produs
import requests

DB_NAME = "efactura.db"

def conectare():
    return sqlite3.connect(DB_NAME)

def creare_tabele():
    conn = conectare()
    c = conn.cursor()

    # Furnizori
    c.execute('''
    CREATE TABLE IF NOT EXISTS furnizori (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nume TEXT,
        cui TEXT,
        onrc TEXT,
        adresa TEXT,
        localitate TEXT,
        judet TEXT,
        tara TEXT,   
        banca TEXT,
        iban TEXT,
        banca1 TEXT,
        iban1 TEXT,
        ser_fac TEXT
    )''')

    # Clienți
    c.execute('''
    CREATE TABLE IF NOT EXISTS clienti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nume TEXT,
        cui TEXT,
        onrc TEXT,
        adresa TEXT,
        localitate TEXT,
        judet TEXT,
        tara TEXT,
        banca TEXT,
        iban TEXT,
        banca1 TEXT,
        iban1 TEXT,
        ser_fac TEXT
    )''')

    # Facturi
    c.execute('''
    CREATE TABLE IF NOT EXISTS facturi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numar TEXT,
        data TEXT,
        furnizor_id INTEGER,
        client_id INTEGER,
        total_fara_tva REAL,
        total_tva REAL,
        total_general REAL,
        nr_chit TEXT,
        FOREIGN KEY(furnizor_id) REFERENCES furnizori(id),
        FOREIGN KEY(client_id) REFERENCES clienti(id)
    )''')

    # Produse facturi
    c.execute('''
    CREATE TABLE IF NOT EXISTS produse_facturi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        factura_id INTEGER,
        denumire TEXT,
        cantitate REAL,
        um TEXT,
        pret_unitar REAL,
        tva_percent REAL,
        FOREIGN KEY(factura_id) REFERENCES facturi(id)
    )''')
    #Unitati de masura
    c.execute('''
    CREATE TABLE IF NOT EXISTS unitati (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cod TEXT UNIQUE,
        denumire TEXT,
        presc TEXT
    )
    ''')

    conn.commit()
    conn.close()

def populate_unitati_default():
    unitati = [
                ("H87", "Bucată", "BUC"),
                ("KMT", "Kilometru", "KM "),
                ("DAY", "Zi", "ZI "),
                ("MTR", "Metru", " M "),
                ("LTR", "Litru", " L "),
                ("KGM", "Kilogram", "KG "),
                ("NAR", "Articol", "ART"),
                ("MIN", "Minut", "MIN"),
                ("TNE", "Tonă", " T "),
            ]

    conn = conectare()
    c = conn.cursor()
    for cod, denumire, presc in unitati: # type: ignore
                try:
                    c.execute("INSERT INTO unitati (cod, denumire, presc) VALUES (?, ?, ?)", (cod, denumire, presc))
                except sqlite3.IntegrityError:
                    pass  # Codul există deja

    conn.commit()
    conn.close()


def get_unitati_text_format():
    # returnează lista în forma "C62 - Bucată"
    conn = conectare()
    c = conn.cursor()
    c.execute("SELECT cod, presc FROM unitati ORDER BY cod")
    rows = c.fetchall()
    conn.close()
    return [ f"{cod}-{presc}" for cod, presc  in rows]

def adauga_entitate(tabela: str, entitate: Entitate) -> int:
    conn = conectare()
    c = conn.cursor()

    # verific dacă există deja după CUI
    c.execute(f"SELECT id FROM {tabela} WHERE cui = ?", (entitate.cui,))
    row = c.fetchone()
    if row:
        entitate_id = row[0]
    else:
        # trebuie EXACT 11 semne de întrebare pentru 11 coloane
        c.execute(f'''
            INSERT INTO {tabela}
              (nume, cui, onrc, adresa, tara,
               iban, localitate, judet, banca, banca1, iban1, ser_fac)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entitate.nume,
            entitate.cui,
            entitate.onrc,
            entitate.adresa,
            entitate.tara,
            entitate.iban,
            entitate.localitate,
            entitate.judet,
            entitate.banca,
            entitate.banca1,
            entitate.iban1,
            entitate.ser_fac
        ))
        entitate_id = c.lastrowid

    conn.commit()
    conn.close()
    return entitate_id

def salveaza_factura_completa(
    furnizor: Entitate,
    client:   Entitate,
    factura:  Factura
) -> None:
    conn = conectare()
    c = conn.cursor()

    furnizor_id = adauga_entitate("furnizori", furnizor)
    client_id   = adauga_entitate("clienti", client)

    c.execute('''
        INSERT INTO facturi
          (numar, data, furnizor_id, client_id,
           total_fara_tva, total_tva, total_general, nr_chit)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        factura.numar,
        factura.data,
        furnizor_id,
        client_id,
        factura.total_fara_tva(),
        factura.total_tva(),
        factura.total_general(),
        factura.nr_chit
    ))
    factura_id = c.lastrowid

    for p in factura.produse:
        c.execute('''
            INSERT INTO produse_facturi
              (factura_id, denumire, cantitate, um,
               pret_unitar, tva_percent)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            factura_id,
            p.denumire,
            p.cantitate,
            p.um,
            p.pret_unitar,
            p.tva_percent
        ))

    conn.commit()
    conn.close()
    print(f"✔ Factura {factura.numar} a fost salvată în baza de date.")



def \
        get_entitate_dupa_cui(tabela: str, cui: str) -> dict | None:
    """
    Returnează un dict cu valorile (cheie = denumire coloană),
    sau None dacă nu găsește nimic.
    """
    conn = conectare()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute(f'''
        SELECT nume, cui, onrc, adresa, tara,
               iban, localitate, judet, banca, banca1, iban1, ser_fac
        FROM {tabela}
        WHERE cui = ?
    ''', (cui,))

    row = c.fetchone()
    conn.close()

    if not row:
        return None

    # row["nume"], etc. – putem returna direct row dacă preferi
    return {
        "nume":       row["nume"],
        "cui":        row["cui"],
        "onrc":       row["onrc"],
        "adresa":     row["adresa"],
        "localitate": row["localitate"],
        "judet":      row["judet"],
        "tara":       row["tara"],
        "banca":      row["banca"],
        "iban":       row["iban"],
        "banca1":     row["banca1"],
        "iban1":      row["iban1"],
        "ser_fac":    row["ser_fac"],
    }

def format_data_ro(data_input):
    # """
    # Transformă o dată din format ISO (YYYY-MM-DD) sau obiect datetime
    # în formatul românesc (DD.MM.YYYY).
    # """
    if not data_input:
        return ""

    # 1. Dacă data este deja un obiect datetime (de ex. extrasă cu un ORM)
    if isinstance(data_input, datetime):
        return data_input.strftime("%d.%m.%Y")
    # 2. Dacă data este un string
    data_str = str(data_input).strip()

    try:
        # Încercăm să procesăm formatul standard ISO: "2025-12-23"
        return datetime.strptime(data_str, "%Y-%m-%d").strftime("%d.%m.%Y")
    except ValueError:
        try:
            # Încercăm și formatul cu ora, dacă există: "2025-12-23 14:30:00"
            return datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y")
        except ValueError:
            # Dacă are deja puncte, probabil e deja formatată corect
            if "." in data_str:
                return data_str
            return data_str # Returnăm originalul dacă nu recunoaștem formatul

def cauta_firma_anaf(cui):
    url = "https://webserviceanaf.ro/api/v6/ws/tva"
    data = {
        "cui": [
            {
                "cui": str(cui),
                "data": datetime.today().strftime("%Y-%m-%d")
            }
        ]
    }
    try:
        r = requests.post(url, json=data)
        if r.status_code == 200:
            rezultat = r.json()
            if rezultat and "found" in rezultat and rezultat["found"]:
                info = rezultat["found"][0]
                adresa_completa = info.get("adresa", "")
                # Împărțim adresa după virgulă
                parts = [p.strip() for p in adresa_completa.split(",")]
                # Heuristic: localitatea e de obicei pe poziția 1 sau 2
                localitate = ""
                if len(parts) > 1:
                    # Caută "ORAȘ", "MUN.", "SAT", "SECTOR", "MUNICIPIUL", "COM.", "BUCURESTI"
                    for p in parts:
                        if any(x in p.upper() for x in ["ORAȘ", "MUN.", "SAT", "SECTOR", "MUNICIPIUL", "COM.", "BUCURESTI"]):
                            localitate = p
                            break
                return {
                    "cui": info.get("cui"),
                    "denumire": info.get("denumire"),
                    "adresa": adresa_completa,
                    "localitate": localitate,
                    "nr_reg_com": info.get("nrRegCom"),
                }
            else:
                return None
        else:
            print("Eroare la răspunsul ANAF:", r.status_code, r.text)
            return None
    except Exception as e:
        print("Eroare la interogare ANAF:", e)
        return None


def cauta_firma_openapi(cui, api_key):
    # OpenAPI acceptă CUI-ul direct în URL
    url = f"https://api.openapi.ro/api/companies/{cui}"

    headers = {
        "x-api-key": api_key
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        # Verificăm dacă cererea a fost de succes
        if response.status_code == 200:
            date = response.json()
            print(f"--- Date pentru {date.get('denumire')} ---")
            print(f"CUI: {date.get('cif')}")
            print(f"Reg. Com: {date.get('numar_reg_com')}")
            print(f"Adresă: {date.get('adresa')}")
            print(f"Plătitor TVA: {'DA' if date.get('vat_status') else 'NU'}")
            return date

        elif response.status_code == 404:
            print("Eroare: CUI-ul introdus nu a fost găsit.")
        elif response.status_code == 401:
            print("Eroare: Cheia API este invalidă.")
        elif response.status_code == 429:
            print("Eroare: Ai depășit limita de cereri pe luna aceasta.")
        else:
            print(f"Eroare neașteptată: {response.status_code}")

    except requests.exceptions.Timeout:
        print("Eroare: Serverul OpenAPI nu a răspuns în timp util.")
    except requests.exceptions.RequestException as e:
        print(f"Eroare de conexiune: {e}")

    return None

def get_ultimul_numar_factura_furnizor(furnizori_cui):
        import sqlite3
        conn = sqlite3.connect('efactura.db')
        cursor = conn.cursor()
        try:
            query = """
                    SELECT MAX(CAST(f.numar AS INTEGER))
                    FROM facturi f
                             JOIN furnizori fr ON f.furnizor_id = fr.id
                    WHERE fr.cui = ?
                    """
            cursor.execute(query, (furnizori_cui,))
            result = cursor.fetchone()
            print("Rezultat:", result)
            conn.close()
            if result and result[0] is not None:
                return int(result[0])
            return None
        except Exception as e:
            try:
                conn.close()
            except:
                pass
            return None

def cauta_facturi_dupa_cui(cui_furnizor, cui_client=None):
    import sqlite3
    conn = sqlite3.connect('efactura.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
        SELECT
            f.numar,
            f.data,
            c.nume AS nume_client,
            c.cui AS cui_client,
            c.id AS id_c,
            fr.nume AS nume_furnizor,
            fr.cui AS cui_furnizor,
            fr.ser_fac,
            fr.id AS id_f,
            f.total_general,
            f.nr_chit
        FROM facturi f
        JOIN furnizori fr ON f.furnizor_id = fr.id
        JOIN clienti c ON f.client_id = c.id
        WHERE fr.cui = ?
            AND (? IS NULL OR c.cui = ?)
        ORDER BY f.numar DESC
    """, (cui_furnizor,cui_client,cui_client))
    rows = c.fetchall()

    conn.close()
    return [dict(row) for row in rows]

def get_ultimul_nr_chitanta(furnizori_cui):
        import sqlite3
        conn = sqlite3.connect('efactura.db')
        cursor = conn.cursor()
        try:
            query = """
                    SELECT MAX(CAST(f.nr_chit AS INTEGER))
                    FROM facturi f
                             JOIN furnizori fr ON f.furnizor_id = fr.id
                    WHERE fr.cui = ?
                    """
            cursor.execute(query,(furnizori_cui,))
            result = cursor.fetchone()
            conn.close()
            if result and result[0] is not None:
                return int(result[0])
            return None
        except Exception as e:
            try:
                conn.close()
            except:
                pass
            return None

def cauta_in_tabel(tabel, camp_denumire, text, campuri_returnate=None, limit=20):
    """
    tabel: numele tabelului (ex: 'clienti', 'furnizori')
    camp_denumire: numele coloanei după care cauți (ex: 'denumire', 'nume')
    text: textul de căutat
    campuri_returnate: listă cu numele coloanelor de returnat (ex: ['id', 'denumire', 'cui', ...])
    limit: câte rezultate să returneze maxim
    """
    conn = sqlite3.connect('efactura.db')
    c = conn.cursor()
    if campuri_returnate is None:
        campuri_returnate = [camp_denumire]
    campuri_sql = ', '.join(campuri_returnate)
    sql = f"SELECT {campuri_sql} FROM {tabel} WHERE {camp_denumire} LIKE ? ORDER BY {camp_denumire} LIMIT ?"
    c.execute(sql, ('%' + text + '%', limit))
    rows = c.fetchall()
    conn.close()
    return rows

def cauta_clienti(text):
        return cauta_in_tabel(
            tabel='clienti',
            camp_denumire='nume',
            text=text,
            campuri_returnate=['cui', 'nume', 'onrc',  'localitate','adresa', 'judet', 'tara', 'banca',
                               'iban', 'banca1', 'iban1']
        )

def cauta_furnizori(text):
        return cauta_in_tabel(
            tabel='furnizori',
            camp_denumire='nume',
            text=text,
            campuri_returnate=['cui', 'nume', 'onrc',  'localitate','adresa', 'judet', 'tara', 'banca',
                               'iban', 'banca1', 'iban1']
        )
