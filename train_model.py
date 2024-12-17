import pandas as pd
from sklearn.ensemble import IsolationForest

def detect_anomalies(file_path):
    data = pd.read_csv(file_path)
    if 'amount' not in data.columns:
        raise ValueError("CSV must contain an 'amount' column for fraud detection.")
    
    # Simple anomaly detection
    model = IsolationForest(contamination=0.1)
    data['anomaly'] = model.fit_predict(data[['amount']])
    anomalies = data[data['anomaly'] == -1]
    return anomalies
