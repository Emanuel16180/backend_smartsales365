# smartsales365_backend

Estructura inicial del backend Django para SmartSales365.

Instrucciones rápidas:

1. Crear y activar un entorno virtual (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependencias:

```powershell
python -m pip install -r requirements.txt
```

3. Configurar `.env` (ya hay un ejemplo en el repo).

4. Ejecutar migraciones y levantar el servidor:

```powershell
python manage.py migrate
python manage.py runserver
```
