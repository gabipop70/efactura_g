from dataclasses import dataclass, field
from typing import List

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

    def total_fara_tva(self):
        return sum(p.total() for p in self.produse)

    def total_tva(self):
        return sum(p.total_tva() for p in self.produse)

    def total_general(self):
        return self.total_fara_tva() + self.total_tva()