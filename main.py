import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os, re

# Theoretischer Wert, falls keine Kalibrierung erfolgt (Luft bei 20°C)
SPEED_OF_SOUND = 343.0  
DEFAULT_CALIBRATION_FOLDER = "Messdaten"

class RadarApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ultraschall Echo – Distanz & Kalibrierung")
        self.geometry("1000x700")
        
        # Kalibrierungsparameter (aus linearer Regression: t = m*d + b)
        self.cal_m = None
        self.cal_b = None
        self.cal_m_err = None
        self.cal_b_err = None
        
        # UI-Elemente: 
        # Kalibrierung
        self.calib_button = tk.Button(self, text="Kalibriere Messdaten (Ordner)", command=self.calibrate)
        self.calib_button.pack(pady=5)
        self.calib_label = tk.Label(self, text="Keine Kalibrierung durchgeführt", font=("Arial", 12))
        self.calib_label.pack(pady=5)
        
        # Einzelmessung
        self.load_button = tk.Button(self, text="Einzelmessung laden (CSV)", command=self.load_csv)
        self.load_button.pack(pady=5)
        self.distance_label = tk.Label(self, text="Gemessene Distanz: - m", font=("Arial", 14))
        self.distance_label.pack(pady=5)
        self.uncertainty_label = tk.Label(self, text="Unsicherheit: - m", font=("Arial", 12))
        self.uncertainty_label.pack(pady=5)
        
        # Matplotlib-Figure für Signalplots
        self.fig, (self.ax_send, self.ax_receive) = plt.subplots(2, 1, figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Platzhalter für Messdaten
        self.t = None
        self.send_signal = None
        self.receive_signal = None

    def calibrate(self):
        # Wähle einen Ordner aus, der die Kalibrierungsdateien enthält
        folder = filedialog.askdirectory(initialdir=DEFAULT_CALIBRATION_FOLDER, title="Ordner mit Messdaten auswählen")
        if not folder:
            return
        
        distances = []  # in m
        times = []      # gemessene Rundlaufzeit (s)
        pattern = re.compile(r"Distance_(\d+(?:\.\d+)?)cm\.csv", re.IGNORECASE)
        
        for file in os.listdir(folder):
            if not file.lower().endswith(".csv"):
                continue
            match = pattern.search(file)
            if not match:
                continue
            distance_cm = float(match.group(1))
            distance_m = distance_cm / 100.0
            
            file_path = os.path.join(folder, file)
            try:
                data = np.genfromtxt(file_path, delimiter=',', skip_header=2)
                if data.ndim != 2 or data.shape[1] < 3:
                    print(f"Datei {file} hat nicht genügend Spalten.")
                    continue
                t_array = data[:, 0]
                send_signal = data[:, 1]
                receive_signal = data[:, 2]
                
                # Bestimme den Puls im Sendesignal anhand eines Schwellwerts (10% des Maximums)
                threshold = 0.1 * np.max(np.abs(send_signal))
                pulse_indices = np.where(np.abs(send_signal) > threshold)[0]
                if pulse_indices.size == 0:
                    print(f"Kein gültiger Puls in Datei {file}.")
                    continue
                pulse_start = pulse_indices[0]
                pulse_end = pulse_indices[-1]
                template = send_signal[pulse_start:pulse_end+1]
                
                # Kreuzkorrelation
                corr = np.correlate(receive_signal, template, mode='full')
                zero_lag_index = len(template) - 1
                search_start = zero_lag_index + len(template)
                if search_start >= len(corr):
                    print(f"Unzureichende Daten in Datei {file} für Echoerkennung.")
                    continue
                corr_search = corr[search_start:]
                peak_index = np.argmax(corr_search)
                sample_delay = (search_start + peak_index) - zero_lag_index
                dt = t_array[1] - t_array[0]
                time_delay = sample_delay * dt  # Rundlaufzeit
                
                distances.append(distance_m)
                times.append(time_delay)
                print(f"{file}: Abstand = {distance_m:.3f} m, t = {time_delay:.6e} s")
            except Exception as e:
                print(f"Fehler in Datei {file}: {e}")
        
        if len(distances) < 2:
            messagebox.showerror("Fehler", "Nicht genügend gültige Messungen für die Kalibrierung gefunden.")
            return
        
        distances = np.array(distances)
        times = np.array(times)
        
        # Linearer Fit: t = m * d + b; mit Unsicherheiten (cov=True)
        (m, b), cov = np.polyfit(distances, times, 1, cov=True)
        m_err = np.sqrt(cov[0,0])
        b_err = np.sqrt(cov[1,1])
        
        self.cal_m = m
        self.cal_b = b
        self.cal_m_err = m_err
        self.cal_b_err = b_err
        
        # Kalibrierte Schallgeschwindigkeit: v = 2/m
        cal_v = 2 / m
        cal_v_err = 2/m**2 * m_err
        
        calib_text = (f"Kalibrierung abgeschlossen:\n"
                      f"t(d) = {m:.2e} * d + {b:.2e}\n"
                      f"Kalibrierte v = {cal_v:.1f} ± {cal_v_err:.1f} m/s")
        self.calib_label.config(text=calib_text)
    
    def load_csv(self):
        # Einzelmessung laden
        file_path = filedialog.askopenfilename(filetypes=[("CSV Dateien", "*.csv")])
        if not file_path:
            return
        try:
            data = np.genfromtxt(file_path, delimiter=',', skip_header=2)
            if data.ndim != 2 or data.shape[1] < 3:
                messagebox.showerror("Fehler", "Die CSV-Datei muss mindestens drei Spalten enthalten.")
                return
            
            self.t = data[:, 0]
            self.send_signal = data[:, 1]
            self.receive_signal = data[:, 2]
            
            self.plot_signals()
            self.process_measurement()
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden der CSV:\n{e}")
    
    def plot_signals(self):
        # Sendesignal plotten
        self.ax_send.clear()
        self.ax_send.plot(self.t, self.send_signal, label="Sendesignal")
        self.ax_send.set_title("Sendesignal")
        self.ax_send.set_xlabel("Zeit (s)")
        self.ax_send.set_ylabel("Spannung (V)")
        self.ax_send.legend()
        
        # Empfangssignal plotten
        self.ax_receive.clear()
        self.ax_receive.plot(self.t, self.receive_signal, label="Empfangssignal", color="orange")
        self.ax_receive.set_title("Empfangssignal")
        self.ax_receive.set_xlabel("Zeit (s)")
        self.ax_receive.set_ylabel("Spannung (V)")
        self.ax_receive.legend()
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def process_measurement(self):
        # Berechne die Rundlaufzeit mittels Kreuzkorrelation
        threshold = 0.1 * np.max(np.abs(self.send_signal))
        pulse_indices = np.where(np.abs(self.send_signal) > threshold)[0]
        if pulse_indices.size == 0:
            messagebox.showerror("Fehler", "Kein gültiger Puls im Sendesignal gefunden.")
            return
        
        pulse_start = pulse_indices[0]
        pulse_end = pulse_indices[-1]
        template = self.send_signal[pulse_start:pulse_end+1]
        
        corr = np.correlate(self.receive_signal, template, mode='full')
        zero_lag_index = len(template) - 1
        search_start = zero_lag_index + len(template)
        if search_start >= len(corr):
            messagebox.showerror("Fehler", "Unzureichende Daten für die Echoerkennung.")
            return
        
        corr_search = corr[search_start:]
        peak_index = np.argmax(corr_search)
        sample_delay = (search_start + peak_index) - zero_lag_index
        dt = self.t[1] - self.t[0]
        time_delay = sample_delay * dt  # gemessene Rundlaufzeit
        
        # Falls Kalibrierungsdaten vorliegen, benutze den linear kalibrierten Zusammenhang:
        if self.cal_m is not None and self.cal_b is not None:
            # t = m*d + b  =>  d = (t - b) / m
            measured_distance = (time_delay - self.cal_b) / self.cal_m
            # Fehlerfortpflanzung: d = (t - b) / m mit t exakt
            # ∂d/∂m = -(t-b)/m²   und   ∂d/∂b = -1/m
            delta_d = np.sqrt(((time_delay - self.cal_b)/self.cal_m**2 * self.cal_m_err)**2 +
                              ((1/self.cal_m) * self.cal_b_err)**2)
        else:
            # Falls keine Kalibrierung vorliegt, benutze den theoretischen Wert
            measured_distance = (time_delay * SPEED_OF_SOUND) / 2.0
            delta_d = 0.0
        
        # Für die digitale Anzeige runden wir auf eine Auflösung von 5 cm
        resolution = 0.05  # 5 cm
        displayed_distance = round(measured_distance / resolution) * resolution

        delta_d = delta_d * 100 # Darstellung in cm
        displayed_distance = displayed_distance * 100 # Darstellung in cm
        
        self.distance_label.config(text=f"Gemessene Distanz: {displayed_distance:.0f} cm")
        self.uncertainty_label.config(text=f"Unsicherheit: ±{delta_d:.1f} cm")
        
if __name__ == "__main__":
    app = RadarApp()
    app.mainloop()