"""Expand seed CSVs to hit 3,500+ rows total"""
import csv, os

base = os.path.join(os.path.dirname(__file__), '..', 'data', 'discovery_seed_universes')

def append_csv(path, rows):
    full = os.path.join(base, path)
    exists = os.path.exists(full)
    with open(full, 'a', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        for row in rows:
            w.writerow(row)
    return len(rows)

total = 0

# ── More professions ──
total += append_csv('professions/professions_office_de.csv', [
    ['Grafikdesigner','profession',68,'kreativ'],['UX-Designer','profession',66,'it'],
    ['Webentwickler','profession',74,'it'],['Datenanalyst','profession',72,'it'],
    ['Buchhalter','profession',76,'finanzen'],['Steuerfachangestellter','profession',74,'finanzen'],
    ['Personalmanager','profession',70,'buero'],['Architekt','profession',74,'bau'],
    ['Bauingenieur','profession',72,'bau'],['Psychotherapeut','profession',78,'gesundheit'],
    ['Logopäde','profession',74,'gesundheit'],['Rettungsassistent','profession',76,'gesundheit'],
    ['Fotograf','profession',68,'kreativ'],['Übersetzer','profession',64,'sprache'],
    ['Journalist','profession',66,'medien'],['Sozialarbeiter','profession',72,'soziales'],
    ['Landschaftsgärtner','profession',66,'garten'],['Bäcker','profession',68,'handwerk'],
    ['Konditor','profession',66,'handwerk'],['Texter','profession',62,'kreativ'],
])

total += append_csv('professions/professions_craft_de.csv', [
    ['Schreiner','profession',74,'handwerk'],['Glaser','profession',66,'handwerk'],
    ['Steinmetz','profession',62,'handwerk'],['Betonbauer','profession',64,'handwerk'],
    ['Raumausstatter','profession',62,'handwerk'],['Ofenbauer','profession',60,'handwerk'],
])

# ── More audiences ──
total += append_csv('audiences/audiences_general_de.csv', [
    ['Hausbesitzer','audience',74,'allgemein'],['Mieter','audience',76,'allgemein'],
    ['Arbeitnehmer','audience',78,'arbeit'],['Pendler','audience',74,'arbeit'],
    ['Berufseinsteiger','audience',80,'arbeit'],['Quereinsteiger','audience',74,'arbeit'],
    ['Stadtbewohner','audience',72,'allgemein'],['Landbewohner','audience',68,'allgemein'],
    ['Nachtschichtarbeitende','audience',70,'arbeit'],['Werkstudenten','audience',68,'arbeit'],
    ['Praktikanten','audience',66,'arbeit'],['Karrierewechsler','audience',70,'arbeit'],
])

total += append_csv('audiences/audiences_senior_de.csv', [
    ['Menschen mit Demenz','audience',90,'pflege'],['Menschen mit Parkinson','audience',82,'pflege'],
    ['Menschen mit Arthrose','audience',80,'pflege'],['Diabetiker','audience',84,'gesundheit'],
    ['Bluthochdruckpatienten','audience',82,'gesundheit'],['Menschen mit Sehbehinderung','audience',74,'senioren'],
    ['Menschen mit Hörbehinderung','audience',72,'senioren'],['Rollstuhlfahrer','audience',70,'senioren'],
    ['Krebspatienten','audience',80,'gesundheit'],['Schlaganfallpatienten','audience',78,'gesundheit'],
])

# ── More problems ──
total += append_csv('problems/problems_organization_de.csv', [
    ['Aufschieben','problem',78,'organisation'],['Perfektionismus','problem',76,'organisation'],
    ['Ablenkung','problem',80,'organisation'],['Papierchaos','problem',76,'organisation'],
    ['digitale Unordnung','problem',74,'organisation'],['E-Mail-Flut','problem',72,'arbeit'],
    ['Erschöpfung','problem',82,'gesundheit'],['Burnout','problem',80,'gesundheit'],
    ['Müdigkeit','problem',76,'gesundheit'],['Antriebslosigkeit','problem',74,'gesundheit'],
    ['Entscheidungsprobleme','problem',74,'organisation'],['Multitasking','problem',72,'organisation'],
])

total += append_csv('problems/problems_health_de.csv', [
    ['Verdauungsprobleme','problem',74,'gesundheit'],['Gelenkschmerzen','problem',78,'gesundheit'],
    ['Nackenschmerzen','problem',76,'gesundheit'],['Tinnitus','problem',72,'gesundheit'],
    ['Hautprobleme','problem',72,'gesundheit'],['Akne','problem',68,'gesundheit'],
    ['Neurodermitis','problem',70,'gesundheit'],['Wechseljahresbeschwerden','problem',76,'gesundheit'],
    ['Menstruationsbeschwerden','problem',72,'gesundheit'],['Heuschnupfen','problem',68,'gesundheit'],
    ['Lebensmittelunverträglichkeiten','problem',72,'gesundheit'],['Sodbrennen','problem',70,'gesundheit'],
    ['Schwindel','problem',70,'gesundheit'],['Glutenunverträglichkeit','problem',66,'gesundheit'],
])

# ── More exams ──
total += append_csv('exams/exams_vocational_de.csv', [
    ['Staplerschein','exam',70,'lizenz'],['Kranschein','exam',66,'lizenz'],
    ['Rettungsschwimmer','exam',62,'lizenz'],['Erste-Hilfe-Kurs','exam',72,'lizenz'],
    ['Elektrofachkraft Prüfung','exam',74,'handwerk'],['Schweißerprüfung','exam',68,'handwerk'],
    ['Sachkundenachweis Pflanzenschutz','exam',60,'lizenz'],['Sachkundeprüfung 34a','exam',66,'lizenz'],
])

# ── More hobbies ──
total += append_csv('hobbies/hobbies_creative_de.csv', [
    ['Töpfern','hobby',66,'kreativ'],['Basteln','hobby',72,'kreativ'],
    ['Schmuckherstellung','hobby',62,'kreativ'],['Digital Art','hobby',64,'kreativ'],
    ['Videobearbeitung','hobby',64,'kreativ'],['Podcast erstellen','hobby',62,'kreativ'],
    ['Bloggen','hobby',66,'kreativ'],['Schreiben','hobby',70,'kreativ'],
    ['Tagebuch schreiben','hobby',68,'kreativ'],['Bullet Journal','hobby',72,'kreativ'],
    ['Tagebuch schreiben','hobby',68,'kreativ'],['Origami','hobby',60,'kreativ'],
])

total += append_csv('hobbies/hobbies_sports_de.csv',
    [['Schwimmen','hobby',76,'sport'],['Joggen','hobby',74,'sport'],
    ['Nordic Walking','hobby',76,'sport'],['Golf','hobby',64,'sport'],
    ['Tennis','hobby',66,'sport'],['Tischtennis','hobby',62,'sport'],
    ['Badminton','hobby',60,'sport'],['Fußball','hobby',68,'sport'],
    ['Reiten','hobby',66,'sport'],['Boxen','hobby',62,'sport'],
    ['Kampfsport','hobby',64,'sport'],['Bouldern','hobby',68,'sport'],
    ['Skilanglauf','hobby',60,'sport'],['Volleyball','hobby',58,'sport'],
    ['Basketball','hobby',62,'sport'],['Segeln','hobby',60,'sport'],
    ['Surfen','hobby',58,'sport'],['Skateboarden','hobby',52,'sport'],
])

# ── More household ──
total += append_csv('household/household_organization_de.csv', [
    ['Einkaufsliste','topic',74,'haushalt'],['Vorratshaltung','topic',72,'haushalt'],
    ['Kleiderschrank organisieren','topic',70,'haushalt'],['Keller aufräumen','topic',66,'haushalt'],
    ['Umzug organisieren','topic',76,'haushalt'],['Renovierung planen','topic',74,'haushalt'],
    ['Strom sparen','topic',72,'haushalt'],['Wäschepflege','topic',68,'haushalt'],
    ['Kompostieren','topic',66,'garten'],['Mülltrennung','topic',64,'haushalt'],
    ['Haushaltshilfe finden','topic',66,'haushalt'],['Dachboden ausmisten','topic',64,'haushalt'],
])

# ── More business ──
total += append_csv('business/business_basics_de.csv', [
    ['Netzwerken','topic',74,'business'],['Online-Shop eröffnen','topic',76,'business'],
    ['Steuerberater finden','topic',72,'business'],['Versicherung für Selbstständige','topic',74,'business'],
    ['Altersvorsorge für Selbstständige','topic',76,'business'],['Krankenversicherung Freelancer','topic',70,'business'],
    ['Aufträge verhandeln','topic',72,'business'],['Honorar kalkulieren','topic',74,'business'],
    ['Kundenbindung','topic',72,'business'],['Datenschutz Grundverordnung','topic',66,'business'],
    ['Kaltakquise','topic',68,'business'],['Beschwerdemanagement','topic',66,'business'],
    ['Personal einstellen','topic',64,'business'],['Rechnungsprogramm wählen','topic',68,'business'],
])

# ── More pets ──
total += append_csv('pets/pets_dogs_de.csv', [
    ['Hundeführerschein','topic',70,'haustiere'],['Hundepflege','topic',68,'haustiere'],
    ['Hundeernährung','topic',72,'haustiere'],['BARF','topic',64,'haustiere'],
    ['Hundeerziehung','topic',88,'haustiere'],['Agility','topic',62,'haustiere'],
    ['Hundesport','topic',60,'haustiere'],['Hundepension','topic',62,'haustiere'],
    ['Hundekrankenversicherung','topic',64,'haustiere'],['Welpenfutter','topic',66,'haustiere'],
])

# ── More learning ──
total += append_csv('learning/learning_topics_de.csv', [
    ['Vokabeln lernen','topic',76,'lernen'],['Mathe lernen','topic',72,'lernen'],
    ['Sprachen lernen','topic',80,'lernen'],['Speed Reading','topic',66,'lernen'],
    ['Mind Mapping','topic',70,'lernen'],['Lerntechniken','topic',78,'lernen'],
    ['Klassenarbeit Vorbereitung','topic',74,'lernen'],['Hausaufgabenplan','topic',72,'lernen'],
    ['Online-Kurse','topic',66,'lernen'],['Weiterbildung','topic',70,'lernen'],
    ['E-Learning','topic',64,'lernen'],['Zertifikatsvorbereitung','topic',68,'lernen'],
    ['Nachhilfe geben','topic',64,'lernen'],['Schulmaterial organisieren','topic',68,'lernen'],
])

# ── More seniors ──
total += append_csv('seniors/senior_topics_de.csv', [
    ['Treppenlift','topic',68,'senioren'],['Hausnotruf','topic',74,'senioren'],
    ['Betreutes Wohnen','topic',76,'senioren'],['Seniorenheim finden','topic',78,'senioren'],
    ['Tagespflege','topic',72,'senioren'],['Kurzzeitpflege','topic',74,'senioren'],
    ['Pflegetagebuch','topic',80,'senioren'],['Pflegeprotokoll','topic',76,'senioren'],
    ['Seniorenhandy','topic',66,'senioren'],['Tablet für Senioren','topic',64,'senioren'],
    ['Digitaler Nachlass','topic',70,'senioren'],['Bestattungsvorsorge','topic',68,'senioren'],
    ['Verhinderungspflege','topic',70,'senioren'],['Pflegesachleistung','topic',68,'senioren'],
    ['Entlastungsbetrag','topic',64,'senioren'],['Pflegeberatung','topic',74,'senioren'],
])

# ── More family ──
total += append_csv('family/family_topics_de.csv', [
    ['Geburtsvorbereitung','topic',82,'familie'],['Wochenbett','topic',78,'familie'],
    ['Stillen','topic',80,'familie'],['Fläschchen','topic',72,'familie'],
    ['Kindergarten Eingewöhnung','topic',76,'familie'],['Kinderkrankheiten','topic',78,'familie'],
    ['Erziehungsratgeber','topic',76,'familie'],['Trotzphase','topic',74,'familie'],
    ['Wutausbrüche Kind','topic',72,'familie'],['Grenzen setzen','topic',78,'familie'],
    ['Einschlafritual','topic',78,'familie'],['Morgenroutine','topic',74,'familie'],
    ['Kinderimpfungen','topic',74,'familie'],['Kinderzahnpflege','topic',68,'familie'],
    ['Geschwisterrivalität','topic',68,'familie'],['Belohnungssystem','topic',70,'familie'],
    ['Schulranzen kaufen','topic',62,'familie'],['Schulweg','topic',66,'familie'],
    ['Krabbelgruppe','topic',64,'familie'],['Familienkonferenz','topic',64,'familie'],
])

# ── More health trackers ──
total += append_csv('health_trackers/health_trackers_de.csv', [
    ['Kopfschmerztagebuch','topic',74,'gesundheit','medium'],
    ['Allergietagebuch','topic',70,'gesundheit','medium'],
    ['Periodentracker','topic',72,'gesundheit','medium'],
    ['Wechseljahrestagebuch','topic',70,'gesundheit','medium'],
    ['Trinktracker','topic',64,'gesundheit','low'],
    ['Schrittzähler Logbuch','topic',68,'gesundheit','low'],
    ['Sporttagebuch','topic',72,'sport','low'],
    ['Trainingsplaner','topic',78,'sport','low'],
    ['Reha Tagebuch','topic',70,'gesundheit','medium'],
    ['Operationsvorbereitung','topic',66,'gesundheit','high'],
    ['Hauttagebuch','topic',66,'gesundheit','medium'],
    ['Dehntagebuch','topic',62,'sport','low'],
    ['Physiotherapie Tagebuch','topic',68,'gesundheit','medium'],
    ['Verdauungstagebuch','topic',68,'gesundheit','medium'],
])

# ── More AI ──
total += append_csv('ai_use_cases/ai_professions_de.csv', [
    ['KI für Architekten','topic',74,'ki'],['KI für Anwälte','topic',72,'ki'],
    ['KI für Ärzte','topic',74,'ki'],['KI für Designer','topic',72,'ki'],
    ['KI für Buchhalter','topic',70,'ki'],['KI für Fotografen','topic',66,'ki'],
    ['KI für Softwareentwickler','topic',78,'ki'],['KI für Vertriebler','topic',68,'ki'],
    ['ChatGPT für Studenten','topic',82,'ki'],['ChatGPT für Lehrer','topic',78,'ki'],
    ['KI für Personaler','topic',66,'ki'],['KI für Datenanalysten','topic',74,'ki'],
    ['KI für Texter','topic',68,'ki'],['KI für Journalisten','topic',64,'ki'],
    ['ChatGPT für Kreative','topic',72,'ki'],['KI für Physiotherapeuten','topic',68,'ki'],
    ['KI für Übersetzer','topic',66,'ki'],['ChatGPT für Eltern','topic',68,'ki'],
])

# ── More contexts ──
total += append_csv('contexts/contexts_de.csv', [
    ['für das Homeoffice','context',78,'arbeit'],['für das Büro','context',74,'arbeit'],
    ['für die Baustelle','context',66,'arbeit'],['für den Pflegealltag','context',80,'pflege'],
    ['für die Nachtschicht','context',72,'arbeit'],['für die Prüfung','context',84,'lernen'],
    ['für den Schulalltag','context',76,'lernen'],['für den Urlaub','context',68,'allgemein'],
    ['für den Notfall','context',78,'allgemein'],['für die Steuererklärung','context',76,'business'],
    ['für den Behördengang','context',74,'allgemein'],['für den Arztbesuch','context',76,'gesundheit'],
    ['in der Schwangerschaft','context',80,'familie'],['nach der Geburt','context',78,'familie'],
    ['in der Pubertät','context',74,'familie'],['im Alter','context',78,'senioren'],
    ['nach der Diagnose','context',72,'gesundheit'],['vor der Prüfung','context',82,'lernen'],
    ['zum Berufseinstieg','context',76,'arbeit'],['zur Existenzgründung','context',74,'business'],
    ['für die Therapie','context',70,'gesundheit'],['in den Wechseljahren','context',72,'gesundheit'],
    ['während der Reha','context',70,'gesundheit'],['für die Reise','context',66,'allgemein'],
])

# ── Expand compatibility CSV to 300+ ──
total += append_csv('compatibility/topic_audience_compatibility.csv', [
    ['Nebengewerbe starten','Selbstständige',90,'compatible','Existenzgründung'],
    ['Nebengewerbe starten','Kleinunternehmer',88,'compatible','kleine Betriebe'],
    ['Kundengewinnung','Selbstständige',90,'compatible','Business-Thema'],
    ['Kundengewinnung','Freelancer',85,'compatible','Akquise-Thema'],
    ['Social Media Marketing','Selbstständige',88,'compatible','Marketing'],
    ['Social Media Marketing','Kleinunternehmer',85,'compatible','Marketing'],
    ['Zeitmanagement','Berufstätige',90,'compatible','Produktivität'],
    ['Zeitmanagement','Selbstständige',88,'compatible','Produktivität'],
    ['Zeitmanagement','Studenten',85,'compatible','Lernplanung'],
    ['Produktivität','Berufstätige',88,'compatible','Arbeitsalltag'],
    ['Produktivität','Selbstständige',88,'compatible','Selbstorganisation'],
    ['Homeoffice','Berufstätige',92,'compatible','Remote Work'],
    ['Homeoffice','Selbstständige',88,'compatible','Home Office'],
    ['Haushaltsbuch','Familien',88,'compatible','Budgetplanung'],
    ['Haushaltsbuch','Singles',82,'compatible','persönliche Finanzen'],
    ['Haushaltsbuch','Studenten',80,'compatible','erstes Budget'],
    ['Putzplan','Familien',84,'compatible','Haushaltsorganisation'],
    ['Putzplan','Singles',78,'compatible','Haushaltsorganisation'],
    ['Putzplan','Berufstätige',82,'compatible','schnelle Reinigung'],
    ['Essensplan','Berufstätige',88,'compatible','Meal Prep'],
    ['Essensplan','Singles',82,'compatible','Meal Prep'],
    ['Meal Prep','Berufstätige',90,'compatible','Essensvorbereitung'],
    ['Meal Prep','Schichtarbeiter',88,'compatible','Schichtarbeit'],
    ['Meal Prep','Studenten',84,'compatible','günstig kochen'],
    ['Minimalismus','Berufstätige',80,'compatible','Lebensstil'],
    ['Minimalismus','Familien',78,'compatible','Ausmisten'],
    ['Aufräumen','Familien',82,'compatible','Ordnung'],
    ['Aufräumen','Erwachsene mit ADHS',88,'compatible','ADHS'],
    ['Notfallordner','Familien',86,'compatible','Dokumente'],
    ['Notfallordner','Senioren',90,'compatible','Vorsorge'],
    ['Notfallordner','Angehörige',88,'compatible','Pflegeorganisation'],
    ['Dokumentenmappe','Selbstständige',82,'compatible','Buchhaltung'],
    ['Dokumentenmappe','Familien',80,'compatible','Haushalt'],
    ['Behördenpost organisieren','Senioren',90,'compatible','Verwaltung'],
    ['Behördenpost organisieren','Angehörige',88,'compatible','Unterstützung'],
    ['Behördenpost organisieren','Berufstätige',82,'compatible','Verwaltung'],
    ['Leinenführigkeit','Hundehalter',95,'compatible','Hundetraining'],
    ['Rückruf','Hundehalter',95,'compatible','Hundetraining'],
    ['Angsthund Training','Hundehalter',92,'compatible','Problemhund'],
    ['Welpentagebuch','Hundehalter',90,'compatible','Welpen'],
    ['Ernährungstagebuch','Diabetiker',88,'compatible','Blutzucker'],
    ['Ernährungstagebuch','Sportler',84,'compatible','Fitness'],
    ['Schlaftagebuch','Menschen mit Schlafproblemen',90,'compatible','Schlaf'],
    ['Schmerztagebuch','Menschen mit chronischen Schmerzen',88,'compatible','Schmerz'],
    ['Medikamentenplan','Pflegebedürftige',92,'compatible','Medikation'],
    ['Vorlesen','Eltern',88,'compatible','Kinder'],
    ['Vorlesen','Großeltern',84,'compatible','Enkel'],
    ['Hausaufgaben','Eltern',86,'compatible','Schule'],
    ['Hausaufgaben','Schüler',84,'compatible','Lernhilfe'],
    ['Pubertät','Eltern',90,'compatible','Erziehung'],
    ['Kindergeburtstag','Eltern',82,'compatible','Planung'],
    ['Kindergeburtstag','Mütter',84,'compatible','Organisation'],
    ['Lernorganisation','Erwachsene mit ADHS',88,'compatible','ADHS Strategie'],
    ['Lernplan','Schüler',84,'compatible','Schule'],
    ['Lernplan','Studenten',86,'compatible','Studium'],
    ['Prüfungsvorbereitung','Azubis',88,'compatible','Ausbildung'],
    ['Prüfungsvorbereitung','Schüler',86,'compatible','Schulabschluss'],
    ['Gedächtnistraining','Senioren',88,'compatible','Gehirntraining'],
    ['Sturzprävention','Senioren',90,'compatible','Sicherheit'],
    ['Seniorengymnastik','Senioren',86,'compatible','Bewegung'],
    ['Sturzprävention','Angehörige',84,'compatible','Pflege'],
    ['Altersvorsorge','Berufstätige',82,'compatible','Finanzen'],
    ['Altersvorsorge','Selbstständige',86,'compatible','Rente'],
    ['Patientenverfügung','Angehörige',88,'compatible','Vorsorge'],
    ['Vorsorgevollmacht','Angehörige',88,'compatible','Vorsorge'],
    ['Testament','Angehörige',82,'compatible','Nachlass'],
    ['Fotografie','Hobbyfotografen',88,'compatible','Hobby'],
    ['Fotografie','Reisende',78,'compatible','Reisefotografie'],
    ['Nähen','Hobbynäherinnen',88,'compatible','Kreativ'],
    ['Stricken','Hobbystrickerinnen',84,'compatible','Handarbeit'],
    ['Malen','Hobbymaler',82,'compatible','Kunst'],
    ['Zeichnen','Hobbyzeichner',82,'compatible','Kunst'],
    ['Garten','Hobbygärtner',88,'compatible','Garten'],
    ['Garten','Hausbesitzer',84,'compatible','Gartenarbeit'],
    ['Balkongarten','Stadtbewohner',86,'compatible','Urban Gardening'],
    ['Gemüsegarten','Hobbygärtner',85,'compatible','Selbstversorgung'],
    ['Kochen','Hobbyköche',86,'compatible','Küche'],
    ['Backen','Hobbybäcker',84,'compatible','Backstube'],
    ['Brot backen','Hobbybäcker',86,'compatible','Brot'],
    ['Grillen','Hobbygriller',80,'compatible','Grillsaison'],
    ['Camping','Camper',88,'compatible','Outdoor'],
    ['Camping','Familien',84,'compatible','Familienurlaub'],
    ['Wandern','Naturfreunde',86,'compatible','Outdoor'],
    ['Angeln','Angler',88,'compatible','Angelverein'],
    ['Radfahren','Radfahrer',84,'compatible','Fahrrad'],
    ['Radfahren','Pendler',82,'compatible','Arbeitsweg'],
    ['Laufen','Läufer',86,'compatible','Joggen'],
    ['Yoga','Sportler',82,'compatible','Beweglichkeit'],
    ['Yoga','Berufstätige',80,'compatible','Stressabbau'],
    ['Fitness','Sportler',84,'compatible','Training'],
    ['Krafttraining','Sportler',84,'compatible','Muskelaufbau'],
    ['Pilates','Sportler',76,'compatible','Beweglichkeit'],
])

# ── Expand incompatible to 100+ ──
total += append_csv('compatibility/incompatible_combinations.csv', [
    ['KI für Handwerker','Pflege','domain_mismatch','hard_block'],
    ['KI für Handwerker','Senioren','domain_mismatch','hard_block'],
    ['KI für Handwerker','Rentner','domain_mismatch','hard_block'],
    ['KI für Pflegekräfte','Handwerker','domain_mismatch','hard_block'],
    ['Pflegegrad','Studenten','life_stage_mismatch','hard_block'],
    ['Pflegegrad','Schüler','life_stage_mismatch','hard_block'],
    ['Pflegeantrag','Studenten','life_stage_mismatch','hard_block'],
    ['Pflegeantrag','Schüler','life_stage_mismatch','hard_block'],
    ['Pflegeorganisation','Studenten','domain_mismatch','hard_block'],
    ['Demenz','Studenten','life_stage_mismatch','hard_block'],
    ['Demenz','Kinder','life_stage_mismatch','hard_block'],
    ['Sturzprävention','Studenten','life_stage_mismatch','hard_block'],
    ['Sturzprävention','Kinder','life_stage_mismatch','hard_block'],
    ['Seniorengymnastik','Studenten','life_stage_mismatch','hard_block'],
    ['Seniorengymnastik','Kinder','life_stage_mismatch','hard_block'],
    ['Rente beantragen','Studenten','life_stage_mismatch','hard_block'],
    ['Rente beantragen','Azubis','life_stage_mismatch','hard_block'],
    ['Altersvorsorge','Schüler','life_stage_mismatch','hard_block'],
    ['Altersvorsorge','Kinder','life_stage_mismatch','hard_block'],
    ['Patientenverfügung','Kinder','life_stage_mismatch','hard_block'],
    ['Patientenverfügung','Studenten','life_stage_mismatch','hard_block'],
    ['Vorsorgevollmacht','Kinder','life_stage_mismatch','hard_block'],
    ['Testament','Schüler','life_stage_mismatch','hard_block'],
    ['Testament','Studenten','life_stage_mismatch','hard_block'],
    ['Babyschlaf','Senioren','life_stage_mismatch','hard_block'],
    ['Babyschlaf','Rentner','life_stage_mismatch','hard_block'],
    ['Babyschlaf','Studenten','life_stage_mismatch','hard_block'],
    ['Stillen','Senioren','life_stage_mismatch','hard_block'],
    ['Stillen','Männer','domain_mismatch','hard_block'],
    ['Beikost','Senioren','life_stage_mismatch','hard_block'],
    ['Beikost','Rentner','life_stage_mismatch','hard_block'],
    ['Geburtsvorbereitung','Senioren','life_stage_mismatch','hard_block'],
    ['Geburtsvorbereitung','Rentner','life_stage_mismatch','hard_block'],
    ['Trotzphase','Senioren','life_stage_mismatch','hard_block'],
    ['Trotzphase','Rentner','life_stage_mismatch','hard_block'],
    ['Pubertät','Senioren','life_stage_mismatch','hard_block'],
    ['Pubertät','Kleinkinder','life_stage_mismatch','hard_block'],
    ['Kindergeburtstag','Senioren','life_stage_mismatch','hard_block'],
    ['Kindergeburtstag','Singles','domain_mismatch','hard_block'],
    ['Vorlesen','Senioren','audience_mismatch','hard_block'],
    ['Hundetraining','Kleinunternehmer','domain_mismatch','hard_block'],
    ['Hundetraining','Senioren','domain_mismatch','hard_block'],
    ['Welpentraining','Senioren','domain_mismatch','hard_block'],
    ['Welpentraining','Kleinunternehmer','domain_mismatch','hard_block'],
    ['Katzenhaltung','Hundehalter','domain_mismatch','hard_block'],
    ['Balkongarten','Landwirte','domain_mismatch','hard_block'],
    ['Fotografie','Hundehalter','domain_mismatch','hard_block'],
    ['Buchhaltung','Senioren','domain_mismatch','hard_block'],
    ['Buchhaltung','Pflegekräfte','domain_mismatch','hard_block'],
    ['Buchhaltung','Schüler','domain_mismatch','hard_block'],
    ['Steuererklärung','Pflegekräfte','domain_mismatch','hard_block'],
    ['Steuererklärung','Schüler','domain_mismatch','hard_block'],
    ['Steuererklärung','Studenten','domain_mismatch','hard_block'],
    ['Existenzgründung','Rentner','life_stage_mismatch','hard_block'],
    ['Existenzgründung','Schüler','life_stage_mismatch','hard_block'],
    ['Firmengründung','Rentner','life_stage_mismatch','hard_block'],
    ['Kundengewinnung','Rentner','domain_mismatch','hard_block'],
    ['Kundengewinnung','Schüler','domain_mismatch','hard_block'],
    ['Akquise','Senioren','domain_mismatch','hard_block'],
    ['Online-Shop','Senioren','domain_mismatch','hard_block'],
    ['Homeoffice','Rentner','domain_mismatch','hard_block'],
    ['Meal Prep','Kinder','domain_mismatch','hard_block'],
    ['Schwangerschaftsyoga','Männer','domain_mismatch','hard_block'],
    ['Medikamentenplan','Kinder','domain_mismatch','hard_block'],
])

# ── Expand risk rules to 100+ ──
total += append_csv('compatibility/risk_rules.csv', [
    ['medikament','high','health_sensitive',False],
    ['diagnose','high','health_sensitive',False],
    ['symptom','high','health_sensitive',False],
    ['erkrankung','high','health_sensitive',False],
    ['krankheit','high','health_sensitive',False],
    ['heilung','high','health_sensitive',False],
    ['medizinisch','high','health_sensitive',False],
    ['psychisch','high','health_sensitive',False],
    ['psychologie','high','health_sensitive',False],
    ['selbsthilfe','medium','health_adjacent',True],
    ['angststörung','high','health_sensitive',False],
    ['panikattacke','high','health_sensitive',False],
    ['trauma','high','health_sensitive',False],
    ['sucht','high','health_sensitive',False],
    ['alkohol','high','health_sensitive',False],
    ['nikotin','high','health_sensitive',False],
    ['abnehmen','medium','health_adjacent',True],
    ['diät','medium','health_adjacent',True],
    ['kalorien','medium','health_adjacent',True],
    ['gesetz','high','legal_sensitive',False],
    ['vertrag','high','legal_sensitive',False],
    ['klage','high','legal_sensitive',False],
    ['gericht','high','legal_sensitive',False],
    ['anwalt','high','legal_sensitive',False],
    ['haftung','high','legal_sensitive',False],
    ['strafrecht','high','legal_sensitive',False],
    ['urteil','high','legal_sensitive',False],
    ['einklagen','high','legal_sensitive',False],
    ['investment','high','financial_sensitive',False],
    ['aktien','high','financial_sensitive',False],
    ['trading','high','financial_sensitive',False],
    ['krypto','high','financial_sensitive',False],
    ['bitcoin','high','financial_sensitive',False],
    ['geldanlage','high','financial_sensitive',False],
    ['rendite','high','financial_sensitive',False],
    ['reich werden','high','financial_sensitive',False],
    ['passives einkommen','medium','financial_sensitive',True],
    ['finanzielle freiheit','medium','financial_sensitive',True],
    ['versicherung','medium','financial_sensitive',True],
    ['kredit','medium','financial_sensitive',True],
    ['schulden','medium','financial_sensitive',True],
    ['insolvenz','medium','financial_sensitive',True],
    ['scheidung','medium','legal_sensitive',True],
    ['sorgerecht','high','legal_sensitive',False],
    ['unterhalt','medium','legal_sensitive',True],
    ['erbrecht','high','legal_sensitive',False],
    ['arbeitsrecht','high','legal_sensitive',False],
    ['mietrecht','high','legal_sensitive',False],
    ['impfung','high','health_sensitive',False],
    ['impfen','high','health_sensitive',False],
    ['allergie','medium','health_adjacent',True],
    ['unverträglichkeit','medium','health_adjacent',True],
    ['intoleranz','medium','health_adjacent',True],
    ['neurofeedback','high','health_sensitive',False],
    ['homöopathie','medium','health_adjacent',True],
    ['alternativmedizin','medium','health_adjacent',True],
    ['naturheilkunde','medium','health_adjacent',True],
    ['energieheilung','medium','health_adjacent',True],
    ['esoterik','medium','health_adjacent',True],
    ['wunderheilung','restricted','unsubstantiated_claims',False],
    ['garantiert','medium','outcome_claim',True],
    ['garantie','medium','outcome_claim',True],
    ['100 prozent','medium','outcome_claim',True],
    ['sicher erfolg','medium','outcome_claim',True],
    ['garantiert heilen','restricted','unsubstantiated_claims',False],
    ['schnell reich','restricted','unsubstantiated_claims',False],
    ['passiv geld','medium','financial_sensitive',True],
    ['nebenbei geld','medium','financial_sensitive',True],
    ['beschaffung','blocked','illegal_content',False],
    ['darknet','blocked','illegal_content',False],
])

print(f'EXPANDED: {total} new rows added')
