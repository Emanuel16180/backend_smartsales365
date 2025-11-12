# apps/ai/model_training.py
import pandas as pd
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error

def train_model():
    print("Iniciando entrenamiento del modelo...")
    
    # 1. Cargar Dataset
    dataset_path = os.path.join(os.path.dirname(__file__), 'data/training_dataset.csv')
    try:
        df = pd.read_csv(dataset_path)
    except FileNotFoundError:
        print(f"Error: No se encontró 'training_dataset.csv'.")
        print("Por favor, ejecuta 'dataset_generator.py' primero.")
        return

    # 2. Definir Features (X) y Target (y)
    target_column = 'target_next_month_sales'
    # Usamos todas las columnas como features EXCEPTO el target y la fecha original
    features = [col for col in df.columns if col not in [target_column, 'date', 'total_sales']]
    
    X = df[features]
    y = df[target_column]
    
    print(f"Features (X): {X.columns.tolist()}")
    print(f"Target (y): {target_column}")

    # 3. Dividir datos (Entrenamiento y Prueba)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False) # No barajar series temporales

    # 4. Entrenar el Modelo
    print("Entrenando RandomForestRegressor...")
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    # 5. Evaluar el Modelo
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = mse ** 0.5
    print(f"\n--- Evaluación del Modelo ---")
    print(f"R^2 Score (Precisión): {r2:.2f}")
    print(f"RMSE (Error Promedio): {rmse:.2f} BOB")
    print(f"-----------------------------")

    # 6. Serializar (Guardar) el Modelo y las Columnas
    model_path = os.path.join(os.path.dirname(__file__), 'data/sales_model.joblib')
    columns_path = os.path.join(os.path.dirname(__file__), 'data/model_columns.joblib')
    
    joblib.dump(model, model_path)
    joblib.dump(features, columns_path) # ¡Guardamos el orden de las columnas!
    
    print(f"¡Modelo guardado en {model_path}!")
    print(f"Columnas del modelo guardadas en {columns_path}!")

if __name__ == '__main__':
    train_model()