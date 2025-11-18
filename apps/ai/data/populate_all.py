# ====================================================================
# SCRIPT CONSOLIDADO: populate_all.py
# Une 01_populate_core, 02_populate_users, 03_populate_products y 04_populate_sales
# ====================================================================

import os
import django
import sys
import random
import uuid
import hashlib
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from faker import Faker

# ====================================================================
# 1. CONFIGURACIÓN DE ENTORNO Y DJANGO
# ====================================================================
print("Iniciando configuración de entorno Django...")
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
print("Configuración de Django completada.")
print("-" * 50)


# ====================================================================
# 2. IMPORTACIONES DE MODELOS
# ====================================================================
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except ImportError:
    # Fallback si get_user_model falla o no está configurado
    print("ADVERTENCIA: No se pudo usar get_user_model(). Usando 'User' de la app users.")
    from apps.users.models import User

# Modelos de products
from apps.products.models import Category, Brand, WarrantyProvider, Warranty, Product
# Modelos de sales (opcional)
try:
    from apps.sales.models import Sale, SaleDetail, ActivatedWarranty
    SALE_APP_EXISTS = True
except ImportError:
    SALE_APP_EXISTS = False
    print("ADVERTENCIA: La app 'sales' no fue importada, se omitirá la población de ventas.")
    
# Herramientas
fake = Faker('es_ES')


# ====================================================================
# 3. Mapeos y Variables Globales (del script 03)
# ====================================================================
LOREMFLICKR_BASE_URL = "https://loremflickr.com/{width}/{height}/{keyword}"
IMAGE_WIDTH = 640
IMAGE_HEIGHT = 480
SALE_COUNT = 3000
DAYS_BACK = 1825

CATEGORY_KEYWORD_MAP = {
    "Refrigeradores": "refrigerator",
    "Cocinas": "kitchen",
    "Lavadoras": "laundry",
    "Televisores": "television",
    "Audio y Video": "audio",
    "Computacion": "laptop",
    "Sofas y Sillones": "sofa",
    "Dormitorio": "bedroom",
    "Comedor": "diningroom",
    "Aires Acondicionados": "air,conditioner",
    "Ventiladores": "fan",
}

PRODUCT_MAP = {
    "Refrigeradores": [
        ("Refrigerador No-Frost {}L", "Refrigerador No-Frost de {} litros. Eficiencia energética A+, color {}."),
        ("Frigobar {}L", "Frigobar compacto de {} litros, ideal para oficina. Puerta reversible. Color {}."),
    ],
    "Cocinas": [
        ("Cocina {} Hornallas", "Cocina a gas de {} hornallas, con horno de gran capacidad y encendido eléctrico. Acero inoxidable."),
        ("Horno Microondas {}L", "Microondas digital de {}L de capacidad. Panel {} y 10 niveles de potencia."),
    ],
    "Lavadoras": [
        ("Lavadora Carga Frontal {}kg", "Lavadora automática Inverter, {}kg de capacidad, 8 programas de lavado. Color {}."),
        ("Lavadora Carga Superior {}kg", "Lavadora automática de {}kg, con tecnología Wobble para un lavado profundo. Color {}."),
    ],
    "Televisores": [
        ("Smart TV {} Pulgadas 4K", "Televisor inteligente {} pulgadas 4K UHD con HDR, sistema operativo {} y control por voz."),
        ("Smart TV {} Pulgadas FHD", "Televisor inteligente {} pulgadas Full HD con acceso a Netflix, YouTube y más."),
    ],
    "Audio y Video": [
        ("Equipo de Sonido {}W", "Minicomponente de {}W de potencia, con Bluetooth, USB y CD. Sonido X-Boom."),
        ("Barra de Sonido {} Canales", "Barra de sonido de {} canales con subwoofer inalámbrico y sonido Dolby Atmos."),
    ],
    "Computacion": [
        ("Laptop Core i{} {}GB RAM", "Laptop de 15.6\", procesador Core i{}, {}GB de RAM y {}GB SSD. Windows 11."),
        ("Monitor Gamer {} Pulgadas", "Monitor Curvo Gamer de {} pulgadas, 144Hz, 1ms de respuesta."),
    ],
    "Sofas y Sillones": [
        ("Sofá {} Cuerpos", "Sofá de {} cuerpos tapizado en tela de lino de alta resistencia, color {}."),
        ("Sillón Reclinable", "Sillón reclinable tipo {} tapizado en ecocuero, con sistema de masaje."),
    ],
    "Dormitorio": [
        ("Colchón {} Plazas", "Colchón ortopédico de {} plazas, con resortes pocket y capa de espuma viscoelástica."),
        ("Ropero {} Puertas", "Ropero de melamina color {}, {} puertas batientes y 2 cajones con rieles metálicos."),
    ],
    "Comedor": [
        ("Juego de Comedor {} Sillas", "Juego de comedor con mesa de {} y {} sillas de madera tapizadas en tela."),
    ],
    "Aires Acondicionados": [
        ("Aire Acondicionado Split {}BTU", "Aire Acondicionado tipo Split de {} BTU, modo frío/calor, con filtro antibacterial."),
    ],
    "Ventiladores": [
        ("Ventilador de Pie {} Pulgadas", "Ventilador de pie de {} pulgadas, 3 velocidades y oscilación automática. Base reforzada."),
    ]
}


