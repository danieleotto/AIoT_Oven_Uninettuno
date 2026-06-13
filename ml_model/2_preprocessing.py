import pandas as pd
from sklearn.preprocessing import StandardScaler
import joblib

train_proc = [1,2,4,6,7,9,10,12,13,15,16,18,19,21,22,24,25,26,28,29,31]
val_proc = [3,5,8,11,30]
test_proc = [14,17,20,23,27,32]

df = pd.read_csv("dataset.csv", sep=";", decimal=",", engine="python")
print("Shape iniziale:", df.shape)
print(df.head())

req_cols = [
    "idProc",
    "tempForno",
    "tempRate",
    "resOutput",
    "tempTarget",
    "step",
    "tempForno_future",
    "deltaT_future"
]

#one-hot
df = pd.get_dummies(df, columns=["step"], prefix="step")

feature_cols = [
    "tempForno",
    "tempRate",
    "resOutput",
    "tempTarget",
    "step_Riscaldamento",
    "step_Essicatura"
]
target_col = "tempForno_future"

#split per idProc
processi = df["idProc"].unique()
n = len(processi)

n_train = int(n * 0.7)
n_val = int(n * 0.15)



df_train = df[df["idProc"].isin(train_proc)]
df_val = df[df["idProc"].isin(val_proc)]
df_test = df[df["idProc"].isin(test_proc)]

print(f"Processi train: {train_proc}")
print(f"Processi val: {val_proc}")
print(f"Processi test: {test_proc}")


#costruzione set
X_train = df_train[feature_cols].values
y_train = df_train[target_col].values

X_val = df_val[feature_cols].values
y_val = df_val[target_col].values

X_test = df_test[feature_cols].values
y_test = df_test[target_col].values

print("Shape X_train:", X_train.shape)
print("Shape X_val:", X_val.shape)
print("Shape X_test:", X_test.shape)


#scaling
scaling_cols = [
    "tempForno",
    "tempRate",
    "resOutput",
    "tempTarget",
]
X_train_scaled = X_train.copy()
X_val_scaled = X_val.copy()
X_test_scaled = X_test.copy()

scaler = StandardScaler()
scaler.fit(X_train[:, :len(scaling_cols)])

X_train_scaled[:, :len(scaling_cols)] = scaler.transform(X_train[:,:len(scaling_cols)])
X_val_scaled[:, :len(scaling_cols)] = scaler.transform(X_val[:,:len(scaling_cols)])
X_test_scaled[:, :len(scaling_cols)] = scaler.transform(X_test[:,:len(scaling_cols)])


joblib.dump(
    {
        "X_train": X_train_scaled,
        "y_train": y_train,
        "X_val": X_val_scaled,
        "y_val": y_val,
        "X_test": X_test_scaled,
        "y_test": y_test,
        "feature_cols": feature_cols,
        "scaler": scaler,
        "train_proc": train_proc,
        "val_proc": val_proc,
        "test_proc": test_proc,
    },
    "model/dataset_preprocessed.pkl",
)
print("Preprocessing Completato.")