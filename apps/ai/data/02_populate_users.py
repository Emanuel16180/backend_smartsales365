import os
import django
import sys
from faker import Faker

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

try:
    from apps.users.models import User
except ImportError:
    from django.contrib.auth import get_user_model
    User = get_user_model()

fake = Faker('es_ES')

def create_clients(count=70):
    print(f"Poblando {count} usuarios (clientes)...")
    
    for i in range(count):
        first_name = fake.first_name()
        last_name = fake.last_name()
        
        username_base = f"{first_name.lower().replace(' ', '')}{i+1}"
        email = f"{username_base}@example.com"
        
        if User.objects.filter(email=email).exists():
            continue
            
        try:
            User.objects.create_user(
                email=email,
                password='password',
                first_name=first_name,
                last_name=last_name,
                role='CUSTOMER'
            )
        except TypeError:
            User.objects.create_user(
                email=email,
                password='password',
                first_name=first_name,
                last_name=last_name,
                is_staff=False
            )

    print(f"\n--- ¡{count} Clientes creados con éxito! ---")
    print(f"Usuario de ejemplo: {email}")
    print("Contraseña para todos: password")

if __name__ == '__main__':
    create_clients()