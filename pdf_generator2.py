import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from db import format_data_ro
from factura import Factura, suma_in_litere


def export_pdf(factura: Factura, filename="Factura.pdf"):
    # Verifica existenta imaginii (cale absoluta sau relativa)
    path_stampila = "d:/lucru/eFactura_python/semn_stamp.jpg"
    if not os.path.exists(path_stampila):
        path_stampila = "semn_stamp.jpg"

    img_stampila = None
    if os.path.exists(path_stampila):
        img_stampila = Image(path_stampila, width=60, height=60)
        img_stampila.hAlign = "CENTER"

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )
    elements = []

    # --- CONFIGURARE STILURI ---
    styles_sheet = getSampleStyleSheet()

    style_titlu_factura = ParagraphStyle(
        "TitluFactura",
        parent=styles_sheet["Normal"],
        alignment=1,  # Centrat
        fontSize=11,
        leading=14,
        fontName="Helvetica-Bold",
    )

    style_text_header = ParagraphStyle(
        "HeaderInfo", parent=styles_sheet["Normal"], fontSize=8, leading=10
    )

    style_produs = ParagraphStyle(
        "DenumireProdus", parent=styles_sheet["Normal"], fontSize=8, leading=10
    )

    style_celula = ParagraphStyle(
        "TextCelula", parent=styles_sheet["Normal"], fontSize=8, leading=10
    )

    data_formatata = format_data_ro(factura.data)

    # --- HEADER TABLES (Furnizor, Info Factura, Client) ---
    data_info = [
        [Paragraph("<b>FACTURA</b>", style_titlu_factura)],
        ["SERIE FACTURA:", factura.furnizor.ser_fac],
        ["NR. FACTURA:", factura.numar],
        ["DATA:", data_formatata],
    ]
    tabel_info = Table(data_info, hAlign="CENTER")
    tabel_info.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.grey),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ])
    )

    data_furnizor = [
        ["Furnizor:", factura.furnizor.nume],
        ["CUI:", factura.furnizor.cui],
        ["ONRC:", factura.furnizor.onrc],
        ["Adresa:", Paragraph(factura.furnizor.adresa, style_text_header)],
        ["Localitate:", factura.furnizor.localitate],
        ["Judet:", factura.furnizor.judet],
        ["Banca:", factura.furnizor.banca],
        ["IBAN:", factura.furnizor.iban],
    ]
    if getattr(factura.furnizor, "banca1", None) and getattr(
        factura.furnizor, "iban1", None
    ):
        data_furnizor.append(["Banca:", factura.furnizor.banca1])
        data_furnizor.append(["IBAN:", factura.furnizor.iban1])

    tabel_furnizor = Table(data_furnizor, colWidths=[45, 145], hAlign="LEFT")
    tabel_furnizor.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (0, -1), "RIGHT"),
            ("ALIGN", (1, 0), (1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ])
    )

    data_client = [
        ["Client:", factura.client.nume],
        ["CUI:", factura.client.cui],
        ["ONRC:", factura.client.onrc],
        ["Adresa:", Paragraph(factura.client.adresa, style_text_header)],
        ["Localitate:", factura.client.localitate],
        ["Judet:", factura.client.judet],
        ["Banca:", factura.client.banca],
        ["IBAN:", factura.client.iban],
    ]
    tabel_client = Table(data_client, colWidths=[45, 145], hAlign="LEFT")
    tabel_client.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (0, -1), "RIGHT"),
            ("ALIGN", (1, 0), (1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ])
    )

    tabel_principal = Table(
        [[tabel_furnizor, tabel_info, tabel_client]], colWidths=[190, 140, 190]
    )
    tabel_principal.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])
    )

    elements.append(tabel_principal)
    elements.append(Spacer(1, 15))

    # --- TABEL PRODUSE ---
    has_tva = factura.total_tva() > 0

    if has_tva:
        headers = ["#", "Produs", "UM", "Cant.", "PU", "TVA", "Total"]
        col_widths = [25, 175, 45, 45, 60, 45, 95]
    else:
        headers = ["#", "Produs", "UM", "Cant.", "PU", "Total"]
        col_widths = [25, 220, 45, 45, 60, 95]

    data_produse = [headers]

    for idx, p in enumerate(factura.produse, 1):
        row = [
            str(idx),
            Paragraph(p.denumire, style_produs),
            str(p.um)[-3:] if p.um else "",
            f"{p.cantitate}",
            f"{p.pret_unitar:.2f}",
        ]
        if has_tva:
            row.append(f"{p.tva_percent:.0f}%")
        row.append(f"{p.total():.2f}")
        data_produse.append(row)

    suma = factura.total_general()

    if has_tva:
        data_produse.append([
            "",
            "",
            "",
            "",
            "",
            "Net:",
            f"{factura.total_fara_tva():.2f}",
        ])
        data_produse.append(
            ["", "", "", "", "", "TVA:", f"{factura.total_tva():.2f}"]
        )
        data_produse.append(["", "", "", "", "", "TOTAL:", f"{suma:.2f}"])
    else:
        data_produse.append(["", "", "", "", "TOTAL:", f"{suma:.2f}"])

    table_produse = Table(data_produse, colWidths=col_widths)
    t_style = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]

    if has_tva:
        t_style.append(("FONTNAME", (0, -3), (-1, -1), "Helvetica-Bold"))
    else:
        t_style.append(("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"))

    table_produse.setStyle(TableStyle(t_style))
    elements.append(table_produse)



    # --- SECȚIUNE FINALĂ: FURNIZOR (S) | DELEGAT (M) | TOTAL + CLIENT (D) ---
    text_delegat = (
        "<b>DATE DELEGAT</b><br/>"
        "Nume si prenume: .................................................<br/>"
        "B.I./C.I.: ........ seria ........ nr .............<br/>"
        "Mijloc transport: ......................... "
        "Data expedierii: ..........................<br/>"
        "Semnatura de primire: ............................."
    )

    text_dreapta = (
        f"<b>TOTAL DE PLATA:</b><br/>"
        f"<font size='11'><b>{factura.total_general():.2f} RON</b></font><br/>"
    )

    cell_furnizor = [
        Paragraph("Semnatura si stampila furnizorului", style_celula)
    ]
    if img_stampila:
        cell_furnizor.append(Spacer(1, 4))
        cell_furnizor.append(img_stampila)

    data_finala = [[
        cell_furnizor,
        Paragraph(text_delegat, style_celula),
        Paragraph(text_dreapta, style_celula),
    ]]

    tabel_final = Table(data_finala, colWidths=[140, 210, 140])
    tabel_final.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (0, 0), "CENTER"),
            ("ALIGN", (1, 0), (1, 0), "LEFT"),
            ("ALIGN", (2, 0), (2, 0), "CENTER"),
            ("BOX", (0, 0), (0, 0), 0.5, colors.black),
            ("BOX", (1, 0), (1, 0), 0.5, colors.black),
            ("BOX", (2, 0), (2, 0), 0.5, colors.black),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ])
    )

    elements.append(tabel_final)

    index_incarcare = getattr(factura, 'nr1', None)
    index_descarcare = getattr(factura, 'nr2', None)

    if index_incarcare or index_descarcare:
        elements.append(Spacer(1, 8))

        text_anaf = "<b>Date RO e-Factura (ANAF):</b> "
        detalii = []
        if index_incarcare:
            detalii.append(f"Index încarcare: <b>{index_incarcare}</b>")
        if index_descarcare:
            detalii.append(f"Index descarcare: <b>{index_descarcare}</b>")

        text_anaf += " | ".join(detalii)

        p_anaf = Paragraph(text_anaf, style_celula)

        tabel_anaf = Table([[p_anaf]], colWidths=[520])
        tabel_anaf.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e0f2f1')),  # nuanță deschisă de verde/teal
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#00897b')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        elements.append(tabel_anaf)
        elements.append(Spacer(1, 10))
    else:
        elements.append(Spacer(1, 15))

    # --- CHITANȚĂ (OPȚIONALĂ) ---
    if factura.nr_chit:
        elements.append(Spacer(1, 12))
        elements.append(
            HRFlowable(
                width="100%",
                thickness=0.8,
                lineCap="round",
                color=colors.grey,
                dash=[3, 3],
            )
        )
        elements.append(Spacer(1, 10))

        cell_chit = [Paragraph("Semnatura si stampila", style_celula)]
        if img_stampila:
            cell_chit.append(Spacer(1, 3))
            cell_chit.append(img_stampila)

        data_chitanta = [
            [
                Paragraph(
                    f"<b>CHITANTA Nr. {factura.nr_chit}</b>", style_titlu_factura
                ),
                "",
            ],
            [f"Data: {data_formatata}", ""],
            [f"Am primit de la: {factura.client.nume}", ""],
            [f"Suma de: {suma:.2f} RON", f"CUI: {factura.client.cui}"],
            [f"Suma în litere: {suma_in_litere(suma)}", ""],
            [
                (
                    f"Reprezentand: Contravaloare factura nr."
                    f" {factura.numar} / {data_formatata}"
                ),
                "",
            ],
            ["", ""],
            [f"Furnizor: {factura.furnizor.nume}", cell_chit],
        ]

        tabel_chitanta = Table(data_chitanta, colWidths=[340, 150])
        tabel_chitanta.setStyle(
            TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("SPAN", (0, 0), (1, 0)),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("ALIGN", (0, 0), (1, 0), "CENTER"),
                ("ALIGN", (1, -1), (1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ])
        )

        elements.append(tabel_chitanta)

    try:
        doc.build(elements)
        print(f"✔ PDF salvat cu succes la: {filename}")
    except Exception as e:
        print(f"✖ Eroare la generarea PDF-ului: {e}")