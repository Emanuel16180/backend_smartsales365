# apps/products/views.py
from rest_framework import viewsets
from rest_framework import generics
from .models import Category, WarrantyProvider, Warranty, Product
from .serializers import (
    CategorySerializer, WarrantyProviderSerializer, 
    WarrantySerializer, ProductSerializer
)
from apps.users.permissions import IsEmployeeOrReadOnly # <-- IMPORTAMOS EL PERMISO
from .models import Brand
from apps.products.serializers import BrandSerializer

# --- Vistas para el Catálogo de Productos ---

class CategoryViewSet(viewsets.ModelViewSet):
    """
    Endpoint para Categorías (CRUD).
    - LECTURA: Todos
    - ESCRITURA: Solo Empleados
    """
    queryset = Category.objects.filter(parent=None) # Mostramos solo las de nivel raíz
    serializer_class = CategorySerializer
    permission_classes = [IsEmployeeOrReadOnly] # <-- APLICADO

class WarrantyProviderViewSet(viewsets.ModelViewSet):
    """
    Endpoint para Proveedores de Garantía (CRUD).
    - LECTURA: Todos
    - ESCRITURA: Solo Empleados
    """
    queryset = WarrantyProvider.objects.all()
    serializer_class = WarrantyProviderSerializer
    permission_classes = [IsEmployeeOrReadOnly] # <-- APLICADO

class WarrantyViewSet(viewsets.ModelViewSet):
    """
    Endpoint para Plantillas de Garantía (CRUD).
    - LECTURA: Todos
    - ESCRITURA: Solo Empleados
    """
    queryset = Warranty.objects.all()
    serializer_class = WarrantySerializer
    permission_classes = [IsEmployeeOrReadOnly] # <-- APLICADO

class ProductViewSet(viewsets.ModelViewSet):
    """
    Endpoint para Productos (CRUD).
    - LECTURA: Todos (con filtrado)
    - ESCRITURA: Solo Empleados
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsEmployeeOrReadOnly] # <-- APLICADO
    
    # --- ¡FILTRADO! ---
    # Esto activa django-filter para este ViewSet
    filterset_fields = {
        'category': ['exact'], # Filtra por ID de categoría
        'category__parent': ['exact'], # Filtra por ID de la categoría padre
        'price': ['gte', 'lte'], # Filtra por precio (ej. price__gte=100)
    }

class BrandListCreateView(generics.ListCreateAPIView):
    """ Listar todas las marcas (ReadOnly para todos) o crear una nueva (solo Employee). """
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    # Aplicamos el permiso que permite GET a todos y POST solo a Empleados
    permission_classes = [IsEmployeeOrReadOnly] 


class BrandRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """ Obtener detalles, actualizar o eliminar una marca específica (solo Employee). """
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    # Aplicamos el permiso que permite ver a todos y editar/borrar solo a Empleados
    permission_classes = [IsEmployeeOrReadOnly]