# ====================================================================
# 4. FUNCIONES AUXILIARES
# ====================================================================

def generate_product_details(category_name, brand_name):
    """Genera un nombre y descripción coherentes basados en la categoría."""
    templates = PRODUCT_MAP.get(category_name)
    
    if not templates:
        name = f"Producto Genérico {brand_name}"
        desc = f"Una descripción genérica para {category_name.lower()}. {fake.text(max_nb_chars=100)}"
        return name, desc

    base_name, desc_template = random.choice(templates)
    
    try:
        if category_name == "Refrigeradores":
            liters = random.choice([250, 300, 380, 450])
            color = fake.color_name().lower()
            name = base_name.format(liters)
            desc = desc_template.format(liters, color)
        elif category_name == "Cocinas":
            items = random.choice([(4, 15, 'digital'), (6, 25, 'manual')])
            name = base_name.format(items[0] if "Hornallas" in base_name else items[1])
            desc = desc_template.format(items[0] if "Hornallas" in base_name else items[1], items[2])
        elif category_name == "Lavadoras":
            kg = random.choice([10, 12, 15, 18])
            color = fake.color_name().lower()
            name = base_name.format(kg)
            desc = desc_template.format(kg, color)
        elif category_name == "Televisores":
            pulgadas = random.choice([43, 50, 55, 65])
            so = random.choice(["Tizen", "WebOS", "Google TV"])
            name = base_name.format(pulgadas)
            desc = desc_template.format(pulgadas, so)
        elif category_name == "Audio y Video":
            potencia = random.choice([1000, 1500, 2000])
            canales = random.choice(["2.1", "5.1"])
            name = base_name.format(potencia if "W" in base_name else canales)
            desc = desc_template.format(potencia if "W" in base_name else canales)
        elif category_name == "Computacion":
            cpu = random.choice([3, 5, 7])
            ram = random.choice([8, 16, 32])
            ssd = random.choice([256, 512, 1024])
            pulgadas = random.choice([24, 27, 32])
            name = base_name.format(cpu, ram) if "Laptop" in base_name else base_name.format(pulgadas)
            desc = desc_template.format(cpu, ram, ssd) if "Laptop" in base_name else desc_template.format(pulgadas)
        elif category_name == "Sofas y Sillones":
            cuerpos = random.choice([2, 3])
            color = fake.color_name().lower()
            tipo = random.choice(["Relax", "Presidencial"])
            name = base_name.format(cuerpos) if "Cuerpos" in base_name else base_name
            desc = desc_template.format(cuerpos, color) if "Cuerpos" in base_name else desc_template.format(tipo)
        elif category_name == "Dormitorio":
            plazas = random.choice(["1.5", "2", "King"])
            color = fake.color_name().lower()
            puertas = random.choice([4, 6, 8])
            name = base_name.format(plazas) if "Colchón" in base_name else base_name.format(puertas)
            desc = desc_template.format(plazas) if "Colchón" in base_name else desc_template.format(color, puertas)
        elif category_name == "Comedor":
            sillas = random.choice([4, 6, 8])
            material = random.choice(["vidrio", "madera laqueada"])
            name = base_name.format(sillas)
            desc = desc_template.format(material, sillas)
        elif category_name == "Aires Acondicionados":
            btu = random.choice([9000, 12000, 18000])
            name = base_name.format(btu)
            desc = desc_template.format(btu)
        elif category_name == "Ventiladores":
            pulgadas = random.choice([16, 18, 20])
            name = base_name.format(pulgadas)
            desc = desc_template.format(pulgadas)
        else:
            name = base_name
            desc = desc_template

    except Exception:
        name = base_name.replace("{}", "")
        desc = desc_template.replace("{}", "")

    return f"{name} {brand_name}", desc


