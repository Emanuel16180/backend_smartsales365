import os
import django
import sys
import random
from decimal import Decimal
from faker import Faker
import hashlib 
import base64 

# --- Configuración de Django ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
# --- Fin Configuración ---

# --- (ACTUALIZADO) CONFIGURACIÓN DE IMÁGENES DE RELLENO ---
# Usamos LoremFlickr, que SÍ funciona y acepta palabras clave
# La sintaxis es /ancho/alto/palabra_clave
LOREMFLICKR_BASE_URL = "https://loremflickr.com/{width}/{height}/{keyword}"
IMAGE_WIDTH = 640
IMAGE_HEIGHT = 480
# --- FIN CONFIGURACIÓN ---

# --- (ACTUALIZADO) Mapeo de Categorías a Palabras Clave ---
# (LoremFlickr funciona bien con una sola palabra clave en inglés)
CATEGORY_KEYWORD_MAP = {
    "Refrigeradores": "refrigerator",
    "Cocinas": "kitchen",
    "Lavadoras": "laundry",
    "Televisores": "television",
    "Audio y Video": "audio",
    "Computación": "laptop",
    "Sofás y Sillones": "sofa",
    "Dormitorio": "bedroom",
    "Comedor": "diningroom",
    "Aires Acondicionados": "air,conditioner", # (Para que tome una de las dos)
    "Ventiladores": "fan",
}
# --- FIN MAPEO ---


# Importa todos los modelos necesarios
from apps.products.models import Product, Category, Brand, Warranty
try:
    from apps.sales.models import Sale
    SALE_APP_EXISTS = True
except ImportError:
    SALE_APP_EXISTS = False

fake = Faker('es_ES')

# (Tu PRODUCT_MAP va aquí, sin cambios)
PRODUCT_MAP = {
    # Electrodomésticos
    "Refrigeradores": [
        ("Refrigerador No-Frost {}L", "Refrigerador No-Frost de {} litros. Eficiencia energética A+, color {}."),
        ("Frigobar {}L", "Frigobar compacto de {} litros, ideal para oficina. Puerta reversible. Color {}.")
    ],
    "Cocinas": [
        ("Cocina {} Hornallas", "Cocina a gas de {} hornallas, con horno de gran capacidad y encendido eléctrico. Acero inoxidable."),
        ("Horno Microondas {}L", "Microondas digital de {}L de capacidad. Panel {} y 10 niveles de potencia.")
    ],
    "Lavadoras": [
        ("Lavadora Carga Frontal {}kg", "Lavadora automática Inverter, {}kg de capacidad, 8 programas de lavado. Color {}."),
        ("Lavadora Carga Superior {}kg", "Lavadora automática de {}kg, con tecnología Wobble para un lavado profundo. Color {}.")
    ],
    
    # Tecnología
    "Televisores": [
        ("Smart TV {} Pulgadas 4K", "Televisor inteligente {} pulgadas 4K UHD con HDR, sistema operativo {} y control por voz."),
        ("Smart TV {} Pulgadas FHD", "Televisor inteligente {} pulgadas Full HD con acceso a Netflix, YouTube y más.")
    ],
    "Audio y Video": [
        ("Equipo de Sonido {}W", "Minicomponente de {}W de potencia, con Bluetooth, USB y CD. Sonido X-Boom."),
        ("Barra de Sonido {} Canales", "Barra de sonido de {} canales con subwoofer inalámbrico y sonido Dolby Atmos.")
    ],
    "Computación": [
        ("Laptop Core i{} {}GB RAM", "Laptop de 15.6\", procesador Core i{}, {}GB de RAM y {}GB SSD. Windows 11."),
        ("Monitor Gamer {} Pulgadas", "Monitor Curvo Gamer de {} pulgadas, 144Hz, 1ms de respuesta.")
    ],
    
    # Muebles
    "Sofás y Sillones": [
        ("Sofá {} Cuerpos", "Sofá de {} cuerpos tapizado en tela de lino de alta resistencia, color {}."),
        ("Sillón Reclinable", "Sillón reclinable tipo {} tapizado en ecocuero, con sistema de masaje.")
    ],
    "Dormitorio": [
        ("Colchón {} Plazas", "Colchón ortopédico de {} plazas, con resortes pocket y capa de espuma viscoelástica."),
        ("Ropero {} Puertas", "Ropero de melamina color {}, {} puertas batientes y 2 cajones con rieles metálicos.")
    ],
    "Comedor": [
        ("Juego de Comedor {} Sillas", "Juego de comedor con mesa de {} y {} sillas de madera tapizadas en tela."),
    ],

    # Climatización
    "Aires Acondicionados": [
        ("Aire Acondicionado Split {}BTU", "Aire Acondicionado tipo Split de {} BTU, modo frío/calor, con filtro antibacterial."),
    ],
    "Ventiladores": [
        ("Ventilador de Pie {} Pulgadas", "Ventilador de pie de {} pulgadas, 3 velocidades y oscilación automática. Base reforzada."),
    ]
}


