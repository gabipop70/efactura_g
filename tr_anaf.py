from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import sqlite3
import os
import glob
import time
import xml.etree.ElementTree as ET
import requests
import tkinter as tk
from tkinter import messagebox, ttk
import urllib.parse
import webbrowser

import requests

# --- CONFIGURĂRI GLOBALE ANAF ---
CLIENT_ID = "7f7e203e913e06a5a06162f2172e8af16c1f1513b7e4c36a"
CLIENT_SECRET = (
    "ad6f39d25da85f1b106d83b0eef0a5f9ac7b89c71c758af16c1f1513b7e4c36a"
)
REDIRECT_URI = "https://gabipop70.github.io/oauth_repo/"
CUI_FIRMA = "12345678"  # CUI-ul firmei (fără RO)
PORT_LOCAL = 8080


# --- CONFIGURĂRI GLOBALE ANAF ---
SANDBOX = False  # True pentru Test, False pentru Producție

# Endpoint-ul OAuth2 este identic (logincert.anaf.ro/anaf-oauth2/v1)
URL_AUTORIZARE = "https://logincert.anaf.ro/anaf-oauth2/v1/authorize"
URL_TOKEN = "https://logincert.anaf.ro/anaf-oauth2/v1/token"

# Endpoint-ul de servicii e-Factura diferă între Test și Producție:
BASE_SERVICES_URL = (
    "https://api.anaf.ro/test/FCTEL/rest/upload" if SANDBOX else "https://api.anaf.ro/prod/FCTEL/rest/upload"
)
DB_NAME = "efactura.db"
FISIER_TOKENS = "tokens_anaf.json"

# URL_AUTORIZARE = "https://logincert.anaf.ro/anaf-oauth2/v1/authorize"
# URL_TOKEN = "https://logincert.anaf.ro/anaf-oauth2/v1/token"


# ==========================================
# 1. BAZĂ DE DATE SQLITE & OPERAȚIUNI E-FACTURA
# ==========================================
def salveaza_token_in_db(token_data, db_path=DB_NAME):
    """Salvează sau actualizează token-urile OAuth în tabela din baza de date SQLite."""
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS anaf_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            access_token TEXT NOT NULL,
            refresh_token TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_in INTEGER
        )
    """
    )

    cursor.execute("DELETE FROM anaf_tokens")

    cursor.execute(
        """
        INSERT INTO anaf_tokens (access_token, refresh_token, created_at, expires_in)
        VALUES (?, ?, CURRENT_TIMESTAMP, ?)
    """,
        (access_token, refresh_token, expires_in),
    )

    conn.commit()
    conn.close()


def preia_refresh_token():
    """Citește ultimul refresh_token salvat din baza de date SQLite."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT refresh_token FROM anaf_tokens ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    except sqlite3.OperationalError:
        conn.close()
        return None


def obtine_access_token_valid():
    """Obține un access_token nou în fundal folosind refresh_token-ul salvat în SQLite."""
    refresh_token = preia_refresh_token()
    if not refresh_token:
        raise Exception(
            "Nu există un token ANAF salvat!\nVă rugăm să apăsați mai întâi pe butonul '🔑 Actualizare Token ANAF' din aplicație."
        )

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }

    try:
        res = requests.post(URL_TOKEN, data=payload, headers=headers, timeout=20)

        try:
            data = res.json()
        except Exception:
            raise Exception(
                f"ANAF a returnat un răspuns non-JSON (HTTP {res.status_code}):\n{res.text[:300]}"
            )

        if res.status_code == 200 and "access_token" in data:
            salveaza_token_in_db(data)
            return data.get("access_token")
        else:
            eroare_detalii = (
                data.get("error_description")
                or data.get("error")
                or res.text
            )
            raise Exception(
                f"Eroare ANAF (HTTP {res.status_code}):\n{eroare_detalii}"
            )

    except requests.exceptions.RequestException as e:
        raise Exception(f"Eroare de conexiune la serverul OAUTH ANAF:\n{e}")

