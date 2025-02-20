import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

# Set random seed for reproducibility
np.random.seed(42)

# Generate sample data
true_mu = 2.0
true_sigma = 1.5
n_samples = 1000
data = np.random.normal(true_mu, true_sigma, n_samples)

# Function to compute standard MLE
def standard_mle(data):
    mu = np.mean(data)
    sigma = np.sqrt(np.mean((data - mu)**2))
    return mu, sigma

# Function to compute weighted MLE
def weighted_mle(data, weights):
    W = np.sum(weights)
    mu = np.sum(weights * data) / W
    sigma = np.sqrt(np.sum(weights * (data - mu)**2) / W)
    return mu, sigma

# Compute standard MLE
std_mu, std_sigma = standard_mle(data)

# Create weights (higher weights for values below the mean)
weights = np.ones_like(data)
weights[data < np.mean(data)] = 2.0  # Double weight for values below mean
weights = weights / np.mean(weights)  # Normalize weights

# Compute weighted MLE
weighted_mu, weighted_sigma = weighted_mle(data, weights)

# Create plot
plt.figure(figsize=(12, 8))

# Plot histogram of data
counts, bins, _ = plt.hist(data, bins=50, density=True, alpha=0.6, 
                          label='Sample Data', color='gray')

# Generate points for the fitted curves
x = np.linspace(min(data), max(data), 200)

# Plot the true distribution
plt.plot(x, norm.pdf(x, true_mu, true_sigma), 
         'k-', label=f'True Distribution (μ={true_mu:.2f}, σ={true_sigma:.2f})', 
         linewidth=2)

# Plot standard MLE fit
plt.plot(x, norm.pdf(x, std_mu, std_sigma), 
         'b--', label=f'Standard MLE (μ={std_mu:.2f}, σ={std_sigma:.2f})', 
         linewidth=2)

# Plot weighted MLE fit
plt.plot(x, norm.pdf(x, weighted_mu, weighted_sigma), 
         'r--', label=f'Weighted MLE (μ={weighted_mu:.2f}, σ={weighted_sigma:.2f})', 
         linewidth=2)

plt.title('Comparison of Standard and Weighted MLE Fits')
plt.xlabel('Value')
plt.ylabel('Density')
plt.legend()
plt.grid(True, alpha=0.3)

# Save the plot
plt.savefig('TheoreticalStatistics/homework3_q2_plot.png', dpi=300, bbox_inches='tight')
plt.close()

# Print the results
print(f'True parameters: μ={true_mu:.3f}, σ={true_sigma:.3f}')
print(f'Standard MLE: μ={std_mu:.3f}, σ={std_sigma:.3f}')
print(f'Weighted MLE: μ={weighted_mu:.3f}, σ={weighted_sigma:.3f}')