# (Tu función generate_product_details va aquí, sin cambios)
def generate_product_details(category_name, brand_name):
    """
    Función auxiliar para generar un nombre y descripción coherentes
    basados en la categoría.
    """
    templates = PRODUCT_MAP.get(category_name)
    
    # --- Fallback (si la categoría no está en nuestro mapa) ---
    if not templates:
        name = f"Producto Genérico {brand_name}"
        desc = f"Una descripción genérica para {category_name.lower()}. {fake.text(max_nb_chars=100)}"
        return name, desc

    # --- Generación dinámica ---
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
        elif category_name == "Computación":
            cpu = random.choice([3, 5, 7])
            ram = random.choice([8, 16, 32])
            ssd = random.choice([256, 512, 1024])
            pulgadas = random.choice([24, 27, 32])
            name = base_name.format(cpu, ram) if "Laptop" in base_name else base_name.format(pulgadas)
            desc = desc_template.format(cpu, ram, ssd) if "Laptop" in base_name else desc_template.format(pulgadas)
        elif category_name == "Sofás y Sillones":
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

    except Exception: # Si algo falla en el format()
        name = base_name.replace("{}", "")
        desc = desc_template.replace("{}", "")

    return f"{name} {brand_name}", desc


def create_products(count=50):
    # (Pequeña edición en el print)
    print(f"Poblando {count} productos (Coherentes + LoremFlickr)...")

    # 1. Obtiene las dependencias (Marcas, Garantías y Categorías)
    brands = list(Brand.objects.all())
    warranties = list(Warranty.objects.all())
    # ¡Importante! Solo poblamos en categorías "hijas"
    categories = list(Category.objects.filter(parent__isnull=False))

    # --- Validación ---
    if not all([brands, warranties, categories]):
        print("\n--- ¡ERROR! ---")
        print("Asegúrate de ejecutar '01_populate_core.py' primero.")
        print("Necesitas Marcas, Garantías y Categorías (hijas) en la BD.")
        return

    # --- Limpieza de datos antiguos ---
    print("Limpiando datos antiguos (Ventas y Productos)...")
    if SALE_APP_EXISTS:
        Sale.objects.all().delete()
    Product.objects.all().delete() 
    
    
    # --- Bucle de Creación ---
    for i in range(count):
        
        # 1. Elige una CATEGORÍA (real de la BD) al azar
        category_obj = random.choice(categories)
        
        # 2. Elige una MARCA y GARANTÍA (reales) al azar
        brand_obj = random.choice(brands)
        warranty_obj = random.choice(warranties)

        # 3. Genera Nombre y Descripción COHERENTES
        name, description = generate_product_details(category_obj.name, brand_obj.name)
        
        # 4. Datos numéricos
        price = Decimal(random.uniform(500.0, 9000.0)).quantize(Decimal('0.01'))
        stock = random.randint(5, 40)
        
        # --- (ACTUALIZADO) 5. Construir la URL de la imagen (LoremFlickr por Categoría) ---
        
        # 5.1. Obtener la palabra clave de nuestro mapa
        category_name = category_obj.name
        # Si no encuentra la categoría, usa 'product' como fallback
        keyword = CATEGORY_KEYWORD_MAP.get(category_name, 'product') 

        # 5.2. Construir la URL
        image_url = LOREMFLICKR_BASE_URL.format(
            width=IMAGE_WIDTH,
            height=IMAGE_HEIGHT,
            keyword=keyword
        )
        
        # 5.3. (NUEVO) Agregar un "seed" para evitar el cache
        # LoremFlickr a veces cachea la misma imagen para la misma keyword.
        # Agregar un parámetro inútil (como un hash) fuerza una nueva imagen.
        seed_data = f"{name}-{category_obj.name}-{i}"
        seed_hash = hashlib.sha256(seed_data.encode()).hexdigest()[:10]
        image_url = f"{image_url}?lock={seed_hash}"

        
        # --- (ACTUALIZADO) 6. Crear el Producto ---
        Product.objects.create(
            name=name,
            description=description,
            price=price,
            stock=stock,
            category=category_obj, # Asigna el objeto categoría real
            brand=brand_obj,       # Asigna el objeto marca real
            warranty=warranty_obj, # Asigna el objeto garantía real
            image_url=image_url    # Asigna la URL de LoremFlickr
        )

    # (Pequeña edición en el print)
    print(f"\n--- ¡{count} Productos (Coherentes + LoremFlickr) creados con éxito! ---")

if __name__ == '__main__':
    create_products()