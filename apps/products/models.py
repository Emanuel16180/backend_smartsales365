# apps/products/models.py

import uuid
from datetime import timedelta
from django.db import models
from django.conf import settings
from django.utils import timezone

class Category(models.Model):
    
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL, # Si se borra el padre, los hijos se vuelven "raíz"
        null=True, 
        blank=True,
        related_name='children', # Para encontrar los hijos: categoria.children.all()
        verbose_name="Categoría Padre"
    )

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} -> {self.name}"
        return self.name

class WarrantyProvider(models.Model):

    name = models.CharField(max_length=150, verbose_name="Nombre de la Empresa")
    contact_email = models.EmailField(blank=True, verbose_name="Email de Contacto")
    contact_phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")

    class Meta:
        verbose_name = "Proveedor de Garantía"
        verbose_name_plural = "Proveedores de Garantía"

    def __str__(self):
        return self.name

class Warranty(models.Model):

    provider = models.ForeignKey(
        WarrantyProvider, 
        on_delete=models.PROTECT,  # No borrar la empresa si aún ofrece garantías
        related_name='warranties',
        verbose_name="Proveedor"
    )
    title = models.CharField(max_length=200, verbose_name="Título")
    terms = models.TextField(verbose_name="Términos y Condiciones")
    duration_days = models.PositiveIntegerField(
        verbose_name="Duración (días)",
        help_text="Duración total en días (ej. 365 para 1 año, 730 para 2 años)"
    )

    class Meta:
        verbose_name = "Plantilla de Garantía"
        verbose_name_plural = "Plantillas de Garantía"

    def __str__(self):
        return f"{self.title} ({self.duration_days} días)"


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name


class Product(models.Model):
    
    name = models.CharField(max_length=255, verbose_name="Nombre del Producto")
    description = models.TextField(blank=True, verbose_name="Descripción")
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Precio"
    )
    stock = models.PositiveIntegerField(default=0, verbose_name="Stock")  
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, # Si se borra la categoría, el producto queda "Sin Categoría"
        null=True, 
        blank=True,
        related_name='products',
        verbose_name="Categoría"
    )
    warranty = models.ForeignKey(
        Warranty, 
        on_delete=models.SET_NULL, # Si se borra la plantilla, el producto queda sin garantía
        null=True, 
        blank=True,
        related_name='products',
        verbose_name="Plantilla de Garantía"
    )
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products', verbose_name="Marca")
    image_url = models.URLField(
        max_length=1024, 
        null=True, 
        blank=True, 
        verbose_name="URL de Imagen"
    )

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self):
        return self.name
