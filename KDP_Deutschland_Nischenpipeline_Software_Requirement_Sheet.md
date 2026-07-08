# Software Requirement Sheet  
# KDP Deutschland Data-Mining & Nischen-Pipeline

## 1. Projektübersicht

Die Software ist eine Python-basierte **KDP Deutschland Nischen-Pipeline** für den deutschsprachigen Amazon-KDP-Markt. Ziel ist es, profitable deutschsprachige Buchnischen auf Amazon.de zu identifizieren, bei denen eine erkennbare Nachfrage vorhanden ist, der Markt aber noch nicht vollständig gesättigt, professionell dominiert oder durch starke Review-Mauern blockiert ist.

Die Software soll nicht einfach Bestseller kopieren, sondern datenbasiert Einstiegschancen finden.

Die zentrale Frage lautet:

> Gibt es eine konkrete deutschsprachige Buchnische mit nachweisbarer Nachfrage, aber noch realistischer Chance, mit einem besseren, sauber positionierten Buch sichtbar zu werden?

Die Software analysiert:

- deutsche Suchbegriffe
- Amazon.de-Suchergebnisse
- deutschsprachige Konkurrenzbücher
- BSR-Signale
- Review-Anzahlen
- deutsche Käuferbewertungen
- Marktsättigung
- Review-Wall-Risiko
- Differenzierungspotenzial
- deutsche KDP-Buchkonzepte
- echte Sachbuch-Chancen
- Risiken bei sensiblen Themen

Am Ende soll die Software keine einfache Keyword-Liste erzeugen, sondern vollständige **KDP Nischen-Reports** mit konkreten Handlungsempfehlungen.

---

## 2. Hauptziel der Software

Die Software soll deutschsprachige KDP-Nischen finden, bei denen folgende Kombination vorliegt:

```text
deutsche Nachfrage vorhanden
+ deutscher Markt noch nicht vollständig gesättigt
+ Einstieg auf Amazon.de realistisch
+ klare Zielgruppe oder klarer Use Case
+ bessere deutsche Umsetzung möglich
= potenzielle KDP-Chance
```

Dabei soll die Software drei verschiedene Buchklassen unterscheiden:

```text
1. Low Content
Notizbücher, einfache Journals, einfache Tracker

2. Medium Content
Workbooks, Planer, strukturierte Tagebücher, Logbücher, Übungsbücher, Ausfüllbücher

3. High Content / echte Sachbücher
Ratgeber, Praxisbücher, Fachbücher, Problemlösungsbücher und erklärende Bücher mit Recherche, Struktur und inhaltlicher Tiefe
```

Für jede Buchklasse gelten eigene Bewertungskriterien.

---

## 3. Nicht-Ziele

Die Software soll nicht:

- exakte Umsatzversprechen erfinden
- behaupten, eine Nische mache garantiert einen bestimmten Monatsumsatz
- englische Buchideen einfach übersetzen
- ausschließlich schlechte Bewertungen suchen
- aggressives Scraping ohne Kontrolle betreiben
- Captcha-Bypass- oder Sperrumgehungslogik enthalten
- rechtliche, medizinische oder finanzielle Fachbehauptungen ungeprüft als Wahrheit ausgeben
- automatisch vollständige Sachbücher ohne Qualitätsprüfung veröffentlichen

Die Software soll stattdessen Wahrscheinlichkeiten, Signale und Chancen bewerten.

Richtige Aussage:

```text
Diese Nische zeigt starke Nachfrage-Signale, moderate Sättigung,
schwache Review-Mauer und hohes Differenzierungspotenzial.
```

Falsche Aussage:

```text
Diese Nische macht garantiert 8.000 € pro Monat.
```

---

## 4. Zielmarkt

Primärer Markt:

```text
Amazon.de
deutsche Keywords
deutsche Käufer
deutsche Buchkonzepte
deutsche Reviews
deutsche Kategorien
```

Sekundär optional:

```text
Amazon.at
Amazon.ch über deutschsprachige Suchintention, soweit über Amazon.de sinnvoll analysierbar
```

Die Software behandelt Deutsch nicht als Übersetzung aus dem Englischen, sondern als eigenen Markt.

---

## 5. Zielbuchtypen

Die Software soll folgende deutschsprachige KDP-Buchtypen analysieren können:

```text
Ratgeber
Praxisratgeber
Fachratgeber
Sachbücher
Arbeitsbücher
Übungsbücher
Ausfüllbücher
Planer
Journals
Tagebücher
Logbücher
Tracker
Checklisten-Bücher
Begleitbücher
Selbsthilfe-nahe Bücher
Hobbybücher
Berufsnischen-Bücher
Familien-, Pflege-, Lern- und Alltagsthemen
```

---

## 6. Grundprinzip der Nischenerkennung

Die Software sucht nicht einfach nach Bestsellern. Sie sucht nach **Einstiegschancen**.

Eine gute Nische kann auch gut bewertet sein. Schlechte Bewertungen sind nur ein Zusatzsignal.

Die Hauptfrage lautet:

```text
Ist Nachfrage vorhanden, aber der Markt noch nicht so stark besetzt,
dass ein neues gutes Buch keine realistische Chance mehr hat?
```

Negative Reviews helfen vor allem dabei, ein besseres Buchkonzept zu entwickeln.

---

## 7. Technischer Stack

### 7.1 Backend

```text
Python 3.12+
FastAPI
PostgreSQL
Redis
Celery oder RQ
SQLAlchemy
Alembic
Pydantic
httpx / aiohttp
BeautifulSoup / selectolax
Playwright nur für kontrollierte Browser-Automation
OpenAI / LLM API für Review- und Konzeptanalyse
```

### 7.2 Frontend / Dashboard

```text
Next.js
React
TailwindCSS
TanStack Table
Recharts
Markdown Export
PDF Export
CSV Export
JSON Export
```

### 7.3 Server

```text
Contabo VPS
Ubuntu 24.04 LTS
Docker
Docker Compose
Nginx
Certbot / Let’s Encrypt
PostgreSQL Volume Backup
Redis
UFW Firewall
Fail2ban
```

### 7.4 Monitoring

```text
Sentry
Uptime Kuma
Log Rotation
Daily Backup Script
Optional: Grafana
Optional: Prometheus
```

