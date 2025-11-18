# apps/products/views.py
from rest_framework import viewsets
from rest_framework import generics
from rest_framework.views import APIView            
from rest_framework.response import Response         
from rest_framework import status                    
from rest_framework.permissions import IsAuthenticated 
from django.shortcuts import get_object_or_404      
from .models import Category, WarrantyProvider, Warranty, Product
from .serializers import (
    CategorySerializer, WarrantyProviderSerializer, 
    WarrantySerializer, ProductSerializer
)
from apps.users.permissions import IsEmployeeOrReadOnly # <-- IMPORTAMOS EL PERMISO
from .models import Brand
from apps.products.serializers import BrandSerializer
from .models import Product, Favorite
from .serializers import FavoriteSerializer


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

class FavoriteListView(generics.ListAPIView):
    """
    Devuelve la lista de productos favoritos del usuario logueado.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = FavoriteSerializer

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).order_by('-created_at')


class ToggleFavoriteView(APIView):
    """
    Si el producto ya es favorito, lo quita. Si no lo es, lo agrega.
    Body JSON: { "product_id": 15 }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({"error": "Se requiere 'product_id'"}, status=400)

        product = get_object_or_404(Product, id=product_id)
        
        # Buscamos si ya existe
        favorite = Favorite.objects.filter(user=request.user, product=product).first()

        if favorite:
            # Si existe, lo borramos (Quitar de favoritos)
            favorite.delete()
            return Response(
                {"message": "Eliminado de favoritos", "is_favorite": False}, 
                status=200
            )
        else:
            # Si no existe, lo creamos (Agregar a favoritos)
            Favorite.objects.create(user=request.user, product=product)
            return Response(
                {"message": "Añadido a favoritos", "is_favorite": True}, 
                status=201
            )