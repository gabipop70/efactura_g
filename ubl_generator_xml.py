from xml.etree.ElementTree import Element, SubElement, tostring, ElementTree
import xml.etree.ElementTree as ET 
from xml.dom import minidom
# Presupunem că clasa Factura este importată corect din factura.py

def export_xml(factura, filename="Factura.xml"):
    """
    Generează un fișier XML în format UBL 2.1 (CIUS-RO) pentru e-Factura,
    pe baza obiectului Factura.

    Args:
        factura (Factura): Obiectul Factura care conține toate datele.
        filename (str): Numele fișierului XML de exportat.
    """
    NSMAP = {
        "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    }

    # Funcție ajutătoare pentru a crea tag-uri cu namespace corect
    def E(name, ns="cbc"): return f"{{{NSMAP[ns]}}}{name}"

    # Elementul rădăcină (Invoice)
    invoice = Element("Invoice", {
        "xmlns": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
        "xmlns:cbc": NSMAP["cbc"],
        "xmlns:cac": NSMAP["cac"]
    })

    # Header și Metadate
    # BR-RO-001: CustomizationID trebuie să fie 1.0.1 (conform validatorului)
    SubElement(invoice, E("CustomizationID")).text = "urn:cen.eu:en16931:2017#compliant#urn:efactura.mfinante.ro:CIUS-RO:1.0.1"
    SubElement(invoice, E("ID")).text = f"FAC {factura.numar}"
    SubElement(invoice, E("IssueDate")).text = factura.data
    SubElement(invoice, E("DueDate")).text = factura.data
    SubElement(invoice, E("InvoiceTypeCode")).text = "380" # Cod standard pentru factură comercială
    SubElement(invoice, E("DocumentCurrencyCode")).text = "RON"

    # BR-CO-25: Adăugăm PaymentTerms (Plata la termen legal)
    payment_terms = SubElement(invoice, E("PaymentTerms", "cac"))
    SubElement(payment_terms, E("Note")).text = "Plata se face in contul bancar specificat in maxim 30 de zile de la emitere."

    # --- Furnizor (AccountingSupplierParty) ---
    supplier_party = SubElement(invoice, E("AccountingSupplierParty", "cac"))
    party = SubElement(supplier_party, E("Party", "cac"))
    
    # Identificare
    SubElement(SubElement(party, E("PartyIdentification", "cac")), E("ID")).text = factura.furnizor.cui
    SubElement(SubElement(party, E("PartyName", "cac")), E("Name")).text = factura.furnizor.nume
    
    # BR-S-02 / BR-RO-065: Adăugăm PartyTaxScheme (Identificator de TVA)
    tax_scheme_supplier = SubElement(party, E("PartyTaxScheme", "cac"))
    SubElement(tax_scheme_supplier, E("CompanyID")).text = factura.furnizor.cui # CUI-ul ca ID de TVA
    SubElement(SubElement(tax_scheme_supplier, E("TaxScheme", "cac")), E("ID")).text = "VAT"
    
    # Adresa (PostalAddress)
    address = SubElement(party, E("PostalAddress", "cac"))
    SubElement(address, E("StreetName")).text = factura.furnizor.adresa
    SubElement(address, E("CityName")).text = factura.furnizor.localitate 
    SubElement(address, E("CountrySubentity")).text = factura.furnizor.tara + "-" + factura.furnizor.judet
    SubElement(SubElement(address, E("Country", "cac")), E("IdentificationCode")).text = factura.furnizor.tara
    
    # Entitate Legală (PartyLegalEntity)
    legal = SubElement(party, E("PartyLegalEntity", "cac"))
    SubElement(legal, E("RegistrationName")).text = factura.furnizor.nume
    SubElement(legal, E("CompanyID")).text = factura.furnizor.cui

    # --- Client (AccountingCustomerParty) ---
    buyer_party = SubElement(invoice, E("AccountingCustomerParty", "cac"))
    party = SubElement(buyer_party, E("Party", "cac"))
    
    # Identificare
    SubElement(SubElement(party, E("PartyIdentification", "cac")), E("ID")).text = factura.client.cui
    SubElement(SubElement(party, E("PartyName", "cac")), E("Name")).text = factura.client.nume

    # Adăugăm PartyTaxScheme și pentru Client (recomandat, deși BT-47/48 nu este strict BR-RO)
    tax_scheme_customer = SubElement(party, E("PartyTaxScheme", "cac"))
    SubElement(tax_scheme_customer, E("CompanyID")).text = factura.client.cui
    SubElement(SubElement(tax_scheme_customer, E("TaxScheme", "cac")), E("ID")).text = "VAT"
    
    # Adresa (PostalAddress)
    address = SubElement(party, E("PostalAddress", "cac"))
    SubElement(address, E("StreetName")).text = factura.client.adresa
    SubElement(address, E("CityName")).text = factura.client.localitate 
    SubElement(address, E("CountrySubentity")).text = factura.client.tara + "-" +factura.client.judet
    SubElement(SubElement(address, E("Country", "cac")), E("IdentificationCode")).text = factura.client.tara
    
    # Entitate Legală (PartyLegalEntity)
    legal = SubElement(party, E("PartyLegalEntity", "cac"))
    SubElement(legal, E("RegistrationName")).text = factura.client.nume
    SubElement(legal, E("CompanyID")).text = factura.client.cui
    
    # --- Sumar Taxe (TaxTotal) ---
    tax_total = SubElement(invoice, E("TaxTotal", "cac"))
    
    # 1. TaxAmount total (suma tuturor TVA-urilor)
    total_tax_amount = SubElement(tax_total, E("TaxAmount"))
    total_tax_amount.attrib['currencyID'] = "RON"
    total_tax_amount.text = f"{factura.total_tva():.2f}"
    
    # 2. Calcularea și adăugarea TaxSubtotal (defalcare per cotă de TVA)
    tax_summary = {} # {tva_percent: {'taxable': 0, 'tax': 0}}
    
    for p in factura.produse:
        rate = p.tva_percent
        # Calculăm baza (total fără TVA) direct.
        base = p.cantitate * p.pret_unitar
        # Calculăm TVA-ul pentru a evita erori de rotunjire la nivel de linie:
        tax = factura.total_general() - factura.total_fara_tva() # Aici calculăm totalul TVA global, dar trebuie să-l defalcăm pe cotă
        
        # Recalculăm tax-ul exact la nivel de produs
        # tax_line = base * (rate / 100) # Dacă avem probleme cu totalul final, ajustăm rotunjirea aici.
        tax_line = p.total() - base

        if rate not in tax_summary:
            tax_summary[rate] = {'taxable': 0.0, 'tax': 0.0}

        tax_summary[rate]['taxable'] += base
        tax_summary[rate]['tax'] += tax_line
        
    for rate, totals in tax_summary.items():
        tax_subtotal = SubElement(tax_total, E("TaxSubtotal", "cac"))
        
        # Baza impozabilă pentru această cotă
        taxable_amount = SubElement(tax_subtotal, E("TaxableAmount"))
        taxable_amount.attrib['currencyID'] = "RON"
        taxable_amount.text = f"{totals['taxable']:.2f}"
        
        # Valoarea TVA pentru această cotă
        tax_amount = SubElement(tax_subtotal, E("TaxAmount"))
        tax_amount.attrib['currencyID'] = "RON"
        tax_amount.text = f"{totals['tax']:.2f}"
        
        # Detalii despre cota de TVA (TaxCategory)
        tax_category = SubElement(tax_subtotal, E("TaxCategory", "cac"))
        SubElement(tax_category, E("ID")).text = "S" # S = Standard
        SubElement(tax_category, E("Percent")).text = f"{rate:.0f}"
        SubElement(SubElement(tax_category, E("TaxScheme", "cac")), E("ID")).text = "VAT" # Valued Added Tax
    
    # --- Sumar Total (LegalMonetaryTotal) ---
    total = SubElement(invoice, E("LegalMonetaryTotal", "cac"))
    
    # BR-13: TaxExclusiveAmount (Totalul facturii fără TVA)
    # CORECȚIE: Elementul LegalMonetaryTotal/TaxExclusiveAmount este OBLIGATORIU
    tax_exclusive_amount = SubElement(total, E("TaxExclusiveAmount"))
    tax_exclusive_amount.attrib['currencyID'] = "RON"
    tax_exclusive_amount.text = f"{factura.total_fara_tva():.2f}"
    
    # Total inclusiv TVA
    tax_inclusive_amount = SubElement(total, E("TaxInclusiveAmount"))
    tax_inclusive_amount.attrib['currencyID'] = "RON"
    tax_inclusive_amount.text = f"{factura.total_general():.2f}"
    
    # Suma de plată
    payable_amount = SubElement(total, E("PayableAmount"))
    payable_amount.attrib['currencyID'] = "RON"
    payable_amount.text = f"{factura.total_general():.2f}"

    # --- Linii Factură (InvoiceLine) ---
    for idx, p in enumerate(factura.produse, start=1):
        line = SubElement(invoice, E("InvoiceLine", "cac"))
        SubElement(line, E("ID")).text = str(idx)
        
        # BR-23: Adăugăm atributul unitCode la InvoicedQuantity
        invoiced_quantity = SubElement(line, E("InvoicedQuantity"))
        invoiced_quantity.attrib['unitCode'] = p.um # Unitatea de măsură
        invoiced_quantity.text = str(p.cantitate)
        
        # Suma totală a liniei (fără TVA) 
        line_extension_amount_line = SubElement(line, E("LineExtensionAmount"))
        line_extension_amount_line.attrib['currencyID'] = "RON"
        line_extension_amount_line.text = f"{p.cantitate * p.pret_unitar:.2f}" 
        
        # Detalii Produs (Item)
        item = SubElement(line, E("Item", "cac"))
        SubElement(item, E("Name")).text = p.denumire
        
        # Categorie Taxă (ClassifiedTaxCategory)
        tax = SubElement(item, E("ClassifiedTaxCategory", "cac"))
        SubElement(tax, E("ID")).text = "S" # S = Standard Rate
        SubElement(tax, E("Percent")).text = f"{p.tva_percent:.0f}" # Adaugă procentul de TVA
        SubElement(SubElement(tax, E("TaxScheme", "cac")), E("ID")).text = "VAT"
        
        # Preț Unitar (Price)
        price = SubElement(line, E("Price", "cac"))
        # Preț Unitar trebuie să aibă și el currencyID, conform standardului UBL
        price_amount = SubElement(price, E("PriceAmount"))
        price_amount.attrib['currencyID'] = "RON"
        price_amount.text = f"{p.pret_unitar:.2f}"
        
        # --- Format și salvare ---
    # tostring(invoice) va genera XML-ul corect, inclusiv cu namespace-uri
    # Întrucât minidom.parseString încearcă să gestioneze namespace-urile, poate fi sursa problemei vizuale.
    # Vom folosi tostring direct pentru a vedea dacă etree o face corect, apoi încercăm din nou pretty print.
    xmlstr = minidom.parseString(tostring(invoice, encoding='utf-8')).toprettyxml(indent="  ")
        
# Final fix: Substituim manual prefixele generice 'ns' cu 'cac'/'cbc' în string-ul XML
    xmlstr = xmlstr.replace('ns0:', 'cbc:')
    xmlstr = xmlstr.replace('ns1:', 'cac:')

    # --- Format și salvare ---
    xmlstr = minidom.parseString(tostring(invoice, 'utf-8')).toprettyxml(indent="  ")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(xmlstr)
    print(f"✔ XML UBL e-Factura salvat la: {filename}")