# apps/ai/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Endpoint para las gráficas de ventas pasadas
    path('dashboard/historical-sales/', 
         views.HistoricalSalesView.as_view(), 
         name='historical-sales'),
         
    # Endpoint para la predicción del próximo mes
    path('dashboard/future-prediction/', 
         views.PredictionSalesView.as_view(), 
         name='future-prediction'),
]