# apps/ai/prediction_service.py
import joblib
import pandas as pd
import os
from .dataset_generator import create_training_dataset # Re-usamos el generador

# (Configuración de Django para acceder a la BD)
import django
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.sales.models import Sale

# 1. Cargar el modelo y las columnas al iniciar
BASE_DIR = os.path.dirname(__file__)
model_path = os.path.join(BASE_DIR, 'data/sales_model.joblib')
columns_path = os.path.join(BASE_DIR, 'data/model_columns.joblib')

try:
    model = joblib.load(model_path)
    model_columns = joblib.load(columns_path)
    print("Servicio de predicción: Modelo y columnas cargados.")
except FileNotFoundError:
    print("ADVERTENCIA: Archivos del modelo no encontrados. Entrenando modelo...")
    create_training_dataset()
    from .model_training import train_model
    train_model()
    model = joblib.load(model_path)
    model_columns = joblib.load(columns_path)


def generate_features_for_prediction():
    """
    Toma los datos REALES de la BD para construir el vector de features (X)
    necesario para predecir el PRÓXIMO mes.
    """
    print("Generando features para predicción en vivo...")
    # 1. Obtener datos históricos (igual que el generador)
    sales = Sale.objects.filter(status=Sale.SaleStatus.COMPLETED)
    df = pd.DataFrame(list(sales.values('created_at', 'total_amount')))
    df['created_at'] = pd.to_datetime(df['created_at'])
    df = df.set_index('created_at')
    df_monthly = df['total_amount'].resample('MS').sum().reset_index()
    df_monthly.columns = ['date', 'total_sales']
    
    # 2. Obtener la ÚLTIMA fila de datos
    last_known_data = df_monthly.iloc[-1]
    
    # 3. Construir los features para el mes SIGUIENTE
    next_period_date = last_known_data['date'] + pd.DateOffset(months=1)
    
    # Calcular los lags basados en los últimos datos
    sales_lag_1 = last_known_data['total_sales']
    sales_lag_2 = df_monthly.iloc[-2]['total_sales'] if len(df_monthly) > 1 else 0
    sales_lag_3 = df_monthly.iloc[-3]['total_sales'] if len(df_monthly) > 2 else 0
    
    # 4. Crear el DataFrame de predicción
    # (Debe tener EXACTAMENTE las mismas columnas que 'model_columns')
    features = {
        'year': [next_period_date.year],
        'month': [next_period_date.month],
        'sales_lag_1': [sales_lag_1],
        'sales_lag_2': [sales_lag_2],
        'sales_lag_3': [sales_lag_3]
    }
    
    features_df = pd.DataFrame(features)
    
    # Asegurar el orden correcto de las columnas
    features_df = features_df[model_columns] 
    
    return features_df, next_period_date

def predict_next_month_sales():
    """
    Función principal llamada por la API.
    """
    try:
        # 1. Genera los features (X) para el próximo mes
        features_df, next_period_date = generate_features_for_prediction()
        
        # 2. Realiza la predicción
        prediction = model.predict(features_df)
        
        # 3. Devuelve un resultado limpio
        return {
            "prediction_period": next_period_date.strftime('%Y-%m'),
            "predicted_sales_bob": round(prediction[0], 2)
        }
        
    except Exception as e:
        print(f"Error en el servicio de predicción: {e}")
        return {"error": str(e)}