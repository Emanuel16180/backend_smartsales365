from django.urls import path
from .views import (
    RegisterView, 
    UserProfileView, 
    CustomTokenObtainPairView,
    TokenRefreshView,
    CustomerListView
)

urlpatterns = [
    # --- Autenticación ---
    
    # POST /api/v1/users/login/
    # (Envía 'email' y 'password', devuelve 'access' y 'refresh' token)
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # POST /api/v1/users/login/refresh/
    # (Envía 'refresh' token, devuelve nuevo 'access' token)
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # --- Gestión de Usuarios ---
    
    # POST /api/v1/users/register/
    path('register/', RegisterView.as_view(), name='user_register'),
    
    # GET, PUT, PATCH /api/v1/users/me/
    # (Requiere token de acceso en el header 'Authorization: Bearer <token>')
    path('me/', UserProfileView.as_view(), name='user_profile'),

    path('admin/customers/', CustomerListView.as_view(), name='admin-customer-list'),
]