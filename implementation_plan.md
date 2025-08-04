## 🔧 **Phase 1 – Grundstruktur & Setup**

1. **Projektverzeichnis & Ordnerstruktur anlegen**
   → `app/`, `data/`, `icons/`, `.github/workflows/`, etc.

2. **`pyproject.toml` mit `uv` einrichten**
   → OR-Tools, ReportLab, tkinter

3. **GUI-Rahmen (`tkinter`) mit Menü & Navigation**

   * Schuljahr-Auswahl
   * Tabs oder Buttons für: Lehrer, Kinder, Tandems, Einstellungen

4. **JSON-Lade- & Speicherlogik (`storage.py`)**

   * Pro Schuljahr eine Datei
   * Bei Auswahl laden, neu anlegen falls nicht vorhanden

---

## ✍️ **Phase 2 – Eingabemaske & Datenmodell**

5. **Lehrer-UI & Datenmodell (`model.py`)**

   * Name
   * Verfügbarkeit (z. B. Checkbuttons + Zeitfelder)

6. **Kinder-UI & Datenmodell**

   * Name
   * Verfügbarkeit
   * Bevorzugte Lehrer
   * Frühpräferenz

7. **Tandem-UI**

   * Dropdowns zur Auswahl von 2 Kindern
   * Prüfung auf Dopplung

8. **Konfigurationsmaske für Gewichtungen**

   * 5 Ziele als Felder oder Slider

---

## 🧠 **Phase 3 – Optimierung & Ergebnisanzeige**

9. **Slotgenerierung (Zeitraster) implementieren**
   → `"Mo", "08:00"` usw. als Tupel

10. **OR-Tools-Modell (`logic.py`)**

    * Variablen: `x[k, l, slot]`
    * Nebenbedingungen (Verfügbarkeit, 1 Slot pro Kind, max. 1/Tandem pro Lehrer)
    * Zielfunktion mit gewichteter Bewertung

11. **Lösungslogik & Fortschrittsanzeige**

    * Solve-Button mit Statusausgabe
    * Anzeige: `✅ optimal`, `⚠️ zulässig`, `❌ keine Lösung`

12. **Ergebnisstruktur + Verletzungsanalyse**

    * `assignments`, `violations`, `schedule` aufbauen
    * In JSON exportierbar

13. **Tabellarische GUI-Ergebnisanzeige**

    * Pro Lehrer, pro Slot → Name(n) anzeigen

---

## 🖨️ **Phase 4 – Export & Distribution**

14. **PDF-Export (`export_pdf.py`)**

    * Wochenraster pro Lehrer
    * Seite mit Verletzungen

15. **Build-Prozess (GitHub Actions + PyInstaller)**

    * `.exe` automatisch erzeugen bei Tag-Release
    * Upload als Release-Asset

16. **README & Dokumentation finalisieren**

    * Features, Setup, Lizenz, Beispiel-Daten

---

## ✅ **Optional – Erweiterungen später**

* Excel-Export (`openpyxl`)
* Mehrsprachigkeit (de/en)
* Farbige Slotanzeige
* Undo-/Änderungshistorie
* Unterstützung für Gruppenunterricht
