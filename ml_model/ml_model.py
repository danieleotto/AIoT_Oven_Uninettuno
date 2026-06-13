import joblib, os
import xgboost as xgb
import numpy as np


class MLModel:
    def __init__(self, preprocess_path, model_path) -> None:
        self.MODEL_DIR = "model"
        os.makedirs(self.MODEL_DIR, exist_ok=True)
        try:
            data = joblib.load(preprocess_path)
        except FileNotFoundError:
            input(f"Preprocess file non trovato: {preprocess_path}")
        self.scaler = data["scaler"]
        self.feature_cols = data["feature_cols"]

        self.model = xgb.XGBRegressor()
        try:
            self.model.load_model(model_path)
        except FileNotFoundError:
            input(f"File modello non trovato: {model_path}")


    def _vettore_feature(self, temp_forno, temp_rate, res_output, temp_target, step):
        x = np.zeros(len(self.feature_cols), dtype=float)
        x[0] = temp_forno
        x[1] = temp_rate
        x[2] = res_output
        x[3] = temp_target

        if step == "Riscaldamento":
            x[4] = 1.0
            x[5] = 0.0
        else:
            x[4] = 0.0
            x[5] = 1.0

        # x_scaled = x.copy()
        # x_scaled[:4] = self.scaler.transform([x[:4]])[0]

        # print("prima", x[:4])
        # print("dopo", x_scaled[:4])

        return x


    def output_corretto_ml(self, pid_output, temp_forno, temp_rate, temp_target, step) -> float:
        x = self._vettore_feature(temp_forno, temp_rate, pid_output, temp_target, step)
        x_scaled = x.copy()
        x_scaled[:4] = self.scaler.transform([x[:4]])[0]
        temp_futura_prevista = self.model.predict(x_scaled.reshape(1, -1))[0]

        match step:
            case "Riscaldamento":
                if temp_forno < temp_target:
                    if temp_target - 10 < temp_futura_prevista <= temp_target -5:
                        output_corretto = pid_output * 0.7
                    elif temp_target - 5 < temp_futura_prevista <= temp_target:
                        output_corretto = pid_output * 0.5
                    elif temp_futura_prevista > temp_target:
                        output_corretto = pid_output * 0.3
                    else:
                        output_corretto = pid_output
                else:
                    output_corretto = pid_output
            case "Essicatura":
                if temp_forno > temp_target:
                    if temp_target - 5 < temp_futura_prevista < temp_target:
                        output_corretto = pid_output + 0.2
                    elif temp_target - 10 < temp_futura_prevista <= 5:
                        output_corretto = pid_output + 0.35
                    elif temp_futura_prevista <= temp_target - 10:
                        output_corretto = pid_output + 0.6
                    else:
                        output_corretto = pid_output
                elif temp_forno < temp_target:
                    if temp_target - 5 < temp_futura_prevista < temp_target:
                        output_corretto = pid_output * 1.2
                    elif temp_target - 10 < temp_futura_prevista <= temp_target - 5:
                        output_corretto = pid_output * 1.4
                    elif temp_futura_prevista <= temp_target - 10:
                        output_corretto = pid_output * 1.6
                    else:
                        output_corretto = pid_output
                else:
                    output_corretto = pid_output
            case _:
                output_corretto = pid_output

        output_corretto = max(0, min(1, output_corretto))
        print("ML --- x:", x[:4])
        print("ML --- x_scaled:", x_scaled[:4])
        print("ML --- temp prevista +12s:", temp_futura_prevista)

        return output_corretto