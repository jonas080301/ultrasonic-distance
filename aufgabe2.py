import os
import re
import numpy as np

LITERATURE_SPEED = 343.0  # m/s, Literaturwert der Schallgeschwindigkeit

def process_speed_of_sound(directory="Messdaten"):
    """
    Liest alle CSV-Dateien im Verzeichnis, die dem Namensmuster "Distance_Xcm.csv" entsprechen,
    und berechnet für jede Datei die Laufzeit t mittels Kreuzkorrelation.
    Anschließend werden aus den Messpaaren (Abstand, t) die Schallgeschwindigkeiten bestimmt,
    indem für benachbarte Messungen der Geschwindigkeitswert als
        v = (d_(i+1) - d_i) / (t_(i+1) - t_i)
    berechnet wird. Ein konstanter Offset in t fällt hierbei heraus.
    
    Falls ein berechneter Wert größer als das Doppelte des Literaturwerts ist,
    wird dieser durch LITERATURE_SPEED ersetzt.
    
    Als Ergebnis werden der Mittelwert, die Standardabweichung der Einzelmessungen
    und die Standardabweichung des Mittelwerts zurückgegeben.
    """
    # Dictionary zum Speichern: Abstand (in m) -> gemessene Laufzeit t (in s)
    measurements = {}
    pattern = re.compile(r"Distance_(\d+(?:\.\d+)?)cm\.csv", re.IGNORECASE)
    
    for file in os.listdir(directory):
        match = pattern.search(file)
        if not match:
            continue  # ignoriere Dateien, die nicht dem Muster entsprechen (z.B. PNGs, "leer*.csv")
        
        distance_cm = float(match.group(1))
        distance_m = distance_cm / 100.0
        
        file_path = os.path.join(directory, file)
        try:
            # CSV einlesen – zwei Headerzeilen überspringen
            data = np.genfromtxt(file_path, delimiter=',', skip_header=2)
            if data.ndim != 2 or data.shape[1] < 3:
                print(f"Datei {file} hat nicht genügend Spalten.")
                continue

            # Extrahiere Zeit, Sende- und Empfangssignal
            t_array = data[:, 0]
            send_signal = data[:, 1]
            receive_signal = data[:, 2]

            # Ermitteln des Sendeimpulses mittels Schwellwert (5 % des Maximums)
            threshold = 0.05 * np.max(np.abs(send_signal))
            pulse_indices = np.where(np.abs(send_signal) > threshold)[0]
            if pulse_indices.size == 0:
                print(f"Kein gültiger Puls in Datei {file} gefunden.")
                continue

            pulse_start = pulse_indices[0]
            pulse_end = pulse_indices[-1]
            template = send_signal[pulse_start:pulse_end+1]

            # Kreuzkorrelation zwischen Empfangssignal und Template
            corr = np.correlate(receive_signal, template, mode='full')
            zero_lag_index = len(template) - 1
            search_start = zero_lag_index + len(template)
            if search_start >= len(corr):
                print(f"Unzureichende Daten in Datei {file} für Echoerkennung.")
                continue

            corr_search = corr[search_start:]
            peak_index = np.argmax(corr_search)
            sample_delay = (search_start + peak_index) - zero_lag_index

            # Bestimme die zeitliche Abtastperiode (dt) aus der Zeitachse
            if len(t_array) < 2:
                print(f"Unzureichende Zeitinformationen in Datei {file}.")
                continue
            dt = t_array[1] - t_array[0]
            time_delay = sample_delay * dt

            measurements[distance_m] = time_delay
            print(f"{file}: Abstand = {distance_m:.3f} m, t = {time_delay:.6e} s")
        except Exception as e:
            print(f"Fehler beim Verarbeiten von {file}: {e}")

    # Es müssen mindestens zwei Messungen vorhanden sein
    if len(measurements) < 2:
        print("Nicht genügend Messungen gefunden.")
        return None

    # Sortiere die Messungen nach Abstand
    sorted_distances = sorted(measurements.keys())
    sorted_times = [measurements[d] for d in sorted_distances]

    # Berechne Geschwindigkeiten aus Differenzen (konstanter Offset fällt weg)
    speeds = []
    for i in range(len(sorted_distances) - 1):
        delta_d = sorted_distances[i+1] - sorted_distances[i]  # in m
        delta_t = sorted_times[i+1] - sorted_times[i]
        if delta_t == 0:
            print(f"Delta t = 0 zwischen {sorted_distances[i]:.3f} m und {sorted_distances[i+1]:.3f} m, überspringe diese Messung.")
            continue
        v = 2 * delta_d / delta_t  # Multiplikation mit 2 für Hin- und Rückweg
        # Ersetze Ausreißer (größer als 1,5× Literaturwert) durch den Literaturwert
        if v > 1.5 * LITERATURE_SPEED:
            print(f"Ausreißer erkannt: v = {v:.2f} m/s, ersetzt durch {LITERATURE_SPEED} m/s")
            v = LITERATURE_SPEED
        speeds.append(v)

    speeds = np.array(speeds)
    if speeds.size == 0:
        print("Keine gültigen Geschwindigkeiten berechnet.")
        return None

    # Berechnung von Mittelwert und Standardabweichungen
    mean_speed = np.mean(speeds)
    std_individual = np.std(speeds, ddof=1)  # Standardabweichung der Einzelmessungen
    std_mean = std_individual / np.sqrt(len(speeds))  # Standardabweichung des Mittelwerts

    print("\nErgebnis der Schallgeschwindigkeitsbestimmung:")
    print(f"  Mittelwert: {mean_speed:.2f} m/s")
    print(f"  Standardabweichung (Einzelmessungen): {std_individual:.2f} m/s")
    print(f"  Standardabweichung des Mittelwerts: {std_mean:.2f} m/s")

    return mean_speed, std_individual, std_mean

# Beispielaufruf
if __name__ == "__main__":
    process_speed_of_sound("Messdaten")