# apps/ai/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser # Solo admins pueden ver el dashboard
from django.db.models.functions import TruncMonth
from django.db.models import Sum
from .prediction_service import predict_next_month_sales
from apps.sales.models import Sale

class HistoricalSalesView(APIView):
    """
    Endpoint para el dashboard de ventas históricas.
    Agrupa las ventas por mes.
    """
    permission_classes = [IsAdminUser] # ¡Asegurado!

    def get(self, request, *args, **kwargs):
        # Usamos el ORM de Django para agrupar por mes
        sales_data = Sale.objects.filter(status=Sale.SaleStatus.COMPLETED)\
            .annotate(month=TruncMonth('created_at'))\
            .values('month')\
            .annotate(total=Sum('total_amount'))\
            .values('month', 'total')\
            .order_by('month')
            
        # Formatear para Chart.js
        formatted_data = [
            {
                "date": item['month'].strftime('%Y-%m-%d'),
                "total_sales_bob": item['total']
            } for item in sales_data
        ]
        
        return Response(formatted_data)

class PredictionSalesView(APIView):
    """
    Endpoint que llama al servicio de IA para obtener
    la predicción del próximo mes.
    """
    permission_classes = [IsAdminUser] # ¡Asegurado!

    def get(self, request, *args, **kwargs):
        # Llama a la función que carga el modelo y predice
        prediction = predict_next_month_sales()
        
        if "error" in prediction:
            return Response(prediction, status=500)
            
        return Response(prediction)