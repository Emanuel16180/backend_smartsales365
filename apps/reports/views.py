import csv 
import io
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone 
from .parser import parse_prompt_to_filters
from .services import generate_sales_pdf, generate_sales_csv, generate_sales_excel, render_to_pdf

# Importaciones de otras apps
from apps.sales.models import Sale
from apps.sales.filters import SaleFilter
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
        
        # Queryset base con prefetch
        queryset = Sale.objects.all().order_by('-created_at').prefetch_related(
            'user',
            'details__product' 
        )
        
        # Aplicamos los filtros
        filterset = SaleFilter(filtering_params, queryset=queryset)
        
        if not filterset.is_valid():
            logger.error(f"Filtro inválido: {filterset.errors}")
            return Response(filterset.errors, status=400)

        filtered_queryset = filterset.qs
        
        # === CAMBIO PRINCIPAL: Usar las funciones de services.py ===
        if report_format == 'csv':
            logger.warning("Llamando a generate_sales_csv()...")
            return generate_sales_csv(filtered_queryset)
            
        elif report_format == 'pdf':
            logger.warning("Llamando a generate_sales_pdf() [DISEÑO MODERNO]...")
            return generate_sales_pdf(filtered_queryset)
            
        elif report_format == 'excel':
            logger.warning("Llamando a generate_sales_excel()...")
            return generate_sales_excel(filtered_queryset)
            
        else:
            logger.warning(f"Formato '{report_format}' no soportado.")
            return Response({
                "error": "Formato no soportado. Usa report_type=csv, report_type=pdf o report_type=excel."
            }, status=400)


class SaleReportPDFView(APIView):
    """
    Vista legacy que usa xhtml2pdf (render_to_pdf)
    """
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
    permission_classes = [IsAdminUser]

    def post(self, request):
        prompt_text = request.data.get('prompt', None)
        if not prompt_text:
            return Response({"error": "No se proporcionó un 'prompt'."}, status=400)
            
        logger.warning(f"Prompt dinámico recibido: {prompt_text}")

        # Traducir el prompt a parámetros de filtro
        try:
            params = parse_prompt_to_filters(prompt_text)
            logger.warning(f"Prompt parseado a params: {params}")
            
            if "error" in params:
                return Response({
                    "error": f"Error al interpretar el prompt (IA): {params['error']}"
                }, status=500)
                
        except Exception as e:
            logger.error(f"Error parseando prompt: {e}")
            return Response({
                "error": f"Error crítico al interpretar el prompt: {e}"
            }, status=500)

        # Extraer el formato y los filtros
        report_type = params.pop('report_type', 'pdf')
        
        # Aplicar los filtros
        queryset = Sale.objects.all().order_by('-created_at')
        filterset = SaleFilter(params, queryset=queryset)
        
        if not filterset.is_valid():
            return Response(filterset.errors, status=400)

        filtered_queryset = filterset.qs

        # Generar el archivo usando las funciones de services.py
        if report_type == 'pdf':
            logger.warning("Generando PDF dinámico con diseño moderno...")
            return generate_sales_pdf(filtered_queryset)
        elif report_type == 'csv':
            return generate_sales_csv(filtered_queryset)
        elif report_type == 'excel':
            return generate_sales_excel(filtered_queryset)
        else:
            return Response({
                "error": f"Formato '{report_type}' no soportado."
            }, status=400)