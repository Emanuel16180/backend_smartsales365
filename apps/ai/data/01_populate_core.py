import os
import django
import sys
from faker import Faker
import random # Importamos random

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.products.models import Category, Brand, WarrantyProvider, Warranty

fake = Faker('es_ES')

def setup_data():
    # --- OPCIONAL: Limpiar datos antiguos ---
    print("Limpiando datos antiguos...")
    Category.objects.all().delete()
    Brand.objects.all().delete()
    Warranty.objects.all().delete()
    WarrantyProvider.objects.all().delete()

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


    print("Poblando Marcas (orden aleatorio)...")
    marcas = ['Samsung', 'LG', 'Sony', 'Hisense', 'Mabe', 'Indurama', 'Oster']
    # --- CAMBIO: Mezclamos la lista ---
    random.shuffle(marcas) 
    
    for marca_nombre in marcas:
        Brand.objects.create(name=marca_nombre)


    print("Poblando Proveedores de Garantía...")
    # --- CAMBIO: Nuevos nombres para proveedores ---
    provider_names = [
        'Servicio Técnico Autorizado S.A.',
        'Garantía Total Bolivia',
        'ReparaFácil S.R.L.',
        'ElectroService Plus',
        'Soluciones Hogar',
        'ServiTec Autorizado',
        'Asistencia Inmediata S.R.L.'
    ]
    
    providers = []
    # Usamos la lista de nombres en lugar de un rango
    for name in provider_names:
        provider = WarrantyProvider.objects.create(
            name=name,
            contact_email=fake.email(),
            contact_phone=fake.phone_number()
        )
        providers.append(provider)


    print("Poblando Plantillas de Garantía...")
    # --- CAMBIO: Nuevos títulos y términos para garantías ---
    Warranty.objects.create(
        title="Garantía Estándar (12 Meses)",
        terms="Cobertura estándar por 12 meses contra defectos de fábrica. No incluye daños por mal uso.",
        duration_days=365,
        provider_id=providers[0].id
    )
    Warranty.objects.create(
        title="Garantía Limitada (6 Meses)",
        terms="Cobertura de 180 días en partes y componentes principales. Excluye accesorios y consumibles.",
        duration_days=180,
        provider_id=providers[1].id
    )
    Warranty.objects.create(
        title="Garantía Extendida Motor/Compresor (2 Años)",
        terms="Cobertura especial de 2 años (730 días) exclusivamente para el motor o compresor del equipo.",
        duration_days=730,
        provider_id=providers[2].id
    )
    Warranty.objects.create(
        title="Garantía Básica (90 Días)",
        terms="Cubre fallas en componentes electrónicos básicos por 90 días. Mano de obra no incluida.",
        duration_days=90,
        provider_id=providers[3].id
    )
    
    print("\n--- ¡Núcleo poblado con éxito! ---")

if __name__ == '__main__':
    setup_data()