---

## 8. Saubere Datenstrategie

Die Software nutzt eine Kombination aus offiziellen Datenquellen, manuellen Importen und kontrollierter, verantwortungsbewusster Datenerfassung, da viele relevante Signale nur aus sichtbaren Amazon.de-Suchergebnissen, Listings und Bewertungen gewonnen werden können.

Die Software muss folgende Prinzipien einhalten:

```text
1. APIs nutzen, wo möglich.
2. Scraping nur in moderatem Umfang und mit klaren Rate-Limits.
3. Requests zeitlich verteilen.
4. Ergebnisse konsequent cachen.
5. Nur notwendige Daten erfassen und speichern.
6. Quellen und Erfassungszeitpunkt immer dokumentieren.
7. Keine Captcha-Bypass-Logik.
8. Keine aggressive Sperrumgehung.
9. Manuelle Importe ermöglichen.
10. Browser-Extension als kontrollierte Erfassungsvariante optional vorsehen.
```

Ziel ist nicht maximale Datenausbeute um jeden Preis, sondern eine stabile, langfristig nutzbare Analysepipeline.

---

# 9. Systemmodule

## Modul 1: Seed Keyword Manager

Der Nutzer gibt deutsche Startbegriffe ein.

Beispiele:

```text
Blutdrucktagebuch
Blutzuckertagebuch
ADHS Planer
Angst Tagebuch
Hundeerziehung Welpen
Haushaltsbuch
Pflege Tagebuch
Schwangerschaftstagebuch
Lernplaner Abitur
Fahrtenbuch
Bautagebuch
Gartentagebuch
Dankbarkeitstagebuch
Schattenarbeit Journal
Trauer Tagebuch
Rauchfrei Tagebuch
Fitness Tagebuch
Ernährungstagebuch
KI für Handwerker
Nebengewerbe starten
Pflege der Eltern organisieren
```

Jedes Seed Keyword bekommt Metadaten:

```text
Sprache
Marketplace
Buchtyp
Zielgruppe
Kategorie
Priorität
Status
Notizen
Erfassungsdatum
```

---

## Modul 2: Deutsche Keyword Expansion Engine

Aus jedem Seed Keyword erzeugt die Software systematisch deutsche Long-Tail-Varianten.

Die Engine berücksichtigt:

```text
Singular und Plural
Umlaute und Schreibvarianten
Bindestrichvarianten
zusammengesetzte deutsche Substantive
Synonyme
Alltagssprache
Fachsprache
Zielgruppen
Problembegriffe
Altersgruppen
Berufsgruppen
Familienrollen
regionale Sprachgewohnheiten
englische Lehnwörter nur dann, wenn sie im deutschen Markt wirklich gesucht werden
```

Beispiel:

Seed:

```text
Blutdrucktagebuch
```

Expansion:

```text
Blutdrucktagebuch für Senioren
Blutdrucktagebuch große Schrift
Blutdruck Tagebuch
Blutdruck Logbuch
Blutdruck und Puls Tagebuch
Blutdrucktagebuch mit Medikamentenplan
Blutdrucktagebuch für Arztbesuche
Blutdruckpass zum Eintragen
Blutdruck Tracker Buch
Blutdrucktagebuch DIN A5
```

Beispiel:

Seed:

```text
ADHS Planer
```

Expansion:

```text
ADHS Planer für Erwachsene
ADHS Tagesplaner
ADHS Wochenplaner
ADHS Journal
ADHS Tagebuch
ADHS Selbsthilfe Arbeitsbuch
ADHS Organisationshilfe
ADHS Fokus Planer
ADHS Routinen Planer
ADHS Planer Frauen
```

Die Software bewertet jedes Keyword grob nach:

```text
Spezifität
Kaufintention
Zielgruppen-Klarheit
Buchformat-Eignung
Konkurrenzwahrscheinlichkeit
Produktionsaufwand
fachliches Risiko
```

---

## Modul 3: Deutsche Suchintention

Die Software darf Keywords nicht einfach aus dem Englischen übersetzen.

Sie muss verstehen, wie deutsche Käufer tatsächlich suchen.

Beispiel:

```text
Englisch: workbook
Deutsch mögliche Varianten:
Arbeitsbuch
Übungsbuch
Begleitbuch
Selbsthilfe Buch
Praxisbuch
Ausfüllbuch
Journal
Tagebuch
Planer
```

Beispiel:

```text
Englisch: log book
Deutsch mögliche Varianten:
Logbuch
Tagebuch
Nachweisbuch
Dokumentationsbuch
Eintragbuch
Tracker
Planer
Heft
```

Das Modul erkennt, welche Begriffsfamilie für den deutschen Markt relevanter ist.

---

## Modul 4: Amazon.de Result Collector

Für jedes deutsche Keyword werden Amazon.de-Suchergebnisse gesammelt.

Pro Suchlauf werden gespeichert:

```text
Keyword
Marketplace
Datum/Uhrzeit
Suchposition
ASIN
deutscher Titel
deutscher Untertitel
Autor
Publisher
Preis in EUR
Format
Kindle vorhanden?
Taschenbuch vorhanden?
Hardcover vorhanden?
Seitenanzahl
Erscheinungsdatum
Bewertungsschnitt
Review-Anzahl
BSR, falls verfügbar
Kategorien
Cover-URL
Listing-Beschreibung
Sponsored/Organic Signal, falls sichtbar
```

Wichtig:

Ein einzelner Snapshot reicht nicht.

Die Software muss wiederholt messen:

```text
Tag 1
Tag 3
Tag 7
Tag 14
Tag 30
```

Dadurch erkennt man, ob Nachfrage stabil ist oder ob ein Buch nur kurzfristig sichtbar war.

---

## Modul 5: Book Entity Resolver

Das gleiche Buch kann über mehrere Keywords gefunden werden. Deshalb muss die Software Bücher anhand der ASIN zusammenführen.

Ein Buch kann mehreren Keywords zugeordnet sein:

```text
ASIN X erscheint für:
- ADHS Planer Erwachsene
- ADHS Wochenplaner
- ADHS Journal Erwachsene
- ADHS Selbsthilfe Arbeitsbuch
```

