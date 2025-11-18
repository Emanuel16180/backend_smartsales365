# apps/ai/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # --- GRÁFICAS GENERALES ---
    path('dashboard/historical-sales/', 
         views.HistoricalSalesView.as_view(), 
         name='historical-sales'),
         
    path('dashboard/future-prediction/', 
         views.PredictionSalesView.as_view(), 
         name='future-prediction'),

    # --- TOP PRODUCTOS ---
    path('dashboard/top-prediction/', 
         views.TopProductsPredictionView.as_view(), 
         name='top-prediction'),
         
    path('dashboard/top-last-month/', 
         views.TopProductsLastMonthView.as_view(), 
         name='top-last-month'),
]