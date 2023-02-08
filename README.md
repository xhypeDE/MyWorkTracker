# MyWorkTracker - Marwand Ayubi

Entwicklung einer Flask-Anwendung mit Datenbankanbindung im Rahmen der Veranstaltung 
webbasierte Systeme an der Hochschule Heilbronn im Wintersemester 2020/2021.

https://myworktracker.wirecoders.com/

## Projektstruktur

Der Projektordner enthält standardmäßig folgende Dateien und Verzeichnisse:

* **db**:
  * **db_credentials.py**: Nicht veröffentlichte Datei, enthält die Zugangsdaten zur Datenbank
  * **db_init.py**: Python-Skript zur Erstellung der Projektdatenbank
  * **db_schema.sql**: enthält SQL-Befehle zur Erzeugung der Datenbank
* **static**:
  * enthält alle statischen Dateien wie CSS-Dateien und Bilder
* **templates**:
  * enthält alle HTML-Templates
* **.gitignore**: enthält alle Dateien und Verzeichnisse, die nicht in die Versionskontrolle mit Git aufgenommen werden sollen
* **LICENSE**: enthält Lizenzbedingungen für das gesamte Projekt
* **README.md**: Diese Datei, enthält die Projektdokumentation im Markdown-Format
* **app.py**: enthält die eigentliche Flask-Anwendung

## Projektbeschreibung und Erläuterung

### Allgemeine Beschreibung

Das Websystem soll eine "kommerzielle" Lösung für kleine Unternehmen bieten, welche die Arbeitszeiten ihrer Mitarbeiter, optimalerweise im Home-Office, erfasst und dementsprechend [eine vereinfachte] Lohnabrechnung erstellt sowie eine Übersicht der Personalkosten anzeigt (und die voraussichtlichen Persoalkosten berechnet und ebenfalls anzeigt.)

### Access Level und Features

- [x] Die registrierten Nutzer im Websystem lassen sich in drei level unterteilen:

* Master-Admin = Level 3 Access
* Group-Admin = Level 2 Access
* Mitarbeiter = Level 1 Access
* Nicht-Registrierter Nutzer = Level 0 Access

Der Access Level bestimmt die Inhalte die der Nutzer sehen kann und die Funktionen auf die er zugreifen kann.
Auf der Registrierungsseite wird abgefragt ob es sich beim Nutzer um eine Person handelt, die für ein Unternehmen oder für eine Organisation das Websystem einrichten möchte, oder ob es sich um einen Mitarbeiter einer bereits bestehenden Gruppe handelt. 
Für Fall 1 werden die passenden Daten abgefragt und gespeichert und eine neue Gruppe erstellt. Für Fall 2 wird ein Invite-Code benötigt, welcher zuvor vom Group-Admin generiert werden muss.



## Projektanforderungen

### Mindestanforderungen - Allgemein

* [x] Startseite mit Buttons zu Login und Registrierung
* [x] Nutzer-Registration und Login
	* [x] Registrierung Fehlermeldungen
	* [x] Registrierung dynamische Gruppenzuweisung mit Invite-Code oder Gruppenerstellung
	* [x] Generierung Verifikationscode für E-Mail Bestätigung
	* [x] Versand des Verifikationscodes
* [x] Admin-Bereich mit Daten- und Nutzerverwaltung
* [x] Einfügen, Ändern und Löschen von Daten: Jeder Nutzer sollte nur seine eigenen Daten, Admin alle Daten bearbeiten können
* [x] Dynamisches Dashboard. (Anzeige der Menüpunkte anhand des Admin Levels des Nutzers)


### Mindestanforderungen - Dashboard
* [x] E-Mail bestätigen durch Verifikationscode
* [x] Logout Button
* [x] Features Master Admin:
	* [x] Nutzer Liste anzeigen
	* [x] Nutzer nach Gruppen listen
	* [x] Passwörter ändern 
* [x] Features Gruppen Admin:
	* [x] Kann optional seine eigene Arbeitszeit erfassen
	* [x] Kann alle Mitarbeiter seiner Organisation verwalten
		* [x] Nutzer Liste anzeigen
		* [x] Stundensätze ändern
		* [x] Arbeitszeit pro Woche ändern (Soll-Wert)
		* [x] Lohnabrechnungen generieren
		* [x] Sieht die Personalkosten Übersicht im Dashboard
		* [x] Passwörter zurücksetzen
		* [x] Invite-Code für neue Mitarbeiter zum Beitreten generieren.
* [x] Features Mitarbeiter:
	* [x] Arbeitszeit eintragen
	* [x] Benutzerdaten verwalten
	* [x] Passwort ändern
	* [x] E-Mail ändern
	* [x] Lohnabrechnung generieren
	<del>
	* [ ] Status ändern. Aktiv, Inaktiv, Urlaub etc.
	</del><br> Dieser Prozess wurde automatisiert.
	
	 
