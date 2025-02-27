# Ultraschall-Distanzmessung mit Tkinter UI

## 🛠️ Projektbeschreibung
Dieses Python-Programm ermöglicht die Berechnung des Abstands zu einem Objekt mithilfe eines Ultraschallsensors. Es bietet eine grafische Benutzeroberfläche (GUI) mit Tkinter, um Messdaten aus CSV-Dateien einzulesen, die Signale zu visualisieren und den Abstand basierend auf einer Kalibrierung zu berechnen.

Die Hauptfunktionen sind:
- Laden und Visualisieren von Messsignalen (Sendesignal & Empfangssignal)
- Berechnung der Rundlaufzeit mittels Kreuzkorrelation
- Kalibrierung anhand von Messwerten (linearer Fit)
- Abstandsanzeige mit realitätsnaher Fehlerabschätzung
- Runden der Anzeige auf sinnvolle Werte (z. B. 5 cm Schritte für digitale Cockpitanzeige)

## 🔧 Installation

### 1. **Python & Abhängigkeiten installieren**
Stelle sicher, dass **Python 3.x** installiert ist. Installiere dann die benötigten Pakete mit:

```sh
pip install -r requirements.txt
```

Falls du noch keine `requirements.txt` hast, erstelle sie mit:
```sh
pip freeze > requirements.txt
```

### 2. **Programm starten**
Das Programm kann mit folgendem Befehl gestartet werden:
```sh
python radar_gui.py
```

## 🎯 Nutzung
### **1. Kalibrierung durchführen**
- Klicke auf **"Kalibriere Messdaten (Ordner)"**
- Wähle einen Ordner mit CSV-Dateien (z. B. `Messdaten/`)
- Das Programm ermittelt automatisch die Kalibrierungsgleichung:  
  
  **t(d) = m * d + b**
  
- Die kalibrierte Schallgeschwindigkeit wird berechnet und angezeigt.

### **2. Einzelmessung analysieren**
- Klicke auf **"Einzelmessung laden (CSV)"**
- Wähle eine Datei mit Messdaten aus
- Die Signale werden geplottet und die Rundlaufzeit mittels Kreuzkorrelation bestimmt
- Falls eine Kalibrierung vorliegt, wird der Abstand berechnet:
  
  **d = (t - b) / m**
  
- Die berechnete Unsicherheit wird ebenfalls angezeigt
- Die digitale Cockpitanzeige zeigt den gerundeten Abstand (z. B. auf 5 cm)

## 📊 Datenformat
Die Messdaten müssen im CSV-Format vorliegen mit **zwei Headerzeilen**, z. B.:

```
x-axis,1,2
second,Volt,Volt
-1.000000E-03,+0.0E+00,-402.010E-06
-995.000E-06,-80.402009E-03,+1.206030E-03
```

Spalten:
1. Zeitstempel (s)
2. Sendesignal (V)
3. Empfangssignal (V)

## 💡 Hinweise
- Falls keine Kalibrierung vorliegt, wird die Schallgeschwindigkeit auf **343 m/s** gesetzt (Standardwert für Luft bei 20°C).
- Falls ein gemessener Wert deutlich von der Erwartung abweicht (> 2× Literaturwert), wird er als Ausreißer erkannt und durch **343 m/s** ersetzt.
- Falls die Zeitmessung als exakt angenommen wird, berechnet sich die Unsicherheit nach der Fehlerfortpflanzungsregel.

## 🏆 Lizenz
Dieses Projekt steht unter der **MIT-Lizenz** – freie Nutzung & Modifikation erlaubt.

