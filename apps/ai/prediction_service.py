# apps/ai/prediction_service.py
import joblib
import pandas as pd
import os
import sys
import django
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

# Configuración Django
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
try:
    django.setup()
except RuntimeError:
    pass

from apps.sales.models import Sale, SaleDetail
from apps.products.models import Product

# --- CARGA DE MODELOS ---
BASE_DIR = os.path.dirname(__file__)

# Modelo 1: Ventas Generales (Total Amount)
general_model_path = os.path.join(BASE_DIR, 'data/sales_model.joblib')
general_columns_path = os.path.join(BASE_DIR, 'data/model_columns.joblib')

# Modelo 2: Ventas por Producto (Top Products)
product_model_path = os.path.join(BASE_DIR, 'data/product_sales_model.joblib')

try:
    general_model = joblib.load(general_model_path)
    general_columns = joblib.load(general_columns_path)
except Exception:
    general_model = None
    print("Advertencia: Modelo General no encontrado.")

try:
    product_model = joblib.load(product_model_path)
except Exception:
    product_model = None
    print("Advertencia: Modelo de Productos no encontrado.")


# --- LÓGICA 1: PREDICCIÓN GENERAL (Monto Total) ---

def generate_features_for_general_prediction():
    """Genera features para predecir el monto total del próximo mes"""
    sales = Sale.objects.filter(status=Sale.SaleStatus.COMPLETED)
    if not sales.exists():
        return None, None
        
    df = pd.DataFrame(list(sales.values('created_at', 'total_amount')))
    df['created_at'] = pd.to_datetime(df['created_at'])
    df = df.set_index('created_at')
    df_monthly = df['total_amount'].resample('MS').sum().reset_index()
    df_monthly.columns = ['date', 'total_sales']
    
    last_known_data = df_monthly.iloc[-1]
    next_period_date = last_known_data['date'] + pd.DateOffset(months=1)
    
    sales_lag_1 = last_known_data['total_sales']
    sales_lag_2 = df_monthly.iloc[-2]['total_sales'] if len(df_monthly) > 1 else 0
    sales_lag_3 = df_monthly.iloc[-3]['total_sales'] if len(df_monthly) > 2 else 0
    
    features = {
        'year': [next_period_date.year],
        'month': [next_period_date.month],
        'sales_lag_1': [sales_lag_1],
        'sales_lag_2': [sales_lag_2],
        'sales_lag_3': [sales_lag_3]
    }
    
    features_df = pd.DataFrame(features)
    # Reordenar columnas según como se entrenó
    if general_columns:
        features_df = features_df[general_columns]
    
    return features_df, next_period_date

def predict_next_month_sales():
    """Predice el MONTO TOTAL de ventas del próximo mes"""
    if not general_model:
        return {"error": "Modelo General no entrenado. Ejecuta model_training.py (General)."}

    try:
        features_df, next_period_date = generate_features_for_general_prediction()
        if features_df is None:
            return {"error": "No hay suficientes datos históricos."}

        prediction = general_model.predict(features_df)
        
        return {
            "prediction_period": next_period_date.strftime('%Y-%m'),
            "predicted_sales_bob": round(prediction[0], 2)
        }
    except Exception as e:
        print(f"Error en predicción general: {e}")
        return {"error": str(e)}


# --- LÓGICA 2: PREDICCIÓN POR PRODUCTO (Top 3) ---

def get_product_sales_last_months(product_id, months=3):
    today = timezone.now()
    sales_data = []
    for i in range(1, months + 1):
        month_start = (today - timedelta(days=30 * i)).replace(day=1)
        month_end = (today - timedelta(days=30 * (i-1))).replace(day=1)
        
        qty = SaleDetail.objects.filter(
            product_id=product_id,
            sale__status='COMPLETED',
            sale__created_at__gte=month_start,
            sale__created_at__lt=month_end
        ).aggregate(total=Sum('quantity'))['total'] or 0
        sales_data.append(qty)
    return sales_data

def predict_top_products():
    """Predice qué PRODUCTOS venderán más unidades el próximo mes"""
    if not product_model:
        return {"error": "Modelo de Productos no entrenado."}

    predictions = []
    all_products = Product.objects.all()
    next_month = (timezone.now().month % 12) + 1

    for product in all_products:
        sales_data = get_product_sales_last_months(product.id, 3)
        lag_1, lag_2, lag_3 = sales_data[0], sales_data[1], sales_data[2]
        rolling_mean = sum(sales_data) / 3
        
        features = pd.DataFrame([{
            'month': next_month,
            'lag_1': lag_1, 'lag_2': lag_2, 'lag_3': lag_3,
            'rolling_mean_3': rolling_mean
        }])
        
        try:
            predicted_qty = product_model.predict(features)[0]
        except:
            predicted_qty = 0
        
        if predicted_qty > 0.1:
            predictions.append({
                "product_id": product.id,
                "product_name": product.name,
                "predicted_quantity": round(predicted_qty),
                "category": product.category.name if product.category else "N/A",
                "image_url": product.image_url
            })

    predictions.sort(key=lambda x: x['predicted_quantity'], reverse=True)
    return predictions[:3]