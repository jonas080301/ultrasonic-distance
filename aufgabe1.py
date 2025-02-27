import os
import numpy as np

def process_all_measurements(directory="Messdaten"):
    """
    Iteriert über alle CSV-Dateien im angegebenen Verzeichnis, berechnet mittels Kreuzkorrelation
    zwischen Sende- und Empfangssignal die Laufzeit t und gibt ein Dictionary zurück, das den Dateinamen 
    und die berechnete Laufzeit enthält.
    
    Es werden nur Dateien mit der Endung .csv verarbeitet; andere Dateitypen (z.B. .png) werden ignoriert.
    """
    results = {}  # Dictionary: Dateiname -> Laufzeit t
    # Liste alle Dateien im Verzeichnis, die mit .csv enden (unabhängig von Groß-/Kleinschreibung)
    for file in os.listdir(directory):
        if not file.lower().endswith(".csv"):
            continue  # Überspringe Nicht-CSV-Dateien
        
        file_path = os.path.join(directory, file)
        try:
            # CSV einlesen – überspringe die zwei Headerzeilen
            data = np.genfromtxt(file_path, delimiter=',', skip_header=2)
            if data.ndim != 2 or data.shape[1] < 3:
                print(f"Datei {file} hat nicht genügend Spalten.")
                continue
            
            # Spalten extrahieren: Zeit, Sende- und Empfangssignal
            t = data[:, 0]
            send_signal = data[:, 1]
            receive_signal = data[:, 2]

            # Bestimme den Sendeimpuls im Sendesignal anhand eines Schwellwerts (5 % des Maximums)
            threshold = 0.05 * np.max(np.abs(send_signal))
            pulse_indices = np.where(np.abs(send_signal) > threshold)[0]
            if pulse_indices.size == 0:
                print(f"Kein gültiger Puls in Datei {file} gefunden.")
                continue

            pulse_start = pulse_indices[0]
            pulse_end = pulse_indices[-1]
            template = send_signal[pulse_start:pulse_end+1]

            # Berechne die Kreuzkorrelation zwischen dem Empfangssignal und dem Sendeimpuls (Template)
            corr = np.correlate(receive_signal, template, mode='full')
            zero_lag_index = len(template) - 1

            # Um direkte Kopplungseffekte zu vermeiden, starte die Suche ab (zero_lag_index + Länge des Templates)
            search_start = zero_lag_index + len(template)
            if search_start >= len(corr):
                print(f"Unzureichende Daten in Datei {file} für die Echoerkennung.")
                continue

            corr_search = corr[search_start:]
            peak_index = np.argmax(corr_search)

            # Berechne den Versatz in Samples
            sample_delay = (search_start + peak_index) - zero_lag_index

            # Bestimme die zeitliche Abtastperiode (dt) aus der Zeitachse
            if len(t) < 2:
                print(f"Unzureichende Zeitinformationen in Datei {file}.")
                continue
            dt = t[1] - t[0]
            time_delay = sample_delay * dt  # Laufzeit t

            results[file] = time_delay
            #print(f"{file}: Laufzeit t = {time_delay:.6e} s")
        except Exception as e:
            print(f"Fehler beim Verarbeiten von {file}: {e}")

    return results

# Beispielaufruf:
if __name__ == "__main__":
    laufzeiten = process_all_measurements("Messdaten")
    for datei, t in laufzeiten.items():
        print(f"{datei}: t = {t:.6e} s")