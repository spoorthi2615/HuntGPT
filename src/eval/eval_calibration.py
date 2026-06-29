import numpy as np
import matplotlib.pyplot as plt
import os
import json

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "../../results/")

def compute_ece(confidences, correct_flags, n_bins=10):
    """
    Computes Expected Calibration Error.
    """
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    
    bin_accs = []
    bin_confs = []
    
    for i in range(n_bins):
        mask = (confidences >= bins[i]) & (confidences < bins[i+1])
        # Include exactly 1.0 in the last bin
        if i == n_bins - 1:
            mask = (confidences >= bins[i]) & (confidences <= bins[i+1])
            
        if mask.sum() == 0:
            bin_accs.append(np.nan)
            bin_confs.append(np.nan)
            continue
            
        bin_acc = correct_flags[mask].mean()
        bin_conf = confidences[mask].mean()
        
        bin_accs.append(bin_acc)
        bin_confs.append(bin_conf)
        
        ece += mask.mean() * abs(bin_acc - bin_conf)
        
    return ece, bins, bin_accs, bin_confs

def plot_calibration(confidences, correct_flags, title, filename):
    ece, bins, bin_accs, bin_confs = compute_ece(confidences, correct_flags)
    
    plt.figure(figsize=(8, 6))
    
    # Plot perfect calibration line
    plt.plot([0, 1], [0, 1], 'r--', label='Perfectly calibrated')
    
    # Plot actual calibration
    bin_centers = bins[:-1] + np.diff(bins) / 2
    
    # Filter out NaNs for plotting
    valid_idx = ~np.isnan(bin_accs)
    valid_centers = bin_centers[valid_idx]
    valid_accs = np.array(bin_accs)[valid_idx]
    
    plt.bar(valid_centers, valid_accs, width=0.1, alpha=0.5, color='blue', edgecolor='black', label=f'Model Accuracy')
    
    plt.xlabel('Confidence')
    plt.ylabel('Accuracy')
    plt.title(f'{title}\nECE: {ece:.4f}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_path = os.path.join(RESULTS_DIR, filename)
    plt.savefig(out_path)
    plt.close()
    
    return ece

def run_evaluation():
    # Stub: Normally we would load predictions, ground truth, raw confidences, and self-consistency confidences
    # For now, we simulate this to ensure the plotting logic works.
    print("Running ECE calibration evaluation...")
    
    np.random.seed(42)
    n_samples = 1000
    
    # Simulate Raw Softmax (usually overconfident)
    raw_confs = np.random.beta(8, 2, n_samples)
    # accuracy isn't as high as confidence implies
    raw_correct = (np.random.rand(n_samples) < raw_confs * 0.7).astype(int) 
    
    # Simulate Self-Consistency (better calibrated)
    # confidence is closer to actual accuracy
    sc_confs = np.random.beta(5, 5, n_samples)
    sc_correct = (np.random.rand(n_samples) < sc_confs).astype(int)
    
    ece_raw = plot_calibration(raw_confs, raw_correct, "Raw Softmax Calibration", "calibration_raw.png")
    print(f"Raw Softmax ECE: {ece_raw:.4f} (Plot saved to results/calibration_raw.png)")
    
    ece_sc = plot_calibration(sc_confs, sc_correct, "Self-Consistency Calibration", "calibration_sc.png")
    print(f"Self-Consistency ECE: {ece_sc:.4f} (Plot saved to results/calibration_sc.png)")

if __name__ == "__main__":
    run_evaluation()