def preia_facturi_netransmise(cui_furnizor=None):
    """Returnează o listă de tuple cu facturile netransmise din DB."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    query = """
            SELECT 
                f.id, 
                f.numar, 
                f.data, 
                COALESCE(c.nume, 'Client necunoscut') AS nume_client, 
                f.total_general, 
                COALESCE(fn.cui, '') AS cui_furnizor,
                f.nr1,
                f.nr2
            FROM facturi f
            LEFT JOIN clienti c ON f.client_id = c.id
            LEFT JOIN furnizori fn ON f.furnizor_id = fn.id
            WHERE (f.tr_efact = 0 OR f.tr_efact IS NULL)
   
        """
 #  OR(f.tr_efact = 1 and f.nr1 not null))
    params = []

    if cui_furnizor:
        query += " AND fn.cui = ?"
        params.append(cui_furnizor)

    query += " ORDER BY f.data DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def proceseaza_trimitere_facturi_selectate(lista_id_facturi):
    """Trimite facturile selectate la ANAF e-Factura, potrivind fișierele XML de tip Fac_NUMAR_*.xml."""
    global index_incarcare
    if not lista_id_facturi:
        return "Nu ai selectat nicio factură pentru transmitere."

    # 1. Preluare Access Token valid
    try:
        access_token = obtine_access_token_valid()
    except Exception as e:
        return f"Eroare la obținerea token-ului ANAF:\n{str(e)}"

    # 2. Preluare date facturi prin JOIN cu tabela furnizori
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    placeholders = ",".join("?" for _ in lista_id_facturi)
    query = f"""
        SELECT 
            f.id, 
            f.numar, 
            COALESCE(fn.cui, '') AS cui_furnizor
        FROM facturi f
        LEFT JOIN furnizori fn ON f.furnizor_id = fn.id
        WHERE f.id IN ({placeholders})
    """
    cursor.execute(query, lista_id_facturi)
    facturi = cursor.fetchall()

    if not facturi:
        conn.close()
        return "Nu s-au găsit facturile selectate în baza de date."

    base_services_url = (
        "https://api.anaf.ro/test/FCTEL/rest/upload"
        if SANDBOX
        else "https://api.anaf.ro/prod/FCTEL/rest/upload"
    )
    trimise_cu_succes = 0
    erori = []
    # Lista în care colectăm mesajele de succes pentru fiecare factură
    mesaje_succes = []

    FOLDER_FACTURI = "facturi"

    # 3. Parcurgere și trimitere facturi
    for id_factura, nr_factura, cui_f in facturi:
        # Curățăm numărul de eventuale spații sau prefixe
        nr_curat = str(nr_factura).strip()

        # Construim un pattern de căutare: facturi/Fac_623_*.xml
        pattern_cautare = os.path.join(
            FOLDER_FACTURI, f"Fac_{nr_curat}_*.xml"
        )
        fisiere_gasite = glob.glob(pattern_cautare)

        # Fallback 1: Încercăm și fără 'Fac_' (în caz că numele diferă la unele facturi)
        if not fisiere_gasite:
            pattern_cautare_alt = os.path.join(
                FOLDER_FACTURI, f"*{nr_curat}*.xml"
            )
            fisiere_gasite = glob.glob(pattern_cautare_alt)

        if not fisiere_gasite:
            erori.append(
                f"Factura {nr_factura}: Nu s-a găsit niciun fișier XML de tipul 'Fac_{nr_curat}_*.xml' în folderul 'facturi\\'."
            )
            continue

        # Luăm primul fișier găsit care se potrivește
        cale_xml = fisiere_gasite[0]

        # Selectăm CUI-ul (fie din furnizor, fie din constanta firmei)
        cui_raw = cui_f if cui_f else CUI_FIRMA

        # Curățăm uniform de RO, spații sau caractere speciale
        cui_curat = str(cui_raw).upper().replace("RO", "").strip()

        print(cui_curat)
    #    url_upload = f"{base_services_url}?cui={cui_curat}&standard=UBL"
        url_upload = f"{base_services_url}?standard=UBL&v=1&cif={cui_curat}"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/xml",

        }

        try:
            with open(cale_xml, "rb") as f:
                xml_bytes = f.read()
        except Exception as e:
            erori.append(
                f"Factura {nr_factura}: Eroare la citirea fișierului {cale_xml} ({e})."
            )
            continue

        try:
            res = requests.post(
                url_upload, headers=headers, data=xml_bytes, timeout=30
            )

            if res.status_code in (200, 201):
                index_incarcare = None

                # 1. Încercăm parsarea JSON
                try:
                    response_data = res.json()
                    if isinstance(response_data, dict):
                        index_incarcare = response_data.get("index_incarcare")
                except Exception:
                    index_incarcare = None

                # 2. Dacă nu este JSON, parsăm XML-ul primit de la ANAF
                if not index_incarcare and ("<?xml" in res.text or "<header" in res.text):
                    try:
                        root = ET.fromstring(res.text)
                        # Extragerea atributului index_incarcare direct din nodul <header>
                        index_incarcare = root.attrib.get("index_incarcare")
                    except Exception as e:
                        print(f"Eroare parsare XML: {e}")

                print("Index încărcare final:", index_incarcare)

                # # 3. Dacă avem index_incarcare, așteptăm obținerea id_descarcare
                # if index_incarcare:
                #     print(f"Index încărcare obținut: {index_incarcare}. Verificăm starea la ANAF...")
                #
                #     # Așteptăm procesarea și obținem id_descarcare
                #     succes, id_descarcare, msg_stare = verifica_stare_anaf(index_incarcare, access_token)
                #
                #     if succes is True:
                #         # Factura a fost VALIDATĂ OK și avem ambele ID-uri
                #         # (Aici presupunem că salvezi id_descarcare în coloana nr2)
                #         cursor.execute(
                #             """
                #             UPDATE facturi
                #             SET tr_efact = 1, nr1 = ?, nr2 = ?, data_tr = CURRENT_TIMESTAMP
                #             WHERE id = ?
                #             """,
                #             (index_incarcare, id_descarcare, id_factura),
                #         )
                #         conn.commit()
                #         trimise_cu_succes += 1
                #         print(
                #             f"Factura {nr_factura} validată! Index încărcare: {index_incarcare}, Index descărcare: {id_descarcare}")

                # 3. Salvarea în baza de date
                if index_incarcare:
                    cursor.execute(
                        """
                        UPDATE facturi
                        SET tr_efact = 1, nr1 = ?, data_tr = CURRENT_TIMESTAMP
                        WHERE id = ?
                        """,
                        (index_incarcare, id_factura),
                    )
                    conn.commit()
                    trimise_cu_succes += 1
                    # Construim mesajul specific pentru factura curentă
                    mesaj_factura = f"Factura {nr_factura} s-a salvat cu succes în DB! Index: {index_incarcare}"
                    print(mesaj_factura)  # Afișare în consolă
                    mesaje_succes.append(mesaj_factura)  # Adăugăm în lista de succese

                else:
                    erori.append(
                        f"Factura {nr_factura}: Răspuns neașteptat de la ANAF: {res.text}"
                    )
        except requests.exceptions.RequestException as req_err:
            erori.append(
                f"Factura {nr_factura}: Eroare la conectarea cu ANAF ({req_err})"
            )

    conn.close()


    mesaj = f"Transmitere finalizată!\nTrimise cu succes: {trimise_cu_succes} din {len(facturi)} cu index {index_incarcare}."
    if erori:
        mesaj += "\n\nErori întâmpinate:\n" + "\n".join(erori)
    return mesaj


