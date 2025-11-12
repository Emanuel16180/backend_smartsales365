from django.urls import path
from . import views

urlpatterns = [
    # Endpoint para el frontend
    path('create-payment-intent/', views.CreatePaymentIntentView.as_view(), name='create-payment-intent'),
    
    # Endpoint para que Stripe nos notifique
    path('webhook/', views.StripeWebhookView.as_view(), name='stripe-webhook'),
    
    # Endpoints para el cliente
    path('my-purchases/', views.MyPurchasesListView.as_view(), name='my-purchases'),
    path('receipt/<int:pk>/', views.ReceiptDetailView.as_view(), name='receipt-detail'),

    path('my-warranties/', views.MyWarrantiesListView.as_view(), name='my-warranties'),

    path('admin/all-sales/', views.AdminSaleListView.as_view(), name='admin-all-sales'),
]