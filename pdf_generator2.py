from db import format_data_ro
from factura import Factura, suma_in_litere


def export_pdf(factura: Factura, filename="Factura.pdf"):
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
    )
    elements = []
    styles = getSampleStyleSheet()

    data_formatata = format_data_ro(factura.data)

    style_titlu_factura = styles["Normal"]
    style_titlu_factura.alignment = 1
    style_titlu_factura.fontSize = 11
    style_titlu_factura.leading = 15

    # --- HEADER TABLES (Furnizor, Info, Client) ---
    data_info = [
        [Paragraph("<b>FACTURA</b>", style_titlu_factura)],
        ['NR. FACTURA:', factura.numar],
        ['DATA:', data_formatata],
    ]
    tabel_info = Table(data_info, hAlign='CENTER')
    tabel_info.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))

    data_furnizor = [
        ['Furnizor:', factura.furnizor.nume],
        ['CUI:', factura.furnizor.cui],
        ['ONRC:', factura.furnizor.onrc],
        ['Adresa:', factura.furnizor.adresa],
        ['Localitate:', factura.furnizor.localitate],
        ['Judet:', factura.furnizor.judet],
        ['Banca:', factura.furnizor.banca],
        ['IBAN:', factura.furnizor.iban],
        ['Banca:', factura.furnizor.banca1],
        ['IBAN:', factura.furnizor.iban1],
    ]
    tabel_furnizor = Table(data_furnizor, hAlign='LEFT')
    tabel_furnizor.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 1),  # Implicit este 3 sau 5
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),  # Reducem la 1 punct
    ]))

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
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 1),  # Implicit este 3 sau 5
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),  # Reducem la 1 punct
    ]))

    tabel_principal = Table(
        [[tabel_furnizor, tabel_info, tabel_client]],
        colWidths=[190, 140, 190]
    )
    tabel_principal.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    elements.append(tabel_principal)
    elements.append(Spacer(1, 24))

    # --- MAIN LOGIC: DETECT IF TVA EXISTS ---
    has_tva = factura.total_tva() > 0

    if has_tva:
        headers = ["#", "Produs", "UM", "Cant.", "PU", "TVA", "Total"]
        col_widths = [30, 170, 50, 50, 60, 50, 80]
    else:
        headers = ["#", "Produs", "UM", "Cant.", "PU", "Total"]
        col_widths = [30, 220, 50, 50, 60, 80]

    data_produse = [headers]

    for idx, p in enumerate(factura.produse, 1):
        row = [
            str(idx),
            p.denumire,
            str(p.um)[-3:] if p.um else "",
            f"{p.cantitate}",
            f"{p.pret_unitar:.2f}"
        ]
        if has_tva:
            row.append(f"{p.tva_percent:.0f}%")
        row.append(f"{p.total():.2f}")
        data_produse.append(row)

    suma = factura.total_general()

    if has_tva:
        data_produse.append(["", "", "", "", "", "Net:", f"{factura.total_fara_tva():.2f}"])
        data_produse.append(["", "", "", "", "", "TVA:", f"{factura.total_tva():.2f}"])
        data_produse.append(["", "", "", "", "", "TOTAL:", f"{suma:.2f}"])
    else:
        data_produse.append(["", "", "", "", "TOTAL:", f"{suma:.2f}"])

    table_produse = Table(data_produse, colWidths=col_widths)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),
        ("ALIGN", (-2, 1), (-2, -1), "RIGHT"),
    ]
    if has_tva:
        style.append(("FONTNAME", (0, -3), (-1, -1), "Helvetica-Bold"))
    else:
        style.append(("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"))
    table_produse.setStyle(TableStyle(style))

    elements.append(table_produse)

    # --- CHITANTA ---
    elements.append(Spacer(1, 30))
    elements.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.grey, dash=[2, 4]))
    elements.append(Spacer(1, 20))

    data_chitanta = [
        [Paragraph(f"<b>CHITANTA Nr. {factura.numar}</b>", style_titlu_factura), ""],
        [f"Data: {data_formatata}", ""],
        [f"Am primit de la: {factura.client.nume}", ""],
        [f"Suma de: {suma:.2f} RON", f"CUI: {factura.client.cui}"],
        [f"Suma în litere: {suma_in_litere(suma)}", ""],
        [f"Reprezentand: Contravaloare factura nr. {factura.numar} / {data_formatata}", ""],
        ["", ""],
        [f"Furnizor: {factura.furnizor.nume}", "Semnatura si stampila"]
    ]

    tabel_chitanta = Table(data_chitanta, colWidths=[350, 150])
    tabel_chitanta.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('SPAN', (0, 0), (1, 0)),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('ALIGN', (1, -1), (1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    elements.append(tabel_chitanta)

    try:
        doc.build(elements)
        print(f"✔ PDF salvat la: {filename}")
    except Exception as e:
        print(f"✖ Eroare PDF: {e}")