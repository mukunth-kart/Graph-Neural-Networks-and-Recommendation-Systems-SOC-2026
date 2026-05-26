import numpy as np
import matplotlib.pyplot as plt

def simulate_wavefunction(x, E, V):
    if E > V:
        k = np.sqrt(2 * (E - V))
        return np.cos(k * x)
    elif E < V:
        kappa = np.sqrt(2 * (V - E))
        return np.exp(-kappa * x)
    else:
        return np.ones_like(x)

x = np.linspace(0, 5, 500)

psi_a = simulate_wavefunction(x, 12, 2)
psi_b = simulate_wavefunction(x, 2, 7)
psi_c = simulate_wavefunction(x, 5, 5)

plt.plot(x, psi_a, label='Case A (Oscillatory): E=12, V=2')
plt.plot(x, psi_b, label='Case B (Decaying): E=2, V=7')
plt.plot(x, psi_c, label='Case C (Threshold): E=5, V=5')

plt.title('1D Time-Independent Schrödinger Equation')
plt.xlabel('Position (x)')
plt.ylabel('Wavefunction psi(x)')
plt.legend()
plt.show()