Dadurch entstehen Keyword- und Nischencluster.

Nicht einzelne Keywords sind entscheidend, sondern ganze **deutsche Nischenräume**.

---

## Modul 6: BSR Snapshot System

Für jedes relevante Buch speichert die Software BSR-Zeitreihen.

Gespeichert wird:

```text
ASIN
Datum
BSR Hauptwert
BSR Kategorie 1
BSR Kategorie 2
BSR Kategorie 3
Marketplace
Quelle
```

Daraus berechnet die Software:

```text
BSR Average
BSR Median
BSR Volatility
BSR Trend
BSR Stability
BSR Improvement
BSR Decay
```

Ziel:

Nicht:

```text
Ein Buch rankt heute gut.
```

Sondern:

```text
Mehrere Bücher in dieser Nische zeigen über Zeit stabile Nachfrage.
```

---

## Modul 7: Competition Strength Analyzer

Die Software bewertet, wie schwer es ist, in eine Nische einzusteigen.

Pro Keyword und Nische werden analysiert:

```text
Top-10 Review Count
Top-10 Average Rating
Top-10 BSR
Top-10 Publication Age
Cover-Qualität
Listing-Qualität
A+ Content vorhanden?
Professioneller Publisher?
Wiederkehrende Marke?
Serienstruktur?
Preisniveau
Anzahl sehr starker Bücher
Anzahl schwacher Bücher
Anzahl neuer Bücher mit Sichtbarkeit
```

Besonders wichtig:

```text
Review Wall Risk
```

Wenn die Top 10 alle sehr viele Reviews haben, ist der Einstieg schwer.

Interessanter sind Nischen, bei denen mehrere Bücher verkaufen, aber viele Top-Ergebnisse nur 20–300 Reviews haben.

---

## Modul 8: Saturation Analyzer

Die Software unterscheidet zwischen Nachfrage und Sättigung.

Eine Nische ist nicht automatisch schlecht, nur weil viele Bücher existieren.

Wichtiger ist:

```text
Wie stark sind die sichtbaren Bücher?
Wie ähnlich sind sie?
Wie professionell sind sie?
Wie schwer ist es, sich abzuheben?
Wie viele neue Bücher schaffen Sichtbarkeit?
```

Sättigungsmetriken:

```text
Result Count Signal
Review Concentration
Publisher Concentration
Title Similarity
Cover Similarity
Keyword Repetition
AI-Slop Density
Price Compression
Ad Density
New Entrant Visibility
```

Besonders starkes Signal:

```text
Neue Bücher mit wenig Reviews erscheinen sichtbar in den Top-Ergebnissen.
```

Das bedeutet:

```text
Der Markt ist noch offen.
```

---

## Modul 9: Deutsche Review Intelligence Engine

Die Software analysiert deutsche Käuferbewertungen nicht nur bei schlechten Büchern, sondern bei allen relevanten Wettbewerbern.

Gesammelt und klassifiziert werden:

```text
1-Sterne Reviews
2-Sterne Reviews
3-Sterne Reviews
4-Sterne Reviews
5-Sterne Reviews
```

Warum auch positive Reviews?

Weil positive Reviews zeigen, was der Markt bereits erwartet.

Die Review-Analyse clustert:

```text
Was lieben Käufer?
Was hassen Käufer?
Was fehlt?
Was ist unklar?
Was ist enttäuschend?
Welche Zielgruppe kauft wirklich?
Welche Wörter verwenden Käufer?
Welche Features werden mehrfach erwähnt?
Welche Beschwerden wiederholen sich?
```

Typische deutsche Review-Cluster:

```text
zu wenig Platz zum Schreiben
Schrift zu klein
Layout unübersichtlich
Inhalt zu oberflächlich
zu allgemein gehalten
zu wenig konkrete Beispiele
wirkt lieblos erstellt
zu viele Wiederholungen
schlechte Übersetzung
nicht für Deutschland passend
zu amerikanisch gedacht
Format unpraktisch
Papierqualität enttäuschend
Cover verspricht mehr als der Inhalt hält
```

Output:

```text
Review Cluster
Sentiment
Frequency
Severity
repräsentative Review-Snippets
Produktverbesserungsvorschlag
```

---

## Modul 10: AI-Slop Detection

Die Software erkennt schwache, austauschbare KI-Konkurrenz.

Das Ziel ist nicht, KI pauschal abzuwerten. Das Ziel ist, Märkte zu erkennen, in denen Käufer zwar Interesse am Thema haben, aber nur generische, oberflächliche oder schlecht lokalisierte Bücher angeboten bekommen.

Signale:

```text
Review-Beschwerden über generischen Inhalt
Review-Beschwerden über Wiederholung
Review-Beschwerden über fehlende Tiefe
unnatürliche Titelmuster
viele ähnliche Bücher vom gleichen Publisher
sehr ähnliche Cover
sehr ähnliche Inhaltsversprechen
generische Beschreibung
fehlende Beispiele
fehlende Zielgruppenanpassung
schlechte Lokalisierung für Deutschland
```

AI-Slop-Score:

```text
0 = keine Hinweise
100 = extrem generischer, austauschbarer Markt
```

Ein hoher AI-Slop-Score kann positiv sein, wenn Nachfrage vorhanden ist.

Dann lautet die Chance:

```text
Käufer wollen das Thema, aber der Markt liefert nur generische oder schlecht lokalisierte Inhalte.
```

---

## Modul 11: Niche Cluster Builder

Ein Keyword allein ist zu schwach. Die Software muss Keywords zu Nischen-Clustern zusammenführen.

Beispiel:

```text
Hundeerziehung Welpen
Welpen Trainingstagebuch
Hunde Trainingstagebuch
Welpen Erziehung Buch
Hundetraining Tagebuch
```

werden zu:

```text
Nischencluster:
Hundeerziehung / Welpen-Trainingstagebuch
```

Ein Cluster enthält:

```text
Cluster Name
Seed Keywords
Related Keywords
Top ASINs
Demand Score
Saturation Score
Competition Score
Review Pain Score
Opportunity Score
Recommended Product Type
Risk Level
```

---

# 10. Spezielles Sachbuch-Modul

## 10.1 Ziel

