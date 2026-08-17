import io
import re
import urllib.request
from datetime import datetime

from flask import send_file
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from entities.log import Log
from entities.usuario import User
from enums.log_type import LogType


def sanitize_pdf_text(text):
    import unicodedata
    if not text:
        return ''
    out = []
    for ch in str(text):
        cp = ord(ch)
        if unicodedata.category(ch) == 'So':
            continue
        if 0x1F300 <= cp <= 0x1FAFF:
            continue
        if 0x1F600 <= cp <= 0x1F64F:
            continue
        if 0x1F680 <= cp <= 0x1F6FF:
            continue
        if 0x2600 <= cp <= 0x26FF:
            if cp in (0x2605, 0x2606):
                out.append('★' if cp == 0x2605 else '☆')
                continue
            continue
        if 0x2700 <= cp <= 0x27BF:
            continue
        if cp < 32:
            continue
        out.append(ch)
    s = ''.join(out)
    return re.sub(r'\s+', ' ', s).strip()


def format_pdf_date(fecha_str):
    if not fecha_str:
        return ''
    for fmt in ('%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(str(fecha_str), fmt).strftime('%d/%m/%Y')
        except ValueError:
            continue
    return str(fecha_str)[:10]


def exportar_coleccion_pdf(elementos, session):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=3 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    style_title = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, alignment=TA_CENTER, spaceAfter=8)
    style_meta = ParagraphStyle('Meta', parent=styles['Normal'], fontSize=10)
    style_meta_small = ParagraphStyle('MetaSmall', parent=styles['Normal'], fontSize=9, textColor=colors.grey)
    style_normal = ParagraphStyle('Normal', parent=styles['BodyText'], fontSize=11, alignment=TA_JUSTIFY)

    flowables = []
    gen_date = datetime.now().strftime('%d/%m/%Y %H:%M')

    def _header_footer(canvas, _doc):
        canvas.saveState()
        canvas.setFont('Helvetica-Bold', 10)
        canvas.drawString(cm, A4[1] - cm + 6, 'Chihuahuateca - Ficha de la Colección')
        canvas.setFont('Helvetica', 8)
        footer = f'Generado: {gen_date} — Página {_doc.page}'
        canvas.drawRightString(A4[0] - cm, cm / 2, footer)
        canvas.restoreState()

    for el in elementos:
        tipo_badge = f"[{(el.tipo or '').upper()}]"
        genero_badge = f"[{sanitize_pdf_text(el.genero or 'Sin género')}]"
        flowables.append(Paragraph(f'{tipo_badge} - {genero_badge}', style_meta))
        flowables.append(Spacer(1, 6))

        imagen_url = getattr(el, 'imagen_url', '') or ''
        if imagen_url:
            try:
                resp = urllib.request.urlopen(imagen_url, timeout=8)
                img = Image(io.BytesIO(resp.read()))
                img._restrictSize(12 * cm, 12 * cm)
                flowables.append(img)
                flowables.append(Spacer(1, 8))
            except Exception:
                tb = Table([['Sin imagen disponible']], colWidths=[12 * cm])
                tb.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 1, colors.lightgrey), ('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
                flowables.append(tb)
                flowables.append(Spacer(1, 8))
        else:
            tb = Table([['Sin imagen disponible']], colWidths=[12 * cm])
            tb.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 1, colors.lightgrey), ('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
            flowables.append(tb)
            flowables.append(Spacer(1, 8))

        titulo_seguro = sanitize_pdf_text(getattr(el, 'titulo', 'Sin título'))
        flowables.append(Paragraph(titulo_seguro or 'Sin título', style_title))
        autor_seguro = sanitize_pdf_text(getattr(el, 'autor_director', ''))
        flowables.append(Paragraph(f'<b>Autor / Director / Creador:</b> {autor_seguro}', style_meta))
        flowables.append(Spacer(1, 4))

        usuario_pub = sanitize_pdf_text(getattr(el, 'usuario_username', None) or getattr(el, 'usuario_nombre', ''))
        fecha_cre = format_pdf_date(getattr(el, 'fecha_creacion', ''))
        fecha_act = format_pdf_date(getattr(el, 'fecha_actualizacion', ''))
        meta_line = f'Publicado por: @{usuario_pub} | Fecha: {fecha_cre}'
        flowables.append(Paragraph(meta_line, style_meta_small))
        if fecha_act and fecha_act != fecha_cre:
            flowables.append(Paragraph(f'(Editado el: {fecha_act})', style_meta_small))
        flowables.append(Spacer(1, 6))

        try:
            calif = int(getattr(el, 'calificacion', 0) or 0)
        except Exception:
            calif = 0
        calif = max(0, min(5, calif))
        stars = ' '.join('★' for _ in range(calif))
        flowables.append(Paragraph(f'Calificación: {stars} ({calif}/5)', style_meta))
        flowables.append(Spacer(1, 8))

        descripcion_text = sanitize_pdf_text(getattr(el, 'descripcion', '') or '')
        flowables.append(Paragraph(descripcion_text or 'Sin sinopsis disponible', style_normal))
        flowables.append(Spacer(1, 8))

        opinion_text = sanitize_pdf_text(getattr(el, 'opinion', '') or '')
        opinion_box = Table([[Paragraph(opinion_text or 'Sin opinión disponible', style_normal)]], colWidths=[None])
        opinion_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f8f9fb')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        flowables.append(opinion_box)
        flowables.append(Spacer(1, 12))
        flowables.append(PageBreak())

    if not flowables:
        flowables.append(Paragraph('No hay elementos en la colección.', styles['Normal']))

    doc.build(flowables, onFirstPage=_header_footer, onLaterPages=_header_footer)
    buffer.seek(0)

    usuario_id = session.get('usuario_id')
    if usuario_id:
        usuario = User(
            id=usuario_id,
            username=session.get('username', ''),
            nombre=session.get('nombre', ''),
            password='',
            rol=(session.get('rol', 'USER') or 'USER')
        )
        Log.save_log(usuario, 'Exportó la colección completa a PDF', LogType.PDF_EXPORT)

    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"Coleccion_Chihuahuateca_{session.get('username', 'usuario')}.pdf"
    )
