from rest_framework import serializers
from .models import Sale, SaleDetail, ActivatedWarranty, Coupon, Delivery
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

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = '__all__'

class ValidateCouponSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=20)

class DeliveryInfoSerializer(serializers.Serializer):
    address = serializers.CharField(required=True)
    latitude = serializers.FloatField(required=True)
    longitude = serializers.FloatField(required=True)
    description = serializers.CharField(required=False, allow_blank=True)

class DeliveryProductSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = SaleDetail
        fields = ['product_name', 'quantity']

# 2. Serializer para mostrar al Repartidor (Output)
class DeliveryOrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='sale.user.full_name', read_only=True)
    customer_phone = serializers.CharField(source='sale.user.phone_number', read_only=True) # Si tienes el campo phone
    sale_total = serializers.DecimalField(source='sale.total_amount', max_digits=10, decimal_places=2, read_only=True)
    
    # --- AQUÍ LA MAGIA: Listamos los productos ---
    products = serializers.SerializerMethodField()

    class Meta:
        model = Delivery
        fields = [
            'id', 
            'status', 
            'address', 
            'latitude', 
            'longitude', 
            'description', 
            'customer_name', 
            'customer_phone', 
            'sale_total', 
            'products',  # <--- No olvides agregar este campo aquí
            'created_at'
        ]

    def get_products(self, obj):
        # obj es la instancia de Delivery.
        # Accedemos a la Venta (obj.sale) y luego a sus detalles.
        # Nota: Django usa 'saledetail_set' por defecto para relaciones inversas.
        details = SaleDetail.objects.filter(sale=obj.sale) 
        return DeliveryProductSerializer(details, many=True).data