Die Pipeline darf nicht nur Planer, Journals, Tagebücher, Logbücher und Workbooks analysieren. Sie muss zusätzlich echte deutschsprachige Sachbuch-Nischen erkennen und bewerten.

Damit erweitert sich der Fokus auf:

```text
Ratgeber
Praxisratgeber
Fachratgeber
Problemlösungsbücher
How-to-Bücher
Einsteigerbücher
Expertenbücher
Berufsnischen-Bücher
lokale Deutschland-spezifische Sachbücher
finanzielle, rechtliche, technische, psychologische oder gesundheitliche Orientierungsthemen, sofern fachlich sauber umsetzbar
Bücher mit echter Kapitelstruktur, Recherche, Quellen, Beispielen und erklärendem Inhalt
```

---

## 10.2 Unterschied zu Low- und Medium-Content

Bei einem Logbuch oder Journal ist die wichtigste Frage:

```text
Gibt es eine konkrete Nutzungssituation und kann man das Buch besser strukturieren?
```

Bei einem echten Sachbuch ist die wichtigste Frage:

```text
Gibt es eine konkrete Wissenslücke, die Käufer lösen wollen,
und kann man dazu ein wirklich besseres, vertrauenswürdiges,
tiefes und deutschsprachig relevantes Buch erstellen?
```

Deshalb braucht die Software für Sachbücher eigene Bewertungskriterien.

---

## 10.3 Sachbuch Opportunity Score

Für echte Sachbücher wird ein separater Score berechnet:

```text
Sachbuch Opportunity Score =
deutsches Nachfrage-Signal
+ Themenlücken-Signal
+ Konkurrenz-Schwäche in Inhaltstiefe
+ Aktualitätsbedarf
+ deutsche Lokalisierungsrelevanz
+ Differenzierungspotenzial
+ Evergreen-Potenzial
+ Monetarisierungspotenzial
- Autoritätsrisiko
- Rechercheaufwand
- Haftungsrisiko
- Aktualisierungsrisiko
- starke Verlagsdominanz
- hohe Review-Mauer
```

Der normale KDP Opportunity Score bleibt bestehen, aber Sachbücher bekommen zusätzlich eine eigene Tiefenanalyse.

---

## 10.4 Sachbuch Topic Gap Analyzer

Dieses Modul analysiert echte Sachbuchthemen auf inhaltliche Lücken.

Erfasst werden pro Konkurrenzbuch:

```text
Titel
Untertitel
Autor
Publisher
Preis
Format
Seitenzahl
Erscheinungsdatum
Auflage / Aktualität, falls sichtbar
Beschreibung
Inhaltsverzeichnis, falls verfügbar
Kategorien
Review-Anzahl
Bewertungsschnitt
BSR
häufige positive Review-Themen
häufige negative Review-Themen
Zielgruppe laut Listing
tatsächliche Zielgruppe laut Reviews
```

Die Software bewertet dann:

```text
Ist das Thema noch aktuell?
Sind die Top-Bücher veraltet?
Gibt es neue gesetzliche, technische, gesellschaftliche oder wirtschaftliche Entwicklungen?
Ist das Thema stark deutschlandspezifisch?
Fehlen praktische Beispiele?
Fehlen Schritt-für-Schritt-Anleitungen?
Fehlen Checklisten oder Vorlagen?
Fehlt eine Version für Anfänger?
Fehlt eine Version für Selbstständige, Eltern, Senioren, Studenten, Auswanderer, Berufseinsteiger oder andere klare Zielgruppen?
```

---

## 10.5 Content Depth Analyzer

Dieses Modul bewertet, ob vorhandene Sachbücher inhaltlich stark oder angreifbar sind.

Signale für schwache Sachbücher:

```text
viele Reviews sagen „zu oberflächlich“
viele Reviews sagen „nichts Neues“
viele Reviews sagen „zu allgemein“
viele Reviews sagen „zu theoretisch“
viele Reviews sagen „nicht praxisnah“
viele Reviews sagen „veraltet“
viele Reviews sagen „schlecht strukturiert“
viele Reviews sagen „zu wenig Beispiele“
viele Reviews sagen „nicht für Deutschland passend“
viele Reviews sagen „liest sich wie KI“
Beschreibung ist generisch
Inhaltsverzeichnis wirkt dünn
Titel verspricht mehr als der Inhalt liefert
```

Signale für starke Sachbücher:

```text
klare Zielgruppe
starke Struktur
viele konkrete Beispiele
aktuelle Informationen
gute Leserführung
Checklisten
Praxisfälle
Vorlagen
Schritt-für-Schritt-System
gute Sprache
hohe Glaubwürdigkeit
viele positive Reviews zur Umsetzbarkeit
```

Ziel:

```text
Ist genug Raum für ein besseres, nützlicheres und klarer positioniertes Buch?
```

---

## 10.6 Authority & Risk Analyzer

Bei echten Sachbüchern ist Autorität wichtiger als bei Planern.

Die Software muss Themen nach fachlichem Risiko einteilen.

### Niedriges Risiko

```text
Organisation
Produktivität
Lernen
Haushalt
Hobbys
Reisen
Alltag
DIY
Bewerbung
Karriereorientierung
Software-Einsteigerwissen
Online-Business-Grundlagen
```

### Mittleres Risiko

```text
Steuern für Selbstständige
Auswandern
Immobilien
Finanzen
Erziehung
Psychologie-nahe Selbsthilfe
Gesundheitliche Orientierung
Ernährung
Fitness
```

### Hohes Risiko

```text
konkrete medizinische Beratung
konkrete Rechtsberatung
konkrete Steuerberatung
Investmentempfehlungen
Therapieversprechen
Diagnose- oder Behandlungsanleitungen
Sicherheit, Waffen, gefährliche Tätigkeiten
```

Bei mittlerem und hohem Risiko muss der Report klare Hinweise geben:

```text
Fachprüfung nötig
Quellen nötig
Disclaimer nötig
keine Heilversprechen
keine Rechtsberatung behaupten
keine Finanzgarantien
keine erfundenen Fakten
```

---

## 10.7 Sachbuch Blueprint Generator

Wenn eine Sachbuch-Nische interessant ist, erzeugt die Software nicht nur ein Keyword-Konzept, sondern einen vollständigen Buchplan.