# ==========================================
# 2. FLUX OAUTH2 LOCAL HTTP SERVER
# ==========================================
class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handler pentru capturarea codului OAuth din redirecționare."""

    auth_code = None

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)

        if "code" in query_params:
            OAuthCallbackHandler.auth_code = query_params["code"][0]

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html_content = """
            <html>
                <body style="font-family: Arial, sans-serif; text-align: center; padding-top: 50px;">
                    <h2 style="color: #2e7d32;">Autorizare reușită!</h2>
                    <p>Puteți închide această fereastră și să reveniți în aplicație.</p>
                </body>
            </html>
            """
            self.wfile.write(html_content.encode("utf-8"))
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header(
            "Access-Control-Allow-Headers", "X-Requested-With, Content-Type"
        )
        self.end_headers()

    def log_message(self, format, *args):
        return


def autorizeaza_anaf_pas_1():
    """Pasul 1: Pornește serverul HTTP local și deschide browserul către ANAF."""
    server_address = ("localhost", PORT_LOCAL)
    httpd = HTTPServer(server_address, OAuthCallbackHandler)
    OAuthCallbackHandler.auth_code = None

    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "token_content_type": "jwt",
    }
    full_url = f"{URL_AUTORIZARE}?{urllib.parse.urlencode(params)}"
    webbrowser.open(full_url)
    return httpd


def finalizeaza_autorizare_pas_2(httpd, timeout_sec=120):
    """Pasul 2: Așteaptă în buclă răspunsul pe serverul local și schimbă codul pe Token-uri."""
    try:
        httpd.timeout = 1
        timp_scurs = 0

        # Așteptăm în buclă primirea codului
        while (
            OAuthCallbackHandler.auth_code is None and timp_scurs < timeout_sec
        ):
            httpd.handle_request()
            timp_scurs += 1

        auth_code = OAuthCallbackHandler.auth_code

        if not auth_code:
            return (
                False,
                "Autorizarea a eșuat sau a fost depășit timpul (nu s-a primit codul de acces).",
            )

        # Establish endpoint-ul OAUTH corect în funcție de mediul SANDBOX
        base_login_url = "https://logincert.anaf.ro"
        service_path = (
            "/anaftest/services/oauth2/token"
            if SANDBOX
            else "/anaf-oauth2/v1/token"
        )
        url_token_efectiv = f"{base_login_url}{service_path}"

        payload = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(
            url_token_efectiv, data=payload, headers=headers, timeout=20
        )

        if response.status_code == 200:
            try:
                token_data = response.json()
            except Exception:
                return (
                    False,
                    f"Răspuns invalid de la ANAF (nu e JSON):\n{response.text[:300]}",
                )

            # 1. Salvăm în fișier JSON
            with open(FISIER_TOKENS, "w", encoding="utf-8") as f:
                json.dump(token_data, f, indent=4)

            # 2. Salvăm în baza de date SQLite
            salveaza_token_in_db(token_data)

            return (
                True,
                "Autentificarea ANAF s-a efectuat cu succes!\nToken-ul a fost salvat în baza de date.",
            )
        else:
            return (
                False,
                f"Eroare ANAF (HTTP {response.status_code}):\n{response.text}",
            )

    except Exception as e:
        return False, f"A apărut o eroare în procesul de autorizare: {str(e)}"
    finally:
        httpd.server_close()


# def verifica_stare_anaf(index_incarcare, access_token, timeout_secunde=60, pauza_secunde=5):
#     """
#     Interoghează ANAF periodic până când starea mesajului devine completă ('ok' sau 'nok').
#     """
#     url_stare = f"https://api.anaf.ro/efactura/prod/v1/stareMesaj?id_incarcare={index_incarcare}"
#     headers = {
#         "Authorization": f"Bearer {access_token}"
#     }
#
#     timp_start = time.time()
#
#     while time.time() - timp_start < timeout_secunde:
#         try:
#             res = requests.get(url_stare, headers=headers, timeout=10)
#             if res.status_code == 200:
#                 data = res.json()
#                 stare = data.get("stare") # Ex: 'in prelucrare', 'ok', 'nok'
#
#                 if stare == "ok":
#                     # Factura a fost procesată și validată cu succes
#                     id_descarcare = data.get("id_descarcare")
#                     return True, f"Validată cu succes (ID Descarcare: {id_descarcare})"
#
#                 elif stare == "nok":
#                     # Factura a fost respinsă la validare (erori XML / reguli de business)
#                     # ANAF pune în 'id_descarcare' ID-ul fișierului de erori
#                     id_descarcare = data.get("id_descarcare")
#                     return False, f"Respinsă de ANAF (ID Descarcare eroare: {id_descarcare})"
#
#                 elif stare == "in prelucrare":
#                     # Încă se procesează, mai așteptăm
#                     time.sleep(pauza_secunde)
#                 else:
#                     time.sleep(pauza_secunde)
#             else:
#                 time.sleep(pauza_secunde)
#
#         except requests.exceptions.RequestException:
#             time.sleep(pauza_secunde)
#
#     return False, "Timeout: ANAF nu a finalizat prelucrarea în timpul alocat."