# ====================================================================
# 5. POBLACIÓN DEL NÚCLEO (Basado en 01_populate_core.py)
# ====================================================================

def setup_core_data():
    """Pobla Categorías, Marcas, Proveedores y Plantillas de Garantía."""
    print("## 1. Población del Núcleo (Core) 📦")
    print("Limpiando datos antiguos (Categorías, Marcas, Garantías)...")
    Category.objects.all().delete()
    Brand.objects.all().delete()
    Warranty.objects.all().delete()
    WarrantyProvider.objects.all().delete()

    # --- Categorías ---
    print("Poblando Categorías...")
    c_electro = Category.objects.create(name='Electrodomésticos')
    Category.objects.create(name='Refrigeradores', parent=c_electro)
    Category.objects.create(name='Cocinas', parent=c_electro)
    Category.objects.create(name='Lavadoras', parent=c_electro)
    
    c_tecno = Category.objects.create(name='Tecnología')
    Category.objects.create(name='Televisores', parent=c_tecno)
    Category.objects.create(name='Audio y Video', parent=c_tecno)
    Category.objects.create(name='Computacion', parent=c_tecno)

    c_muebles = Category.objects.create(name='Muebles')
    Category.objects.create(name='Sofas y Sillones', parent=c_muebles)
    Category.objects.create(name='Dormitorio', parent=c_muebles)
    Category.objects.create(name='Comedor', parent=c_muebles)

    c_clima = Category.objects.create(name='Climatización')
    Category.objects.create(name='Aires Acondicionados', parent=c_clima)
    Category.objects.create(name='Ventiladores', parent=c_clima)

    # --- Marcas ---
    print("Poblando Marcas...")
    marcas = ['Samsung', 'LG', 'Sony', 'Hisense', 'Mabe', 'Indurama', 'Oster', 'HP', 'Apple', 'Xiaomi', 'TCL', 'Electrolux', 'Bosch']
    random.shuffle(marcas) 
    for marca_nombre in marcas:
        Brand.objects.create(name=marca_nombre)

    # --- Proveedores de Garantía ---
    print("Poblando Proveedores de Garantía...")
    provider_names = [
        'Servicio Técnico Autorizado S.A.', 'Garantía Total Bolivia', 'ReparaFácil S.R.L.',
        'ElectroService Plus', 'Soluciones Hogar', 'ServiTec Autorizado', 'Asistencia Inmediata S.R.L.'
    ]
    providers = []
    for name in provider_names:
        provider = WarrantyProvider.objects.create(
            name=name,
            contact_email=fake.email(),
            contact_phone=fake.phone_number()
        )
        providers.append(provider)

    # --- Plantillas de Garantía ---
    print("Poblando Plantillas de Garantía...")
    Warranty.objects.create(title="Garantía Estándar (12 Meses)", terms="Cobertura estándar por 12 meses contra defectos de fábrica. No incluye daños por mal uso.", duration_days=365, provider_id=providers[0].id)
    Warranty.objects.create(title="Garantía Limitada (6 Meses)", terms="Cobertura de 180 días en partes y componentes principales. Excluye accesorios y consumibles.", duration_days=180, provider_id=providers[1].id)
    Warranty.objects.create(title="Garantía Extendida Motor/Compresor (2 Años)", terms="Cobertura especial de 2 años (730 días) exclusivamente para el motor o compresor del equipo.", duration_days=730, provider_id=providers[2].id)
    Warranty.objects.create(title="Garantía Básica (90 Días)", terms="Cubre fallas en componentes electrónicos básicos por 90 días. Mano de obra no incluida.", duration_days=90, provider_id=providers[3].id)
    
    print("\n--- ¡Núcleo poblado con éxito! ---")
    print("-" * 50)


