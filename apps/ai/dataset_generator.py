# apps/ai/dataset_generator.py
import os
import django
import sys
import pandas as pd

# --- Configuración de Django ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
# --- Fin Configuración ---

from apps.sales.models import Sale

def create_training_dataset():
    print("Iniciando generación de dataset...")
    
    # 1. Extraer todas las ventas "Completadas" de la BD
    sales = Sale.objects.filter(status=Sale.SaleStatus.COMPLETED)
    
    if not sales.exists():
        print("Error: No hay ventas en la base de datos para entrenar.")
        return

    # Convertir a un DataFrame de Pandas
    df = pd.DataFrame(list(sales.values('created_at', 'total_amount')))
    
    # 2. Transformar (Ingeniería de Características)
    # Convertir fechas a formato datetime
    df['created_at'] = pd.to_datetime(df['created_at'])
    df = df.set_index('created_at')
    
    # Agrupar las ventas por mes (MS = Month Start) y sumarlas
    df_monthly = df['total_amount'].resample('MS').sum().reset_index()
    df_monthly.columns = ['date', 'total_sales']
    
    print(f"Datos agrupados por mes (primeras filas):\n{df_monthly.head()}")

    # 3. Crear Características (Features)
    # El modelo predecirá las ventas del próximo mes (y)
    # usando las ventas de los meses anteriores (X)
    
    df_monthly['year'] = df_monthly['date'].dt.year
    df_monthly['month'] = df_monthly['date'].dt.month
    
    # "Lag features" (ventas del mes pasado, de hace 2 meses, etc.)
    df_monthly['sales_lag_1'] = df_monthly['total_sales'].shift(1)
    df_monthly['sales_lag_2'] = df_monthly['total_sales'].shift(2)
    df_monthly['sales_lag_3'] = df_monthly['total_sales'].shift(3)
    
    # 4. Crear el Target (lo que queremos predecir)
    # El target 'y' son las ventas del *siguiente* mes
    df_monthly['target_next_month_sales'] = df_monthly['total_sales'].shift(-1)
    
    # 5. Limpiar
    # Eliminar filas con NaN (los primeros meses que no tienen lag,
    # y el último mes que no tiene target)
    df_final = df_monthly.dropna()
    
    if df_final.empty:
        print("Error: No se generaron suficientes datos (necesitas al menos 5 meses de ventas).")
        return

    # 6. Cargar (Guardar el dataset limpio)
    output_path = os.path.join(os.path.dirname(__file__), 'data/training_dataset.csv')
    df_final.to_csv(output_path, index=False)
    
    print(f"\n¡Dataset de entrenamiento guardado en {output_path}!")
    print(f"Columnas del dataset: {df_final.columns.tolist()}")

if __name__ == '__main__':
    create_training_dataset()