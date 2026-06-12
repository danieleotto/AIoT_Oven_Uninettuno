import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, max_error
import joblib
import matplotlib.pyplot as plt

data = joblib.load("model/dataset_preprocessed.pkl")

X_test = data["X_test"]
y_test = data["y_test"]
feature_cols = data["feature_cols"]
test_proc = data["test_proc"]

model = xgb.XGBRegressor()
model.load_model("model/model_xgb.json")

df_originale = pd.read_csv("dataset_12s.csv", sep=";", decimal=",", engine="python")
df_originale = pd.get_dummies(df_originale, columns=["step"], prefix="step")
df_originale_test = df_originale[df_originale["idProc"].isin(test_proc)].reset_index(drop=True)

y_pred_test = model.predict(X_test)

df_test = pd.DataFrame(X_test, columns=feature_cols)
df_test["y_true"] = y_test
df_test["y_pred"] = y_pred_test
df_test["idProc"] = df_originale_test["idProc"]

print("\nMetriche per singolo processo")
mae_per_proc = {}
rmse_per_proc = {}
mape_per_proc = {}
r2_per_proc = {}
max_error_per_proc = {}

for proc in test_proc:
    dfp = df_test[df_test["idProc"] == proc]
    mae_proc = mean_absolute_error(dfp["y_true"], dfp["y_pred"])
    rmse_proc = np.sqrt(mean_squared_error(dfp["y_true"], dfp["y_pred"]))
    mape_proc = np.mean(np.abs(dfp["y_true"] - dfp["y_pred"]) / dfp["y_true"]) * 100
    r2_proc = r2_score(dfp["y_true"], dfp["y_pred"])
    max_error_proc = max_error(dfp["y_true"], dfp["y_pred"])

    mae_per_proc[proc] = mae_proc
    rmse_per_proc[proc] = rmse_proc
    mape_per_proc[proc] = mape_proc
    r2_per_proc[proc] = r2_proc
    max_error_per_proc[proc] = max_error_proc

    print(f"Processo: {proc}")
    print(f"MAE         = {mae_proc:.4f} °C")
    print(f"RMSE        = {rmse_proc:.4f} °C")
    print(f"MAPE        = {mape_proc:.2f} %")
    print(f"R^2         = {r2_proc:.4f}")
    print(f"MAX ERROR   = {max_error_proc:.4f} °C\n\n")

    plt.figure(figsize = (14,6))
    plt.plot(dfp["y_true"], label="Temp Reale", alpha=0.8)
    plt.plot(dfp["y_pred"], label="Temp Predetta", alpha=0.8)
    plt.title(f"Processo {proc} - reale vs predetta")
    plt.xlabel("Campioni")
    plt.ylabel("Temperatura [°C]")
    plt.grid(True)
    plt.legend()
    plt.show()
