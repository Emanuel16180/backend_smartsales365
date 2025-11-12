import django_filters
from .models import Sale
from django_filters import DateFilter
from django.db.models import Q

class SaleFilter(django_filters.FilterSet):
    """
    Filtro personalizado para el endpoint de administrador de Ventas.
    """
    
    # 1. Filtro por Cliente (user__id)
    client_search = django_filters.CharFilter(
        method='filter_by_client_name_or_email',
        label="Buscar por Cliente (Nombre, Apellido o Email)"
    )

    # 2. Filtro por Mes y Año
    month = django_filters.NumberFilter(field_name='created_at__month')
    year = django_filters.NumberFilter(field_name='created_at__year')

    # 3. Filtro por Producto (busca en los SaleDetail)
    product_search = django_filters.CharFilter(
        method='filter_by_product_or_category', # <-- Usamos un método
        label="Buscar por Nombre de Producto o Categoría"
    )
    # 4. Filtro por Monto (Rango)
    monto_min = django_filters.NumberFilter(field_name='total_amount', lookup_expr='gte')
    monto_max = django_filters.NumberFilter(field_name='total_amount', lookup_expr='lte')

    #5. Filtro por Fecha (Rango)
    fecha_inicio = DateFilter(field_name='created_at', lookup_expr='gte')
    fecha_fin = DateFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Sale
        # Define los campos que se pueden filtrar exactamente (además de los personalizados)
        fields = ['status', 'client_search', 'month', 'year', 'product_search', 'monto_min', 'monto_max', 'fecha_inicio', 'fecha_fin']


    def filter_by_client_name_or_email(self, queryset, name, value):
        """
        Filtra el queryset por nombre, apellido o email.
        (ACTUALIZADO) Ahora soporta múltiples palabras (ej. "Ana Gomez").
        """
        if not value:
            return queryset
        
        # 1. Buscar por email (coincidencia simple)
        email_query = Q(user__email__icontains=value)
        
        # 2. Construir consulta de nombre (más compleja)
        # Divide la búsqueda por espacios (ej. "Ana Gomez" -> ["Ana", "Gomez"])
        name_parts = value.split()
        
        # Inicia una consulta "AND" vacía
        name_query = Q()
        
        for part in name_parts:
            # Añade una condición "AND" por cada parte
            # La parte ("Ana") debe estar en el nombre O en el apellido
            name_query &= (
                Q(user__first_name__icontains=part) |
                Q(user__last_name__icontains=part)
            )
        
        # 3. Combinar las búsquedas
        # Devuelve resultados que coincidan con el email O con la búsqueda de nombre
        return queryset.filter(email_query | name_query).distinct()

    def filter_by_product_or_category(self, queryset, name, value):
        """
        Filtra el queryset por nombre de producto O nombre de categoría
        en los detalles de la venta.
        """
        if not value:
            return queryset
        
        return queryset.filter(
            Q(details__product__name__icontains=value) |
            Q(details__product__category__name__icontains=value)
        ).distinct()