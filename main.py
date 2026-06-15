import sys
sys.path.append("/home/orangepi/.local/lib/python3.12/site-packages")
import xgboost
print("XGBoost OK:", xgboost.__version__)

import json
from thermocouple import Termocoppia
from sqlite_db import SQLiteDB
from ss_relay import SolidStateRelay
from console_menu import TextMenu, ANSI
from processi import Essicatura, Ricottura, SaldaturaSMD
from temp_sensor import TempSensor
from context import Context
from customlib.pzem004t_modbus_lib import PZEM004TModbus
from customlib.sgp30 import SGP30
from pid_pwm import PID
from ml_model.ml_model import MLRegressorModel, MLIsolationModel

CONFIG_FILE:str = 'config.json'
DEFAULT_CONFIG = {
    "TC_SAMPLE_SIZE" : 11,
    "TC_MAX_TEMP": 200,
    "TC_PIN_SCK": 8,
    "TC_PIN_CS": 7,
    "TC_PIN_DO": 5,
    "RES_SSR_PIN": 2,
    "FAN_SSR_PIN": 3,
    "DHT22_PIN": 10,
    "PZEM_PORT": "/dev/ttyUSB0",
    "PZEM_TIMEOUT": 0.3,
    "PZEM_ADDRESS": 248,
    "I2C_BUS_ID": 2,
    "DB_FILENAME": "ovenDB.db",
    "SAMPLE_INTERVAL": 0.6,
    "KP": 0.018,
    "KI": 0.0000134,
    "KD": 0.10,
    "XGB_PREPROCESS_PATH": "ml_model/model/dataset_preprocessed.pkl",
    "XGB_MODEL_PATH": "ml_model/model/model_xgb.json",
    "ISO_SCALER_PATH": "ml_model/model/scaler_if.pkl",
    "ISO_MODEL_PATH": "ml_model/model/isolation_forest.pkl",
    "ISO_MODEL_LIMIT": 0.1,
}
config_loaded:bool = False

while not config_loaded:
    try:
        with open(CONFIG_FILE, "r") as f:
            config_data = json.load(f)
            config_loaded = True
    except FileNotFoundError:
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        continue
    except json.JSONDecodeError:
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        continue
        
TC_MAX_TEMP:float = config_data["TC_MAX_TEMP"]
TC_SCK_PIN:int = config_data["TC_PIN_SCK"]
TC_CS_PIN:int = config_data["TC_PIN_CS"]
TC_DO_PIN:int = config_data["TC_PIN_DO"]
RES_SSR_PIN:int = config_data["RES_SSR_PIN"]
FAN_SSR_PIN:int = config_data["FAN_SSR_PIN"]
DHT22_PIN:int = config_data["DHT22_PIN"]
I2C_BUS_ID:int = config_data["I2C_BUS_ID"]
PZEM_PORT:str = config_data["PZEM_PORT"]
PZEM_TIMEOUT:float = config_data["PZEM_TIMEOUT"]
PZEM_ADDRESS:int = config_data["PZEM_ADDRESS"]
SAMPLE_SIZE:int = config_data["TC_SAMPLE_SIZE"]
SAMPLING_INTERVAL:float = config_data["SAMPLE_INTERVAL"]
DB_FILENAME:str = config_data["DB_FILENAME"]
KP:float = config_data["KP"]
KI:float = config_data["KI"]
KD:float = config_data["KD"]
XGB_PREPROCESS_PATH:str = config_data["XGB_PREPROCESS_PATH"]
XGB_MODEL_PATH:str = config_data["XGB_MODEL_PATH"]
ISO_SCALER_PATH:str = config_data["ISO_SCALER_PATH"]
ISO_MODEL_PATH:str = config_data["ISO_MODEL_PATH"]
ISO_MODEL_LIMIT:float = config_data["ISO_MODEL_LIMIT"]


tc:Termocoppia = Termocoppia(TC_SCK_PIN, TC_CS_PIN, TC_DO_PIN, SAMPLE_SIZE, TC_MAX_TEMP)
sq:SQLiteDB = SQLiteDB(DB_FILENAME)
dht22:TempSensor = TempSensor(DHT22_PIN)
pzem:PZEM004TModbus = PZEM004TModbus(PZEM_PORT, PZEM_TIMEOUT, PZEM_ADDRESS)
sgp:SGP30 = SGP30(I2C_BUS_ID)
ssr_res:SolidStateRelay = SolidStateRelay(RES_SSR_PIN)
ssr_fan:SolidStateRelay = SolidStateRelay(FAN_SSR_PIN)
pid:PID = PID(KP, KI, KD) #creiamo l'oggetto con kp-ki-kd standard da config.json, temp target verrà impostata all'interno delle fasi

ml_pred:MLRegressorModel = MLRegressorModel(XGB_PREPROCESS_PATH, XGB_MODEL_PATH)
ml_anomalie:MLIsolationModel = MLIsolationModel(ISO_MODEL_PATH, ISO_SCALER_PATH, ISO_MODEL_LIMIT)

ctx:Context = Context(tc, SAMPLING_INTERVAL, sq, ssr_res, ssr_fan, dht22, pzem, sgp, pid, ml_pred, ml_anomalie)

e_proc:Essicatura = Essicatura(ctx)
r_proc:Ricottura = Ricottura(ctx)
s_proc:SaldaturaSMD = SaldaturaSMD(ctx)

menu_principale:TextMenu = TextMenu("             --- MENU PRINCIPALE ---", color_title=ANSI.GREEN, color_option=ANSI.CYAN)
menu_principale.add_option("1", "Essicatura", e_proc.process_menu)
menu_principale.add_option("2", "Ricottura", r_proc.process_menu)
menu_principale.add_option("3", "Saldatura SMD", s_proc.process_menu)

if __name__ == '__main__':
    menu_principale.run()
    sq.log_processes()