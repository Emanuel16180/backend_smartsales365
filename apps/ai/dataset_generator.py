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

from apps.sales.models import SaleDetail

def create_training_dataset():
    print("Iniciando generación de dataset POR PRODUCTO...")
    
    # 1. Extraer detalles de ventas completadas
    # Necesitamos: Fecha, ID del Producto, Cantidad Vendida
    details = SaleDetail.objects.filter(sale__status='COMPLETED').values(
        'sale__created_at', 
        'product__id', 
        'quantity'
    )
    
    if not details.exists():
        print("Error: No hay ventas para entrenar.")
        return

    df = pd.DataFrame(list(details))
    
    # 2. Limpieza y Agrupación
    df['date'] = pd.to_datetime(df['sale__created_at'])
    df['product_id'] = df['product__id']
    
    # Agrupar por Mes Y por Producto
    # Esto nos da: Enero -> TV Samsung -> 5 vendidos
    df_grouped = df.groupby([pd.Grouper(key='date', freq='MS'), 'product_id'])['quantity'].sum().reset_index()
    
    print(f"Datos agrupados (muestras): \n{df_grouped.head()}")

    # 3. Ingeniería de Características (Lags por Producto)
    # Necesitamos que los lags sean respetando el ID del producto
    df_final = pd.DataFrame()
    
    for pid, group in df_grouped.groupby('product_id'):
        group = group.sort_values('date')
        
        # Features de tiempo
        group['month'] = group['date'].dt.month
        
        # Lags: Cuánto vendió este producto hace 1, 2 y 3 meses
        group['lag_1'] = group['quantity'].shift(1)
        group['lag_2'] = group['quantity'].shift(2)
        group['lag_3'] = group['quantity'].shift(3)
        
        # Promedio móvil (Rolling mean) de 3 meses (Tendencia reciente)
        group['rolling_mean_3'] = group['quantity'].shift(1).rolling(window=3).mean()
        
        # Target: Cuánto venderá el mes siguiente
        group['target'] = group['quantity'] # El target es la cantidad actual
        # Pero para entrenar, usamos los lags para predecir el actual.
        # Al generar features para predicción futura, usaremos los datos actuales como lags.
        
        df_final = pd.concat([df_final, group])
    
    # 4. Limpieza final
    df_final = df_final.dropna() # Eliminar filas sin historia suficiente
    
    if df_final.empty:
        print("Error: Datos insuficientes por producto.")
        return

    output_path = os.path.join(os.path.dirname(__file__), 'data/product_training_dataset.csv')
    df_final.to_csv(output_path, index=False)
    
    print(f"\n¡Dataset por producto guardado en {output_path}!")
    print(f"Columnas: {df_final.columns.tolist()}")

if __name__ == '__main__':
    create_training_dataset()