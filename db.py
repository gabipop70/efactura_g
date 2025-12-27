from datetime import datetime
import sqlite3
from factura import Entitate, Factura, Produs

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
        iban1 TEXT
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
        iban1 TEXT
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
               iban, localitate, judet, banca, banca1, iban1)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            entitate.iban1
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
           total_fara_tva, total_tva, total_general)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        factura.numar,
        factura.data,
        furnizor_id,
        client_id,
        factura.total_fara_tva(),
        factura.total_tva(),
        factura.total_general()
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

    

def get_entitate_dupa_cui(tabela: str, cui: str) -> dict | None:
    """
    Returnează un dict cu valorile (cheie = denumire coloană),
    sau None dacă nu găsește nimic.
    """
    conn = conectare()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute(f'''
        SELECT nume, cui, onrc, adresa, tara,
               iban, localitate, judet, banca, banca1, iban1
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