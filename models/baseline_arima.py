"""
ARIMA Baseline Model for Shipping Delay Prediction

What this does:
1. Pulls time-series data for our test route (Caguas → NYC)
2. Trains ARIMA model on 80% of the data
3. Predicts delays for the remaining 20%
4. Calculates MAE (Mean Absolute Error)

Why we need this:
- ARIMA is the "industry standard" statistical model
- This MAE becomes the number Chronos has to beat
- Resume bullet: "31% MAE improvement over ARIMA baseline"

What is ARIMA:
- Auto-Regressive: Uses past values to predict future
- Integrated: Removes trends to make data stable
- Moving Average: Smooths out noise
- Been around since 1970s, still used in logistics today
"""

import psycopg2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_absolute_error
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("TIMESCALE_HOST", "localhost"),
        port=os.getenv("TIMESCALE_PORT", 5434),
        dbname=os.getenv("TIMESCALE_DB", "freightsense"),
        user=os.getenv("TIMESCALE_USER", "postgres"),
        password=os.getenv("TIMESCALE_PASSWORD", "postgres")
    )

def load_route_data(route_id=6636):
    """
    Load time-series delay data for a specific route.
    Default: Caguas → NYC (route_id 6636, 811 shipments)
    """
    conn = get_connection()
    
    query = """
        SELECT 
            time,
            delay_days
        FROM route_metrics
        WHERE route_id = %s
        ORDER BY time ASC;
    """
    
    df = pd.read_sql(query, conn, params=(route_id,))
    conn.close()
    
    print(f"📊 Loaded {len(df)} data points for route {route_id}")
    print(f"   Date range: {df['time'].min()} to {df['time'].max()}")
    print(f"   Avg delay: {df['delay_days'].mean():.2f} days")
    
    return df

def train_arima_baseline(df, train_ratio=0.8):
    """
    Train ARIMA model and evaluate performance.
    
    Parameters explained:
    - order=(5,1,0) means:
      - p=5: Use last 5 time steps to predict next one
      - d=1: Apply differencing once to remove trends
      - q=0: Don't use moving average component
    
    These are typical starting values for delay forecasting.
    """
    
    # Split into train/test
    split_idx = int(len(df) * train_ratio)
    train_data = df['delay_days'][:split_idx]
    test_data = df['delay_days'][split_idx:]
    
    print(f"\n📊 Train/Test Split:")
    print(f"   Training: {len(train_data)} points")
    print(f"   Testing: {len(test_data)} points")
    
    # Train ARIMA model
    print(f"\n🔧 Training ARIMA(5,1,0) model...")
    model = ARIMA(train_data, order=(5,1,0))
    fitted_model = model.fit()
    
    print("✅ Model trained successfully")
    
    # Make predictions on test set
    print(f"\n🔮 Generating predictions for {len(test_data)} test points...")
    predictions = fitted_model.forecast(steps=len(test_data))
    
    # Calculate error metrics
    mae = mean_absolute_error(test_data, predictions)
    
    print(f"\n📈 ARIMA Baseline Results:")
    print(f"   MAE (Mean Absolute Error): {mae:.4f} days")
    print(f"   Interpretation: On average, predictions are off by {mae:.2f} days")
    
    # Show some example predictions vs actual
    print(f"\n📋 Sample Predictions vs Actual:")
    comparison = pd.DataFrame({
        'Actual': test_data.values[:10],
        'Predicted': predictions[:10],
        'Error': np.abs(test_data.values[:10] - predictions[:10])
    })
    print(comparison.to_string(index=False))
    
    # Plot results
    plot_predictions(test_data, predictions, mae)
    
    # Save baseline metric
    save_baseline_metric(mae)
    
    return mae, fitted_model

def plot_predictions(actual, predicted, mae):
    """Visualize predictions vs actual delays."""
    plt.figure(figsize=(12, 6))
    
    # Plot first 100 points for clarity
    n = min(100, len(actual))
    
    plt.plot(range(n), actual.values[:n], label='Actual Delays', marker='o', markersize=4, alpha=0.7)
    plt.plot(range(n), predicted[:n], label='ARIMA Predictions', marker='s', markersize=4, alpha=0.7)
    
    plt.xlabel('Test Sample')
    plt.ylabel('Delay (days)')
    plt.title(f'ARIMA Baseline: Actual vs Predicted Delays\nMAE = {mae:.4f} days')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Save plot
    os.makedirs('data/processed', exist_ok=True)
    plt.savefig('data/processed/arima_baseline.png', dpi=150, bbox_inches='tight')
    print(f"\n📊 Plot saved to data/processed/arima_baseline.png")
    
    plt.close()

def save_baseline_metric(mae):
    """Save the baseline MAE for comparison with Chronos later."""
    os.makedirs('data/processed', exist_ok=True)
    
    with open('data/processed/baseline_metrics.txt', 'w') as f:
        f.write(f"ARIMA Baseline MAE: {mae:.4f} days\n")
        f.write(f"Route: Caguas → New York City (811 shipments)\n")
        f.write(f"Model: ARIMA(5,1,0)\n")
        f.write(f"Train/Test Split: 80/20\n")
    
    print(f"💾 Baseline metric saved to data/processed/baseline_metrics.txt")

def main():
    print("=" * 60)
    print("ARIMA BASELINE MODEL - SHIPPING DELAY PREDICTION")
    print("=" * 60)
    
    # Load data for busiest route
    df = load_route_data(route_id=6636)
    
    # Train and evaluate
    mae, model = train_arima_baseline(df)
    
    print("\n" + "=" * 60)
    print(f"✅ BASELINE ESTABLISHED: MAE = {mae:.4f} days")
    print("=" * 60)
    print("\n📌 Next Step: Train Chronos model to beat this baseline")
    print(f"   Target: Achieve MAE < {mae:.4f} days (31% improvement = {mae * 0.69:.4f} days)")
    print("\n")

if __name__ == "__main__":
    main()