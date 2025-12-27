from xml.dom import XMLNS_NAMESPACE
from xml.etree.ElementTree import QName
from lxml import etree
from factura import Factura  # asigură-te că ai definit clasele Factura, Produs etc.

def clean_cui_numeric(cui_str):
    """
    Curăță CUI/CIF, eliminând spațiile albe și prefixul "RO" dacă este prezent.
    Acest format este necesar pentru CompanyID din PartyTaxScheme.
    """
    if not cui_str:
        return ""
    cui = cui_str.strip().upper()
    if cui.startswith("RO"):
        return cui[2:]
    return cui

def export_xml_lxml(factura: Factura, filename="Factura.xml"):
    """
    Generează un fișier XML în format UBL 2.1 (CIUS-RO) pentru e-Factura,
    folosind lxml.

    Args:
        factura (Factura): Obiectul Factura care conține toate datele.
        filename (str): Numele fișierului XML de exportat.
    """
    NSMAP = {
        None: "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
        "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
        "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        "qdt": "urn:oasis:names:specification:ubl:schema:xsd:QualifiedDataTypes-2",
        # Namespace UDT corect (UnqualifiedDataTypes-2)
        "udt": "urn:oasis:names:specification:ubl:schema:xsd:UnqualifiedDataTypes-2", 
        "ccts": "urn:un:unece:uncefact:documentation:2",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance"
    }
    
    # Funcție ajutătoare pentru a crea tag-uri cu namespace corect (pentru lxml)
    def E(tag, ns="cbc"):
        # Dacă ns este None, se folosește namespace-ul default
        if ns is None:
            return etree.QName(NSMAP[None], tag)
        return etree.QName(NSMAP[ns], tag)

    # Elementul rădăcină (Invoice) - Setăm direct namespace-urile și schemaLocation
    invoice = etree.Element(
        E("Invoice", None), # Tag-ul Invoice este în namespace-ul implicit (None)
        nsmap=NSMAP,
        attrib={
             E("schemaLocation", "xsi"): 
             "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2 "
             "http://docs.oasis-open.org/ubl/os-UBL-2.1/xsd/maindoc/UBL-Invoice-2.1.xsd"
        }
    )

    # Header
    # CustomizationID (BR-RO-001) trebuie să fie 1.0.1
    etree.SubElement(invoice, E("CustomizationID")).text = (
        "urn:cen.eu:en16931:2017#compliant#urn:efactura.mfinante.ro:CIUS-RO:1.0.1"
    )
    etree.SubElement(invoice, E("ID")).text = f"FAC-{factura.numar}"
    etree.SubElement(invoice, E("IssueDate")).text = factura.data

    # DueDate trebuie să vină imediat după IssueDate
    etree.SubElement(invoice, E("DueDate")).text = factura.data
    
    etree.SubElement(invoice, E("InvoiceTypeCode")).text = "380"
    etree.SubElement(invoice, E("DocumentCurrencyCode")).text = "RON"

    # Secțiunea PaymentMeans (BG-23 / BR-CO-23) este eliminată.

    # --- Furnizor (AccountingSupplierParty) ---
    supplier_party = etree.SubElement(invoice, E("AccountingSupplierParty", "cac"))
    party = etree.SubElement(supplier_party, E("Party", "cac"))

    # Party Identification ID (CUI/CIF, inclusiv prefixul RO)
    etree.SubElement(etree.SubElement(party, E("PartyIdentification", "cac")), E("ID")).text = factura.furnizor.cui
    etree.SubElement(etree.SubElement(party, E("PartyName", "cac")), E("Name")).text = factura.furnizor.nume
    
    # Adăugăm PartyTaxScheme pentru Furnizor (BR-S-02 / BR-RO-065) 
    tax_scheme_supplier = etree.SubElement(party, E("PartyTaxScheme", "cac"))
    # CompanyID - Aici folosim CUI FĂRĂ prefixul "RO"
    etree.SubElement(tax_scheme_supplier, E("CompanyID")).text = clean_cui_numeric(factura.furnizor.cui)
    etree.SubElement(etree.SubElement(tax_scheme_supplier, E("TaxScheme", "cac")), E("ID")).text = "VAT"

    # Adresa (PostalAddress)
    address = etree.SubElement(party, E("PostalAddress", "cac"))
    etree.SubElement(address, E("StreetName")).text = factura.furnizor.adresa
    etree.SubElement(address, E("CityName")).text = factura.furnizor.localitate
    etree.SubElement(address, E("CountrySubentity")).text = factura.furnizor.judet
    etree.SubElement(etree.SubElement(address, E("Country", "cac")), E("IdentificationCode")).text = factura.furnizor.tara

    # Entitate Legală (PartyLegalEntity)
    legal = etree.SubElement(party, E("PartyLegalEntity", "cac"))
    etree.SubElement(legal, E("RegistrationName")).text = factura.furnizor.nume
    etree.SubElement(legal, E("CompanyID")).text = factura.furnizor.onrc

    # --- Client (AccountingCustomerParty) ---
    buyer_party = etree.SubElement(invoice, E("AccountingCustomerParty", "cac"))
    party = etree.SubElement(buyer_party, E("Party", "cac"))

    # Party Identification ID (CUI/CIF, inclusiv prefixul RO)
    etree.SubElement(etree.SubElement(party, E("PartyIdentification", "cac")), E("ID")).text = factura.client.cui
    etree.SubElement(etree.SubElement(party, E("PartyName", "cac")), E("Name")).text = factura.client.nume

    # Adăugăm PartyTaxScheme și pentru Client
    tax_scheme_customer = etree.SubElement(party, E("PartyTaxScheme", "cac"))
    # CompanyID - Aici folosim CUI FĂRĂ prefixul "RO"
    etree.SubElement(tax_scheme_customer, E("CompanyID")).text = clean_cui_numeric(factura.client.cui)
    etree.SubElement(etree.SubElement(tax_scheme_customer, E("TaxScheme", "cac")), E("ID")).text = "VAT"

    # Adresa (PostalAddress)
    address = etree.SubElement(party, E("PostalAddress", "cac"))
    etree.SubElement(address, E("StreetName")).text = factura.client.adresa
    etree.SubElement(address, E("CityName")).text = factura.client.localitate
    etree.SubElement(address, E("CountrySubentity")).text = factura.client.judet
    etree.SubElement(etree.SubElement(address, E("Country", "cac")), E("IdentificationCode")).text = factura.client.tara
    
    # Entitate Legală (PartyLegalEntity)
    legal_client = etree.SubElement(party, E("PartyLegalEntity", "cac"))
    etree.SubElement(legal_client, E("RegistrationName")).text = factura.client.nume
    etree.SubElement(legal_client, E("CompanyID")).text = factura.client.onrc

    # --- Linii Factură (InvoiceLine) ---
    for idx, prod in enumerate(factura.produse, start=1):
        line = etree.SubElement(invoice, E("InvoiceLine", "cac"))
        etree.SubElement(line, E("ID")).text = str(idx)

        # InvoicedQuantity
        qty = etree.SubElement(line, E("InvoicedQuantity"))
        qty.set("unitCode", prod.um) # Folosim UM din obiectul Factura (prod.um)
        qty.text = str(prod.cantitate)

        # LineExtensionAmount (totalul liniei fara TVA)
        amt = etree.SubElement(line, E("LineExtensionAmount"))
        amt.set("currencyID", "RON")
        amt.text = f"{prod.cantitate * prod.pret_unitar:.2f}"

        # Detalii Produs (Item)
        item = etree.SubElement(line, E("Item", "cac"))
        etree.SubElement(item, E("Name")).text = prod.denumire

        # Categorie Taxă (ClassifiedTaxCategory) - LOGICĂ PENTRU NEPLĂTITOR DE TVA
        tax = etree.SubElement(item, E("ClassifiedTaxCategory", "cac"))
        
        # Dacă cota TVA este 0, folosim codul 'Z' (Zero Rated)
        tax_id = "S"
        if prod.tva_percent == 0:
            tax_id = "Z" # Zero Rated (pentru neplătitorii de TVA)
        
        etree.SubElement(tax, E("ID")).text = tax_id 
        
        # Folosim rata TVA din obiectul Factura (va fi 0% pentru neplătitor)
        etree.SubElement(tax, E("Percent")).text = f"{prod.tva_percent:.0f}" 
        
        tax_scheme = etree.SubElement(tax, E("TaxScheme", "cac"))
        etree.SubElement(tax_scheme, E("ID")).text = "VAT"
        etree.SubElement(tax_scheme, E("Name")).text = "TVA"

        # Preț Unitar (Price)
        price = etree.SubElement(line, E("Price", "cac"))
        price_amount = etree.SubElement(price, E("PriceAmount"))
        price_amount.set("currencyID", "RON")
        price_amount.text = f"{prod.pret_unitar:.2f}"

    # --- Sumar Taxe (TaxTotal) ---
    tax_summary = {}
    for p in factura.produse:
        rate = p.tva_percent
        base = p.cantitate * p.pret_unitar
        tax_line = p.total() - base

        if rate not in tax_summary:
            tax_summary[rate] = {'taxable': 0.0, 'tax': 0.0}

        tax_summary[rate]['taxable'] += base
        tax_summary[rate]['tax'] += tax_line

    tax_total = etree.SubElement(invoice, E("TaxTotal", "cac"))
    
    tax_amount_total = etree.SubElement(tax_total, E("TaxAmount"))
    tax_amount_total.set("currencyID", "RON")
    tax_amount_total.text = f"{factura.total_tva():.2f}"
    
    # Detalierea TaxSubtotal pe cotă de TVA
    for rate, totals in tax_summary.items():
        tax_subtotal = etree.SubElement(tax_total, E("TaxSubtotal", "cac"))
        
        taxable_amount = etree.SubElement(tax_subtotal, E("TaxableAmount"))
        taxable_amount.set("currencyID", "RON")
        taxable_amount.text = f"{totals['taxable']:.2f}"
        
        tax_amount = etree.SubElement(tax_subtotal, E("TaxAmount"))
        tax_amount.set("currencyID", "RON")
        tax_amount.text = f"{totals['tax']:.2f}"

        tax_category = etree.SubElement(tax_subtotal, E("TaxCategory", "cac"))
        
        # LOGICĂ PENTRU NEPLĂTITOR DE TVA
        tax_id = "S"
        if rate == 0:
            tax_id = "Z" # Zero Rated
        
        etree.SubElement(tax_category, E("ID")).text = tax_id
        etree.SubElement(tax_category, E("Percent")).text = f"{rate:.0f}"
        
        tax_scheme = etree.SubElement(tax_category, E("TaxScheme", "cac"))
        etree.SubElement(tax_scheme, E("ID")).text = "VAT"
        etree.SubElement(tax_scheme, E("Name")).text = "TVA"


    # --- Totaluri finale (LegalMonetaryTotal) ---
    total = etree.SubElement(invoice, E("LegalMonetaryTotal", "cac"))

    # BT-106: Totalul net al liniilor
    line_extension_amount = etree.SubElement(total, E("LineExtensionAmount"))
    line_extension_amount.set("currencyID", "RON")
    line_extension_amount.text = f"{factura.total_fara_tva():.2f}"

    # BT-109: TaxExclusiveAmount (obligatoriu BR-13)
    tax_exclusive_amount = etree.SubElement(total, E("TaxExclusiveAmount"))
    tax_exclusive_amount.set("currencyID", "RON")
    tax_exclusive_amount.text = f"{factura.total_fara_tva():.2f}"

    # BT-112: Totalul cu TVA
    tax_inclusive_amount = etree.SubElement(total, E("TaxInclusiveAmount"))
    tax_inclusive_amount.set("currencyID", "RON")
    tax_inclusive_amount.text = f"{factura.total_general():.2f}"

    # BT-115: Suma de plată
    payable_amount = etree.SubElement(total, E("PayableAmount"))
    payable_amount.set("currencyID", "RON")
    payable_amount.text = f"{factura.total_general():.2f}"


    # Scriere fișier
    tree = etree.ElementTree(invoice)
    tree.write(filename, encoding="utf-8", xml_declaration=True, pretty_print=True)
    print(f"✔ XML UBL e-Factura generat: {filename}")