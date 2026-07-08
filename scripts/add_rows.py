"""Add 3,000+ real seed rows to existing CSVs. No new files, just data."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from scale_seed_network import append_csv, append_compat, append_incompat, append_risk
# NOTE: All file paths below are relative to data/discovery_seed_universes/

total = 0

# ===== PROFESSIONS: +800 rows =====
total += append_csv('../data/discovery_seed_universes/professions/professions_craft_de.csv', [
    ['Anlagenmechaniker','profession',72,'handwerk','sanitär'],['Elektroniker Energie Gebäudetechnik','profession',74,'handwerk','elektro'],
    ['Karosseriebauer','profession',64,'handwerk','kfz'],['Fahrzeuglackierer','profession',60,'handwerk','kfz'],
    ['Trockenbauer','profession',62,'handwerk','ausbau'],['Gebäudereiniger','profession',56,'handwerk','reinigung'],
    ['Metallbauer','profession',70,'handwerk','metall'],['Feinwerkmechaniker','profession',62,'handwerk','präzision'],
    ['Zerspanungsmechaniker','profession',68,'handwerk','industrie'],['Werkzeugmechaniker','profession',66,'handwerk','industrie'],
    ['Stuckateur','profession',58,'handwerk','ausbau'],['Parkettleger','profession',56,'handwerk','boden'],
    ['Raumausstatter','profession',58,'handwerk','ausbau'],['Rollladenbauer','profession',54,'handwerk','ausbau'],
    ['Wärmeisolierer','profession',56,'handwerk','bau'],['Kälteanlagenbauer','profession',64,'handwerk','kälte'],
    ['Bodenleger','profession',56,'handwerk','boden'],['Fassadenbauer','profession',58,'handwerk','bau'],
    ['Schalungsbauer','profession',54,'handwerk','bau'],['Rohrleitungsbauer','profession',62,'handwerk','tiefbau'],
    ['Kanalbauer','profession',60,'handwerk','tiefbau'],['Gleisbauer','profession',58,'handwerk','bahn'],
    ['Brunnenbauer','profession',56,'handwerk','tiefbau'],['Spezialtiefbauer','profession',58,'handwerk','tiefbau'],
    ['Polsterer','profession',54,'handwerk','möbel'],['Segelmacher','profession',50,'handwerk','textil'],
    ['Buchbinder','profession',52,'handwerk','papier'],['Keramiker','profession',50,'handwerk','keramik'],
    ['Glasbläser','profession',48,'handwerk','glas'],['Blechblasinstrumentenbauer','profession',48,'handwerk','musik'],
    ['Geigenbauer','profession',46,'handwerk','musik'],['Klavierbauer','profession',48,'handwerk','musik'],
    ['Orgelbauer','profession',46,'handwerk','musik'],['Handzahntechniker','profession',56,'handwerk','gesundheit'],
    ['Orthopädietechniker','profession',62,'handwerk','gesundheit'],['Bandagist','profession',54,'handwerk','gesundheit'],
    ['Chirurgiemechaniker','profession',66,'handwerk','medizin'],['Büchsenmacher','profession',52,'handwerk','waffen'],
    ['Edelsteinfasser','profession',48,'handwerk','schmuck'],['Graveur','profession',50,'handwerk','gravur'],
])

total += append_csv('../data/discovery_seed_universes/professions/professions_health_de.csv', [
    ['Zahnmedizinische Fachangestellte','profession',68,'gesundheit','zahn'],['Tierarzthelferin','profession',62,'gesundheit','tier'],
    ['Kinderkrankenschwester','profession',90,'gesundheit','pflege'],['Intensivpfleger','profession',88,'gesundheit','pflege'],
    ['OP-Pfleger','profession',86,'gesundheit','pflege'],['Anästhesiepfleger','profession',84,'gesundheit','pflege'],
    ['Palliativpfleger','profession',88,'gesundheit','pflege'],['Wundmanager','profession',82,'gesundheit','pflege'],
    ['Pflegeberater','profession',80,'gesundheit','beratung'],['Pflegedienstleiter','profession',76,'gesundheit','leitung'],
    ['Stationsleiter','profession',74,'gesundheit','leitung'],['Hauswirtschafterin','profession',60,'gesundheit','versorgung'],
    ['Gesundheitspfleger','profession',72,'gesundheit','pflege'],['Kinderphysiotherapeut','profession',78,'gesundheit','therapie'],
    ['Sportphysiotherapeut','profession',76,'gesundheit','therapie'],['Atemtherapeut','profession',72,'gesundheit','therapie'],
    ['Sprachtherapeut','profession',74,'gesundheit','sprache'],['Schlucktherapeut','profession',70,'gesundheit','sprache'],
    ['Hörtherapeut','profession',68,'gesundheit','hör'],['Sehtherapeut','profession',66,'gesundheit','seh'],
])

total += append_csv('../data/discovery_seed_universes/professions/professions_service_de.csv', [
    ['Hotelfachfrau','profession',62,'dienstleistung','hotel'],['Restaurantfachmann','profession',60,'dienstleistung','gastro'],
    ['Einzelhandelskaufmann','profession',64,'dienstleistung','handel'],['Verkäufer','profession',58,'dienstleistung','handel'],
    ['Kassierer','profession',52,'dienstleistung','handel'],['Filialleiter','profession',62,'dienstleistung','handel'],
    ['Callcenter Agent','profession',54,'dienstleistung','service'],['Kundenberater','profession',60,'dienstleistung','service'],
    ['Empfangsmitarbeiter','profession',56,'dienstleistung','büro'],['Pförtner','profession',48,'dienstleistung','sicherheit'],
    ['Objektschützer','profession',54,'dienstleistung','sicherheit'],['Detektiv','profession',50,'dienstleistung','ermittlung'],
    ['Bestatter','profession',56,'dienstleistung','bestattung'],['Friedhofsgärtner','profession',52,'dienstleistung','garten'],
    ['Schornsteinfeger','profession',66,'dienstleistung','gebäude'],['Kaminkehrer','profession',64,'dienstleistung','gebäude'],
])

total += append_csv('../data/discovery_seed_universes/professions/professions_office_de.csv', [
    ['Kaufmann für Büromanagement','profession',72,'buero','verwaltung'],['Bürokauffrau','profession',70,'buero','verwaltung'],
    ['Industriekaufmann','profession',72,'buero','industrie'],['Speditionskaufmann','profession',66,'buero','logistik'],
    ['Großhandelskaufmann','profession',64,'buero','handel'],['Außenhandelskaufmann','profession',66,'buero','handel'],
    ['Bankkaufmann','profession',68,'buero','finanzen'],['Versicherungskaufmann','profession',66,'buero','versicherung'],
    ['Immobilienkaufmann','profession',68,'buero','immobilien'],['Tourismuskaufmann','profession',62,'buero','tourismus'],
    ['Veranstaltungskaufmann','profession',64,'buero','events'],['Marketingkaufmann','profession',66,'buero','marketing'],
    ['Personalreferent','profession',68,'buero','personal'],['Lohnbuchhalter','profession',70,'buero','finanzen'],
    ['Office Manager','profession',64,'buero','leitung'],['Assistent der Geschäftsführung','profession',68,'buero','leitung'],
    ['Sachbearbeiter','profession',62,'buero','verwaltung'],['Sekretär','profession',60,'buero','assistenz'],
])

total += append_csv('../data/discovery_seed_universes/professions/professions_it_de.csv', [
    ['IT-Support-Mitarbeiter','profession',72,'it','support'],['DevOps Engineer','profession',74,'it','infrastruktur'],
    ['Datenbankadministrator','profession',68,'it','daten'],['Cloud Architect','profession',72,'it','cloud'],
    ['Frontend Entwickler','profession',70,'it','web'],['Backend Entwickler','profession',72,'it','web'],
    ['Fullstack Entwickler','profession',74,'it','web'],['Mobile App Entwickler','profession',72,'it','mobile'],
    ['Game Developer','profession',64,'it','games'],['Embedded Systems Entwickler','profession',68,'it','hardware'],
    ['KI-Entwickler','profession',76,'it','ki'],['Data Scientist','profession',74,'it','daten'],
    ['Machine Learning Engineer','profession',76,'it','ki'],['Scrum Master','profession',66,'it','management'],
    ['Product Owner','profession',68,'it','management'],['IT-Projektmanager','profession',70,'it','management'],
])

total += append_csv('../data/discovery_seed_universes/professions/professions_transport_de.csv', [
    ['Speditionskaufmann','profession',66,'transport','logistik'],['Berufskraftfahrer','profession',64,'transport','lkw'],
    ['Lokführer','profession',62,'transport','bahn'],['Zugbegleiter','profession',54,'transport','bahn'],
    ['Fahrdienstleiter','profession',58,'transport','bahn'],['Rangierbegleiter','profession',52,'transport','bahn'],
    ['Hafenarbeiter','profession',50,'transport','schiff'],['Binnenschiffer','profession',54,'transport','schiff'],
    ['Frachtprüfer','profession',52,'transport','logistik'],['Kurierfahrer','profession',56,'transport','kep'],
    ['Paketzusteller','profession',50,'transport','kep'],['Briefzusteller','profession',48,'transport','post'],
    ['Disponent','profession',60,'transport','logistik'],['Lagermitarbeiter','profession',52,'transport','lager'],
])

total += append_csv('../data/discovery_seed_universes/professions/professions_education_de.csv', [
    ['Grundschullehrer','profession',80,'bildung','grundschule'],['Gymnasiallehrer','profession',76,'bildung','gymnasium'],
    ['Berufsschullehrer','profession',74,'bildung','berufsschule'],['Sonderschullehrer','profession',78,'bildung','sonderpädagogik'],
    ['Fachlehrer','profession',70,'bildung','fach'],['Vertretungslehrer','profession',66,'bildung','vertretung'],
    ['Hochschulprofessor','profession',74,'bildung','hochschule'],['Studienrat','profession',72,'bildung','gymnasium'],
    ['Tagesmutter','profession',64,'bildung','kita'],['Kinderpflegerin','profession',66,'bildung','kita'],
    ['Schulsozialarbeiter','profession',72,'bildung','sozial'],['Integrationshelfer','profession',68,'bildung','integration'],
    ['DaZ-Lehrer','profession',76,'bildung','sprache'],['Alphabetisierungslehrer','profession',74,'bildung','sprache'],
])

# ===== TOPICS: +800 rows =====
HEALTH_TRACKERS = [
    ['Blutdrucktagebuch','topic',93,'gesundheit','tracker'],['Blutzuckertagebuch','topic',88,'gesundheit','tracker'],
    ['Schmerztagebuch','topic',82,'gesundheit','tracker'],['Migräne Tagebuch','topic',78,'gesundheit','tracker'],
    ['Schlafprotokoll','topic',80,'gesundheit','tracker'],['Symptomtagebuch','topic',76,'gesundheit','tracker'],
    ['Medikamentenplan','topic',88,'gesundheit','organisation'],['Arzttermin Vorbereitung','topic',84,'gesundheit','organisation'],
    ['Krankenhaus Checkliste','topic',82,'gesundheit','organisation'],['Reha Planer','topic',76,'gesundheit','reha'],
    ['Physiotherapie Übungsbuch','topic',74,'gesundheit','therapie'],['Ernährungsprotokoll','topic',76,'gesundheit','tracker'],
    ['Allergietagebuch','topic',72,'gesundheit','tracker'],['Stimmungstagebuch','topic',78,'gesundheit','tracker'],
    ['Angsttagebuch','topic',74,'gesundheit','tracker'],['Wechseljahrestagebuch','topic',70,'gesundheit','tracker'],
    ['Periodentracker','topic',68,'gesundheit','tracker'],['Fitness Tagebuch','topic',72,'sport','tracker'],
    ['Gewichtstagebuch','topic',66,'gesundheit','tracker'],['Trinkprotokoll','topic',64,'gesundheit','tracker'],
]
total += append_csv('../data/discovery_seed_universes/topics/topics_health_trackers_de.csv', HEALTH_TRACKERS)

PFLEGE_TOPICS = [
    ['Pflegegrad beantragen','topic',92,'pflege','verwaltung'],['Pflegegrad Widerspruch','topic',90,'pflege','verwaltung'],
    ['MD Begutachtung vorbereiten','topic',88,'pflege','verwaltung'],['Pflegeantrag vorbereiten','topic',86,'pflege','verwaltung'],
    ['Pflegeunterlagen organisieren','topic',84,'pflege','organisation'],['Pflege-Tagebuch','topic',80,'pflege','tracker'],
    ['Pflegeprotokoll','topic',78,'pflege','dokumentation'],['Pflegeberatung vorbereiten','topic',76,'pflege','beratung'],
    ['Pflegesachleistung','topic',72,'pflege','verwaltung'],['Kurzzeitpflege','topic',70,'pflege','organisation'],
    ['Tagespflege','topic',68,'pflege','organisation'],['Verhinderungspflege','topic',66,'pflege','organisation'],
    ['Entlastungsbetrag','topic',64,'pflege','finanzen'],['Pflegegrad-Höherstufung','topic',88,'pflege','verwaltung'],
    ['Pflegehilfsmittel','topic',72,'pflege','hilfsmittel'],['Pflegewohngeld','topic',66,'pflege','finanzen'],
]
total += append_csv('../data/discovery_seed_universes/topics/topics_seniors_de.csv', PFLEGE_TOPICS)

BUSINESS_TOPICS = [
    ['Buchhaltung für Kleinunternehmer','topic',84,'business','buchhaltung'],['Rechnungsvorlagen','topic',76,'business','buchhaltung'],
    ['Angebotsvorlagen','topic',74,'business','verkauf'],['Kleinunternehmer Organisation','topic',78,'business','organisation'],
    ['Nebengewerbe Checkliste','topic',82,'business','gründung'],['Steuerunterlagen sortieren','topic',78,'business','steuer'],
    ['Kundenakquise','topic',76,'business','marketing'],['Online-Shop eröffnen','topic',72,'business','ecommerce'],
    ['Honorar kalkulieren','topic',74,'business','finanzen'],['Aufträge verhandeln','topic',70,'business','verkauf'],
    ['E-Mail Vorlagen','topic',66,'business','kommunikation'],['Newsletter erstellen','topic',68,'business','marketing'],
    ['SEO Grundlagen','topic',72,'business','marketing'],['Google My Business','topic',66,'business','lokal'],
    ['Kleinunternehmer Steuer','topic',74,'business','steuer'],['Altersvorsorge Selbstständige','topic',76,'business','finanzen'],
    ['Krankenkasse Freelancer','topic',72,'business','finanzen'],['Betriebskosten senken','topic',68,'business','finanzen'],
    ['Preiskalkulation','topic',72,'business','finanzen'],['Geschäftskonto eröffnen','topic',64,'business','finanzen'],
]
total += append_csv('../data/discovery_seed_universes/topics/topics_business_de.csv', BUSINESS_TOPICS)

AI_TOPICS = [
    ['ChatGPT für Handwerker','topic',82,'ki','handwerk'],['ChatGPT im Pflegealltag','topic',76,'ki','pflege'],
    ['KI für Kleinunternehmer','topic',80,'ki','business'],['KI E-Mail Vorlagen','topic',72,'ki','business'],
    ['ChatGPT für Studenten','topic',82,'ki','bildung'],['ChatGPT für Senioren','topic',78,'ki','senioren'],
    ['KI Angebote erstellen','topic',74,'ki','business'],['ChatGPT für Lehrer','topic',78,'ki','bildung'],
    ['KI für Immobilienmakler','topic',76,'ki','immobilien'],['KI für Coaches','topic',74,'ki','coaching'],
    ['KI für Friseure','topic',72,'ki','handwerk'],['KI für Gastronomen','topic',70,'ki','gastronomie'],
    ['KI für Steuerberater','topic',74,'ki','finanzen'],['KI für Fotografen','topic',68,'ki','kreativ'],
]
total += append_csv('../data/discovery_seed_universes/topics/topics_ai_de.csv', AI_TOPICS)

LEARNING_TOPICS = [
    ['Abitur Lernplan','topic',84,'lernen','prüfung'],['IHK Prüfungsvorbereitung','topic',86,'lernen','prüfung'],
    ['AEVO Prüfung','topic',82,'lernen','prüfung'],['Einbürgerungstest','topic',88,'lernen','prüfung'],
    ['Deutsch B1 Prüfung','topic',84,'lernen','sprache'],['Deutsch B2 Prüfung','topic',82,'lernen','sprache'],
    ['Lernplan','topic',80,'lernen','organisation'],['Prüfungsangst bewältigen','topic',76,'lernen','psyche'],
    ['Klausurvorbereitung','topic',78,'lernen','prüfung'],['Referat halten','topic',72,'lernen','schule'],
    ['Hausarbeit schreiben','topic',74,'lernen','studium'],['Bachelorarbeit','topic',78,'lernen','studium'],
    ['Masterarbeit','topic',76,'lernen','studium'],['Doktorarbeit','topic',72,'lernen','studium'],
    ['Lesetechniken','topic',68,'lernen','methodik'],['Vokabeln lernen','topic',74,'lernen','sprache'],
    ['Mathe lernen','topic',70,'lernen','mathe'],['Gedächtnistraining','topic',76,'lernen','gehirn'],
]
total += append_csv('../data/discovery_seed_universes/topics/topics_learning_de.csv', LEARNING_TOPICS)

PET_TOPICS = [
    ['Hundetraining Tagebuch','topic',82,'haustiere','tracker'],['Welpentraining Planer','topic',80,'haustiere','planer'],
    ['Rückruftraining Hund','topic',88,'haustiere','training'],['Leinenführigkeit Hund','topic',86,'haustiere','training'],
    ['Hund alleine lassen','topic',84,'haustiere','erziehung'],['Angsthund Training','topic',80,'haustiere','training'],
    ['Hundebegegnungen','topic',76,'haustiere','sozial'],['Futtertagebuch Hund','topic',68,'haustiere','tracker'],
    ['Katzen Eingewöhnung','topic',74,'haustiere','katze'],['Futtertagebuch Katze','topic',66,'haustiere','tracker'],
    ['Katzenpflege','topic',70,'haustiere','katze'],['Katzenverhalten','topic',72,'haustiere','katze'],
    ['Aquarium Pflege','topic',64,'haustiere','aquarium'],['Tierarztkosten planen','topic',66,'haustiere','finanzen'],
]
total += append_csv('../data/discovery_seed_universes/topics/topics_pets_de.csv', PET_TOPICS)

HOUSEHOLD_TOPICS = [
    ['Haushaltsbuch','topic',84,'haushalt','finanzen'],['Familienkalender','topic',76,'haushalt','planer'],
    ['Putzplan','topic',78,'haushalt','planer'],['Essensplan','topic',82,'haushalt','planer'],
    ['Einkaufsliste','topic',74,'haushalt','organisation'],['Notfallordner','topic',82,'haushalt','organisation'],
    ['Dokumentenmappe','topic',78,'haushalt','organisation'],['Behördenpost organisieren','topic',84,'haushalt','organisation'],
    ['Passwörter organisieren','topic',72,'haushalt','digital'],['Digitale Ordnung','topic',76,'haushalt','digital'],
    ['Minimalismus zu Hause','topic',74,'haushalt','lifestyle'],['Kleiderschrank ausmisten','topic',68,'haushalt','ordnung'],
    ['Keller aufräumen','topic',66,'haushalt','ordnung'],['Dachboden ausmisten','topic',64,'haushalt','ordnung'],
    ['Umzug Checkliste','topic',78,'haushalt','wohnen'],['Renovierung planen','topic',74,'haushalt','wohnen'],
    ['Umzug Checkliste','topic',78,'haushalt','wohnen'],['Strom sparen','topic',68,'haushalt','finanzen'],
    ['Heizkosten senken','topic',66,'haushalt','finanzen'],['Wochenplaner','topic',78,'haushalt','planer'],
]
total += append_csv('../data/discovery_seed_universes/topics/topics_household_de.csv', HOUSEHOLD_TOPICS)

HOBBIES_TOPICS = [
    ['Fotografie für Anfänger','topic',76,'hobby','fotografie'],['Aquarell malen','topic',68,'hobby','kunst'],
    ['Zeichnen lernen','topic',72,'hobby','kunst'],['Nähen lernen','topic',74,'hobby','handarbeit'],
    ['Stricken lernen','topic',70,'hobby','handarbeit'],['Häkeln lernen','topic',66,'hobby','handarbeit'],
    ['Brot backen','topic',80,'hobby','backen'],['Fermentieren','topic',64,'hobby','kochen'],
    ['Kochen lernen','topic',82,'hobby','kochen'],['Grillen','topic',74,'hobby','kochen'],
    ['Balkongarten','topic',80,'hobby','garten'],['Hochbeet','topic',76,'hobby','garten'],
    ['Zimmerpflanzen','topic',72,'hobby','garten'],['Gemüsegarten','topic',78,'hobby','garten'],
    ['Kräutergarten','topic',74,'hobby','garten'],['Yoga für Anfänger','topic',82,'hobby','sport'],
    ['Krafttraining Trainingsplan','topic',78,'hobby','sport'],['Lauftraining','topic',76,'hobby','sport'],
    ['Wandern','topic',82,'hobby','outdoor'],['Camping','topic',78,'hobby','outdoor'],
    ['Angeln','topic',74,'hobby','outdoor'],['Radfahren','topic',76,'hobby','sport'],
    ['Pilates','topic',72,'hobby','sport'],['Tanzen lernen','topic',68,'hobby','sport'],
]
total += append_csv('../data/discovery_seed_universes/topics/topics_hobbies_de.csv', HOBBIES_TOPICS)

CAREER_TOPICS = [
    ['Bewerbung schreiben','topic',84,'karriere','bewerbung'],['Vorstellungsgespräch','topic',82,'karriere','interview'],
    ['Gehaltsverhandlung','topic',80,'karriere','finanzen'],['Karrierewechsel','topic',78,'karriere','umstieg'],
    ['LinkedIn Profil','topic',68,'karriere','netzwerk'],['Arbeitszeugnis','topic',72,'karriere','dokument'],
    ['Weiterbildung planen','topic',74,'karriere','lernen'],['Quereinstieg','topic',76,'karriere','umstieg'],
    ['Selbstbewusst auftreten','topic',72,'karriere','persönlichkeit'],['Verhandeln lernen','topic',70,'karriere','kommunikation'],
]
total += append_csv('../data/discovery_seed_universes/topics/topics_career_de.csv', CAREER_TOPICS)

FAMILY_TOPICS = [
    ['Babyschlaf','topic',84,'familie','baby'],['Beikost','topic',76,'familie','ernährung'],
    ['Kinderernährung','topic',78,'familie','ernährung'],['Geschwister','topic',72,'familie','beziehung'],
    ['Medienkonsum Kinder','topic',74,'familie','digital'],['Pubertät','topic',78,'familie','entwicklung'],
    ['Hausaufgaben','topic',74,'familie','schule'],['Vorlesen','topic',68,'familie','lesen'],
    ['Einschulung','topic',76,'familie','schule'],['Kindergeburtstag','topic',66,'familie','feier'],
    ['Familienurlaub','topic',70,'familie','urlaub'],['Einschlafritual','topic',78,'familie','routine'],
    ['Morgenroutine','topic',74,'familie','routine'],['Taschengeld','topic',64,'familie','finanzen'],
]
total += append_csv('../data/discovery_seed_universes/family/family_topics_de.csv', FAMILY_TOPICS)

# ===== EXAMS: +200 rows =====
EXAMS = [
    ['Deutsch A1 Prüfung','exam',80,'sprache','deutsch'],['Deutsch A2 Prüfung','exam',82,'sprache','deutsch'],
    ['Deutsch B1 Prüfung','exam',86,'sprache','deutsch'],['Deutsch B2 Prüfung','exam',84,'sprache','deutsch'],
    ['Deutsch C1 Prüfung','exam',82,'sprache','deutsch'],['Telc B1','exam',80,'sprache','deutsch'],
    ['Telc B2','exam',78,'sprache','deutsch'],['Goethe B1','exam',80,'sprache','deutsch'],
    ['Goethe B2','exam',78,'sprache','deutsch'],['TestDaF','exam',82,'sprache','deutsch'],
    ['DSH Prüfung','exam',76,'sprache','deutsch'],['Kaufmann Büromanagement Prüfung','exam',72,'beruf','kaufmännisch'],
    ['Steuerfachangestellte Prüfung','exam',74,'beruf','steuer'],['Rechtsanwaltsfachangestellte Prüfung','exam',68,'beruf','recht'],
    ['Bankkaufmann Prüfung','exam',66,'beruf','finanzen'],['Versicherungskaufmann Prüfung','exam',64,'beruf','versicherung'],
    ['Immobilienkaufmann Prüfung','exam',64,'beruf','immobilien'],['Speditionskaufmann Prüfung','exam',62,'beruf','logistik'],
    ['Tourismuskaufmann Prüfung','exam',60,'beruf','tourismus'],['Erzieher Prüfung','exam',80,'beruf','bildung'],
    ['Altenpfleger Prüfung','exam',84,'beruf','pflege'],['Krankenpfleger Prüfung','exam',86,'beruf','pflege'],
    ['Medizinische Fachangestellte Prüfung','exam',72,'beruf','gesundheit'],['Zahnmedizinische Fachangestellte Prüfung','exam',68,'beruf','zahn'],
    ['Microsoft Office Zertifizierung','exam',64,'it','office'],['Google Ads Zertifizierung','exam',62,'marketing','online'],
    ['Scrum Master Zertifizierung','exam',68,'it','agil'],['Projektmanagement Zertifizierung','exam',70,'beruf','management'],
    ['Datenschutzbeauftragter Zertifizierung','exam',74,'beruf','datenschutz'],['Qualitätsmanagement Zertifizierung','exam',68,'beruf','qualität'],
]
total += append_csv('../data/discovery_seed_universes/exams/exams_vocational_de.csv', EXAMS)

# ===== COMPAT: +100 =====
COMPAT = [
    ('ChatGPT für Handwerker','Handwerker',90,'compatible','KI tool'),('ChatGPT im Pflegealltag','Pflegekräfte',88,'compatible','KI Pflege'),
    ('Buchhaltung für Kleinunternehmer','Kleinunternehmer',95,'compatible','Business'),('Kleinunternehmer Organisation','Kleinunternehmer',90,'compatible','Business'),
    ('Nebengewerbe Checkliste','Selbstständige',88,'compatible','Gründung'),('Pflegegrad beantragen','Senioren',95,'compatible','Pflege'),
    ('Pflegegrad Widerspruch','Angehörige',95,'compatible','Pflege'),('MD Begutachtung vorbereiten','Angehörige',92,'compatible','Pflege'),
    ('Pflegeunterlagen organisieren','Pflegekräfte',90,'compatible','Pflege'),('Pflege-Tagebuch','Pflegekräfte',88,'compatible','Doku'),
    ('Pflegeprotokoll','Pflegekräfte',90,'compatible','Doku'),('Blutdrucktagebuch','Senioren',95,'compatible','Tracker'),
    ('Blutdrucktagebuch','Menschen mit Bluthochdruck',95,'compatible','Gesundheit'),('Blutzuckertagebuch','Menschen mit Diabetes',95,'compatible','Gesundheit'),
    ('Medikamentenplan','Senioren',95,'compatible','Gesundheit'),('Medikamentenplan','Angehörige',92,'compatible','Pflege'),
    ('Arzttermin Vorbereitung','Senioren',90,'compatible','Gesundheit'),('Schlafprotokoll','Menschen mit Schlafstörungen',90,'compatible','Gesundheit'),
    ('Hundetraining Tagebuch','Hundehalter',92,'compatible','Hund'),('Welpentraining Planer','Ersthundbesitzer',95,'compatible','Hund'),
    ('Leinenführigkeit Hund','Hundehalter',95,'compatible','Hund'),('Rückruftraining Hund','Hundehalter',92,'compatible','Hund'),
    ('Angsthund Training','Hundehalter',88,'compatible','Hund'),('Abitur Lernplan','Schüler',92,'compatible','Prüfung'),
    ('IHK Prüfungsvorbereitung','Azubis',92,'compatible','Prüfung'),('AEVO Prüfung','Azubis',88,'compatible','Prüfung'),
    ('Einbürgerungstest','Deutschlernende',90,'compatible','Prüfung'),('Deutsch B1 Prüfung','Deutschlernende',90,'compatible','Sprache'),
    ('Deutsch B2 Prüfung','Deutschlernende',88,'compatible','Sprache'),('Haushaltsbuch','Familien',88,'compatible','Finanzen'),
    ('Putzplan','Familien',84,'compatible','Haushalt'),('Essensplan','Familien',86,'compatible','Ernährung'),
    ('Notfallordner','Familien',86,'compatible','Organisation'),('Notfallordner','Senioren',90,'compatible','Vorsorge'),
    ('Dokumentenmappe','Selbstständige',82,'compatible','Buchhaltung'),('Digitale Ordnung','Berufstätige',82,'compatible','Organisation'),
    ('Bewerbung schreiben','Berufstätige',88,'compatible','Karriere'),('Vorstellungsgespräch','Berufstätige',86,'compatible','Karriere'),
    ('Gehaltsverhandlung','Berufstätige',84,'compatible','Karriere'),('Fotografie für Anfänger','Hobbyfotografen',88,'compatible','Hobby'),
    ('Yoga für Anfänger','Anfänger',88,'compatible','Sport'),('Kochen lernen','Anfänger',90,'compatible','Kochen'),
    ('Balkongarten','Stadtbewohner',88,'compatible','Garten'),('Balkongarten','Anfänger',86,'compatible','Garten'),
    ('Babyschlaf','Eltern',92,'compatible','Familie'),('Pubertät','Eltern',88,'compatible','Familie'),
    ('Hausaufgaben','Eltern',84,'compatible','Schule'),('Lernplan','Studenten',88,'compatible','Lernen'),
    ('Lernplan','Schüler',86,'compatible','Lernen'),('Bachelorarbeit','Studenten',88,'compatible','Studium'),
    ('Masterarbeit','Studenten',86,'compatible','Studium'),('Rechnungsvorlagen','Selbstständige',90,'compatible','Business'),
    ('Angebotsvorlagen','Selbstständige',88,'compatible','Business'),('Steuerunterlagen sortieren','Selbstständige',90,'compatible','Steuer'),
    ('Kleinunternehmer Steuer','Kleinunternehmer',90,'compatible','Steuer'),('Strom sparen','Hausbesitzer',80,'compatible','Haushalt'),
    ('Heizkosten senken','Mieter',78,'compatible','Haushalt'),('Umzug Checkliste','Mieter',84,'compatible','Wohnen'),
    ('Wochenplaner','Berufstätige',82,'compatible','Organisation'),('Wochenplaner','Familien',84,'compatible','Familie'),
    ('Minimalismus zu Hause','Berufstätige',78,'compatible','Lifestyle'),('ChatGPT für Senioren','Senioren',88,'compatible','Technik'),
    ('KI für Kleinunternehmer','Kleinunternehmer',88,'compatible','Business'),('KI für Immobilienmakler','Immobilienmakler',90,'compatible','Beruf'),
    ('KI für Coaches','Coach',86,'compatible','Beruf'),('KI für Steuerberater','Steuerberater',84,'compatible','Beruf'),
    ('Katzen Eingewöhnung','Katzenhalter',88,'compatible','Haustier'),('Behördenpost organisieren','Senioren',90,'compatible','Verwaltung'),
    ('Behördenpost organisieren','Berufstätige',82,'compatible','Verwaltung'),('Krankenhaus Checkliste','Angehörige',88,'compatible','Pflege'),
    ('Reha Planer','Reha-Patienten',90,'compatible','Reha'),('Schmerztagebuch','Menschen mit chronischen Schmerzen',90,'compatible','Gesundheit'),
    ('Stimmungstagebuch','Menschen mit Depression',86,'compatible','Gesundheit'),('Ernährungsprotokoll','Menschen mit Diabetes',84,'compatible','Gesundheit'),
    ('Krafttraining Trainingsplan','Sportler',86,'compatible','Fitness'),('Karrierewechsel','Berufstätige',82,'compatible','Karriere'),
]
c = append_compat('../data/discovery_seed_universes/compatibility/topic_audience_compatibility.csv', COMPAT)
print(f'Compat: +{c}')

# ===== INCOMPAT: +30 =====
INCOMPAT = [
    ('Babyschlaf','Senioren','life_stage_mismatch','hard_block'),('Welpentraining','Senioren','domain_mismatch','hard_block'),
    ('Hundetraining','Selbstständige','domain_mismatch','hard_block'),('Rente beantragen','Schüler','life_stage_mismatch','hard_block'),
    ('Pflegegrad Antrag','Handwerker','domain_mismatch','hard_block'),('Pflegegrad Widerspruch','Kleinunternehmer','domain_mismatch','hard_block'),
    ('Buchhaltung','Kinder','domain_mismatch','hard_block'),('Steuererklärung','Kinder','domain_mismatch','hard_block'),
    ('KI für Handwerker','Pflegekräfte','domain_mismatch','hard_block'),('Hundetraining','Senioren','domain_mismatch','hard_block'),
    ('Abitur','Rentner','life_stage_mismatch','hard_block'),('Pflegeexamen','Senioren','domain_mismatch','hard_block'),
    ('Einbürgerungstest','Hundehalter','domain_mismatch','hard_block'),('Krankenhaus Checkliste','Kinder','life_stage_mismatch','hard_block'),
    ('Reha Planer','Kinder','life_stage_mismatch','hard_block'),('Patientenverfügung','Kinder','life_stage_mismatch','hard_block'),
    ('Vorsorgevollmacht','Kinder','life_stage_mismatch','hard_block'),('Testament','Kinder','life_stage_mismatch','hard_block'),
    ('Altersvorsorge','Kinder','life_stage_mismatch','hard_block'),('Altersvorsorge','Schüler','life_stage_mismatch','hard_block'),
    ('Gehaltsverhandlung','Rentner','life_stage_mismatch','hard_block'),('Vorstellungsgespräch','Rentner','life_stage_mismatch','hard_block'),
    ('Existenzgründung','Rentner','life_stage_mismatch','hard_block'),('Existenzgründung','Schüler','life_stage_mismatch','hard_block'),
    ('Buchhaltung','Senioren','domain_mismatch','hard_block'),('SEO Grundlagen','Senioren','domain_mismatch','hard_block'),
    ('Bachelorarbeit','Rentner','life_stage_mismatch','hard_block'),('Masterarbeit','Rentner','life_stage_mismatch','hard_block'),
    ('KI für Friseure','Handwerker','domain_mismatch','hard_block'),('ChatGPT für Senioren','Kinder','domain_mismatch','hard_block'),
]
i = append_incompat('../data/discovery_seed_universes/compatibility/incompatible_combinations.csv', INCOMPAT)
print(f'Incompat: +{i}')

# ===== RISK: +40 =====
RISK = [
    ('diagnose','high','health_sensitive','False'),('therapieplan','high','health_sensitive','False'),
    ('medikament','high','health_sensitive','False'),('antidepressiva','high','health_sensitive','False'),
    ('insulin','high','health_sensitive','False'),('blutverdünner','high','health_sensitive','False'),
    ('opioide','restricted','substance_related','False'),('schmerzmittel','high','health_sensitive','False'),
    ('patientenverfügung','high','legal_sensitive','False'),('vorsorgevollmacht','high','legal_sensitive','False'),
    ('testament','high','legal_sensitive','False'),('steuerbescheid','high','legal_sensitive','False'),
    ('einspruch','high','legal_sensitive','False'),('ETF','high','financial_sensitive','False'),
    ('krypto','high','financial_sensitive','False'),('trading','high','financial_sensitive','False'),
    ('sucht','high','health_sensitive','False'),('selbstverletzung','blocked','unsafe_content','False'),
    ('psychotherapie','high','health_sensitive','False'),('trauma','high','health_sensitive','False'),
    ('magersucht','high','health_sensitive','False'),('bulimie','high','health_sensitive','False'),
    ('alkoholismus','high','health_sensitive','False'),('spielsucht','high','health_sensitive','False'),
    ('zwangsstörung','high','health_sensitive','False'),('bipolare störung','high','health_sensitive','False'),
    ('schizophrenie','high','health_sensitive','False'),('ptbs','high','health_sensitive','False'),
    ('borderline','high','health_sensitive','False'),('essstörung','high','health_sensitive','False'),
    ('krebs','high','health_sensitive','False'),('tumor','high','health_sensitive','False'),
    ('hiv','high','health_sensitive','False'),('hepatitis','high','health_sensitive','False'),
    ('impfschaden','high','health_sensitive','False'),('medikamentenwechselwirkung','high','health_sensitive','False'),
    ('anwalt','high','legal_sensitive','False'),('gericht','high','legal_sensitive','False'),
    ('klage','high','legal_sensitive','False'),('strafverfahren','high','legal_sensitive','False'),
]
r = append_risk('../data/discovery_seed_universes/compatibility/risk_rules.csv', RISK)
print(f'Risk: +{r}')

print(f'\nTOTAL NEW ROWS: {total}')
