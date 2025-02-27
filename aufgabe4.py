import numpy as np
import matplotlib.pyplot as plt

# Beispielhafte Messdaten (Entfernung in m, gemessene Laufzeit in s)
# Diese Daten stammen aus den vorherigen Messungen:
distances = np.array([0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40,
                      0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85])
times = np.array([9.38e-04, 1.248e-03, 1.880e-03, 2.110e-03, 2.400e-03,
                  2.645e-03, 2.985e-03, 3.2425e-03, 3.4875e-03, 3.875e-03,
                  4.66e-03, 4.95e-03, 5.135e-03, 5.5e-03, 5.8e-03, 6.025e-03,
                  6.3e-03])

# Linearen Fit durchführen: Wir nehmen an, dass t = m * d + b gilt.
m, b = np.polyfit(distances, times, 1)
print(f"Linearer Fit: t(d) = {m:.2e} * d + {b:.2e}")

# Plot der Messdaten und des Fits
d_fit = np.linspace(0, 1, 100)
t_fit = m * d_fit + b

plt.figure()
plt.plot(distances, times, 'o', label="Messdaten")
plt.plot(d_fit, t_fit, '-', label="Linearer Fit")
plt.xlabel("Entfernung d (m)")
plt.ylabel("Laufzeit t (s)")
plt.title("Lineare Regression: Laufzeit vs. Entfernung")
plt.legend()
plt.grid(True)
plt.show()

# Für die digitale Anzeige im Auto: Um aus einer gemessenen Laufzeit t die Entfernung zu berechnen,
# verwenden Sie die invertierte Funktion:
# d(t) = (t - b) / m
#
# Beispiel:
t_measured = 4.5e-03  # gemessene Laufzeit in s
distance_calc = (t_measured - b) / m
print(f"Berechnete Entfernung für t = {t_measured:.2e} s: {distance_calc:.3f} m")