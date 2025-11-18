# apps/ai/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models.functions import TruncMonth
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

# Importamos AMBAS funciones
from .prediction_service import predict_next_month_sales, predict_top_products
from apps.sales.models import Sale, SaleDetail


# --- BLOQUE 1: VENTAS GENERALES (Monto) ---

class HistoricalSalesView(APIView):
    """Dashboard: Ventas históricas agrupadas por mes (Gráfica de líneas)"""
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        sales_data = Sale.objects.filter(status=Sale.SaleStatus.COMPLETED)\
            .annotate(month=TruncMonth('created_at'))\
            .values('month')\
            .annotate(total=Sum('total_amount'))\
            .values('month', 'total')\
            .order_by('month')
            
        formatted_data = [
            {
                "date": item['month'].strftime('%Y-%m-%d'),
                "total_sales_bob": item['total']
            } for item in sales_data
        ]
        return Response(formatted_data)

class PredictionSalesView(APIView):
    """Dashboard: Predicción del MONTO TOTAL para el próximo mes"""
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        prediction = predict_next_month_sales()
        if "error" in prediction:
            return Response(prediction, status=500)
        return Response(prediction)


# --- BLOQUE 2: VENTAS POR PRODUCTO (Top 3) ---

class TopProductsPredictionView(APIView):
    """Dashboard: Predicción de los 3 productos más vendidos"""
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        top_3 = predict_top_products()
        if isinstance(top_3, dict) and "error" in top_3:
             return Response(top_3, status=500)
        return Response(top_3)

class TopProductsLastMonthView(APIView):
    """Dashboard: Top 3 productos reales del mes pasado"""
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        today = timezone.now()
        first_this_month = today.replace(day=1)
        last_month_end = first_this_month - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        
        top_products = SaleDetail.objects.filter(
            sale__status='COMPLETED',
            sale__created_at__gte=last_month_start,
            sale__created_at__lte=last_month_end
        ).values('product__name', 'product__image_url')\
         .annotate(total_sold=Sum('quantity'))\
         .order_by('-total_sold')[:3]
         
        return Response(list(top_products))