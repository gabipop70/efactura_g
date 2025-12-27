from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from factura import Factura
from datetime import datetime
from reportlab.platypus import Table, TableStyle, HRFlowable
from reportlab.lib import colors
from db import format_data_ro

def export_pdf(factura: Factura, filename="Factura.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # data_obj = datetime.strptime(factura.data, "%Y-%m-%d")
    data_formatata = format_data_ro(factura.data)
   
    style_titlu_factura = styles["Normal"]
    style_titlu_factura.alignment = 1  # Centrat
    style_titlu_factura.fontSize = 11
    style_titlu_factura.leading = 15
    
    # 1. Datele Facturii (Coloana din mijloc)
    data_info = [
    [Paragraph("<b>FACTURA</b>", style_titlu_factura)],
    ['NR. FACTURA:', factura.numar],
    ['DATA:', data_formatata],
    ]

    tabel_info = Table(data_info, hAlign='CENTER')
    tabel_info.setStyle(TableStyle([
    ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
    ('FONTSIZE', (0,0), (-1,-1), 8),
    ('ALIGN', (0,0), (0,-1), 'LEFT'),
    ('ALIGN', (1,0), (1,-1), 'RIGHT'),
    ('TEXTCOLOR', (0,0), (0,-1), colors.grey),
    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))     

    # furnizor = f"<b>Furnizor:</b> {factura.furnizor.nume}<br/>" \
    #            f"CUI: {factura.furnizor.cui} | ONRC: {factura.furnizor.onrc}<br/>" \
    #            f"Adresa: {factura.furnizor.adresa}<br/>" \
    #            f"Localitate: {factura.furnizor.localitate}<br/>" \
    #            f"Județ: {factura.furnizor.judet}<br/>" \
    #            f"Banca: {factura.furnizor.banca}<br/>" \
    #            f"IBAN: {factura.furnizor.iban}"
                
    # elements.append(Paragraph(furnizor, styles["Normal"]))
    # elements.append(Spacer(1, 12))

    # client = f"<b>Client:</b> {factura.client.nume}<br/>" \
    #          f"CUI: {factura.client.cui} | ONRC: {factura.client.onrc}<br/>" \
    #          f"Adresa: {factura.client.adresa}<br/>" \
    #          f"Adresa: {factura.client.localitate}<br/>" \
    #          f"Banca: {factura.client.banca}<br/>" \
    #          f"IBAN: {factura.client.iban}"
    # elements.append(Paragraph(client, styles["Normal"]))
    # elements.append(Spacer(1, 12))
    data_furnizor = [
        ['Furnizor:', factura.furnizor.nume],
        ['CUI:', factura.furnizor.cui],
        ['ONRC:', factura.furnizor.onrc],
        ['Adresa:', factura.furnizor.adresa],
        ['Localitate:', factura.furnizor.localitate],
        ['Judet:', factura.furnizor.judet],
        ['Banca:', factura.furnizor.banca],
        ['IBAN:', factura.furnizor.iban],
    ]

    tabel_furnizor = Table(data_furnizor, hAlign='LEFT')
    tabel_furnizor.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), -1),
        ('ALIGN', (0,0), (0,-1), 'RIGHT'),
        ('ALIGN', (1,0), (1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        # ('BOX', (0,0), (-1,-1), 0.25, colors.black),
        # ('INNERGRID', (0,0), (-1,-1), 0.25, colors.grey),
    ]))
    
    

    # Date client
    data_client = [
        ['Client:', factura.client.nume],
        ['CUI:', factura.client.cui],
        ['ONRC:', factura.client.onrc],
        ['Adresa:', factura.client.adresa],
        ['Localitate:', factura.client.localitate],
        ['Judet:', factura.client.judet],
        ['Banca:', factura.client.banca],
        ['IBAN:', factura.client.iban],
    ]

    tabel_client = Table(data_client, hAlign='LEFT')
    tabel_client.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('TOPPADDING',(0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), -1),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        # ('BOX', (0,0), (-1,-1), 0.25, colors.black),
        # ('INNERGRID', (0,0), (-1,-1), 0.25, colors.grey),
    ]))

    # Tabel cu trei coloane: furnizor | client
    tabel_principal = Table(
    [[tabel_furnizor, tabel_info, tabel_client]],
    colWidths=[190, 120, 190]  # Ajustate pentru a încăpea în pagină
    )

    tabel_principal.setStyle(TableStyle([
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('ALIGN', (0,0), (0,0), 'LEFT'),   # Furnizor la stânga
    ('ALIGN', (1,0), (1,0), 'CENTER'), # Info la centru
    ('ALIGN', (2,0), (2,0), 'RIGHT'),  # Client la dreapta
    ('LEFTPADDING', (0,0), (-1,-1), 0),
    ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))

    elements.append(tabel_principal)
    elements.append(Spacer(1, 12))

    data = [
        ["#", "Produs", "UM", "Cant.", "PU", "TVA %", "Total"]
    ]
    for idx, p in enumerate(factura.produse, 1):
        data.append([
            str(idx),
            p.denumire,
            p.um[-3:],
            f"{p.cantitate}",
            f"{p.pret_unitar:.2f}",
            f"{p.tva_percent:.0f}%",
            f"{p.total():.2f}"
        ])
    data.append(["", "", "", "", "", "Total fara TVA", f"{factura.total_fara_tva():.2f}"])
    data.append(["", "", "", "", "", "TVA", f"{factura.total_tva():.2f}"])
    data.append(["", "", "", "", "", "TOTAL", f"{factura.total_general():.2f}"])

    table = Table(data, colWidths=[30, 170, 50, 50, 60, 50, 80])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica"),
        ('FONTSIZE',(0,0),(-1,-1),7),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    
    

# 1. Linie de separare (foarfecă)
    
   

# 2. Datele Chitanței
    data_chitanta = [
        [Paragraph(f"<b>CHITANTA Nr. {factura.numar}</b>", style_titlu_factura), ""],
        [f"Data: {data_formatata}", ""],
        [f"Am primit de la: {factura.client.nume}", ""],
        [f"Suma de: {factura.total_general()} RON", f"CUI: {factura.client.cui}"],
    #    [f"Suma în litere: {factura.suma_in_litere}", ""],
        [f"Reprezentand: Contravaloare factura nr. {factura.numar} / {data_formatata}", ""],
        ["", ""],
        [f"Furnizor: {factura.furnizor.nume}", "Semnatura si stampila"]
    ]

# 3. Crearea și stilizarea tabelului de chitanță
    tabel_chitanta = Table(data_chitanta, colWidths=[350, 150])

    tabel_chitanta.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('SPAN', (0,0), (1,0)), # Unește prima linie pentru titlu
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (1,0), 'CENTER'),
        ('ALIGN', (1, -1), (1, -1), 'CENTER'), # Semnătura la dreapta
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    elements.append(table)
    
    elements.append(Spacer(1,30))
    elements.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.grey, dash=[2, 4]))
    elements.append(Spacer(1, 20))
    elements.append(tabel_chitanta)
    
    
    doc.build(elements)
    print(f"✔ PDF salvat la: {filename}")