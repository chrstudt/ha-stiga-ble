# Stiga G1200 BLE - Home Assistant Custom Component

Diese Custom Component integriert den Stiga G1200 Mähroboter in Home Assistant über Bluetooth Low Energy (BLE). Die Kommunikation wird direkt über die internen Home Assistant Bluetooth-Manager geroutet, was bedeutet, dass **Active Bluetooth Proxys (z.B. Shelly)** nahtlos unterstützt werden.

## Features
- Lokale Push-Steuerung (ohne Cloud).
- Unterstützt Shelly Bluetooth Proxys und andere ESPHome Proxys.
- Start-Button Entität, um den Mähroboter asynchron zu starten.

## Installation via HACS

Diese Integration ist vollständig HACS-kompatibel.

1. Gehe in Home Assistant zu **HACS** -> **Integrationen**.
2. Klicke auf die drei Punkte oben rechts und wähle **Benutzerdefinierte Repositories**.
3. Füge die URL dieses GitHub-Repositories hinzu und wähle als Kategorie **Integration**.
4. Klicke auf **Hinzufügen** und lade die Integration herunter.
5. Starte Home Assistant neu.

## Manuelle Installation

1. Lade das Repository als ZIP herunter oder klone es.
2. Kopiere den Ordner `custom_components/stiga_ble` in dein lokales `custom_components` Verzeichnis deiner Home Assistant Installation.
3. Starte Home Assistant neu.

## Konfiguration

Nach der Installation kannst du die Integration bequem über die Home Assistant Benutzeroberfläche hinzufügen:

1. Gehe in Home Assistant zu **Einstellungen** -> **Geräte & Dienste**.
2. Klicke unten rechts auf **Integration hinzufügen**.
3. Suche nach **Stiga G1200 BLE** und wähle die Integration aus.
4. Gib im folgenden Dialog die **MAC-Adresse** deines Mähroboters ein (z.B. `34:AB:95:47:B2:E6`).
5. Klicke auf **Senden**.

Home Assistant wird die Integration laden und dir eine Start-Button-Entität zur Verfügung stellen.

## Fehlerbehebung
- **Keine Verbindung / Timeout:** Stelle sicher, dass sich der Mähroboter in der Nähe deines Home Assistant Hosts oder eines **aktiven** Bluetooth-Proxys befindet.
- **Entity wird nicht erstellt:** Prüfe die Home Assistant Logs (unter Einstellungen -> System -> Logs) auf Fehler der Integration `stiga_ble`.

## Zukünftige Features (Roadmap)
- Hinzufügen von Befehlen für "Stop" und "Home" (Rückkehr zur Ladestation).
- **Sensoren:** Auslesen des Batteriestatus (Ladezustand in %) und der aktuellen Mäh-Aktivität (Mäht, Lädt, Fehler).
- **Diagnose:** Hinzufügen einer Entität für die BLE-Signalstärke (RSSI) zur Überprüfung der Verbindung zwischen Proxy und Mäher.
- **Benachrichtigungen (Subskriptionen):** Reagieren auf spontane Statusänderungen des Mähers, um Home Assistant direkt zu aktualisieren (Push statt Polling).
- **Zeitpläne & Zonen:** (Falls per BLE unterstützt) Steuerung von speziellen Startpunkten und Mähzeiten direkt über Home Assistant.
