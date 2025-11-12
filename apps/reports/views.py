import csv 
import io
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone 
from .services import render_to_pdf
from .parser import parse_prompt_to_filters
from .services import generate_sales_pdf, generate_sales_csv, generate_sales_excel

# --- LIBRERÍA DE PDF (ReportLab - Python Puro) ---
from reportlab.pdfgen import canvas         
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

# Importaciones de otras apps
from apps.sales.models import Sale
from apps.sales.filters import SaleFilter # <-- Usamos el filtro actualizado
from .utils import format_sale_details_for_csv 

# Configura el logger
logger = logging.getLogger(__name__)


class AdminReportView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        
        logger.warning("--- ADMIN REPORT VIEW: GET INICIADO ---")
        
        # Usamos 'report_type' para evitar conflictos con DRF
        report_format = request.query_params.get('report_type', 'csv').lower()
        
        logger.warning(f"Query params RECIBIDOS: {request.query_params}")
        logger.warning(f"Formato detectado: {report_format}")

        # Copiamos los params y eliminamos 'report_type'
        filtering_params = request.query_params.copy()
        filtering_params.pop('report_type', None)
        logger.warning(f"Params para FILTRADO: {filtering_params}")
        
        # --- (ACTUALIZADO) Usamos el mismo Queryset que AdminSaleListView ---
        # Esto nos da los 'details__product' eficientemente
        queryset = Sale.objects.all().order_by('-created_at').prefetch_related(
            'user',
            'details__product' 
        )
        
        # Aplicamos los filtros potentes de SaleFilter
        filterset = SaleFilter(filtering_params, queryset=queryset)
        
        if not filterset.is_valid():
            logger.error(f"Filtro inválido: {filterset.errors}")
            return Response(filterset.errors, status=400)

        filtered_queryset = filterset.qs
        
        
        if report_format == 'csv':
            logger.warning("Generando CSV...")
            # --- Lógica de CSV (OK) ---
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="reporte_ventas_filtrado.csv"'
            
            # (El CSV ya incluía el detalle, así que esto funcionará)
            writer = csv.writer(response)
            writer.writerow(['ID_Venta', 'Fecha', 'Cliente', 'Email', 'Monto_Total', 'Estado', 'Detalle_Productos'])

            for sale in filtered_queryset:
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
            
        elif report_format == 'pdf':
            logger.warning("Generando PDF (ReportLab)...")
            
            # --- (LÓGICA DE PDF CON DETALLES) ---
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            
            p.setFont("Helvetica-Bold", 16)
            p.drawString(1 * inch, height - 1 * inch, "REPORTE DE VENTAS")
            
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
            # Definir un tamaño de fuente más pequeño para los detalles
            detalle_font_size = 7
            line_height_detalle = 0.18 * inch
            line_height_venta = 0.25 * inch
            
            for sale in filtered_queryset:
                # 1. Chequear espacio para la venta principal + al menos 1 detalle
                if y_position < (1 * inch + line_height_venta + line_height_detalle):
                    p.showPage()
                    p.setFont("Helvetica", 8)
                    y_position = height - 1 * inch # Reiniciar en página nueva
            
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
                    if y_position < 1 * inch: # Chequeo de página por cada detalle
                        p.showPage()
                        p.setFont("Helvetica", detalle_font_size)
                        y_position = height - 1 * inch
                    
                    detalle_texto = f"   - {detail.quantity}x {detail.product.name} (Bs. {detail.price_at_purchase:,.2f} c/u)"
                    p.drawString(1.1 * inch, y_position, detalle_texto[:80]) # Acortar si es muy largo
                    y_position -= line_height_detalle
                
                count += 1
                y_position -= 0.05 * inch # Pequeño espacio extra entre ventas
            
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
            
        else:
            logger.warning(f"Formato '{report_format}' no soportado.")
            return Response({"error": "Formato no soportado. Usa report_type=csv o report_type=pdf."}, status=400)

# ... (Tu clase SaleReportPDFView se queda igual, ya que es un endpoint separado) ...
class SaleReportPDFView(APIView):
    def get(self, request):
        context = {
            'filters': request.GET.dict(),
            'current_date': timezone.now(),
            'sales_data': [],
        }
        pdf_bytes = render_to_pdf('reports/sale_report.html', context)
        if not pdf_bytes:
            return Response({'detail': 'Error generando PDF'}, status=500)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'
        return response

class DynamicReportView(APIView):
    """
    Endpoint para generar reportes dinámicos
    basados en un prompt de texto (o voz convertida a texto).
    """
    permission_classes = [IsAdminUser] # Recomiendo IsAdminUser para esto

    def post(self, request):
        prompt_text = request.data.get('prompt', None)
        if not prompt_text:
            return Response({"error": "No se proporcionó un 'prompt'."}, status=400)
            
        logger.warning(f"Prompt dinámico recibido: {prompt_text}")

        # 2. "Traducir" el prompt a parámetros de filtro
        try:
            params = parse_prompt_to_filters(prompt_text)
            logger.warning(f"Prompt parseado a params: {params}")
            
            # (NUEVO) Manejo de error de la API
            if "error" in params:
                return Response({"error": f"Error al interpretar el prompt (IA): {params['error']}"}, status=500)
                
        except Exception as e:
            logger.error(f"Error parseando prompt: {e}")
            return Response({"error": f"Error crítico al interpretar el prompt: {e}"}, status=500)

        # 3. Extraer el formato y los filtros
        report_type = params.pop('report_type', 'pdf')
        
        # 4. Aplicar los filtros (¡REUTILIZANDO SaleFilter!)
        queryset = Sale.objects.all().order_by('-created_at') # No prefetch aquí, el servicio lo hará
        filterset = SaleFilter(params, queryset=queryset)
        
        if not filterset.is_valid():
            return Response(filterset.errors, status=400)

        filtered_queryset = filterset.qs

        # 5. Generar el archivo correspondiente
        # (Las funciones de servicio ya hacen el prefetch_related)
        if report_type == 'pdf':
            return generate_sales_pdf(filtered_queryset)
        elif report_type == 'csv':
            return generate_sales_csv(filtered_queryset)
        elif report_type == 'excel':
            return generate_sales_excel(filtered_queryset)
        else:
            return Response({"error": f"Formato '{report_type}' no soportado."}, status=400)