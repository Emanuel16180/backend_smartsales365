from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from apps.products.models import Product, Warranty
from django.conf import settings

class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True, verbose_name="Código")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Descuento (Bs)")
    active = models.BooleanField(default=True, verbose_name="¿Activo?")
    usage_limit = models.PositiveIntegerField(default=1, verbose_name="Límite de usos")
    used_count = models.PositiveIntegerField(default=0, verbose_name="Veces usado")
    expiration_date = models.DateTimeField(null=True, blank=True, verbose_name="Fecha Expiración")

    def __str__(self):
        return f"{self.code} -Bs.{self.discount_amount}"

    @property
    def is_valid(self):
        # Verifica si está activo, si no ha expirado y si le quedan usos
        from django.utils import timezone
        now = timezone.now()
        
        if not self.active:
            return False
        if self.used_count >= self.usage_limit:
            return False
        if self.expiration_date and now > self.expiration_date:
            return False
        return True

# Modelo 1: La Venta (u Orden)
class Sale(models.Model):
    class SaleStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente'
        COMPLETED = 'COMPLETED', 'Completada'
        FAILED = 'FAILED', 'Fallida'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, # No borrar la venta si se borra el usuario
        null=True,
        related_name='sales'
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20, 
        choices=SaleStatus.choices, 
        default=SaleStatus.PENDING
    )
    stripe_payment_intent_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    
    def __str__(self):
        return f"Venta {self.id} - {self.user.email} - {self.status}"

# Modelo 2: El Detalle (los productos de la venta)
class SaleDetail(models.Model):
    sale = models.ForeignKey(Sale, related_name='details', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='sale_details', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2) # Guarda el precio al momento de la compra

    def __str__(self):
        return f"{self.quantity} x {self.product.name} en Venta {self.sale.id}"

# Modelo 3: La Garantía Activada
class ActivatedWarranty(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='activated_warranties', 
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    sale = models.ForeignKey(Sale, related_name='activated_warranties', on_delete=models.CASCADE)
    warranty_template = models.ForeignKey(Warranty, on_delete=models.PROTECT) # La plantilla de garantía
    start_date = models.DateField(auto_now_add=True)
    expiration_date = models.DateField()

    def save(self, *args, **kwargs):
        # Lógica de activación:
        # Al guardar, calcula la fecha de expiración
        if not self.id: # Solo al crear
            duration_days = self.warranty_template.duration_days
            self.expiration_date = timezone.now().date() + timedelta(days=duration_days)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Garantía de {self.product.name} para {self.user.email} (Vence: {self.expiration_date})"

class Delivery(models.Model):
    class DeliveryStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente de Asignación'
        ASSIGNED = 'ASSIGNED', 'Asignado a Repartidor'
        IN_TRANSIT = 'IN_TRANSIT', 'En Camino'
        DELIVERED = 'DELIVERED', 'Entregado'
        FAILED = 'FAILED', 'No se pudo entregar'

    # Relación 1 a 1 con la Venta (Una venta tiene una nota de entrega)
    sale = models.OneToOneField(Sale, on_delete=models.CASCADE, related_name='delivery_note')
    
    # El repartidor asignado (puede ser nulo al principio)
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='assigned_deliveries'
    )

    # Datos de ubicación
    address = models.CharField(max_length=255, verbose_name="Dirección Física")
    latitude = models.FloatField(verbose_name="Latitud")
    longitude = models.FloatField(verbose_name="Longitud")
    description = models.TextField(blank=True, null=True, verbose_name="Detalles de la casa/referencias")
    
    status = models.CharField(
        max_length=20, 
        choices=DeliveryStatus.choices, 
        default=DeliveryStatus.PENDING
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Entrega #{self.id} para Venta #{self.sale.id} ({self.status})"