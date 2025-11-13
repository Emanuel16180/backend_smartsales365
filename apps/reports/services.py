import logging
import csv
import io
from django.http import HttpResponse
from django.utils import timezone
from .utils import format_sale_details_for_csv

# --- LIBRERÍAS DE REPORTLAB (PLATYPUS) ---
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

# Configurar el logger
logger = logging.getLogger(__name__)


# --- ESTILOS MODERNOS PARA EL PDF ---
styles = getSampleStyleSheet()

# Estilo de título principal moderno
try:
    styles.add(ParagraphStyle(
        name='ModernTitle',
        fontName='Helvetica-Bold',
        fontSize=28,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a237e'),  # Azul índigo oscuro
        spaceAfter=20,
        spaceBefore=10
    ))
    
    styles.add(ParagraphStyle(
        name='Subtitle',
        fontName='Helvetica',
        fontSize=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#666666'),
        spaceAfter=30
    ))
    
    styles.add(ParagraphStyle(
        name='SectionHeader',
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=12,
        spaceBefore=20,
        borderWidth=0,
        borderColor=colors.HexColor('#1a237e'),
        borderPadding=5
    ))
    
    styles.add(ParagraphStyle(
        name='TableHeader',
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.white,
        alignment=TA_CENTER
    ))
    
    styles.add(ParagraphStyle(
        name='TableCell',
        fontName='Helvetica',
        fontSize=8,
        textColor=colors.HexColor('#333333')
    ))
    
    styles.add(ParagraphStyle(
        name='TableCellSmall',
        fontName='Helvetica',
        fontSize=7,
        textColor=colors.HexColor('#555555'),
        leftIndent=5
    ))
    
    styles.add(ParagraphStyle(
        name='InfoBox',
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#444444'),
        spaceAfter=8
    ))
    
    styles.add(ParagraphStyle(
        name='Footer',
        fontName='Helvetica-Oblique',
        fontSize=8,
        textColor=colors.HexColor('#999999'),
        alignment=TA_CENTER
    ))
    
except KeyError:
    pass

# Colores modernos
COLOR_PRIMARY = colors.HexColor('#1a237e')      # Azul índigo oscuro
COLOR_SECONDARY = colors.HexColor('#3949ab')    # Azul índigo
COLOR_ACCENT = colors.HexColor('#00acc1')       # Cyan
COLOR_HEADER = colors.HexColor('#3949ab')       # Para encabezados de tabla
COLOR_ROW_ALT = colors.HexColor('#f5f5f5')      # Gris muy claro para filas alternas
COLOR_BORDER = colors.HexColor('#e0e0e0')       # Borde suave


def modern_header_footer(canvas, doc):
    """Dibuja encabezado y pie de página modernos"""
    canvas.saveState()
    
    # Línea decorativa superior
    canvas.setStrokeColor(COLOR_PRIMARY)
    canvas.setLineWidth(3)
    canvas.line(doc.leftMargin, doc.height + doc.topMargin + 0.3*inch, 
                doc.width + doc.leftMargin, doc.height + doc.topMargin + 0.3*inch)
    
    # Encabezado
    canvas.setFont('Helvetica-Bold', 10)
    canvas.setFillColor(COLOR_PRIMARY)
    canvas.drawString(doc.leftMargin, doc.height + doc.topMargin + 0.45*inch, 
                      "SmartSales365")
    
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#666666'))
    canvas.drawRightString(doc.width + doc.leftMargin, 
                          doc.height + doc.topMargin + 0.45*inch,
                          "Reporte Confidencial")
    
    # Línea decorativa inferior
    canvas.setStrokeColor(COLOR_PRIMARY)
    canvas.setLineWidth(2)
    canvas.line(doc.leftMargin, doc.bottomMargin - 15, 
                doc.width + doc.leftMargin, doc.bottomMargin - 15)
    
    # Pie de página
    page_num = canvas.getPageNumber()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#999999'))
    canvas.drawCentredString(doc.width/2 + doc.leftMargin, 
                            doc.bottomMargin - 30,
                            f"Página {page_num}")
    
    canvas.drawString(doc.leftMargin, doc.bottomMargin - 30,
                     timezone.now().strftime('%d/%m/%Y'))
    
    canvas.restoreState()