# def verifica_stare_anaf(index_incarcare, access_token, timeout_secunde=60, pauza_secunde=5):
#     url_stare = f"https://api.anaf.ro/efactura/prod/v1/stareMesaj?id_incarcare={index_incarcare}"
#     headers = {"Authorization": f"Bearer {access_token}"}
#
#     timp_start = time.time()
#
#     while time.time() - timp_start < timeout_secunde:
#         try:
#             res = requests.get(url_stare, headers=headers, timeout=10)
#             if res.status_code == 200:
#                 data = res.json()
#                 stare = data.get("stare")
#
#                 if stare == "ok":
#                     id_descarcare = data.get("id_descarcare")
#                     return True, id_descarcare, "Validată cu succes"
#
#                 elif stare == "nok":
#                     id_descarcare = data.get("id_descarcare")
#                     return False, id_descarcare, "Respinsă de ANAF"
#
#                 elif stare == "in prelucrare":
#                     time.sleep(pauza_secunde)
#                 else:
#                     time.sleep(pauza_secunde)
#             else:
#                 time.sleep(pauza_secunde)
#
#         except requests.exceptions.RequestException:
#             time.sleep(pauza_secunde)
#
#     return False, None, "Timeout: ANAF nu a finalizat prelucrarea în timpul alocat."