Output:

```text
Arbeitstitel
Untertitel
Zielgruppe
Leserversprechen
Problem des Lesers
Positionierung
Warum dieses Buch besser sein kann
Kapitelstruktur
Unterkapitel
Praxisbeispiele
Checklisten
Vorlagen
Fallbeispiele
Glossar
Quellenbedarf
Expertenbedarf
Recherchefragen
Risiken
KDP-Keyword-Vorschläge
Kategorie-Vorschläge
Cover-Richtung
Buchumfang
Schreibaufwand
Go/Maybe/No-Go Empfehlung
```

---

## 10.8 Beispiel für eine deutsche Sachbuch-Chance

```text
Nische:
KI für Handwerker und kleine Betriebe

Mögliche Zielgruppe:
Selbstständige Handwerker, kleine lokale Dienstleister, kleine Unternehmen ohne technische Vorkenntnisse

Warum interessant:
Viele allgemeine KI-Bücher sind zu breit, zu technisch oder zu sehr auf Startups und Büroangestellte ausgerichtet.
Eine deutsche, praktische Version für Handwerker könnte eine klarere Zielgruppe bedienen.

Mögliche Differenzierung:
- konkrete Beispiele für Handwerksbetriebe
- Angebotsvorlagen
- E-Mail-Vorlagen
- Kundenkommunikation
- lokale Werbung
- einfache Automatisierungen
- keine Fachsprache
- deutsche Tools und Datenschutzkontext
- Schritt-für-Schritt-Anleitungen

Möglicher Titel:
KI für Handwerker: Wie kleine Betriebe mit einfachen Tools Zeit sparen,
bessere Angebote schreiben und neue Kunden gewinnen
```

---

## 10.9 Weitere mögliche deutsche Sachbuch-Nischenräume

```text
KI für Selbstständige
KI für Lehrer
KI für Handwerker
KI für Immobilienmakler
Online-Marketing für lokale Dienstleister
Bewerbung mit KI
Nebengewerbe starten in Deutschland
Auswandern nach Thailand für Deutsche
Rente in Thailand
Pflege der Eltern organisieren
Vollmachten und Notfallordner verstehen
ADHS im Erwachsenenalter organisieren
Lernen lernen für Schüler
Prüfungsangst bewältigen
Buchhaltung für Kleinunternehmer einfach erklärt
WordPress für Selbstständige
ChatGPT für Senioren
Digitale Ordnung für Familien
```

Diese Themen müssen einzeln auf Nachfrage, Konkurrenz, Aktualität, Risiko und fachliche Umsetzbarkeit geprüft werden.

---

# 11. Scoring-Algorithmus

## 11.1 Hauptscore

```text
KDP Deutschland Opportunity Score =
Demand Score
+ Entry Feasibility Score
+ Keyword Specificity Score
+ Differentiation Potential Score
+ New Entrant Signal
+ Review Insight Score
- Saturation Risk
- Review Wall Risk
- Brand Dominance Risk
- Content Complexity Risk
- Compliance Risk
- Price Compression Risk
```

Score von 0 bis 100.

---

## 11.2 Demand Score

Misst, ob Nachfrage vorhanden ist.

Signale:

```text
mehrere Bücher mit erkennbarem BSR
BSR-Stabilität über Zeit
mehrere verwandte Keywords
wiederkehrende Suchmuster
neue Bücher mit Sichtbarkeit
Kategorie-Relevanz
Preisniveau tragfähig
```

Bewertung:

```text
0–20: kaum Nachfrage
21–40: schwaches Signal
41–60: moderate Nachfrage
61–80: gute Nachfrage
81–100: starke Nachfrage
```

---

## 11.3 Saturation Risk

Misst, ob der Markt bereits zu voll ist.

Signale:

```text
Top-10 Bücher mit sehr vielen Reviews
starke Marken
viele professionelle Cover
viele optimierte Listings
sehr viele ähnliche Bücher
starke Preisunterbietung
dominante Publisher
hohe Ad-Dichte
```

Bewertung:

```text
0–20: kaum gesättigt
21–40: leicht besetzt
41–60: mittel besetzt
61–80: stark besetzt
81–100: sehr schwer angreifbar
```

---

## 11.4 Entry Feasibility Score

Misst, ob ein neues Buch realistisch sichtbar werden kann.

Positive Signale:

```text
Top-Ergebnisse mit unter 300 Reviews
neue Bücher ranken bereits
schwache Cover in den Top 10
schwache Listings in den Top 10
keine große Marke dominiert
Nische ist spezifisch
klarer Use Case
```

---

## 11.5 Review Wall Risk

Misst, wie stark Bewertungen den Einstieg erschweren.

```text
Top-10 Average Review Count
Median Review Count
Review Count of Position 1–3
Review Distribution
New Book Review Gap
```

Wenn alle sichtbaren Bücher tausende Bewertungen haben, ist der Markt schwer.

Wenn mehrere sichtbare Bücher unter 100–300 Reviews haben, ist der Markt offener.

---

## 11.6 Differentiation Potential Score

Misst, ob man wirklich ein besseres Buch bauen kann.

Positive Signale:

```text
Reviews zeigen klare Wünsche
Listings sind generisch
Cover sind austauschbar
Inhalte sind oberflächlich
Zielgruppe ist schlecht angesprochen
Format ist unpraktisch
es fehlen Templates, Übungen, Beispiele oder Tracker
deutscher Alltag wird nicht sauber abgedeckt
```

---

## 11.7 Content Complexity Risk

Nicht jede Nische ist gut, nur weil Nachfrage da ist.

Risiko steigt bei:

```text
medizinischen Themen
rechtlichen Themen
Finanzthemen
psychologischen Therapie-Versprechen
Prüfungsvorbereitung mit hoher Genauigkeitspflicht
Themen mit Haftungsrisiko
Themen mit Copyright-/Trademark-Risiko
```

Diese Nischen können profitabel sein, brauchen aber echte Expertise, Quellenprüfung und vorsichtige Formulierungen.

---

# 12. Datenbankmodell

## Tabelle: keywords

```sql
id
keyword
language
marketplace
seed_keyword_id
keyword_type
specificity_score
intent_score
book_type
risk_level
status
created_at
updated_at
```

