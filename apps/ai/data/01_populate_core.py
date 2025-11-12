import os
import django
import sys
from faker import Faker

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


    print("Poblando Marcas...")
    marcas = ['Samsung', 'LG', 'Sony', 'Hisense', 'Mabe', 'Indurama', 'Oster']
    for marca_nombre in marcas:
        Brand.objects.create(name=marca_nombre)


    print("Poblando Proveedores de Garantía...")
    providers = []
    for _ in range(7):
        provider = WarrantyProvider.objects.create(
            name=f"{fake.company()} S.R.L.",
            contact_email=fake.email(),
            contact_phone=fake.phone_number()
        )
        providers.append(provider)


    print("Poblando Plantillas de Garantía...")
    Warranty.objects.create(
        title="Garantía 1 Año (Fábrica)",
        terms="Cubre defectos de fabricación por 365 días.",
        duration_days=365,
        provider_id=providers[0].id
    )
    Warranty.objects.create(
        title="Garantía 6 Meses (Tienda)",
        terms="Cubre fallas de componentes por 180 días.",
        duration_days=180,
        provider_id=providers[1].id
    )
    Warranty.objects.create(
        title="Garantía 2 Años Motor (Extendida)",
        terms="Cubre fallas de motor por 730 días.",
        duration_days=730,
        provider_id=providers[2].id
    )
    Warranty.objects.create(
        title="Garantía 3 Meses (Componentes)",
        terms="Cubre fallas en componentes electrónicos por 90 días.",
        duration_days=90,
        provider_id=providers[3].id
    )
    
    print("\n--- ¡Núcleo poblado con éxito! ---")

if __name__ == '__main__':
    setup_data()