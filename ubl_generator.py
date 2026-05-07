from lxml import etree
from factura import Factura, Produs  # asigură-te că ai clasele: Factura, Client, Furnizor, Produs

def E(tag, ns="cbc"):
    NSMAP = {
        "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
        "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        "ccts": "urn:un:unece:uncefact:documentation:",
        "qdt": "urn:oasis:names:specification:ubl:schema:xsd:QualifiedDataTypes-2",
        "udt": "urn:oasis:names:specification:ubl:schema:xsd:UnqualifiedDataTypes-2",
        None:  "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        
        
    }
    return etree.QName(NSMAP[ns], tag)

def export_xml_lxml(factura: Factura, filename="Factura.xml"):
    NSMAP = {
        "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
        "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        "ccts": "urn:un:unece:uncefact:documentation:",
        "qdt": "urn:oasis:names:specification:ubl:schema:xsd:QualifiedDataTypes-2",
        "udt": "urn:oasis:names:specification:ubl:schema:xsd:UnqualifiedDataTypes-2",
        None:  "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    }

    invoice = etree.Element(E("Invoice", None), nsmap=NSMAP)

    # === [BG-1] Header ===
    etree.SubElement(invoice, E("CustomizationID")).text = "urn:cen.eu:en16931:2017#compliant#urn:efactura.mfinante.ro:CIUS-RO:1.0.1"  # BT-24
    # etree.SubElement(invoice, E("ProfileID")).text = "urn:fdc:gov.ro:2022:businessprocess:01:06:receipt"                            # BT-25
    etree.SubElement(invoice, E("ID")).text = factura.numar                     # BT-1
    etree.SubElement(invoice, E("IssueDate")).text = factura.data              # BT-2
    etree.SubElement(invoice, E("DueDate")).text = factura.data       # BT-9
    etree.SubElement(invoice, E("InvoiceTypeCode")).text = "380"               # BT-3
    etree.SubElement(invoice, E("DocumentCurrencyCode")).text = "RON"          # BT-5

    # === [BG-4] Furnizor ===
    supplier_party = etree.SubElement(invoice, E("AccountingSupplierParty", "cac"))
    party = etree.SubElement(supplier_party, E("Party", "cac"))
    etree.SubElement(etree.SubElement(party, E("PartyIdentification", "cac")), E("ID")).text = f"RO{factura.furnizor.cui}"  # BT-31
    etree.SubElement(etree.SubElement(party, E("PartyName", "cac")), E("Name")).text = factura.furnizor.nume               # BT-27

    address = etree.SubElement(party, E("PostalAddress", "cac"))
    etree.SubElement(address, E("StreetName")).text = factura.furnizor.adresa         # BT-35
    etree.SubElement(address, E("CityName")).text = factura.furnizor.localitate       # BT-36
    etree.SubElement(address, E("CountrySubentity")).text = f"{factura.furnizor.tara}-{factura.furnizor.judet}"    # BT-38
    etree.SubElement(etree.SubElement(address, E("Country", "cac")), E("IdentificationCode")).text = factura.furnizor.tara  # BT-40

    tax_scheme = etree.SubElement(party, E("PartyTaxScheme", "cac"))
    etree.SubElement(tax_scheme, E("CompanyID")).text = f"RO{factura.furnizor.cui}"   # BT-31
    scheme = etree.SubElement(tax_scheme, E("TaxScheme", "cac"))
    etree.SubElement(scheme, E("ID")).text = "VAT"

    legal = etree.SubElement(party, E("PartyLegalEntity", "cac"))
    etree.SubElement(legal, E("RegistrationName")).text = factura.furnizor.nume       # BT-27
    etree.SubElement(legal, E("CompanyID")).text = factura.furnizor.cui              # BT-30

    # === [BG-7] Client ===
    customer_party = etree.SubElement(invoice, E("AccountingCustomerParty", "cac"))
    party = etree.SubElement(customer_party, E("Party", "cac"))
    etree.SubElement(etree.SubElement(party, E("PartyIdentification", "cac")), E("ID")).text = f"RO{factura.client.cui}"  # BT-48
    etree.SubElement(etree.SubElement(party, E("PartyName", "cac")), E("Name")).text = factura.client.nume               # BT-44

    address = etree.SubElement(party, E("PostalAddress", "cac"))
    etree.SubElement(address, E("StreetName")).text = factura.client.adresa          # BT-52
    etree.SubElement(address, E("CityName")).text = factura.client.localitate        # BT-53
    etree.SubElement(address, E("CountrySubentity")).text = f"{factura.client.tara}-{factura.client.judet}"     # BT-55
    etree.SubElement(etree.SubElement(address, E("Country", "cac")), E("IdentificationCode")).text = factura.client.tara # BT-57

    tax_scheme = etree.SubElement(party, E("PartyTaxScheme", "cac"))
    etree.SubElement(tax_scheme, E("CompanyID")).text = f"RO{factura.client.cui}"     # BT-48
    scheme = etree.SubElement(tax_scheme, E("TaxScheme", "cac"))
    etree.SubElement(scheme, E("ID")).text = "VAT"

    legal = etree.SubElement(party, E("PartyLegalEntity", "cac"))
    etree.SubElement(legal, E("RegistrationName")).text = factura.client.nume         # BT-44
    etree.SubElement(legal, E("CompanyID")).text = factura.client.cui                 # BT-47

    # === [BG-16] Instrucțiuni de plată ===
    if factura.furnizor.iban:
        payment_means = etree.SubElement(invoice, E("PaymentMeans", "cac"))

        # BT-81: Codul modalității de plată (31 = Transfer credit)
        etree.SubElement(payment_means, E("PaymentMeansCode")).text = "31"

        # BT-83: Notă privind plata
        etree.SubElement(payment_means, E("PaymentID")).text = f"Plata factura {factura.numar}"

        # [BG-17] Detalii cont bancar
        payee_account = etree.SubElement(payment_means, E("PayeeFinancialAccount", "cac"))

        # BT-84: IBAN-ul furnizorului (OBLIGATORIU)
        etree.SubElement(payee_account, E("ID")).text = factura.furnizor.iban

        # NOTĂ: Am eliminat tag-ul FinancialInstitutionBranch/Name care genera eroarea UBL-CR-429.
        # Numele băncii nu este permis în acest punct conform regulii de validare.
    if factura.furnizor.iban1:
        payment_means = etree.SubElement(invoice, E("PaymentMeans", "cac"))

        # BT-81: Codul modalității de plată (31 = Transfer credit)
        etree.SubElement(payment_means, E("PaymentMeansCode")).text = "31"

        # BT-83: Notă privind plata
        etree.SubElement(payment_means, E("PaymentID")).text = f"Plata factura {factura.numar}"

        # [BG-17] Detalii cont bancar
        payee_account = etree.SubElement(payment_means, E("PayeeFinancialAccount", "cac"))

        # BT-84: IBAN-ul furnizorului (OBLIGATORIU)
        etree.SubElement(payee_account, E("ID")).text = factura.furnizor.iban1


     # === [BG-23] TVA totală ===
    tax_total = etree.SubElement(invoice, E("TaxTotal", "cac"))
    tax_amt = etree.SubElement(tax_total, E("TaxAmount"))
    tax_amt.set("currencyID", "RON")
    tax_amt.text = f"{factura.total_tva():.2f}"   # BT-110

    if factura.produse:
        tva_percent = factura.produse[0].tva_percent
    else:
        tva_percent = 0

    tax_sub = etree.SubElement(tax_total, E("TaxSubtotal", "cac"))
    tax_amt1 = etree.SubElement(tax_sub, E("TaxableAmount"))
    tax_amt1.set("currencyID", "RON")
    tax_amt1.text = f"{factura.total_fara_tva():.2f}"  # BT-116
    tax_amt3 = etree.SubElement(tax_sub, E("TaxAmount"))
    tax_amt3.set("currencyID", "RON")
    tax_amt3.text = f"{factura.total_tva():.2f}"                                  # BT-117

    tax = etree.SubElement(tax_sub, E("TaxCategory", "cac"))
    if tva_percent > 0:
        etree.SubElement(tax, E("ID")).text = "S"
        etree.SubElement(tax, E("Percent")).text = f"{tva_percent:.2f}"
    else:
        etree.SubElement(tax, E("ID")).text ="E"                                            # BT-118
        etree.SubElement(tax, E("Percent")).text = "0.00"                                      # BT-119
        etree.SubElement(tax, E("TaxExemptionReasonCode")).text = "VATEX-EU-O"              # BT-120
        etree.SubElement(tax, E("TaxExemptionReason")).text = "Neimpozabil conform art. 292 Cod Fiscal"  # BT-121

    scheme1 = etree.SubElement(tax, E("TaxScheme", "cac"))
    etree.SubElement(scheme1, E("ID")).text = "VAT"
  #  etree.SubElement(scheme, E("ID")).text = "VAT"
    # === [BG-24] Totaluri Factura ===
    total = etree.SubElement(invoice, E("LegalMonetaryTotal", "cac"))
    etree.SubElement(total, E("LineExtensionAmount", "cbc"), currencyID="RON").text = f"{factura.total_fara_tva():.2f}"     # BT-106
    etree.SubElement(total, E("TaxExclusiveAmount", "cbc"), currencyID="RON").text = f"{factura.total_fara_tva():.2f}"      # BT-109
    etree.SubElement(total, E("TaxInclusiveAmount", "cbc"), currencyID="RON").text = f"{factura.total_general():.2f}"       # BT-112
    etree.SubElement(total, E("PayableAmount", "cbc"), currencyID="RON").text = f"{factura.total_general():.2f}"            # BT-115

    # === [BG-22] Produse ===
    for idx, p in enumerate(factura.produse, start=1):
        line = etree.SubElement(invoice, E("InvoiceLine", "cac"))
        etree.SubElement(line, E("ID")).text = str(idx)                                  # BT-126

        qty = etree.SubElement(line, E("InvoicedQuantity"))
        qty.set("unitCode", p.um[:3])                                                 # BT-130
        qty.text = str(p.cantitate)                                                      # BT-129

        amount = etree.SubElement(line, E("LineExtensionAmount"))
        amount.set("currencyID", "RON")
        amount.text = f"{p.total():.2f}"                                                 # BT-131

        item = etree.SubElement(line, E("Item", "cac"))
        etree.SubElement(item, E("Name")).text = p.denumire                              # BT-153

        # TVA - NEPLĂTITOR ("O")
        tax = etree.SubElement(item, E("ClassifiedTaxCategory", "cac"))
        if tva_percent > 0:
            etree.SubElement(tax, E("ID")).text = "S"
            etree.SubElement(tax, E("Percent")).text = f"{tva_percent:.2f}"
        else:
            etree.SubElement(tax, E("ID")).text = "E"
            etree.SubElement(tax, E("Percent")).text = "0.00"                                # BT-151
            # scheme = etree.SubElement(tax, E("TaxScheme", "cac"))
            # etree.SubElement(scheme, E("ID")).text = "VAT"

        scheme = etree.SubElement(tax, E("TaxScheme", "cac"))
        etree.SubElement(scheme, E("ID")).text = "VAT"

        price = etree.SubElement(line, E("Price", "cac"))
        price_amt = etree.SubElement(price, E("PriceAmount"))
        price_amt.set("currencyID", "RON")
        price_amt.text = f"{p.pret_unitar:.2f}"                                          # BT-146

   
    
    

    # === Scriere XML ===
    tree = etree.ElementTree(invoice)
    tree.write(filename, pretty_print=True, xml_declaration=True, encoding="utf-8")
    print(f"✅ XML generat: {filename}")