# ====================================================================
# 6. POBLACIÓN DE USUARIOS (Basado en 02_populate_users.py)
# ====================================================================

def create_clients(count=70):
    """Crea usuarios con rol de cliente."""
    print(f"## 2. Población de Usuarios (Clientes) 🧑‍🤝‍🧑")
    print(f"Poblando {count} usuarios (clientes)...")
    
    emails_created = []

    for i in range(count):
        first_name = fake.first_name()
        last_name = fake.last_name()
        
        # Generación de email único y sencillo
        username_base = f"{first_name.lower().replace(' ', '')}{last_name.lower().replace(' ', '')[:3]}{i+1}"
        email = f"{username_base}@example.com"
        
        if User.objects.filter(email=email).exists():
            continue
            
        try:
            # Asume un campo 'role' (modelo personalizado)
            User.objects.create_user(
                email=email,
                password='password',
                first_name=first_name,
                last_name=last_name,
                role='CUSTOMER'
            )
        except TypeError:
            # Fallback para el modelo de usuario estándar de Django
            User.objects.create_user(
                email=email,
                password='password',
                first_name=first_name,
                last_name=last_name,
                is_staff=False,
                is_superuser=False,
                is_active=True
            )
        emails_created.append(email)

    print(f"\n--- ¡{count} Clientes creados con éxito! ---")
    if emails_created:
        print(f"Usuario de ejemplo: {emails_created[0]}")
    print("Contraseña para todos: password")
    print("-" * 50)


# ====================================================================
# 7. POBLACIÓN DE PRODUCTOS (Basado en 03_populate_products.py)
# ====================================================================

def create_products(count=50):
    """Crea productos con datos coherentes y URLs de imagen de relleno."""
    print(f"## 3. Población de Productos 🛍️")
    print(f"Poblando {count} productos...")

    # 1. Obtiene las dependencias
    brands = list(Brand.objects.all())
    warranties = list(Warranty.objects.all())
    categories = list(Category.objects.filter(parent__isnull=False)) # Solo categorías hijas

    if not all([brands, warranties, categories]):
        print("\n--- ¡ERROR! Asegúrate de que los datos Core se poblaron correctamente. ---")
        return

    # --- Limpieza ---
    print("Limpiando datos antiguos (Ventas y Productos)...")
    if SALE_APP_EXISTS:
        Sale.objects.all().delete()
    Product.objects.all().delete() 
    
    
    # --- Bucle de Creación ---
    for i in range(count):
        
        category_obj = random.choice(categories)
        brand_obj = random.choice(brands)
        warranty_obj = random.choice(warranties)

        # Genera Nombre y Descripción COHERENTES
        name, description = generate_product_details(category_obj.name, brand_obj.name)
        
        # Datos numéricos
        price = Decimal(random.uniform(500.0, 9000.0)).quantize(Decimal('0.01'))
        stock = random.randint(5, 40)
        
        # Construir la URL de la imagen
        category_name = category_obj.name
        keyword = CATEGORY_KEYWORD_MAP.get(category_name, 'product') 

        image_url = LOREMFLICKR_BASE_URL.format(
            width=IMAGE_WIDTH,
            height=IMAGE_HEIGHT,
            keyword=keyword
        )
        
        # Agregar un "seed" para forzar una nueva imagen
        seed_data = f"{name}-{category_obj.name}-{i}"
        seed_hash = hashlib.sha256(seed_data.encode()).hexdigest()[:10]
        image_url = f"{image_url}?lock={seed_hash}"

        
        # Crear el Producto
        Product.objects.create(
            name=name,
            description=description,
            price=price,
            stock=stock,
            category=category_obj,
            brand=brand_obj,
            warranty=warranty_obj,
            image_url=image_url
        )

    print(f"\n--- ¡{count} Productos creados con éxito! ---")
    print("-" * 50)