## Tabelle: search_runs

```sql
id
keyword_id
marketplace
run_at
source_type
status
result_count
notes
```

## Tabelle: books

```sql
id
asin
title
subtitle
author
publisher
marketplace
formats
publication_date
page_count
description
cover_url
book_class
created_at
updated_at
```

## Tabelle: search_results

```sql
id
search_run_id
book_id
position
is_sponsored
price
rating
review_count
captured_at
```

## Tabelle: bsr_snapshots

```sql
id
book_id
marketplace
bsr_main
category_bsr_1
category_bsr_2
category_bsr_3
captured_at
source
```

## Tabelle: reviews

```sql
id
book_id
rating
title
body
review_date
verified_purchase
helpful_count
language
captured_at
```

## Tabelle: review_clusters

```sql
id
book_id
cluster_name
sentiment
frequency
severity
summary
example_snippets
suggested_improvements
created_at
```

## Tabelle: niche_clusters

```sql
id
name
description
marketplace
language
main_keyword
book_class
status
created_at
updated_at
```

## Tabelle: niche_cluster_keywords

```sql
id
niche_cluster_id
keyword_id
relevance_score
```

## Tabelle: niche_cluster_books

```sql
id
niche_cluster_id
book_id
relevance_score
```

## Tabelle: opportunity_scores

```sql
id
niche_cluster_id
demand_score
saturation_risk
entry_feasibility_score
review_wall_risk
differentiation_score
ai_slop_score
content_complexity_risk
price_compression_risk
authority_risk
research_effort_score
final_score
explanation
created_at
```

## Tabelle: sachbuch_topic_gaps

```sql
id
niche_cluster_id
topic_gap_summary
outdated_content_signal
missing_examples_signal
missing_checklists_signal
localization_gap_signal
content_depth_score
authority_required
expert_review_required
created_at
```

## Tabelle: reports

```sql
id
niche_cluster_id
title
report_type
markdown_content
pdf_path
csv_path
status
created_at
```

---

# 13. Worker-Pipeline

Die Pipeline läuft nicht synchron im Dashboard, sondern als Job-System.

## Job 1: Expand Keywords

Input:

```text
Seed Keyword
```

Output:

```text
100–1.000 deutsche Long-Tail-Keywords
```

---

## Job 2: Collect Search Results

Input:

```text
Keyword-Liste
```

Output:

```text
Top 10–50 Bücher pro Keyword
```

---

## Job 3: Normalize Books

Input:

```text
Rohdaten
```

Output:

```text
bereinigte ASIN-basierte Buchdaten
```

---

## Job 4: Classify Book Type

Input:

```text
Buchdaten
```

Output:

```text
Low Content / Medium Content / High Content / Sachbuch
```

---

## Job 5: Collect BSR Snapshots

Input:

```text
ASIN-Liste
```

Output:

```text
BSR-Zeitreihe
```

---

## Job 6: Collect Reviews

Input:

```text
ASIN-Liste
```

Output:

```text
relevante deutsche Reviews
```

---

## Job 7: Analyze Reviews

Input:

```text
Review-Daten
```

Output:

```text
Cluster, Pain Points, positive Erwartungen, Zielgruppenhinweise
```

---

## Job 8: Build Niche Clusters

Input:

```text
Keywords + Books + BSR + Reviews
```

Output:

```text
Nischencluster
```

---

## Job 9: Score Opportunities

Input:

```text
Nischencluster
```

Output:

```text
Opportunity Scores
```

---

## Job 10: Analyze Sachbuch Gaps

Input:

```text
Sachbuch-relevante Cluster
```

Output:

```text
Themenlücken, Aktualitätslücken, Autoritätsrisiken, Recherchebedarf
```

---

## Job 11: Generate Reports

Input:

```text
Top-Nischen
```

Output:

```text
Markdown/PDF/CSV Report
```

---

# 14. Dashboard

## 14.1 Overview

Zeigt:

```text
Anzahl analysierter Keywords
Anzahl gefundener Bücher
Anzahl aktiver Nischencluster
Top Opportunities
Top Sachbuch-Chancen
Risk Alerts
letzte Crawls
fehlgeschlagene Jobs
```

---

## 14.2 Keyword Explorer

Funktionen:

```text
Seed Keyword anlegen
Keyword-Cluster ansehen
Suchintention bewerten
Keyword-Status setzen
Keyword ignorieren
Keyword priorisieren
```

---

## 14.3 Niche Explorer

Zeigt pro Nische:

```text
Opportunity Score
Demand Score
Saturation Risk
Entry Feasibility
Review Wall Risk
Differentiation Potential
Top Keywords
Top Bücher
Top Beschwerden
Top Chancen
empfohlene Buchklasse
```

---

## 14.4 Competitor View

Pro Buch:

```text
Cover
Titel
Autor
Preis
Formate
BSR-Verlauf
Review-Verlauf
Kategorien
Top Keywords
Stärken
Schwächen
Buchklasse
```

---

## 14.5 Review Intelligence

Zeigt:

```text
Positive Review Cluster
Negative Review Cluster
häufige Beschwerden
fehlende Features
Käuferwörter
Zielgruppenhinweise
Produktverbesserungen
```

---

## 14.6 Sachbuch Explorer

Zeigt für echte Sachbuch-Chancen:

```text
Themenlücke
Aktualitätsbedarf
Konkurrenz-Inhaltstiefe
Autoritätsrisiko
Rechercheaufwand
Verlagsdominanz
Fachprüfungsbedarf
mögliche Kapitelstruktur
mögliche Praxisbausteine
Go/Maybe/No-Go
```

---

## 14.7 Report Builder

Erzeugt:

```text
KDP Nischenreport
Sachbuch Opportunity Report
Book Concept Report
Keyword Report
Competitor Report
Go/No-Go Report
```

Export:

```text
Markdown
PDF
CSV
JSON
```

---

# 15. Report-Struktur

Jeder Report muss folgende Struktur haben:

## 15.1 Executive Summary

```text
Nische:
Marketplace:
Sprache:
Buchklasse:
Hauptkeyword:
Opportunity Score:
Empfehlung:
GO / MAYBE / NO-GO
```

