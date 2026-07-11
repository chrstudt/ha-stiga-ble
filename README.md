# ⚠️ ACHTUNG: Integration stark in Entwicklung ⚠️

> **WICHTIGER HINWEIS:** Diese Integration befindet sich aktuell noch **stark in der Entwicklung** (Work in Progress). Funktionen können sich jederzeit ändern, und Fehler sind zu erwarten. Die Nutzung erfolgt auf eigene Gefahr!

# Stiga G1200 BLE - Home Assistant Custom Component

Diese Custom Component integriert den Stiga G1200 Mähroboter in Home Assistant über Bluetooth Low Energy (BLE). Die Kommunikation wird direkt über die internen Home Assistant Bluetooth-Manager geroutet. 

> **Zwingende Voraussetzung:** Da die Integration eine aktive Bluetooth-Verbindung (Active Connections) aufbauen und aufrechterhalten muss, um Status-Benachrichtigungen vom Mäher zu abonnieren, wird zwingend ein fähiger **ESPHome Bluetooth Proxy** benötigt! 
> *(Hinweis: Shelly Bluetooth Proxys unterstützen aktuell keine ausreichenden aktiven Verbindungen für diesen Zweck und können daher mit dieser Integration nicht genutzt werden. Die Integration versucht, Shelly-Proxys bei der Verbindungsherstellung automatisch zu ignorieren.)*

## Features
- Lokale Überwachung und Steuerung (ohne Cloud).
- Erfordert einen **ESPHome Bluetooth Proxy** für zuverlässige aktive Verbindungen.
- Liest Batteriestatus und Mäherstatus (Mowing, Charging, Error etc.) direkt über Bluetooth-Notifications.
- Steuerungs-Buttons für Start, Stop, Home und sofortigen Status-Refresh.

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

Home Assistant wird die Integration laden und dir eine Batterie- sowie Status-Entität zur Verfügung stellen.

## Fehlerbehebung
- **Keine Sensordaten:** Stelle sicher, dass sich der Mähroboter in der Nähe deines Home Assistant Hosts oder deines **ESPHome Bluetooth Proxys** befindet. Der Proxy muss zwingend aktive Verbindungen (`active: true`) unterstützen! Shelly Proxys funktionieren hierfür *nicht*.
- **Entity wird nicht erstellt:** Prüfe die Home Assistant Logs (unter Einstellungen -> System -> Logs) auf Fehler der Integration `stiga_ble`.

## Zukünftige Features (Roadmap)
- **Diagnose:** Hinzufügen einer Entität für die BLE-Signalstärke (RSSI) zur Überprüfung der Verbindung zwischen Proxy und Mäher.
- **Benachrichtigungen (Subskriptionen):** Noch robustere Handhabung von Verbindungsabbrüchen.
