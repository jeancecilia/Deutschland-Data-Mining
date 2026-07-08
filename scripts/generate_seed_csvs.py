"""Generate all 50+ seed CSV files for the Discovery Seed Network."""
import csv, os

base = os.path.join(os.path.dirname(__file__), '..', 'data', 'discovery_seed_universes')

def write_csv(path, header, rows):
    full = os.path.join(base, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(header)
        for row in rows:
            w.writerow(row)
    return len(rows)

count = 0

count += write_csv('audiences/audiences_general_de.csv', ['name','entity_type','priority','domain'], [
    ['Anfänger','audience',88,'allgemein'],['Einsteiger','audience',86,'allgemein'],
    ['Fortgeschrittene','audience',70,'allgemein'],['Erwachsene','audience',80,'allgemein'],
    ['Frauen','audience',75,'allgemein'],['Männer','audience',72,'allgemein'],
    ['Berufstätige','audience',82,'arbeit'],['Vielbeschäftigte','audience',74,'allgemein'],
    ['Singles','audience',68,'allgemein'],['Paare','audience',70,'allgemein']])

count += write_csv('audiences/audiences_senior_de.csv', ['name','entity_type','priority','domain'], [
    ['Senioren','audience',95,'senioren'],['Rentner','audience',90,'senioren'],
    ['Ruheständler','audience',88,'senioren'],['Menschen ab 60','audience',80,'senioren'],
    ['Menschen ab 70','audience',75,'senioren'],['Pflegebedürftige','audience',90,'pflege'],
    ['Angehörige','audience',96,'pflege'],['Pflegende Angehörige','audience',95,'pflege'],
    ['Pflegekräfte','audience',90,'pflege']])

count += write_csv('audiences/audiences_family_de.csv', ['name','entity_type','priority','domain'], [
    ['Eltern','audience',92,'familie'],['Mütter','audience',88,'familie'],
    ['Väter','audience',85,'familie'],['Alleinerziehende','audience',90,'familie'],
    ['Familien','audience',88,'familie'],['Kinder','audience',82,'familie'],
    ['Großeltern','audience',76,'familie'],['Patchworkfamilien','audience',74,'familie'],
    ['Jugendliche','audience',70,'familie']])

count += write_csv('audiences/audiences_business_de.csv', ['name','entity_type','priority','domain'], [
    ['Selbstständige','audience',95,'business'],['Freelancer','audience',88,'business'],
    ['Kleinunternehmer','audience',86,'business'],['Gründer','audience',84,'business'],
    ['Solo-Selbstständige','audience',84,'business'],['Handwerker','audience',88,'handwerk'],
    ['Kleine Betriebe','audience',82,'business'],['Startups','audience',70,'business'],
    ['Nebengewerbler','audience',78,'business']])

count += write_csv('audiences/audiences_learning_de.csv', ['name','entity_type','priority','domain'], [
    ['Schüler','audience',80,'bildung'],['Studenten','audience',82,'bildung'],
    ['Studierende','audience',82,'bildung'],['Azubis','audience',76,'bildung'],
    ['Lehrer','audience',78,'bildung'],['Erwachsene mit ADHS','audience',92,'gesundheit'],
    ['Menschen mit ADHS','audience',88,'gesundheit'],['Schichtarbeiter','audience',78,'arbeit'],
    ['Menschen mit Schichtarbeit','audience',76,'arbeit']])

count += write_csv('professions/professions_health_de.csv', ['name','entity_type','priority','domain'], [
    ['Pflegefachfrau','profession',96,'pflege'],['Pflegefachmann','profession',96,'pflege'],
    ['Krankenpfleger','profession',95,'pflege'],['Krankenschwester','profession',95,'pflege'],
    ['Altenpfleger','profession',94,'pflege'],['Arzt','profession',90,'medizin'],
    ['Zahnarzt','profession',85,'medizin'],['Physiotherapeut','profession',84,'medizin'],
    ['Ergotherapeut','profession',80,'medizin'],['Hebamme','profession',88,'medizin'],
    ['Notfallsanitäter','profession',86,'medizin'],['Apotheker','profession',82,'medizin']])

count += write_csv('professions/professions_craft_de.csv', ['name','entity_type','priority','domain'], [
    ['Handwerker','profession',88,'handwerk'],['Elektriker','profession',82,'handwerk'],
    ['Tischler','profession',78,'handwerk'],['Maler','profession',74,'handwerk'],
    ['Installateur','profession',76,'handwerk'],['Dachdecker','profession',72,'handwerk'],
    ['Maurer','profession',70,'handwerk'],['Fliesenleger','profession',68,'handwerk'],
    ['Zimmerer','profession',70,'handwerk'],['Kfz-Mechatroniker','profession',78,'handwerk'],
    ['Mechatroniker','profession',80,'handwerk']])

count += write_csv('professions/professions_office_de.csv', ['name','entity_type','priority','domain'], [
    ['Bürokaufmann','profession',74,'buero'],['Industriekaufmann','profession',72,'buero'],
    ['Fachinformatiker','profession',92,'it'],['Softwareentwickler','profession',90,'it'],
    ['IT-Administrator','profession',85,'it'],['Steuerberater','profession',80,'finanzen'],
    ['Rechtsanwalt','profession',76,'recht'],['Immobilienmakler','profession',72,'immobilien'],
    ['Versicherungsmakler','profession',68,'finanzen']])

count += write_csv('professions/professions_service_de.csv', ['name','entity_type','priority','domain'], [
    ['Friseur','profession',70,'dienstleistung'],['Kosmetiker','profession',66,'dienstleistung'],
    ['Koch','profession',76,'gastronomie'],['Gastronom','profession',68,'gastronomie'],
    ['Verkäufer','profession',64,'handel'],['Einzelhandelskaufmann','profession',64,'handel'],
    ['Busfahrer','profession',64,'transport'],['LKW-Fahrer','profession',68,'transport'],
    ['Berufskraftfahrer','profession',68,'transport']])

count += write_csv('professions/professions_education_de.csv', ['name','entity_type','priority','domain'], [
    ['Lehrer','profession',82,'bildung'],['Erzieher','profession',84,'bildung'],
    ['Sozialpädagoge','profession',78,'bildung'],['Dozent','profession',72,'bildung'],
    ['Trainer','profession',68,'bildung'],['Coach','profession',66,'beratung'],
    ['Berater','profession',62,'beratung']])

count += write_csv('exams/exams_school_de.csv', ['name','entity_type','priority','domain'], [
    ['Abitur','exam',90,'schule'],['Fachabitur','exam',85,'schule'],
    ['Mittlere Reife','exam',82,'schule'],['Hauptschulabschluss','exam',78,'schule'],
    ['Qualifizierender Hauptschulabschluss','exam',76,'schule']])

count += write_csv('exams/exams_vocational_de.csv', ['name','entity_type','priority','domain'], [
    ['IHK-Prüfung','exam',95,'beruf'],['IHK Abschlussprüfung','exam',94,'beruf'],
    ['IHK Zwischenprüfung','exam',88,'beruf'],['Ausbildereignungsprüfung','exam',85,'beruf'],
    ['Meisterprüfung','exam',90,'handwerk'],['Fachwirtprüfung','exam',82,'beruf'],
    ['Betriebswirt IHK','exam',80,'beruf'],['Sachkundeprüfung','exam',78,'beruf'],
    ['Pflegeexamen','exam',86,'pflege'],['Fachinformatiker Prüfung','exam',88,'it']])

count += write_csv('exams/exams_language_de.csv', ['name','entity_type','priority','domain'], [
    ['Einbürgerungstest','exam',92,'sprache'],['Deutsch B1','exam',88,'sprache'],
    ['Deutsch B2','exam',86,'sprache'],['Deutsch C1','exam',84,'sprache'],
    ['telc Deutsch','exam',80,'sprache'],['Goethe-Zertifikat','exam',78,'sprache']])

count += write_csv('exams/exams_licenses_de.csv', ['name','entity_type','priority','domain'], [
    ['Führerschein Klasse B','exam',82,'lizenz'],['Führerschein Theorie','exam',84,'lizenz'],
    ['LKW-Führerschein','exam',72,'lizenz'],['Jagdprüfung','exam',64,'lizenz'],
    ['Sportbootführerschein','exam',62,'lizenz'],['Hundeführerschein','exam',66,'lizenz']])

count += write_csv('problems/problems_organization_de.csv', ['name','entity_type','priority','domain'], [
    ['Stress','problem',90,'organisation'],['Überforderung','problem',89,'organisation'],
    ['Zeitmangel','problem',88,'organisation'],['fehlende Struktur','problem',91,'organisation'],
    ['Prokrastination','problem',82,'organisation'],['Unordnung','problem',84,'organisation'],
    ['Motivationsprobleme','problem',76,'organisation'],['Routinen aufbauen','problem',84,'organisation']])

count += write_csv('problems/problems_learning_de.csv', ['name','entity_type','priority','domain'], [
    ['Prüfungsangst','problem',86,'lernen'],['Lernprobleme','problem',82,'lernen'],
    ['Konzentrationsprobleme','problem',80,'lernen'],['ADHS','problem',90,'lernen'],
    ['Leseschwäche','problem',72,'lernen']])

count += write_csv('problems/problems_health_de.csv', ['name','entity_type','priority','domain'], [
    ['Schlafprobleme','problem',86,'gesundheit'],['Rückenschmerzen','problem',84,'gesundheit'],
    ['Kopfschmerzen','problem',78,'gesundheit'],['Migräne','problem',76,'gesundheit'],
    ['Blutdruck','problem',88,'gesundheit'],['Blutzucker','problem',84,'gesundheit'],
    ['Allergien','problem',74,'gesundheit']])

count += write_csv('problems/problems_work_de.csv', ['name','entity_type','priority','domain'], [
    ['Kundenkommunikation','problem',78,'arbeit'],['Angebote schreiben','problem',72,'arbeit'],
    ['Rechnungen schreiben','problem',70,'arbeit'],['Personalmanagement','problem',68,'arbeit'],
    ['Termindruck','problem',76,'arbeit'],['Work-Life-Balance','problem',74,'arbeit']])

count += write_csv('problems/problems_pets_de.csv', ['name','entity_type','priority','domain'], [
    ['Hund zieht an der Leine','problem',88,'haustiere'],['Hund bleibt nicht alleine','problem',86,'haustiere'],
    ['Welpe stubenrein','problem',84,'haustiere'],['Angsthund','problem',82,'haustiere'],
    ['Hundebegegnungen','problem',78,'haustiere'],['Rückruftraining','problem',85,'haustiere'],
    ['Katzen Eingewöhnung','problem',74,'haustiere']])

count += write_csv('health_trackers/health_trackers_de.csv', ['name','entity_type','priority','domain','risk_level'], [
    ['Blutdrucktagebuch','topic',93,'gesundheit','high'],['Blutzuckertagebuch','topic',88,'gesundheit','high'],
    ['Schlaftagebuch','topic',82,'gesundheit','medium'],['Schmerztagebuch','topic',80,'gesundheit','high'],
    ['Migräne Tagebuch','topic',78,'gesundheit','high'],['Symptomtagebuch','topic',76,'gesundheit','high'],
    ['Medikamentenplan','topic',86,'gesundheit','high'],['Arztbesuch Notizbuch','topic',80,'gesundheit','medium'],
    ['Stimmungstagebuch','topic',78,'gesundheit','high'],['ADHS Tagesplaner','topic',88,'gesundheit','high'],
    ['Ernährungstagebuch','topic',82,'gesundheit','medium'],['Fitness Tagebuch','topic',76,'gesundheit','low'],
    ['Gewichtstagebuch','topic',74,'gesundheit','medium'],['Zyklustagebuch','topic',72,'gesundheit','medium']])

count += write_csv('business/business_basics_de.csv', ['name','entity_type','priority','domain'], [
    ['Nebengewerbe starten','topic',88,'business'],['Kleinunternehmen gründen','topic',84,'business'],
    ['Existenzgründung','topic',86,'business'],['Firmengründung','topic',82,'business'],
    ['Businessplan','topic',80,'business'],['Geschäftsidee','topic',76,'business'],
    ['Kunden gewinnen','topic',82,'business'],['Akquise','topic',78,'business'],
    ['Marketing','topic',80,'business'],['Social Media Marketing','topic',78,'business'],
    ['Online-Marketing','topic',74,'business'],['Produktivität','topic',80,'business'],
    ['Zeitmanagement','topic',78,'business'],['Selbstorganisation','topic',80,'business'],
    ['Homeoffice','topic',82,'business']])

count += write_csv('business/business_admin_de.csv', ['name','entity_type','priority','domain'], [
    ['Buchhaltung','topic',84,'business'],['Steuererklärung','topic',82,'business'],
    ['Umsatzsteuer','topic',76,'business'],['EÜR','topic',74,'business'],
    ['Rechnung schreiben','topic',78,'business'],['Angebote schreiben','topic',74,'business'],
    ['Preiskalkulation','topic',72,'business'],['Steuerunterlagen sortieren','topic',76,'business']])

count += write_csv('ai_use_cases/ai_professions_de.csv', ['name','entity_type','priority','domain'], [
    ['KI für Handwerker','topic',88,'ki'],['KI für Lehrer','topic',82,'ki'],
    ['KI für Pflegekräfte','topic',80,'ki'],['KI für Immobilienmakler','topic',78,'ki'],
    ['KI für Coaches','topic',76,'ki'],['KI für Friseure','topic',74,'ki'],
    ['KI für Gastronomen','topic',72,'ki'],['KI für Steuerberater','topic',76,'ki'],
    ['ChatGPT für Selbstständige','topic',84,'ki'],['ChatGPT für Senioren','topic',80,'ki'],
    ['ChatGPT für Bewerbungen','topic',76,'ki'],['KI für E-Mails','topic',72,'ki'],
    ['KI für Social Media','topic',74,'ki']])

count += write_csv('household/household_organization_de.csv', ['name','entity_type','priority','domain'], [
    ['Haushaltsbuch','topic',84,'haushalt'],['Putzplan','topic',78,'haushalt'],
    ['Essensplan','topic',82,'haushalt'],['Wochenplaner','topic',80,'haushalt'],
    ['Familienkalender','topic',76,'haushalt'],['Notfallordner','topic',82,'haushalt'],
    ['Dokumentenmappe','topic',80,'haushalt'],['Behördenpost organisieren','topic',84,'haushalt'],
    ['Passwörter organisieren','topic',72,'haushalt'],['Digitale Ordnung','topic',74,'haushalt'],
    ['Minimalismus','topic',76,'haushalt'],['Aufräumen','topic',78,'haushalt']])

count += write_csv('pets/pets_dogs_de.csv', ['name','entity_type','priority','domain'], [
    ['Hundetraining','topic',92,'haustiere'],['Welpentraining','topic',88,'haustiere'],
    ['Leinenführigkeit','topic',86,'haustiere'],['Hund alleine lassen','topic',84,'haustiere'],
    ['Rückruf','topic',85,'haustiere'],['Angsthund Training','topic',82,'haustiere'],
    ['Hundebegegnungen','topic',78,'haustiere'],['Welpentagebuch','topic',80,'haustiere'],
    ['Hundetraining Tagebuch','topic',78,'haustiere'],['Futtertagebuch Hund','topic',70,'haustiere']])

count += write_csv('pets/pets_cats_de.csv', ['name','entity_type','priority','domain'], [
    ['Katzenhaltung','topic',78,'haustiere'],['Katzen Eingewöhnung','topic',74,'haustiere'],
    ['Katzen Gesundheitstagebuch','topic',72,'haustiere'],['Futtertagebuch Katze','topic',68,'haustiere']])

count += write_csv('hobbies/hobbies_creative_de.csv', ['name','entity_type','priority','domain'], [
    ['Fotografie','hobby',80,'kreativ'],['Zeichnen','hobby',74,'kreativ'],
    ['Malen','hobby',76,'kreativ'],['Aquarell','hobby',70,'kreativ'],
    ['Handlettering','hobby',72,'kreativ'],['Nähen','hobby',74,'kreativ'],
    ['Stricken','hobby',70,'kreativ'],['Häkeln','hobby',68,'kreativ']])

count += write_csv('hobbies/hobbies_food_de.csv', ['name','entity_type','priority','domain'], [
    ['Kochen','hobby',86,'essen'],['Backen','hobby',82,'essen'],
    ['Brot backen','hobby',80,'essen'],['Fermentieren','hobby',64,'essen'],
    ['Meal Prep','hobby',78,'essen'],['Grillen','hobby',74,'essen']])

count += write_csv('hobbies/hobbies_outdoor_de.csv', ['name','entity_type','priority','domain'], [
    ['Camping','hobby',78,'outdoor'],['Wandern','hobby',82,'outdoor'],
    ['Angeln','hobby',74,'outdoor'],['Radfahren','hobby',76,'sport'],
    ['Laufen','hobby',78,'sport'],['Klettern','hobby',68,'sport'],
    ['Yoga','hobby',84,'sport'],['Krafttraining','hobby',78,'sport'],
    ['Fitness','hobby',82,'sport'],['Pilates','hobby',72,'sport'],['Tanzen','hobby',70,'sport']])

count += write_csv('hobbies/hobbies_garden_de.csv', ['name','entity_type','priority','domain'], [
    ['Garten','hobby',86,'garten'],['Balkongarten','hobby',82,'garten'],
    ['Gemüsegarten','hobby',80,'garten'],['Kräutergarten','hobby',78,'garten'],
    ['Zimmerpflanzen','hobby',74,'garten'],['Hochbeet','hobby',76,'garten']])

count += write_csv('learning/learning_topics_de.csv', ['name','entity_type','priority','domain'], [
    ['Lernorganisation','topic',84,'lernen'],['Prüfungsvorbereitung','topic',86,'lernen'],
    ['Lernplan','topic',80,'lernen'],['Gedächtnistraining','topic',78,'lernen'],
    ['Lesetechniken','topic',70,'lernen'],['Notizen machen','topic',72,'lernen']])

count += write_csv('seniors/senior_topics_de.csv', ['name','entity_type','priority','domain'], [
    ['Pflegegrad','topic',90,'senioren'],['Pflegeantrag','topic',88,'senioren'],
    ['Pflegeorganisation','topic',86,'senioren'],['Pflegedokumentation','topic',84,'senioren'],
    ['Demenz','topic',88,'senioren'],['Sturzprävention','topic',80,'senioren'],
    ['Seniorengymnastik','topic',76,'senioren'],['Rente beantragen','topic',82,'senioren'],
    ['Altersvorsorge','topic',80,'senioren'],['Patientenverfügung','topic',84,'senioren'],
    ['Vorsorgevollmacht','topic',82,'senioren'],['Testament','topic',80,'senioren']])

count += write_csv('family/family_topics_de.csv', ['name','entity_type','priority','domain'], [
    ['Familienalltag','topic',86,'familie'],['Routinen mit Kindern','topic',82,'familie'],
    ['Babyschlaf','topic',84,'familie'],['Beikost','topic',76,'familie'],
    ['Geschwister','topic',74,'familie'],['Medienkonsum','topic',72,'familie'],
    ['Pubertät','topic',78,'familie'],['Hausaufgaben','topic',74,'familie'],
    ['Vorlesen','topic',68,'familie'],['Kindergeburtstag','topic',66,'familie']])

# Formats
count += write_csv('formats/book_formats_de.csv', ['name','entity_type','priority','domain'], [
    ['Ratgeber','book_format',95,'format'],['Praxisratgeber','book_format',92,'format'],
    ['Leitfaden','book_format',90,'format'],['Workbook','book_format',88,'format'],
    ['Arbeitsbuch','book_format',86,'format'],['Übungsbuch','book_format',84,'format'],
    ['Tagebuch','book_format',90,'format'],['Logbuch','book_format',82,'format'],
    ['Planer','book_format',88,'format'],['Checkliste','book_format',85,'format'],
    ['Vorlagenbuch','book_format',82,'format'],['Notizbuch','book_format',78,'format'],
    ['Journal','book_format',76,'format'],['Tracker','book_format',84,'format'],
    ['Lernplaner','book_format',86,'format'],['Trainingsjournal','book_format',78,'format'],
    ['Schritt-für-Schritt-Anleitung','book_format',82,'format']])

# Contexts
count += write_csv('contexts/contexts_de.csv', ['name','entity_type','priority','domain'], [
    ['im Alltag','context',84,'allgemein'],['für Anfänger','context',86,'allgemein'],
    ['für Einsteiger','context',86,'allgemein'],['im Berufsalltag','context',80,'arbeit'],
    ['im Familienalltag','context',82,'familie'],['bei Schichtarbeit','context',72,'arbeit'],
    ['für Senioren','context',82,'senioren'],['für Selbstständige','context',80,'business'],
    ['ohne Vorkenntnisse','context',78,'allgemein'],['mit wenig Zeit','context',76,'allgemein'],
    ['mit klarer Struktur','context',80,'allgemein'],['mit Vorlagen','context',78,'allgemein'],
    ['mit Checklisten','context',82,'allgemein'],['für die Prüfungsvorbereitung','context',80,'lernen'],
    ['für zu Hause','context',74,'allgemein'],['für unterwegs','context',70,'allgemein']])

# Compatibility files
count += write_csv('compatibility/topic_audience_compatibility.csv',
    ['topic','audience','confidence','relation_type','notes'], [
    ['KI im Handwerk','Handwerker',95,'compatible','direkte Zielgruppe'],
    ['KI im Handwerk','Kleinunternehmer',90,'compatible','kleine Betriebe'],
    ['KI im Handwerk','Selbstständige',88,'compatible','Business-Thema'],
    ['Pflegegrad','Senioren',95,'compatible','direkter Use Case'],
    ['Pflegegrad','Angehörige',95,'compatible','Angehörige beantragen'],
    ['Pflegegrad','Rentner',92,'compatible','häufiger Use Case'],
    ['Pflegeantrag','Senioren',95,'compatible','direkter Use Case'],
    ['Pflegeantrag','Angehörige',95,'compatible','Angehörige stellen Antrag'],
    ['Pflege','Pflegekräfte',95,'compatible','direkte Zielgruppe'],
    ['Pflege','Angehörige',95,'compatible','pflegende Angehörige'],
    ['ADHS','Erwachsene mit ADHS',95,'compatible','direkte Zielgruppe'],
    ['ADHS','Eltern',90,'compatible','Eltern von ADHS-Kindern'],
    ['Hundetraining','Hundehalter',95,'compatible','direkte Zielgruppe'],
    ['Welpentraining','Hundehalter',95,'compatible','neue Hundehalter'],
    ['Buchhaltung','Selbstständige',95,'compatible','Pflichtthema'],
    ['Buchhaltung','Kleinunternehmer',95,'compatible','Pflichtthema'],
    ['Buchhaltung','Freelancer',95,'compatible','Pflichtthema'],
    ['Steuererklärung','Selbstständige',95,'compatible','Pflichtthema'],
    ['Steuererklärung','Freelancer',92,'compatible','Pflichtthema'],
    ['Steuererklärung','Rentner',88,'compatible','Rentner mit Einkünften'],
    ['Demenz','Senioren',95,'compatible','direkte Zielgruppe'],
    ['Demenz','Angehörige',95,'compatible','pflegende Angehörige'],
    ['Blutdruck','Senioren',95,'compatible','häufigstes Tracking-Thema'],
    ['Blutzucker','Senioren',88,'compatible','Diabetes-Management'],
    ['Blutdrucktagebuch','Senioren',95,'compatible','direkter Use Case'],
    ['Blutdrucktagebuch','Angehörige',90,'compatible','Hilfe beim Tracken'],
    ['Essensplan','Familien',90,'compatible','Familienorganisation'],
    ['Essensplan','Berufstätige',88,'compatible','Meal Prep'],
    ['Haushaltsbuch','Familien',88,'compatible','Budgetplanung'],
    ['Haushaltsbuch','Singles',82,'compatible','persönliche Finanzen'],
    ['Babyschlaf','Eltern',95,'compatible','direkter Use Case'],
    ['Babyschlaf','Mütter',92,'compatible','häufige Zielgruppe'],
    ['Rente beantragen','Rentner',95,'compatible','direkter Use Case'],
    ['Rente beantragen','Ruheständler',95,'compatible','direkter Use Case'],
    ['Patientenverfügung','Senioren',95,'compatible','Vorsorgethema'],
    ['Patientenverfügung','Angehörige',88,'compatible','rechtliche Vorsorge'],
    ['Testament','Senioren',90,'compatible','Vorsorgethema'],
    ['Sturzprävention','Senioren',90,'compatible','Gesundheitsthema'],
    ['Balkongarten','Anfänger',88,'compatible','Einsteiger-Thema'],
    ['Kochen','Anfänger',90,'compatible','Lernthema'],
    ['Kochen','Studenten',88,'compatible','erste eigene Küche'],
    ['Yoga','Anfänger',88,'compatible','Einsteiger-Thema'],
    ['Yoga','Frauen',85,'compatible','starke Zielgruppe'],
    ['Fotografie','Anfänger',88,'compatible','Einsteiger-Thema'],
    ['Nähen','Anfänger',86,'compatible','Einsteiger-Thema'],
    ['Garten','Anfänger',86,'compatible','Einsteiger-Thema'],
    ['Medikamentenplan','Senioren',92,'compatible','Gesundheitsmanagement'],
    ['Medikamentenplan','Angehörige',88,'compatible','Hilfe bei Verwaltung'],
    ['ADHS Tagesplaner','Erwachsene mit ADHS',95,'compatible','direktes Hilfsmittel'],
    ['Lernorganisation','Studenten',92,'compatible','Lernhilfe'],
    ['Lernorganisation','Schüler',88,'compatible','Lernhilfe'],
    ['Prüfungsvorbereitung','Studenten',92,'compatible','Lernhilfe'],
    ['Prüfungsvorbereitung','Azubis',88,'compatible','Ausbildungsprüfung'],
])

count += write_csv('compatibility/incompatible_combinations.csv',
    ['topic','audience','reason','severity'], [
    ['KI im Handwerk','Pflege','domain_mismatch','hard_block'],
    ['KI im Handwerk','Pflegekräfte','domain_mismatch','hard_block'],
    ['KI im Handwerk','Rentner','domain_mismatch','hard_block'],
    ['KI im Handwerk','Ruheständler','domain_mismatch','hard_block'],
    ['KI im Handwerk','Senioren','domain_mismatch','hard_block'],
    ['KI im Handwerk','Angehörige','domain_mismatch','hard_block'],
    ['Pflegegrad','Kleinunternehmer','domain_mismatch','hard_block'],
    ['Pflegegrad','Selbstständige','domain_mismatch','hard_block'],
    ['Pflegegrad','Freelancer','domain_mismatch','hard_block'],
    ['Pflegegrad','Handwerker','domain_mismatch','hard_block'],
    ['Pflegeantrag','Kleinunternehmer','domain_mismatch','hard_block'],
    ['Pflegeantrag','Freelancer','domain_mismatch','hard_block'],
    ['Pflegebedürftigkeit','Freelancer','domain_mismatch','hard_block'],
    ['Pflegebedürftigkeit','Kleinunternehmer','domain_mismatch','hard_block'],
    ['Alleinerziehend','Ruheständler','life_stage_mismatch','hard_block'],
    ['Alleinerziehend','Rentner','life_stage_mismatch','hard_block'],
    ['Alleinerziehend','Freelancer','life_stage_mismatch','hard_block'],
    ['Eltern','Pflege','audience_as_topic','hard_block'],
    ['Eltern','Ruheständler','life_stage_mismatch','hard_block'],
    ['Eltern','Rentner','life_stage_mismatch','hard_block'],
    ['Eltern','Freelancer','audience_as_topic','hard_block'],
    ['Eltern','Kleinunternehmer','audience_as_topic','hard_block'],
    ['Babyschlaf','Senioren','life_stage_mismatch','hard_block'],
    ['Babyschlaf','Rentner','life_stage_mismatch','hard_block'],
    ['Welpentraining','Senioren','domain_mismatch','hard_block'],
    ['Rente beantragen','Studenten','life_stage_mismatch','hard_block'],
    ['Rente beantragen','Freelancer','life_stage_mismatch','hard_block'],
    ['Existenzgründung','Rentner','life_stage_mismatch','hard_block'],
    ['Existenzgründung','Ruheständler','life_stage_mismatch','hard_block'],
    ['Hundetraining','Kleinunternehmer','domain_mismatch','hard_block'],
    ['Hundetraining','Freelancer','domain_mismatch','hard_block'],
    ['Buchhaltung','Senioren','domain_mismatch','hard_block'],
    ['Buchhaltung','Pflegekräfte','domain_mismatch','hard_block'],
    ['Steuererklärung','Pflegekräfte','domain_mismatch','hard_block'],
    ['Steuererklärung','Schüler','domain_mismatch','hard_block'],
    ['Haushaltsbuch','Kinder','domain_mismatch','hard_block'],
    ['Medikamentenplan','Studenten','domain_mismatch','hard_block'],
    ['Patientenverfügung','Studenten','life_stage_mismatch','hard_block'],
    ['Patientenverfügung','Kinder','life_stage_mismatch','hard_block'],
])

count += write_csv('compatibility/risk_rules.csv',
    ['keyword','risk_category','reason','auto_promote_allowed'], [
    ['anabol','high','substance_related',False],
    ['steroide','high','substance_related',False],
    ['doping','high','substance_related',False],
    ['testosteron','high','substance_related',False],
    ['hormon','high','substance_related',False],
    ['dosierung','restricted','dosage_content',False],
    ['zyklus','restricted','dosage_content',False],
    ['cycle','restricted','dosage_content',False],
    ['kur','restricted','dosage_content',False],
    ['blutdruck','high','health_sensitive',False],
    ['blutzucker','high','health_sensitive',False],
    ['diabetes','high','health_sensitive',False],
    ['demenz','high','health_sensitive',False],
    ['alzheimer','high','health_sensitive',False],
    ['adhs','high','health_sensitive',False],
    ['depression','high','health_sensitive',False],
    ['angststörung','high','health_sensitive',False],
    ['neurofeedback','high','health_sensitive',False],
    ['therapie','high','health_sensitive',False],
    ['behandlung','high','health_sensitive',False],
    ['steuer','high','legal_sensitive',False],
    ['recht','high','legal_sensitive',False],
    ['investment','high','financial_sensitive',False],
    ['aktien','high','financial_sensitive',False],
    ['trading','high','financial_sensitive',False],
    ['krypto','high','financial_sensitive',False],
    ['geldanlage','high','financial_sensitive',False],
    ['rendite','high','financial_sensitive',False],
    ['beschaffung','blocked','illegal_content',False],
    ['darknet','blocked','illegal_content',False],
    ['steuerhinterziehung','blocked','illegal_content',False],
])

print(f'Created {count} total seed rows across all CSV files')
