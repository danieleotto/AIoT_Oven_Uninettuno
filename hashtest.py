import hashlib

with open("ml_model/model/model_xgb.json", "rb") as f:
    data = f.read()
print("MD5:", hashlib.md5(data).hexdigest())
print("SHA1:", hashlib.sha1(data).hexdigest())

import xgboost as xgb
print("OrangePi XGBoost:", xgb.__version__)