---

## 15.2 Warum diese Nische interessant ist

```text
Nachfrage-Indikatoren
BSR-Indikatoren
Keyword-Indikatoren
Konkurrenz-Indikatoren
deutsche Suchintention
```

---

## 15.3 Wettbewerb

```text
Top 10 Bücher
Review-Anzahl
BSR
Preis
Formate
Cover-Qualität
Listing-Qualität
Verlags-/Publisher-Signal
```

---

## 15.4 Sättigungsanalyse

```text
Review Wall
Publisher Dominance
Cover Similarity
Title Similarity
Price Compression
New Entrant Visibility
```

---

## 15.5 Review Intelligence

```text
Was Käufer mögen
Was Käufer kritisieren
Was fehlt
Welche Wörter Käufer verwenden
Welche Zielgruppe wirklich kauft
```

---

## 15.6 Produktchance

```text
Empfohlener Buchtyp
Zielgruppe
Positionierung
Hauptversprechen
Differenzierung
```

---

## 15.7 Buchstruktur

Für Low-/Medium-Content:

```text
Titel-Ideen
Untertitel-Ideen
Interior-Struktur
Seitenanzahl
Format
Bonus-Seiten
Templates
Tracker
Checklisten
Übungen
```

Für Sachbücher:

```text
Arbeitstitel
Untertitel
Kapitelstruktur
Unterkapitel
Praxisbeispiele
Checklisten
Vorlagen
Fallbeispiele
Glossar
Quellenbedarf
Expertenbedarf
Recherchefragen
```

---

## 15.8 Keyword-Strategie

```text
Hauptkeywords
Nebenkeywords
Long-Tail Keywords
Backend Keyword Vorschläge
Keywords vermeiden
Keyword Cluster
```

---

## 15.9 Kategorie-Strategie

```text
mögliche Kategorien
Kategorie-Relevanz
Kategorie-Risiko
Sichtbarkeitschance
```

---

## 15.10 Risikoanalyse

```text
Content Risk
Compliance Risk
Copyright Risk
Trademark Risk
Medical/Legal/Finance Risk
Production Complexity
Review Wall Risk
Saturation Risk
Authority Risk
Research Effort Risk
```

---

## 15.11 Entscheidung

```text
GO:
starke Chance, direkt Produktkonzept erstellen

MAYBE:
erst weiter beobachten, manuell prüfen oder Ads-Test machen

NO-GO:
zu gesättigt, zu riskant, zu hoher Fachaufwand oder Nachfrage zu schwach
```

---

# 16. Qualitätslogik: Was ist eine gute deutsche KDP-Nische?

Eine sehr gute KDP-Nische erfüllt möglichst viele dieser Kriterien:

```text
deutsche Käufer suchen aktiv danach
Suchbegriff ist konkret
Zielgruppe ist klar
Problem ist praktisch oder emotional relevant
mehrere Bücher zeigen Nachfrage
Top-Bücher sind nicht unbesiegbar
Top-Bücher nicht alle mit tausenden Reviews
neue Bücher können sichtbar werden
Käufer verstehen sofort den Nutzen
Buch kann besser strukturiert werden
Cover kann besser positioniert werden
Interior kann echten Mehrwert liefern
deutscher Alltag wird sauber abgedeckt
kein massives rechtliches/medizinisches Risiko
```

Eine schlechte Nische:

```text
zu allgemein
zu viele starke Bücher
zu viele Reviews
zu viele etablierte Marken
unklare Zielgruppe
keine echte Suchintention
nur Trend ohne Kaufabsicht
zu viel Preisunterbietung
zu hohes Haftungsrisiko
zu hoher Expertenanspruch ohne Expertise
```

---

# 17. Beispiel-Output: Medium Content

## Nische

```text
Blutdrucktagebuch für Senioren große Schrift
```

## Bewertung

```text
Opportunity Score: 82/100
Demand Score: 76/100
Saturation Risk: 38/100
Entry Feasibility: 81/100
Review Wall Risk: 42/100
Differentiation Potential: 88/100
Content Complexity Risk: 35/100
```

## Warum interessant?

```text
Die Nische hat klare Suchintention, praktische Nutzung und eine konkrete Zielgruppe.
Mehrere Bücher zeigen Nachfrage, aber nicht alle Wettbewerber sind professionell positioniert.
Der Markt ist nicht leer, aber auch nicht vollständig blockiert.
```

## Produktchance

```text
Ein großformatiges Blutdrucktagebuch für Senioren mit extra großen Schreibfeldern,
Medikamentenübersicht, Arzttermin-Seiten, Monatsübersichten und einfachen Trenddiagrammen.
```

## Differenzierung

```text
größere Schrift
bessere Schreibfelder
weniger klinisches Design
mehr Arzttermin-Vorbereitung
klare Wochen- und Monatsstruktur
```

---

# 18. Beispiel-Output: Sachbuch

## Nische

```text
KI für Handwerker und kleine Betriebe
```

## Bewertung

```text
Sachbuch Opportunity Score: 84/100
Demand Score: 78/100
Saturation Risk: 41/100
Content Depth Gap: 86/100
Authority Risk: 38/100
Research Effort: 55/100
Differentiation Potential: 91/100
```

## Warum interessant?

```text
Viele KI-Bücher sind zu breit, zu technisch oder zu sehr auf Startups, Büroangestellte
oder allgemeine Produktivität ausgerichtet. Eine deutsche, praktische Version für
Handwerker und lokale Dienstleister könnte eine klarere Zielgruppe bedienen.
```

## Mögliche Differenzierung

```text
konkrete Beispiele für Handwerksbetriebe
Angebotsvorlagen
E-Mail-Vorlagen
Kundenkommunikation
lokale Werbung
einfache Automatisierungen
keine Fachsprache
deutsche Tools und Datenschutzkontext
Schritt-für-Schritt-Anleitungen
```

## Möglicher Titel

```text
KI für Handwerker:
Wie kleine Betriebe mit einfachen Tools Zeit sparen,
bessere Angebote schreiben und neue Kunden gewinnen
```

---

# 19. Deployment auf Contabo VPS

## 19.1 Server-Struktur