def actualizeaza_stare_facturi_pending():
    """Interoghează ANAF pentru facturile trimise (care au nr1/index_incarcare) dar fără nr2/id_descarcare."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, numar, nr1 
        FROM facturi 
        WHERE tr_efact = 1 AND nr1 IS NOT NULL AND (nr2 IS NULL OR nr2 = '')
        """
    )
    facturi_pending = cursor.fetchall()

    if not facturi_pending:
        conn.close()
        return "Toate facturile au starea actualizată sau nu există facturi în așteptare."

    try:
        access_token = obtine_access_token_valid()
    except Exception as e:
        conn.close()
        return f"Eroare la obținerea token-ului ANAF:\n{str(e)}"

    actualizate = 0
    in_prelucrare = 0
    erori = []

    headers = {"Authorization": f"Bearer {access_token}"}

    # URL-ul oficial de starea mesajului ANAF
    base_stare_url = (
        "https://api.anaf.ro/test/FCTEL/rest/stareMesaj"
        if SANDBOX
        else "https://api.anaf.ro/prod/FCTEL/rest/stareMesaj"
    )

    for id_factura, nr_factura, index_incarcare in facturi_pending:
        url_stare = f"{base_stare_url}?id_incarcare={index_incarcare}"

        try:
            res = requests.get(url_stare, headers=headers, timeout=15)

            if res.status_code == 200:
                data = {}
                # Încercăm mai întâi parsare JSON
                try:
                    data = res.json()
                except Exception:
                    # Dacă ANAF a returnat XML/HTML în loc de JSON
                    if "<?xml" in res.text or "<header" in res.text:
                        try:
                            root = ET.fromstring(res.text)
                            stare_xml = root.attrib.get("stare")
                            id_desc_xml = root.attrib.get("id_descarcare")
                            data = {"stare": stare_xml, "id_descarcare": id_desc_xml}
                        except Exception as e_xml:
                            erori.append(f"Factura {nr_factura}: Eroare parsare XML stare ({e_xml})")
                            continue
                    else:
                        erori.append(f"Factura {nr_factura}: Răspuns neașteptat de la ANAF: {res.text[:150]}")
                        continue

                stare = data.get("stare")

                if stare == "ok":
                    id_descarcare = data.get("id_descarcare")
                    cursor.execute(
                        "UPDATE facturi SET nr2 = ? WHERE id = ?",
                        (id_descarcare, id_factura),
                    )
                    conn.commit()
                    actualizate += 1
                    print(f"Factura {nr_factura}: id_descarcare obținut -> {id_descarcare}")

                elif stare == "nok":
                    id_descarcare = data.get("id_descarcare")
                    cursor.execute(
                        "UPDATE facturi SET nr2 = ? WHERE id = ?",
                        (f"RESPINS_{id_descarcare}", id_factura),
                    )
                    conn.commit()
                    erori.append(f"Factura {nr_factura}: Respinsă la validare de ANAF (ID Eroare: {id_descarcare})")

                elif stare == "in prelucrare":
                    in_prelucrare += 1
                else:
                    erori.append(f"Factura {nr_factura}: Stare necunoscută '{stare}' (Răspuns: {res.text[:100]})")
            else:
                erori.append(f"Factura {nr_factura}: HTTP {res.status_code} - {res.text[:100]}")

        except requests.exceptions.RequestException as e:
            erori.append(f"Factura {nr_factura}: Eroare conexiune rețea ({e})")

    conn.close()

    rezultat = "Verificare finalizată!\n"
    rezultat += f"• ID Descărcare obținut: {actualizate}\n"
    rezultat += f"• Încă în prelucrare la ANAF: {in_prelucrare}\n"

    if erori:
        rezultat += "\nErori/Respingeri:\n" + "\n".join(erori)

    return rezultat