import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import joblib

# ===================== LOAD DATA =====================
df = pd.read_csv('emissions.csv')   # Change path if needed

print("📊 Columns in your CSV:")
print(df.columns.tolist())

# Auto-detect target column
target_col = None
for col in df.columns:
    if col.lower() in ['energy_consumed', 'energy', 'kwh', 'emissions']:
        target_col = col
        break

if target_col is None:
    print("❌ Could not find energy column. Check CSV.")
    exit()

print(f"✅ Using target column: {target_col}")

# Drop all non-numeric + metadata columns
drop_cols = [
    target_col, 'timestamp', 'project_name', 'run_id', 'experiment_id',
    'country_name', 'country_iso_code', 'region', 'os', 'python_version',
    'codecarbon_version', 'tracking_mode', 'on_cloud', 'pue', 'wue',
    'cloud_provider', 'cloud_region', 'longitude', 'latitude',
    'cpu_model', 'gpu_model', 'os'  # string columns
]

X = df.drop(columns=drop_cols, errors='ignore')
X = X.select_dtypes(include=['number'])   # Keep only numeric columns

y = df[target_col]

print(f"✅ Final features used ({X.shape[1]} columns):")
print(X.columns.tolist())

# ===================== TRAIN MODEL =====================
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestRegressor(
    n_estimators=200,
    max_depth=15,
    n_jobs=-1,           # uses all CPU cores for speed
    random_state=42
)

model.fit(X_train, y_train)

print(f"✅ Model trained successfully!")
print(f"R² Score: {model.score(X_test, y_test):.4f}")

# ===================== SAVE MODEL =====================
joblib.dump(model, 'energy_predictor.pkl')
print("✅ Model saved as 'energy_predictor.pkl'")