```text
/app
  /backend
  /frontend
  /worker
  /scheduler
  /nginx
  /postgres
  /redis
  /backups
  docker-compose.yml
  .env
```

---

## 19.2 Docker Services

```yaml
services:
  backend:
    description: FastAPI App

  worker:
    description: Celery oder RQ Worker

  scheduler:
    description: Celery Beat oder APScheduler

  frontend:
    description: Next.js Dashboard

  postgres:
    description: PostgreSQL Database

  redis:
    description: Queue + Cache

  nginx:
    description: Reverse Proxy + SSL
```

---

## 19.3 Sicherheitssetup

```text
SSH nur mit Key
Root Login deaktivieren
UFW Firewall
Fail2ban
Nginx Rate Limits
.env Secrets
Datenbank nicht öffentlich erreichbar
tägliche Backups
wöchentliche externe Backup-Kopie
Log Rotation
Monitoring
```

---

# 20. Entwicklungsphasen

## Phase 1: Core Research Engine

Ziel:

```text
Seed Keyword rein, deutsche Nischenanalyse raus.
```

Funktionen:

```text
Keyword Manager
deutsche Keyword Expansion
Amazon.de Search Result Collection
Book Normalization
Basic BSR Snapshot
Basic Review Collection
Basic Scoring
Markdown Export
```

---

## Phase 2: Review Intelligence

Funktionen:

```text
deutsches Review Clustering
Pain Point Detection
Positive Expectation Detection
AI-Slop Detection
Product Improvement Suggestions
Zielgruppenhinweise
```

---

## Phase 3: Niche Cluster System

Funktionen:

```text
Keyword Clustering
ASIN Clustering
Niche Cluster Builder
Opportunity Score v2
Saturation Score
Review Wall Risk
New Entrant Detection
```

---

## Phase 4: Sachbuch-Modul

Funktionen:

```text
Sachbuch-Erkennung
Topic Gap Analyzer
Content Depth Analyzer
Authority & Risk Analyzer
Sachbuch Blueprint Generator
Quellenbedarf-Erkennung
Rechercheaufwand-Bewertung
```

---

## Phase 5: Dashboard

Funktionen:

```text
Next.js Dashboard
Niche Explorer
Keyword Explorer
Competitor View
Review Intelligence View
Sachbuch Explorer
Report Builder
```

---

## Phase 6: Report Automation

Funktionen:

```text
PDF Export
CSV Export
Book Concept Generator
KDP Metadata Draft
Category Suggestions
Cover Direction
Interior Blueprint
Sachbuch Blueprint
Go/No-Go Report
```

---

# 21. Definition of Done

Die Software ist erst akzeptabel, wenn sie:

```text
1. aus einem deutschen Seed Keyword mindestens 100 relevante deutsche Long-Tail-Ideen erzeugt
2. pro Keyword sichtbare Amazon.de-KDP-Konkurrenz erfasst
3. Bücher über ASIN sauber dedupliziert
4. BSR-Snapshots historisch speichert
5. deutsche Review-Daten strukturiert auswertet
6. Keyword-Cluster zu echten deutschen Nischen clustert
7. Nachfrage und Sättigung getrennt bewertet
8. Review-Wall-Risiko berechnet
9. neue Einstiegschancen erkennt
10. Nischen nach Opportunity Score rankt
11. Low Content, Medium Content und echte Sachbücher unterscheidet
12. für Sachbücher Content Depth, Topic Gaps, Authority Risk und Rechercheaufwand bewertet
13. klare GO/MAYBE/NO-GO-Entscheidungen ausgibt
14. konkrete deutsche Buchkonzepte generiert
15. deutsche Titel-, Untertitel-, Keyword- und Kategorieideen erzeugt
16. Reports als Markdown/PDF/CSV exportiert
17. auf Contabo stabil per Docker läuft
18. Logs, Backups und Fehlerbehandlung besitzt
19. keine exakten Umsatzversprechen erfindet
20. jede Empfehlung anhand gespeicherter Daten begründet
21. sensible Themen mit Fachprüfungs- und Risiko-Hinweisen markiert
```

---

# 22. Sachbuch-spezifische Definition of Done

Das Sachbuch-Modul ist erst akzeptabel, wenn es:

```text
1. echte Sachbuchthemen von Journals, Planern und Logbüchern unterscheiden kann
2. deutsche Sachbuch-Konkurrenz auf Amazon.de analysiert
3. Inhaltslücken anhand von Reviews, Listings und Struktur erkennt
4. Aktualitätsrisiken bewertet
5. Autoritäts- und Haftungsrisiken einstuft
6. Themen nach Rechercheaufwand bewertet
7. konkrete deutsche Sachbuchkonzepte erzeugt
8. Kapitelstrukturen und Praxisbausteine vorschlägt
9. Quellenbedarf und Expertenprüfungsbedarf markiert
10. keine erfundenen Fachbehauptungen als Wahrheit ausgibt
11. bei sensiblen Themen klare Qualitäts- und Prüfhinweise ausgibt
12. Go/Maybe/No-Go nicht nur nach Marktchance, sondern auch nach Umsetzbarkeit bewertet
```

---

# 23. Finale Kurzbeschreibung

Die Software ist eine Python-basierte **KDP Deutschland Opportunity Intelligence Engine** für Amazon.de.

Sie analysiert deutsche Suchbegriffe, deutsche Buchkonkurrenz, Amazon.de-BSR-Signale, deutsche Bewertungen, Sättigung, Review-Wall-Risiko und Differenzierungspotenzial.

Zusätzlich erkennt sie echte deutschsprachige Sachbuch-Chancen und bewertet diese nach Inhaltstiefe, Aktualität, Autoritätsrisiko, Rechercheaufwand und Umsetzbarkeit.

Der Kern lautet:

```text
deutsche Nachfrage vorhanden
+ deutscher Markt noch nicht gesättigt
+ Einstieg auf Amazon.de realistisch
+ bessere deutsche Umsetzung möglich
+ passende Buchklasse erkannt
= KDP-Chance
```

Die Software erzeugt am Ende keine englischen Buchideen und keine generischen Keyword-Listen, sondern konkrete deutschsprachige Buchkonzepte, Reports und Go-/No-Go-Entscheidungen für den deutschen KDP-Markt.
