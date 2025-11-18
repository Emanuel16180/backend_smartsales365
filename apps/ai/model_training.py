# apps/ai/model_training.py
import pandas as pd
import joblib
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error

def train_model():
    print("Entrenando modelo de predicción de productos...")
    
    dataset_path = os.path.join(os.path.dirname(__file__), 'data/product_training_dataset.csv')
    if not os.path.exists(dataset_path):
        print("Ejecuta dataset_generator.py primero.")
        return

    df = pd.read_csv(dataset_path)

    # Features: Mes del año + Ventas pasadas + Tendencia
    features = ['month', 'lag_1', 'lag_2', 'lag_3', 'rolling_mean_3']
    target = 'target'
    
    X = df[features]
    y = df[target]
    
    # Entrenar
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluar
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    print(f"Precisión del modelo (R2): {r2:.2f}")

    # Guardar
    model_path = os.path.join(os.path.dirname(__file__), 'data/product_sales_model.joblib')
    joblib.dump(model, model_path)
    print("¡Modelo guardado!")

if __name__ == '__main__':
    train_model()