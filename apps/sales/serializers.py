from rest_framework import serializers
from .models import Sale, SaleDetail, ActivatedWarranty
from apps.products.models import Product
from apps.users.serializers import UserSerializer  # (Ajusta si tu serializer de User está en otra parte)

# --- Serializers de Salida (Output) ---

class ProductLiteSerializer(serializers.ModelSerializer):
    """ Un serializer simple para mostrar info del producto anidada """
    class Meta:
        model = Product
        fields = ['id', 'name', 'image_url']

class SaleDetailSerializer(serializers.ModelSerializer):
    """ Serializer para los detalles de la venta (lo que va en la factura) """
    product = ProductLiteSerializer(read_only=True)
    
    class Meta:
        model = SaleDetail
        fields = ['product', 'quantity', 'price_at_purchase']

class ActivatedWarrantySerializer(serializers.ModelSerializer):
    """ Serializer para ver las garantías activadas """
    product = ProductLiteSerializer(read_only=True)

    class Meta:
        model = ActivatedWarranty
        fields = ['product', 'start_date', 'expiration_date']

class SaleSerializer(serializers.ModelSerializer):
    """ Serializer para la lista "Mis Compras" """
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Sale
        fields = ['id', 'total_amount', 'status', 'created_at', 'item_count']
        
    def get_item_count(self, obj):
        # Cuenta cuántos items *totales* (no distintos) tuvo la compra
        return sum(detail.quantity for detail in obj.details.all())

class SaleDetailReceiptSerializer(serializers.ModelSerializer):
    """ Serializer para la vista de "Recibo" (Nota de Compra) """
    user = UserSerializer(read_only=True)
    details = SaleDetailSerializer(many=True, read_only=True)
    activated_warranties = ActivatedWarrantySerializer(many=True, read_only=True)

    class Meta:
        model = Sale
        fields = [
            'id', 'user', 'total_amount', 'status', 'created_at',
            'stripe_payment_intent_id', 'details', 'activated_warranties'
        ]

# --- Serializers de Entrada (Input) ---

class CartItemSerializer(serializers.Serializer):
    """ Valida cada item del carrito que envía el frontend """
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)