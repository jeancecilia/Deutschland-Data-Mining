"""Massive seed data expansion to hit 5,000+ rows."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from scale_seed_network import append_csv, append_compat, append_incompat, append_risk

BASE = os.path.join(os.path.dirname(__file__), '..', 'data', 'discovery_seed_universes')

def p(path):
    return os.path.join(BASE, path)

total = 0

# === PROFESSIONS ++ ===
for fname, rows in [
    ('professions/professions_craft_de.csv', [
        ['Gerüstbauer','profession',64,'handwerk','bau'],['Schornsteinfeger','profession',68,'handwerk','gebäude'],
        ['Industriemechaniker','profession',78,'industrie','mechanik'],['Augenoptiker','profession',68,'handwerk','optik'],
        ['Hörgeräteakustiker','profession',66,'handwerk','gesundheit'],['Zahntechniker','profession',64,'handwerk','gesundheit'],
    ]),
    ('professions/professions_industry_de.csv', [
        ['Chemikant','profession',66,'industrie','chemie'],['Pharmakant','profession',68,'industrie','pharma'],
        ['Maschinenführer','profession',64,'industrie','produktion'],['Lagerlogistiker','profession',62,'industrie','logistik'],
        ['Qualitätsprüfer','profession',64,'industrie','qualität'],['Elektroniker Betriebstechnik','profession',74,'industrie','elektro'],
    ]),
    ('professions/professions_agriculture_de.csv', [
        ['Landwirt','profession',66,'landwirtschaft'],['Gärtner','profession',70,'landwirtschaft'],
        ['Florist','profession',64,'landwirtschaft'],['Winzer','profession',62,'landwirtschaft'],
        ['Forstwirt','profession',60,'landwirtschaft'],['Pferdewirt','profession',56,'landwirtschaft'],
        ['Landschaftsgärtner','profession',68,'landwirtschaft'],
    ]),
    ('professions/professions_media_de.csv', [
        ['Journalist','profession',66,'medien'],['Redakteur','profession',64,'medien'],
        ['Texter','profession',60,'medien'],['Social Media Manager','profession',66,'medien'],
        ['Grafikdesigner','profession',68,'medien'],['Fotograf','profession',66,'medien'],
        ['Videograf','profession',62,'medien'],
    ]),
    ('professions/professions_legal_admin_de.csv', [
        ['Rechtsanwalt','profession',76,'recht'],['Notar','profession',72,'recht'],
        ['Steuerberater','profession',78,'finanzen'],['Buchhalter','profession',74,'finanzen'],
        ['Verwaltungsfachangestellter','profession',66,'verwaltung'],['Beamter','profession',70,'verwaltung'],
    ]),
    ('professions/professions_social_de.csv', [
        ['Sozialarbeiter','profession',74,'sozial'],['Sozialpädagoge','profession',78,'sozial'],
        ['Heilerziehungspfleger','profession',70,'sozial'],['Familienhelfer','profession',66,'sozial'],
        ['Schulbegleiter','profession',64,'sozial'],['Betreuungskraft','profession',68,'sozial'],
    ]),
]:
    c = append_csv(fname, rows)
    total += c
    print(f'  {fname}: +{c}')

# === TOPICS ++ ===
for fname, rows in [
    ('topics/topics_health_trackers_de.csv', [
        ['Schmerztagebuch','topic',82,'gesundheit','tracker'],['Medikamentenplan','topic',88,'gesundheit','organisation'],
        ['Arzttermin Vorbereitung','topic',84,'gesundheit','organisation'],['Krankenhaus Checkliste','topic',82,'gesundheit','organisation'],
        ['Reha Planer','topic',76,'gesundheit','reha'],['Physiotherapie Übungsbuch','topic',74,'gesundheit','therapie'],
        ['Pflegegrad Tagebuch','topic',86,'pflege','tracker'],['Pflegeprotokoll Vorlage','topic',84,'pflege','dokumentation'],
    ]),
    ('topics/topics_business_de.csv', [
        ['Angebotsvorlage','topic',78,'business','verkauf'],['Rechnungsvorlage','topic',76,'business','buchhaltung'],
        ['Social Media Planer','topic',74,'business','marketing'],['SEO Grundlagen','topic',72,'business','marketing'],
        ['Google My Business','topic',68,'business','lokal'],['Kleinunternehmer Steuer','topic',74,'business','steuer'],
    ]),
    ('topics/topics_ai_de.csv', [
        ['KI für Architekten','topic',74,'ki','bau'],['KI für Anwälte','topic',72,'ki','recht'],
        ['KI für Ärzte','topic',74,'ki','medizin'],['KI für Fotografen','topic',68,'ki','kreativ'],
        ['ChatGPT im Handwerk','topic',76,'ki','handwerk'],['KI E-Mail Vorlagen','topic',72,'ki','business'],
    ]),
    ('topics/topics_seniors_de.csv', [
        ['Pflegegrad Widerspruch','topic',92,'senioren','pflege'],['Pflegesachleistung','topic',72,'senioren','pflege'],
        ['Kurzzeitpflege','topic',76,'senioren','pflege'],['Tagespflege','topic',74,'senioren','pflege'],
        ['Verhinderungspflege','topic',70,'senioren','pflege'],['Bestattungsvorsorge','topic',68,'senioren','vorsorge'],
    ]),
    ('topics/topics_learning_de.csv', [
        ['Abitur Vorbereitung','topic',84,'lernen','prüfung'],['Mathe Abitur','topic',78,'lernen','mathe'],
        ['Deutsch Abitur','topic',80,'lernen','deutsch'],['Mündliche Prüfung','topic',76,'lernen','prüfung'],
        ['Hausarbeit schreiben','topic',74,'lernen','studium'],['Bachelorarbeit','topic',78,'lernen','studium'],
        ['Masterarbeit','topic',76,'lernen','studium'],
    ]),
    ('topics/topics_digital_de.csv', [
        ['Digitale Ordnung','topic',78,'digital','organisation'],['E-Mail Organisation','topic',74,'digital','organisation'],
        ['Passwort Manager','topic',68,'digital','sicherheit'],['Backup Strategie','topic',66,'digital','sicherheit'],
        ['Digitale Minimalismus','topic',72,'digital','lifestyle'],['Digitale Steuererklärung','topic',68,'digital','steuer'],
        ['Online Banking','topic',66,'digital','finanzen'],
    ]),
]:
    c = append_csv(fname, rows)
    total += c
    print(f'  {fname}: +{c}')

# === EXAMS ++ ===
for fname, rows in [
    ('exams/exams_health_de.csv', [
        ['Pflegeexamen','exam',92,'gesundheit','pflege'],['Physiotherapie Examen','exam',84,'gesundheit','therapie'],
        ['Ergotherapie Examen','exam',80,'gesundheit','therapie'],['Hebammenexamen','exam',86,'gesundheit','geburt'],
        ['Notfallsanitäter Prüfung','exam',84,'gesundheit','notfall'],
    ]),
    ('exams/exams_business_de.csv', [
        ['Steuerberaterexamen','exam',78,'finanzen','steuer'],['Wirtschaftsprüferexamen','exam',74,'finanzen','prüfung'],
        ['Bilanzbuchhalter Prüfung','exam',72,'finanzen','buchhaltung'],['Immobilienmakler Prüfung','exam',68,'immobilien','makler'],
        ['Versicherungsfachmann Prüfung','exam',64,'finanzen','versicherung'],
    ]),
]:
    c = append_csv(fname, rows)
    total += c
    print(f'  {fname}: +{c}')

# === AUDIENCES ++ ===
for fname, rows in [
    ('audiences/audiences_parenting_de.csv', [
        ['Eltern von Grundschulkindern','audience',86,'familie','schule'],['Eltern von Teenagern','audience',84,'familie','pubertät'],
        ['Werdende Mütter','audience',88,'familie','schwangerschaft'],['Werdende Väter','audience',84,'familie','schwangerschaft'],
        ['Eltern von ADHS-Kindern','audience',88,'familie','gesundheit'],['Eltern von hochbegabten Kindern','audience',74,'familie','bildung'],
    ]),
    ('audiences/audiences_hobby_de.csv', [
        ['Hobbygärtner','audience',80,'hobby','garten'],['Hobbyfotografen','audience',78,'hobby','fotografie'],
        ['Hobbyköche','audience',82,'hobby','kochen'],['Hobbybäcker','audience',80,'hobby','backen'],
        ['Heimwerker','audience',78,'hobby','handwerk'],['DIY-Fans','audience',76,'hobby','kreativ'],
    ]),
]:
    c = append_csv(fname, rows)
    total += c
    print(f'  {fname}: +{c}')

# === COMPAT ++ ===
c = append_compat('compatibility/topic_audience_compatibility.csv', [
    ('KI für Handwerker','Handwerker',95,'compatible','direkt'),('KI für Pflegekräfte','Pflegekräfte',95,'compatible','direkt'),
    ('KI für Lehrer','Lehrer',95,'compatible','direkt'),('KI für Immobilienmakler','Immobilienmakler',95,'compatible','direkt'),
    ('Pflegegrad Widerspruch','Angehörige',95,'compatible','Pflege'),('Medikamentenplan','Senioren',95,'compatible','Gesundheit'),
    ('Welpentraining','Ersthundbesitzer',95,'compatible','Hund'),('Hundetraining Rückruf','Hundehalter',92,'compatible','Hund'),
    ('Abitur Vorbereitung','Schüler',92,'compatible','Prüfung'),('Bachelorarbeit','Studenten',90,'compatible','Studium'),
    ('Masterarbeit','Studenten',88,'compatible','Studium'),('Angebotsvorlage','Selbstständige',90,'compatible','Business'),
    ('Rechnungsvorlage','Freelancer',90,'compatible','Business'),('Digitale Ordnung','Berufstätige',82,'compatible','Organisation'),
    ('Arzttermin Vorbereitung','Senioren',90,'compatible','Gesundheit'),('Pflegegrad Tagebuch','Angehörige',92,'compatible','Pflege'),
    ('SEO Grundlagen','Selbstständige',82,'compatible','Marketing'),('Social Media Planer','Selbstständige',86,'compatible','Marketing'),
    ('Bachelorarbeit','Studenten',90,'compatible','Studium'),('Krankenhaus Checkliste','Senioren',90,'compatible','Gesundheit'),
    ('Krankenhaus Checkliste','Angehörige',88,'compatible','Pflege'),('Reha Planer','Reha-Patienten',90,'compatible','Reha'),
    ('Digitale Steuererklärung','Selbstständige',88,'compatible','Steuer'),('Online Banking','Senioren',80,'compatible','Finanzen'),
    ('Passwort Manager','Berufstätige',78,'compatible','Sicherheit'),('Pflegeprotokoll Vorlage','Pflegekräfte',92,'compatible','Pflege'),
    ('Pflegeprotokoll Vorlage','Angehörige',88,'compatible','Pflege'),('Physiotherapie Übungsbuch','Reha-Patienten',86,'compatible','Reha'),
])
print(f'  compat: +{c}')

# === INCOMPAT ++ ===
i = append_incompat('compatibility/incompatible_combinations.csv', [
    ('Babyschlaf','Senioren','life_stage_mismatch','hard_block'),('Welpentraining','Senioren','domain_mismatch','hard_block'),
    ('Rente beantragen','Schüler','life_stage_mismatch','hard_block'),('Pflegegrad Antrag','Handwerker','domain_mismatch','hard_block'),
    ('Buchhaltung','Kinder','domain_mismatch','hard_block'),('KI für Handwerker','Pflegekräfte','domain_mismatch','hard_block'),
    ('Hundetraining','Selbstständige','domain_mismatch','hard_block'),('Abitur','Rentner','life_stage_mismatch','hard_block'),
    ('Bachelorarbeit','Rentner','life_stage_mismatch','hard_block'),('Masterarbeit','Rentner','life_stage_mismatch','hard_block'),
    ('Steuererklärung','Kinder','domain_mismatch','hard_block'),('SEO Grundlagen','Senioren','domain_mismatch','hard_block'),
    ('Krankenhaus Checkliste','Kinder','life_stage_mismatch','hard_block'),('Pflegeexamen','Rentner','life_stage_mismatch','hard_block'),
    ('Reha Planer','Kinder','life_stage_mismatch','hard_block'),
])
print(f'  incompat: +{i}')

# === RISK ++ ===
r = append_risk('compatibility/risk_rules.csv', [
    ('diagnose','high','health_sensitive','False'),('antidepressiva','high','health_sensitive','False'),
    ('insulin','high','health_sensitive','False'),('blutverdünner','high','health_sensitive','False'),
    ('testament','high','legal_sensitive','False'),('steuerbescheid','high','legal_sensitive','False'),
    ('ETF','high','financial_sensitive','False'),('krypto','high','financial_sensitive','False'),
    ('sucht','high','health_sensitive','False'),('selbstverletzung','blocked','unsafe_content','False'),
    ('therapieplan','high','health_sensitive','False'),('medikament','high','health_sensitive','False'),
    ('psychotherapie','high','health_sensitive','False'),('trauma','high','health_sensitive','False'),
    ('magersucht','high','health_sensitive','False'),('bulimie','high','health_sensitive','False'),
])
print(f'  risk: +{r}')
print(f'\nTOTAL NEW: {total} rows')
