import joblib
import numpy as np
import xgboost as xgb
import os
import sys

# ============================================================
#  CONFIGURAZIONE PERCORSI
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "ml_model/model/")

PICKLE_PATH = os.path.join(MODEL_DIR, "dataset_preprocessed.pkl")
MODEL_PATH = os.path.join(MODEL_DIR, "model_xgb.json")

# ============================================================
#  CARICAMENTO PICKLE (scaler + feature_cols)
# ============================================================

print("\n=== CARICAMENTO PICKLE ===")
try:
    data = joblib.load(PICKLE_PATH)
except Exception as e:
    print(f"ERRORE nel caricamento del pickle: {e}")
    sys.exit(1)

scaler = data.get("scaler", None)
feature_cols = data.get("feature_cols", None)

print(f"Pickle caricato da: {PICKLE_PATH}")
print(f"Tipo scaler: {type(scaler)}")
print(f"Numero feature: {len(feature_cols)}")
print("feature_cols:", feature_cols)

print("\n--- SCALER INFO ---")
print("mean_:", scaler.mean_)
print("scale_:", scaler.scale_)

# ============================================================
#  CARICAMENTO MODELLO XGBOOST
# ============================================================

print("\n=== CARICAMENTO MODELLO XGBOOST ===")
try:
    model = xgb.XGBRegressor()
    model.load_model(MODEL_PATH)
except Exception as e:
    print(f"ERRORE nel caricamento del modello: {e}")
    sys.exit(1)

print(f"Modello caricato da: {MODEL_PATH}")
print("Modello OK.")

# ============================================================
#  FUNZIONE PER COSTRUIRE IL VETTORE FEATURE
# ============================================================

def build_feature_vector(tempForno, tempRate, resOutput, tempTarget, step):
    """
    step = 0 → Riscaldamento
    step = 1 → Essicatura
    """
    x = np.zeros(len(feature_cols), dtype=float)

    mapping = {
        "tempForno": tempForno,
        "tempRate": tempRate,
        "resOutput": resOutput,
        "tempTarget": tempTarget,
        "step_Riscaldamento": 1.0 if step == 0 else 0.0,
        "step_Essicatura": 1.0 if step == 1 else 0.0,
    }

    for i, name in enumerate(feature_cols):
        if name in mapping:
            x[i] = mapping[name]

    return x

# ============================================================
#  CICLO INTERATTIVO
# ============================================================

print("\n=== DEBUG INTERATTIVO ===")
print("Inserisci i valori delle 5 feature:")
print("tempForno, tempRate, resOutput, tempTarget, step (0=Riscaldamento, 1=Essicatura)")
print("CTRL+C per uscire.\n")

while True:
    try:
        tempForno = float(input("tempForno: "))
        tempRate = float(input("tempRate: "))
        resOutput = float(input("resOutput: "))
        tempTarget = float(input("tempTarget: "))
        step = int(input("step (0=Risc, 1=Ess): "))

        # Costruzione vettore
        x = build_feature_vector(tempForno, tempRate, resOutput, tempTarget, step)
        print("\nVettore x:", x)

        # Scaling
        x_scaled = x.copy()
        x_scaled[:len(scaler.mean_)] = scaler.transform([x[:len(scaler.mean_)]])[0]
        print("Vettore x_scaled:", x_scaled)

        # Predizione
        pred = model.predict(x_scaled.reshape(1, -1))[0]
        print(f"\n>>> PREVISIONE MODELLO: {pred:.3f} °C\n")

    except KeyboardInterrupt:
        print("\nUscita dal debug.")
        break

    except Exception as e:
        print(f"Errore: {e}\n")
