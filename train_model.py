import pandas as pd
from sklearn.ensemble import IsolationForest


def detect_anomalies(file_path):
    # Load data
    data = pd.read_csv(file_path)

    # Ensure required columns are present
    required_columns = ['Predicted Valuation', 'NET_LOSS']
    if not all(col in data.columns for col in required_columns):
        raise ValueError(f"CSV must contain the following columns: {', '.join(required_columns)}")

    # Calculate difference percentage
    data['Difference (%)'] = ((data['NET_LOSS'] - data['Predicted Valuation']) / data['Predicted Valuation']) * 100

    # Train IsolationForest on numerical data
    features = ['Predicted Valuation', 'NET_LOSS', 'Difference (%)']
    model = IsolationForest(contamination=0.1, random_state=42)
    data['anomaly'] = model.fit_predict(data[features])

    # Extract anomalies
    anomalies = data[data['anomaly'] == -1].copy()

    # Add reasons for anomalies
    anomalies['reason'] = anomalies.apply(lambda row: get_reason(row, data.columns), axis=1)

    return anomalies


def get_reason(row, columns):
    """
    Analyze the row and supporting columns to determine the likely cause of anomaly.
    """
    reasons = []

    # Check for extreme difference percentages
    if row['Difference (%)'] > 50:
        reasons.append("NET_LOSS significantly exceeds Predicted Valuation")
    elif row['Difference (%)'] < -20:
        reasons.append("Predicted Valuation is too high compared to NET_LOSS")

    # Asset-related analysis
    if 'ASSET_COST' in columns and row['ASSET_COST'] > 0 and row['Predicted Valuation'] < row['ASSET_COST'] * 0.5:
        reasons.append("Asset has depreciated significantly")
    
    # Loan-related analysis
    if 'LTV' in columns and row['LTV'] > 80:
        reasons.append("High Loan-to-Value ratio, indicating risky lending")
    
    if 'LOAN_AMOUNT' in columns and row['LOAN_AMOUNT'] > 0 and row['NET_LOSS'] > row['LOAN_AMOUNT'] * 0.8:
        reasons.append("High loss compared to loan amount")

    # Region-related analysis
    if 'STATE' in columns and row['STATE'] == 'Region_X':
        reasons.append("Region_X has high-risk transactions")

    # Seizure-related analysis
    if 'DAYS_IN_YARD' in columns and row['DAYS_IN_YARD'] > 90:
        reasons.append("Prolonged days in yard may have led to depreciation")
    
    # Previous ownership analysis
    if 'PREVIOUS_OWNER_COUNT' in columns and row['PREVIOUS_OWNER_COUNT'] > 2:
        reasons.append("Asset has multiple previous owners, reducing valuation")
    
    # Odometer-related analysis
    if 'ODOMETER_READING' in columns and row['ODOMETER_READING'] > 200000:
        reasons.append("High mileage may have reduced the asset valuation")

    return "; ".join(reasons) if reasons else "Unknown cause"


# Example usage
file_path = "valuations.csv"
anomalies = detect_anomalies(file_path)
print(anomalies)
