from dataclasses import dataclass, field
from typing import List

from sqlalchemy import true, false


@dataclass
class Entitate:
    nume: str
    cui: str
    onrc: str
    adresa: str
    localitate: str
    judet: str
    tara: str
    banca: str
    iban: str
    banca1: str
    iban1: str
    ser_fac: str = ""

@dataclass
class Produs:
    denumire: str
    cantitate: float
    um: str
    pret_unitar: float
    tva_percent: float

    def total(self):
        return self.cantitate * self.pret_unitar

    def total_tva(self):
        return self.total() * self.tva_percent / 100

@dataclass
class Factura:
    numar: str
    data: str
    furnizor: Entitate
    client: Entitate
    produse: List[Produs] = field(default_factory=list)

    def adauga_produs(self, produs):
        """Aceasta este metoda care lipsește acum"""
        self.produse.append(produs)

    def total_fara_tva(self):
        return sum(p.total() for p in self.produse)

    def total_tva(self):
        return sum(p.total_tva() for p in self.produse)

    def total_general(self):
        return self.total_fara_tva() + self.total_tva()

    nr_chit: str = ""
    cu_chitanta: bool = False

def suma_in_litere(suma):
    # Liste cu cifre și zeci
    cifre = ["zero", "unu", "doi", "trei", "patru", "cinci", "sase", "șapte", "opt", "noua"]
    zeci = ["", "zece", "douazeci", "treizeci", "patruzeci", "cincizeci", "saizeci", "saptezeci", "optzeci", "nouazeci"]
    sute = ["", "o suta", "doua sute", "trei sute", "patru sute", "cinci sute", "sase sute", "sapte sute", "opt sute", "noua sute"]
    ordin = [
        ("miliard", "miliarde"),
        ("milion", "milioane"),
        ("mie", "mii"),
        ("", "")
    ]

    def sub_1000(n):
        n = int(n)
        if n == 0:
            return ""
        s = ""
        if n >= 100:
            s += sute[n // 100]
            n = n % 100
            if n:
                s += " "
        if n >= 20:
            s += zeci[n // 10]
            n = n % 10
            if n:
                s += " si " + cifre[n]
        elif n >= 10:
            if n == 10:
                s += "zece"
            elif n == 11:
                s += "unsprezece"
            elif n == 12:
                s += "doisprezece"
            elif n == 13:
                s += "treisprezece"
            elif n == 14:
                s += "paisprezece"
            elif n == 15:
                s += "cincisprezece"
            elif n == 16:
                s += "saisprezece"
            elif n == 17:
                s += "saptesprezece"
            elif n == 18:
                s += "optsprezece"
            elif n == 19:
                s += "nouasprezece"
        elif n > 0:
            if n == 1:
                s += "unu"
            else:
                s += cifre[n]
        return s

    def grupare(n):
        n = int(n)
        grupuri = []
        while n > 0:
            grupuri.append(n % 1000)
            n //= 1000
        while len(grupuri) < 4:
            grupuri.append(0)
        return grupuri[::-1]  # de la miliarde la unități

    suma = round(float(suma), 2)
    lei = int(suma)
    bani = int(round((suma - lei) * 100))

    grupuri = grupare(lei)
    text = ""
    for i, val in enumerate(grupuri):
        if val == 0:
            continue
        if i == 0 and val > 0:  # miliarde
            if val == 1:
                text += "un miliard "
            else:
                text += sub_1000(val) + " miliarde "
        elif i == 1 and val > 0:  # milioane
            if val == 1:
                text += "un milion "
            else:
                text += sub_1000(val) + " milioane "
        elif i == 2 and val > 0:  # mii
            if val == 1:
                text += "o mie "
            else:
                text += sub_1000(val) + " mii "
        elif i == 3 and val > 0:  # unități
            if val == 1 and text == "":
                text += "unu "
            elif val == 1:
                text += "unu "
            else:
                text += sub_1000(val) + " "

    text = text.strip()
    if not text:
        text = "zero"

    # Corectare pentru "una mie" (nu "unu mie")
    text = text.replace("unu mie", "o mie")
    text = text.replace("unu milioane", "un milion")
    text = text.replace("unu miliarde", "un miliard")

    # Adăugare "lei"
    if lei == 1:
        text += " leu"
    else:
        text += " lei"

    # Adăugare "bani"
    if bani > 0:
        text += f" și {sub_1000(bani)} bani"

    return text.strip()