def generate_sales_pdf(queryset) -> HttpResponse:
    """
    Genera un PDF con diseño moderno y profesional
    """
    logger.warning("Iniciando generación de PDF moderno...")
    
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        leftMargin=0.75*inch, 
        rightMargin=0.75*inch,
        topMargin=1.3*inch, 
        bottomMargin=0.75*inch
    )
    
    elements = []

    # === PORTADA MODERNA ===
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("REPORTE DE VENTAS", styles['ModernTitle']))
    elements.append(Paragraph(
        f"Análisis Detallado de Transacciones", 
        styles['Subtitle']
    ))
    
    # Cuadro de información del reporte
    fecha_actual = timezone.now().strftime('%d de %B de %Y, %H:%M')
    info_data = [
        ["Fecha de Generación:", fecha_actual],
        ["Total de Registros:", str(queryset.count())],
        ["Sistema:", "SmartSales365"]
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), COLOR_ROW_ALT),
        ('TEXTCOLOR', (0, 0), (0, -1), COLOR_PRIMARY),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 0.3*inch))

    # === SECCIÓN DE DATOS ===
    elements.append(Paragraph("Detalle de Transacciones", styles['SectionHeader']))
    elements.append(Spacer(1, 0.15*inch))

    # Construir tabla de ventas
    table_data = [
        [
            Paragraph('ID', styles['TableHeader']),
            Paragraph('Fecha', styles['TableHeader']),
            Paragraph('Cliente', styles['TableHeader']),
            Paragraph('Monto<br/>(Bs.)', styles['TableHeader']),
            Paragraph('Estado', styles['TableHeader']),
            Paragraph('Productos', styles['TableHeader']),
        ]
    ]

    queryset = queryset.prefetch_related('user', 'details__product')
    total_ventas = 0

    for sale in queryset:
        # Cliente
        if hasattr(sale, 'user') and sale.user:
            cliente_text = f"<b>{sale.user.full_name}</b><br/><font size=7>{sale.user.email}</font>"
            cliente_p = Paragraph(cliente_text, styles['TableCell'])
        else:
            cliente_p = Paragraph("N/A", styles['TableCell'])
        
        # Estado con color
        status_color = '#4caf50' if sale.status == 'COMPLETED' else '#ff9800'
        estado_p = Paragraph(
            f'<font color="{status_color}"><b>{sale.status}</b></font>', 
            styles['TableCell']
        )
        
        # Detalles de productos
        details_list = []
        for detail in sale.details.all():
            detail_text = f"• {detail.quantity}x {detail.product.name}<br/><font size=6>Bs. {detail.price_at_purchase:,.2f} c/u</font>"
            details_list.append(Paragraph(detail_text, styles['TableCellSmall']))
        
        total_ventas += sale.total_amount
        
        # Agregar fila
        table_data.append([
            Paragraph(f"<b>#{sale.id}</b>", styles['TableCell']),
            Paragraph(sale.created_at.strftime('%d/%m/%Y<br/>%H:%M'), styles['TableCell']),
            cliente_p,
            Paragraph(f"<b>{sale.total_amount:,.2f}</b>", styles['TableCell']),
            estado_p,
            details_list,
        ])

    # Crear tabla
    if len(table_data) > 1:
        sale_table = Table(table_data, colWidths=[
            0.5*inch,   # ID
            0.9*inch,   # Fecha
            1.8*inch,   # Cliente
            0.8*inch,   # Monto
            0.9*inch,   # Estado
            2.1*inch    # Productos
        ])
        
        # Estilos de tabla modernos
        table_style = TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_HEADER),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            
            # Celdas
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            
            # Bordes
            ('LINEBELOW', (0, 0), (-1, 0), 2, COLOR_PRIMARY),
            ('GRID', (0, 1), (-1, -1), 0.5, COLOR_BORDER),
            ('BOX', (0, 0), (-1, -1), 1.5, COLOR_PRIMARY),
            
            # Filas alternas
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_ROW_ALT]),
            
            # Alineación específica
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # ID
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Fecha
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),   # Monto
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Estado
        ])
        
        sale_table.setStyle(table_style)
    else:
        sale_table = Table(
            [["No se encontraron ventas que coincidan con los filtros."]], 
            colWidths=[7*inch]
        )
    
    elements.append(sale_table)
    
    # === RESUMEN FINAL ===
    elements.append(Spacer(1, 0.3*inch))
    
    summary_data = [
        ["TOTAL GENERAL:", f"Bs. {total_ventas:,.2f}"]
    ]
    
    summary_table = Table(summary_data, colWidths=[5*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
    ]))
    
    elements.append(summary_table)

    # Construir PDF
    try:
        doc.build(elements, onFirstPage=modern_header_footer, onLaterPages=modern_header_footer)
        logger.warning("PDF moderno generado exitosamente.")
    except Exception as e:
        logger.error(f"Error al construir PDF moderno: {e}")
        return HttpResponse(f"Error generando PDF: {e}", status=500)

    pdf_content = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_ventas_moderno.pdf"'
    return response


def generate_sales_csv(queryset) -> HttpResponse:
    """
    Genera un CSV de ventas (sin cambios)
    """
    logger.warning("Generando CSV...")
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_ventas_filtrado.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID_Venta', 'Fecha', 'Cliente', 'Email', 'Monto_Total', 'Estado', 'Detalle_Productos'])

    queryset = queryset.prefetch_related('details__product')

    for sale in queryset:
        if hasattr(sale, 'details'):
            try:
                product_details = format_sale_details_for_csv(sale.details.all())
            except Exception:
                product_details = "N/A"
        else:
            product_details = "N/A"

        if hasattr(sale, 'user') and sale.user:
            user_name = f"{sale.user.first_name} {sale.user.last_name}"
            user_email = sale.user.email
        else:
            user_name = "N/A"
            user_email = "N/A"

        total_amount = getattr(sale, 'total_amount', 'N/A')
        status = getattr(sale, 'status', 'N/A')

        writer.writerow([
            sale.id, 
            sale.created_at.strftime('%Y-%m-%d %H:%M:%S'), 
            user_name, 
            user_email, 
            total_amount, 
            status, 
            product_details
        ])
    
    logger.warning("CSV generado exitosamente.")
    return response


def generate_sales_excel(queryset) -> HttpResponse:
    """
    Stub para la generación de Excel
    """
    logger.warning("Generación de Excel no implementada.")
    return HttpResponse("Formato Excel aún no implementado.", status=501)


# === FUNCIÓN LEGACY (para compatibilidad) ===
from django.template.loader import get_template
from xhtml2pdf import pisa

def render_to_pdf(template_src, context_dict=None):
    """
    Función legacy para convertir templates HTML a PDF usando xhtml2pdf
    NOTA: Esta función está obsoleta, usa generate_sales_pdf() en su lugar
    """
    context_dict = context_dict or {}
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.CreatePDF(src=html, dest=result)
    if pdf.err:
        logger.error(f"Error en pisa.CreatePDF: {pdf.err}")
        return None
    return result.getvalue()