import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
import joblib

df = pd.read_csv('emissions.csv')

print("Columns:", df.columns.tolist())

target_col = 'emissions'          

# Dropping non-numeric + useless columns
drop_cols = [
    target_col, 'timestamp', 'project_name', 'run_id', 'experiment_id',
    'country_name', 'country_iso_code', 'region', 'os', 'python_version',
    'codecarbon_version', 'tracking_mode', 'on_cloud', 'pue', 'wue',
    'cloud_provider', 'cloud_region', 'longitude', 'latitude',
    'cpu_model', 'gpu_model'
]

X = df.drop(columns=drop_cols, errors='ignore')
X = X.select_dtypes(include=['number'])

y = df[target_col]

print(f"Using {X.shape[1]} features for training")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Using XGBoost
model = XGBRegressor(
    n_estimators=300,
    max_depth=8,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

print(f" Model trained!")
print(f"R² Score: {model.score(X_test, y_test):.4f}")

joblib.dump(model, 'energy_predictor.pkl')
print(" Model saved as 'energy_predictor.pkl'")