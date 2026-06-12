import joblib
import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, max_error
import matplotlib.pyplot as plt

data = joblib.load("model/dataset_preprocessed.pkl")

X_train = data["X_train"]
y_train = data["y_train"]
X_test = data["X_test"]
y_test = data["y_test"]
X_val = data["X_val"]
y_val = data["y_val"]

feature_cols = data["feature_cols"]
train_proc = data["train_proc"]
test_proc = data["test_proc"]
val_proc = data["val_proc"]

print("Train:", X_train.shape, "Val:", X_val.shape, "Test:", X_test.shape)

model = xgb.XGBRegressor(
    n_estimators=2000,
    learning_rate=0.01,
    max_depth=6,
    subsample=0.9,
    colsample_bytree=0.9,
    reg_lambda=1.0,
    random_state=42,
    eval_metric="rmse",
    early_stopping_rounds=50,
)

#training
model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    verbose=True,
)

#test
y_pred_test = model.predict(X_test)
rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_test))
mae_test = mean_absolute_error(y_test, y_pred_test)
r2_test = r2_score(y_test, y_pred_test)
mape_test = np.mean(np.abs((y_test - y_pred_test) / y_test)) * 100
max_err = max_error(y_test, y_pred_test)

print(f"RMSE        = {rmse_test:.4f} °C")
print(f"MAE         = {mae_test:.4f} °C")
print(f"MAPE        = {mape_test:.2f} %")
print(f"R^2         = {r2_test:.4f}")
print(f"MAX ERROR   = {max_err:.4f} °C")


model.save_model("model/model_xgb.json")


#grafico reale vs predetto
plt.figure(figsize=(14, 6))
plt.plot(y_test, label="Reale temp futura", alpha=0.8)
plt.plot(y_pred_test, label="Temp futura predetta", alpha=0.8)
plt.title("Temperatura reale vs predetta")
plt.xlabel("Campioni")
plt.ylabel("Temperatura [°C]")
plt.grid(True)
plt.legend()
plt.show()