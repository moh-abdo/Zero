"""
import os
import tempfile
from fpdf import FPDF
import qrcode
from bidi.algorithm import get_display
import arabic_reshaper

FONT_NAME = 'DejaVu'
FONT_FILE = 'DejaVuSans.ttf'  # The repo user should place a TTF that supports Arabic or use system font


def reshape_ar(text: str) -> str:
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def generate_sick_leave_pdf(data: dict) -> str:
    """
    data keys: patient_name, duration, uuid, issuer_name (optional), amount
    Returns path to generated PDF
    """
    patient_name = data.get('patient_name')
    duration = data.get('duration')
    uuid = data.get('uuid')
    issuer_name = data.get('issuer_name', '')
    amount = data.get('amount')

    tmp_dir = tempfile.gettempdir()
    out_path = os.path.join(tmp_dir, f"sick_leave_{uuid}.pdf")

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()

    # Add a font that supports Arabic. User must ensure FONT_FILE exists.
    font_path = os.path.join(os.getcwd(), FONT_FILE)
    if os.path.exists(font_path):
        pdf.add_font(FONT_NAME, '', font_path, uni=True)
        pdf.set_font(FONT_NAME, size=14)
    else:
        pdf.set_font('Arial', size=14)

    # Header
    pdf.cell(0, 10, reshape_ar('شهادة إجازة مرضية'), ln=True, align='C')
    pdf.ln(5)

    # Body
    text_lines = [
        f"الاسم: {patient_name}",
        f"مدة الإجازة: {duration}",
        f"المبلغ المدفوع: {amount} ر.ي",
        f"معرّف الإجازة: {uuid}"
    ]

    for line in text_lines:
        try:
            pdf.cell(0, 10, reshape_ar(line), ln=True, align='R')
        except Exception:
            pdf.cell(0, 10, line, ln=True, align='L')

    pdf.ln(10)
    pdf.cell(0, 10, reshape_ar('توقيع الطبيب: ____________________'), ln=True, align='R')

    # Generate QR / Barcode
    qr = qrcode.make(uuid)
    qr_path = os.path.join(tmp_dir, f"qr_{uuid}.png")
    qr.save(qr_path)

    # place QR
    pdf.image(qr_path, x=10, y=200, w=40)

    # print UUID under barcode
    try:
        pdf.set_xy(10, 245)
        pdf.cell(40, 6, reshape_ar(uuid), align='C')
    except Exception:
        pdf.set_xy(10, 245)
        pdf.cell(40, 6, uuid, align='C')

    pdf.output(out_path)

    # cleanup qr image
    try:
        os.remove(qr_path)
    except Exception:
        pass

    return out_path
"""
