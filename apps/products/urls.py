# apps/products/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # --- Rutas de Productos ---
    path('products/', 
         views.ProductViewSet.as_view({
             'get': 'list',      # GET a /products/ -> lista de productos
             'post': 'create'    # POST a /products/ -> crear producto
         }), 
         name='product-list'),
    
    path('products/<int:pk>/', 
         views.ProductViewSet.as_view({
             'get': 'retrieve',       # GET a /products/1/ -> ver producto 1
             'put': 'update',       # PUT a /products/1/ -> actualizar producto 1
             'patch': 'partial_update', # PATCH a /products/1/ -> actualizar parcialmente
             'delete': 'destroy'      # DELETE a /products/1/ -> borrar producto 1
         }), 
         name='product-detail'),

    # --- Rutas de Categorías ---
    path('categories/', 
         views.CategoryViewSet.as_view({
             'get': 'list', 
             'post': 'create'
         }), 
         name='category-list'),
    
    path('categories/<int:pk>/', 
         views.CategoryViewSet.as_view({
             'get': 'retrieve', 
             'put': 'update', 
             'patch': 'partial_update', 
             'delete': 'destroy'
         }), 
         name='category-detail'),

    # --- Rutas de Plantillas de Garantía ---
    path('warranties/', 
         views.WarrantyViewSet.as_view({
             'get': 'list', 
             'post': 'create'
         }), 
         name='warranty-list'),
    
    path('warranties/<int:pk>/', 
         views.WarrantyViewSet.as_view({
             'get': 'retrieve', 
             'put': 'update', 
             'patch': 'partial_update', 
             'delete': 'destroy'
         }), 
         name='warranty-detail'),

    # --- Rutas de Proveedores de Garantía ---
    path('providers/', 
         views.WarrantyProviderViewSet.as_view({
             'get': 'list', 
             'post': 'create'
         }), 
         name='provider-list'),
    
    path('providers/<int:pk>/', 
         views.WarrantyProviderViewSet.as_view({
             'get': 'retrieve', 
             'put': 'update', 
             'patch': 'partial_update', 
             'delete': 'destroy'
         }), 
         name='provider-detail'),


    path('brands/', views.BrandListCreateView.as_view(), name='brand-list-create'),
    path('brands/<int:pk>/', views.BrandRetrieveUpdateDestroyView.as_view(), name='brand-detail'),
]