# ====================================================================
# 8. POBLACIÓN DE VENTAS (Basado en 04_populate_sales.py)
# ====================================================================

def create_historical_sales(count=SALE_COUNT):
    """Crea ventas históricas con detalles y activación de garantías."""
    if not SALE_APP_EXISTS:
        print("## 4. Población de Ventas Omitida ❌")
        print("La app 'sales' no fue importada. Omite este paso.")
        print("-" * 50)
        return

    print(f"## 4. Población de Ventas Históricas 🛒")
    print(f"Iniciando la creación de {count} ventas históricas...")

    # 1. Obtener los "ingredientes"
    try:
        users = list(User.objects.filter(role='CUSTOMER'))
    except Exception:
        users = list(User.objects.filter(is_staff=False))
        
    products = list(Product.objects.all())

    if not users:
        print("--- ¡ERROR! No se encontraron usuarios (clientes). ---")
        return
    if not products:
        print("--- ¡ERROR! No se encontraron productos. ---")
        return

    # 2. Limpiar ventas antiguas
    print("Limpiando ventas y garantías antiguas...")
    Sale.objects.all().delete()
    
    # 3. Definir el rango de fechas
    today = timezone.now()
    start_date = today - timedelta(days=DAYS_BACK)

    print(f"Creando ventas entre {start_date.date()} y {today.date()}...")
    
    created_count = 0
    # 4. Bucle principal de creación
    for i in range(count):
        try:
            with transaction.atomic():
                
                # A. Elegir un usuario y una fecha
                random_user = random.choice(users)
                random_days_ago = random.randint(0, DAYS_BACK)
                sale_date = today - timedelta(days=random_days_ago)

                # B. Construir un "carrito"
                cart = []
                total_amount = Decimal('0.00')
                items_in_cart = random.randint(1, 4)

                for _ in range(items_in_cart):
                    product = random.choice(products)
                    quantity = random.randint(1, 3)

                    if product.stock < 5:
                        continue
                    
                    price = product.price
                    total_amount += (price * quantity)
                    cart.append({"product": product, "quantity": quantity, "price": price})

                if not cart:
                    continue

                # C. Crear la Venta (Sale)
                sale = Sale.objects.create(
                    user=random_user,
                    total_amount=total_amount,
                    status=Sale.SaleStatus.COMPLETED,
                    stripe_payment_intent_id=f"fake_sale_{uuid.uuid4()}"
                )
                
                # Sobrescribimos la fecha de creación (Truco)
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
                    
                    if product.warranty:
                        aw = ActivatedWarranty.objects.create(
                            user=random_user,
                            product=product,
                            sale=sale,
                            warranty_template=product.warranty
                        )
                        
                        # Truco para fechas (Garantía)
                        duration = product.warranty.duration_days
                        aw.start_date = sale_date.date()
                        aw.expiration_date = sale_date.date() + timedelta(days=duration)
                        aw.save(update_fields=['start_date', 'expiration_date'])
                
                created_count += 1
                if created_count % 500 == 0:
                    print(f"    ... {created_count} ventas creadas ...")

        except Exception as e:
            print(f"Error al crear venta {i}: {e}. Saltando.")
            
    print(f"\n--- ¡Proceso completado! Se crearon {created_count} ventas históricas. ---")
    print("-" * 50)


# ====================================================================
# 9. EJECUCIÓN PRINCIPAL
# ====================================================================

if __name__ == '__main__':
    # 1. PUEBLA LAS DEPENDENCIAS (Categorías, Marcas, Garantías)
    setup_core_data()
    
    # 2. PUEBLA LOS USUARIOS (Clientes)
    create_clients()

    # 3. PUEBLA LOS PRODUCTOS
    create_products()

    # 4. PUEBLA LAS VENTAS (Requiere usuarios y productos)
    create_historical_sales()

    print("\n✅ ¡Todos los scripts de población han finalizado su ejecución! ✅")