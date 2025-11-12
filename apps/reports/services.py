# apps/reports/services.py

import logging  # <-- Importación de logging (del paso anterior)
import csv 
import io
from django.http import HttpResponse
from django.utils import timezone 
from django.template.loader import get_template
from xhtml2pdf import pisa
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

# Importar la utilidad de CSV desde utils.py
from .utils import format_sale_details_for_csv 

# Configurar el logger para este módulo
logger = logging.getLogger(__name__)


# --- (FUNCIÓN QUE FALTA) ---
# Esta función es la que causa el error de importación
def render_to_pdf(template_src, context_dict=None):
    """Renderiza una plantilla Django a PDF y devuelve los bytes del PDF."""
    context_dict = context_dict or {}
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO() # Usa io.BytesIO
    pdf = pisa.CreatePDF(src=html, dest=result)
    if pdf.err:
        logger.error(f"Error en pisa.CreatePDF: {pdf.err}")
        return None
    return result.getvalue()


def generate_sales_pdf(queryset) -> HttpResponse:
    """
    Toma un queryset de Ventas y genera un PDF detallado con ReportLab.
    """
    logger.warning("Iniciando generación de PDF (ReportLab)...")
    
    buffer = io.BytesIO() # Usa io.BytesIO
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(1 * inch, height - 1 * inch, "REPORTE DE VENTAS (DETALLADO)")
    
    p.setFont("Helvetica", 10)
    fecha_actual = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    p.drawString(1 * inch, height - 1.3 * inch, f"Generado: {fecha_actual}")
    
    # Encabezados de columna
    p.setFont("Helvetica-Bold", 9)
    y_position = height - 1.8 * inch
    p.drawString(0.5 * inch, y_position, "ID")
    p.drawString(1 * inch, y_position, "Fecha")
    p.drawString(2.5 * inch, y_position, "Cliente")
    p.drawString(5.0 * inch, y_position, "Monto")
    p.drawString(6.0 * inch, y_position, "Estado")
    p.drawString(7.0 * inch, y_position, "Items")
    
    p.line(0.5 * inch, y_position - 0.1 * inch, 7.5 * inch, y_position - 0.1 * inch)
    
    y_position -= 0.3 * inch
    
    count = 0
    detalle_font_size = 7
    line_height_detalle = 0.18 * inch
    line_height_venta = 0.25 * inch
    
    # Asegúrate de que el queryset traiga los detalles
    queryset = queryset.prefetch_related('details__product')
    
    for sale in queryset:
        # 1. Chequear espacio
        if y_position < (1 * inch + line_height_venta + line_height_detalle):
            p.showPage()
            p.setFont("Helvetica", 8) # Re-establecer fuente en página nueva
            y_position = height - 1 * inch
            # (Opcional: redibujar encabezados en página nueva)
    
        # 2. Dibujar Fila Principal de la Venta
        p.setFont("Helvetica-Bold", 8)
        if hasattr(sale, 'user') and sale.user:
            user_name = f"{sale.user.first_name} {sale.user.last_name}"
        else:
            user_name = "N/A"
        fecha = sale.created_at.strftime('%Y-%m-%d')
        total_text = f"Bs. {sale.total_amount:,.2f}"
        status_text = getattr(sale, 'status', 'N/A')
        item_count = sale.details.count()

        p.drawString(0.5 * inch, y_position, str(sale.id))
        p.drawString(1 * inch, y_position, fecha)
        p.drawString(2.5 * inch, y_position, user_name[:25])
        p.drawString(5.0 * inch, y_position, total_text)
        p.drawString(6.0 * inch, y_position, status_text[:15])
        p.drawString(7.0 * inch, y_position, str(item_count))
        
        y_position -= line_height_venta
        
        # 3. Dibujar Detalles (sub-bucle)
        p.setFont("Helvetica", detalle_font_size)
        for detail in sale.details.all():
            if y_position < 1 * inch:
                p.showPage()
                p.setFont("Helvetica", detalle_font_size) # Re-establecer fuente
                y_position = height - 1 * inch
            
            detalle_texto = f"   - {detail.quantity}x {detail.product.name} (Bs. {detail.price_at_purchase:,.2f} c/u)"
            p.drawString(1.1 * inch, y_position, detalle_texto[:80])
            y_position -= line_height_detalle
        
        count += 1
        y_position -= 0.05 * inch
    
    # Total de registros
    p.setFont("Helvetica-Bold", 10)
    if y_position < 1.5 * inch:
        p.showPage()
        y_position = height - 1 * inch
    y_position -= 0.3 * inch
    p.drawString(0.5 * inch, y_position, f"Total de ventas filtradas: {count}")
    
    p.showPage()
    p.save()
    
    pdf_content = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_ventas_detallado.pdf"'
    logger.warning("PDF detallado generado exitosamente.")
    return response


def generate_sales_csv(queryset) -> HttpResponse:
    """
    Toma un queryset de Ventas y genera un CSV.
    """
    logger.warning("Generando CSV...")
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_ventas_filtrado.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID_Venta', 'Fecha', 'Cliente', 'Email', 'Monto_Total', 'Estado', 'Detalle_Productos'])

    # Asegúrate de que el queryset traiga los detalles
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

        writer.writerow([sale.id, sale.created_at.strftime('%Y-%m-%d %H:%M:%S'), user_name, user_email, total_amount, status, product_details])
    
    logger.warning("CSV generado exitosamente.")
    return response

def generate_sales_excel(queryset) -> HttpResponse:
    """
    Stub para la generación de Excel.
    """
    logger.warning("Generación de Excel no implementada.")
    return HttpResponse("Formato Excel aún no implementado.", status=501)