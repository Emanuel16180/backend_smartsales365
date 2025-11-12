from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from apps.products.models import Product, Warranty

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