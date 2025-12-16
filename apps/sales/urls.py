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

    # --- CUPONES (Configuración Manual / Sin Router) ---
    
    # 1. Validar Cupón (Poner ANTES del ID para evitar conflictos)
    #    POST /api/v1/sales/coupons/validate/
    path('coupons/validate/', views.CouponViewSet.as_view({
        'post': 'validate'
    }), name='coupon-validate'),

    # 2. Listar y Crear Cupones
    #    GET /api/v1/sales/coupons/  -> Ver lista
    #    POST /api/v1/sales/coupons/ -> Crear uno nuevo
    path('coupons/', views.CouponViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='coupon-list'),

    # 3. Ver, Editar y Borrar un Cupón específico por ID
    #    GET /api/v1/sales/coupons/5/    -> Ver detalle
    #    PUT /api/v1/sales/coupons/5/    -> Editar
    #    DELETE /api/v1/sales/coupons/5/ -> Borrar
    path('coupons/<int:pk>/', views.CouponViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='coupon-detail'),
]