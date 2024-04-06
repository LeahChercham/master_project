"""
Script python pour générer un graphique de comparaison des prédictions
avec les données réelles observées.
"""
from datetime import datetime
import matplotlib.pyplot as plt

def plot_true_pred(true_labels, predictions):
    
    start_date = predictions.index[0].date()
    end_date = predictions.index[-1].date()
    timestamp = datetime.now().date()

    plt.figure(figsize=(25,10))
    # TODO: Legend and labels not showing. Confusing
    plt.legend(f"Predictions (green) vs. true labels (red) from {start_date} to {end_date} predicted on {timestamp}")
    plt.xlabel('Date')
    plt.ylabel("Temperature 2m")
    plt.plot(predictions.index, true_labels, color="r", label="True labels")
    plt.plot(predictions.index, predictions.values, color="g", label="Predicted")
    
    path = r"api/monitoring/outputs/"
    all_path = f"{path}plot_{timestamp}_range_{start_date}_{end_date}.png"
    plt.savefig(all_path)

    return path