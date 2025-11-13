import os
import django
import sys
import random
import uuid
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db import transaction

# --- Configuración de Django ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
# --- Fin Configuración ---

# Importa todos los modelos necesarios
from django.contrib.auth import get_user_model
from apps.products.models import Product, Warranty
from apps.sales.models import Sale, SaleDetail, ActivatedWarranty

User = get_user_model()

# --- (ACTUALIZADO) Configuración del Script ---
SALE_COUNT = 3000  # Cuántas ventas crear
DAYS_BACK = 1825   # Desde hace cuántos días (5 años)
# --- FIN ACTUALIZACIÓN ---

def create_historical_sales(count=SALE_COUNT):
    print(f"Iniciando la creación de {count} ventas históricas...")

    # 1. Obtener los "ingredientes"
    try:
        # (Ajusta el filtro si tus clientes no tienen rol 'CLIENT')
        users = list(User.objects.filter(role='CUSTOMER'))
        products = list(Product.objects.all())
    except Exception as e:
        print(f"Error: Parece que tu modelo User no tiene 'role'. Intentando con 'is_staff=False'.")
        users = list(User.objects.filter(is_staff=False))
        products = list(Product.objects.all())


    if not users:
        print("--- ¡ERROR! No se encontraron usuarios (clientes) en la BD. ---")
        print("Asegúrate de correr '02_populate_users.py' primero.")
        return
        
    if not products:
        print("--- ¡ERROR! No se encontraron productos en la BD. ---")
        print("Asegúrate de correr '03_populate_products.py' primero.")
        return

    # 2. Limpiar ventas antiguas (para que el script sea re-ejecutable)
    print("Limpiando ventas y garantías antiguas...")
    Sale.objects.all().delete()
    # (SaleDetail y ActivatedWarranty se borran en cascada)

    # 3. Definir el rango de fechas
    today = timezone.now()
    start_date = today - timedelta(days=DAYS_BACK)

    print(f"Creando ventas entre {start_date.date()} y {today.date()}...")
    
    created_count = 0
    # 4. Bucle principal de creación
    for i in range(count):
        # Envolvemos cada venta en una transacción. Si algo falla,
        # solo se revierte esta venta y el script continúa.
        try:
            with transaction.atomic():
                
                # A. Elegir un usuario y una fecha
                random_user = random.choice(users)
                random_days_ago = random.randint(0, DAYS_BACK) # Usará 1825
                sale_date = today - timedelta(days=random_days_ago)

                # B. Construir un "carrito"
                cart = []
                total_amount = Decimal('0.00')
                items_in_cart = random.randint(1, 4) # De 1 a 4 productos por venta

                for _ in range(items_in_cart):
                    product = random.choice(products)
                    quantity = random.randint(1, 3)

                    # ¡IMPORTANTE!
                    # Hacemos un chequeo de stock, pero NO reducimos el stock
                    # de los productos poblados. Así el script es re-ejecutable.
                    if product.stock < 5: # Si el producto tiene poco stock, no lo vendemos
                        continue
                    
                    price = product.price
                    total_amount += (price * quantity)
                    cart.append({"product": product, "quantity": quantity, "price": price})

                if not cart: # Si el carrito quedó vacío (ej. no había stock)
                    continue # Salta esta iteración

                # C. Crear la Venta (Sale)
                # (Usamos un UUID falso para el ID de Stripe)
                sale = Sale.objects.create(
                    user=random_user,
                    total_amount=total_amount,
                    status=Sale.SaleStatus.COMPLETED,
                    stripe_payment_intent_id=f"fake_sale_{uuid.uuid4()}"
                )
                
                # --- ¡Truco para fechas! ---
                # Sobrescribimos la fecha de creación (auto_now_add=True)
                sale.created_at = sale_date
                sale.save(update_fields=['created_at'])

                # D. Crear los Detalles y Garantías
                for item in cart:
                    product = item['product']
                    
                    SaleDetail.objects.create(
                        sale=sale,
                        product=product,
                        quantity=item['quantity'],
                        price_at_purchase=item['price']
                    )
                    
                    # Activar la garantía (si el producto tiene una)
                    if product.warranty:
                        aw = ActivatedWarranty.objects.create(
                            user=random_user,
                            product=product,
                            sale=sale,
                            warranty_template=product.warranty
                        )
                        
                        # --- ¡Truco para fechas (Garantía)! ---
                        duration = product.warranty.duration_days
                        aw.start_date = sale_date.date()
                        aw.expiration_date = sale_date.date() + timedelta(days=duration)
                        aw.save(update_fields=['start_date', 'expiration_date'])
                
                created_count += 1
                if created_count % 100 == 0:
                    print(f"    ... {created_count} ventas creadas ...")

        except Exception as e:
            # Si algo falla (ej. un producto sin garantía), solo lo reporta
            # y continúa con la siguiente venta.
            print(f"Error al crear venta {i}: {e}. Saltando.")
            
    print(f"\n--- ¡Proceso completado! Se crearon {created_count} ventas históricas. ---")

if __name__ == '__main__':
    create_historical_sales()