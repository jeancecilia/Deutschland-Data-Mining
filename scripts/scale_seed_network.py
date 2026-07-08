"""Scale Discovery Seed Network to 5,000+ rows.
Usage: python scripts/scale_seed_network.py [--report]
"""
import csv, os, sys, glob as _glob
from pathlib import Path
from collections import Counter

BASE = Path(__file__).resolve().parents[1] / "data" / "discovery_seed_universes"
TARGET_ROWS = 5000
TARGET_COMPAT = 300
TARGET_INCOMPAT = 150
TARGET_RISK = 150

# ── helpers ──────────────────────────────────────────────────────────
def csv_path(subpath):
    return BASE / subpath

def ensure_dir(path):
    path.parent.mkdir(parents=True, exist_ok=True)

def count_rows(path):
    if not path.exists():
        return 0
    with open(path, encoding='utf-8-sig') as f:
        return sum(1 for _ in f) - 1

def append_csv(subpath, rows):
    path = csv_path(subpath)
    ensure_dir(path)
    exists = path.exists()
    existing_names = set()
    if exists:
        with open(path, encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                existing_names.add((row.get('name', '') or '').strip().casefold())
    new_count = 0
    with open(path, 'a', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(['name', 'entity_type', 'priority', 'domain', 'subdomain', 'language', 'country', 'notes'])
        for row in rows:
            name = (row[0] or '').strip()
            if name.casefold() in existing_names:
                continue
            existing_names.add(name.casefold())
            full = list(row)
            while len(full) < 8:
                full.append('')
            full[4] = full[4] or 'de'
            full[5] = full[5] or 'DE'
            w.writerow(full[:8])
            new_count += 1
    return new_count

def append_compat(subpath, rows):
    path = csv_path(subpath)
    ensure_dir(path)
    exists = path.exists()
    existing = set()
    if exists:
        with open(path, encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                existing.add(((row.get('topic','') or '').casefold(), (row.get('audience','') or '').casefold()))
    new_count = 0
    with open(path, 'a', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(['topic','audience','confidence','relation_type','notes'])
        for t, a, conf, rtype, notes in rows:
            if (t.casefold(), a.casefold()) in existing:
                continue
            existing.add((t.casefold(), a.casefold()))
            w.writerow([t, a, conf, rtype, notes])
            new_count += 1
    return new_count

def append_incompat(subpath, rows):
    path = csv_path(subpath)
    ensure_dir(path)
    exists = path.exists()
    existing = set()
    if exists:
        with open(path, encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                existing.add(((row.get('topic','') or '').casefold(), (row.get('audience','') or '').casefold()))
    new_count = 0
    with open(path, 'a', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(['topic','audience','reason','severity'])
        for t, a, reason, severity in rows:
            if (t.casefold(), a.casefold()) in existing:
                continue
            existing.add((t.casefold(), a.casefold()))
            w.writerow([t, a, reason, severity])
            new_count += 1
    return new_count

def append_risk(subpath, rows):
    path = csv_path(subpath)
    ensure_dir(path)
    exists = path.exists()
    existing = set()
    if exists:
        with open(path, encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                existing.add((row.get('keyword','') or '').casefold())
    new_count = 0
    with open(path, 'a', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(['keyword','risk_category','reason','auto_promote_allowed'])
        for kw, risk, reason, auto in rows:
            if kw.casefold() in existing:
                continue
            existing.add(kw.casefold())
            w.writerow([kw, risk, reason, auto])
            new_count += 1
    return new_count

# ── MAIN SCALING ─────────────────────────────────────────────────────
def main():
    report = '--report' in sys.argv
    total = 0
    compat_new = 0
    incompat_new = 0
    risk_new = 0

    if report:
        all_csvs = list(_glob.glob(str(BASE / "**/*.csv"), recursive=True))
        total_rows = sum(count_rows(Path(f)) for f in all_csvs)
        print(f"Seed files: {len(all_csvs)}")
        print(f"Total seed rows: {total_rows}")
        print(f"Compatibility pairs: {count_rows(csv_path('compatibility/topic_audience_compatibility.csv'))}")
        print(f"Incompatible pairs: {count_rows(csv_path('compatibility/incompatible_combinations.csv'))}")
        print(f"Risk rules: {count_rows(csv_path('compatibility/risk_rules.csv'))}")
        return

    # ── AUDIENCES ──
    total += append_csv('audiences/audiences_general_de.csv', [
        ['Berufseinsteiger','audience',80,'allgemein','arbeit','de','DE',''],
        ['Quereinsteiger','audience',74,'allgemein','arbeit','de','DE',''],
        ['Menschen mit wenig Zeit','audience',82,'allgemein','zeit','de','DE',''],
        ['Menschen mit ADHS','audience',88,'allgemein','gesundheit','de','DE',''],
        ['Menschen mit Schichtarbeit','audience',78,'allgemein','arbeit','de','DE',''],
        ['Nachtschichtarbeitende','audience',70,'allgemein','arbeit','de','DE',''],
        ['Frühaufsteher','audience',62,'allgemein','routine','de','DE',''],
        ['Vielreisende','audience',66,'allgemein','mobilität','de','DE',''],
        ['Weniger mobile Menschen','audience',72,'allgemein','gesundheit','de','DE',''],
    ])
    total += append_csv('audiences/audiences_family_de.csv', [
        ['Eltern von Kleinkindern','audience',88,'familie','elternschaft','de','DE',''],
        ['Eltern von Schulkindern','audience',86,'familie','elternschaft','de','DE',''],
        ['Eltern von Teenagern','audience',84,'familie','elternschaft','de','DE',''],
        ['Alleinerziehende Mütter','audience',88,'familie','elternschaft','de','DE',''],
        ['Alleinerziehende Väter','audience',86,'familie','elternschaft','de','DE',''],
        ['Großfamilien','audience',72,'familie','familienstruktur','de','DE',''],
        ['Pflegefamilien','audience',76,'familie','pflege','de','DE',''],
        ['Adoptiveltern','audience',70,'familie','elternschaft','de','DE',''],
        ['Regenbogenfamilien','audience',68,'familie','familienstruktur','de','DE',''],
    ])
    total += append_csv('audiences/audiences_business_de.csv', [
        ['Solo-Selbstständige','audience',88,'business','selbstständigkeit','de','DE',''],
        ['Handwerksbetriebe','audience',82,'business','handwerk','de','DE',''],
        ['Lokale Dienstleister','audience',78,'business','dienstleistung','de','DE',''],
        ['Online-Händler','audience',76,'business','ecommerce','de','DE',''],
        ['Kreative Selbstständige','audience',80,'business','kreativ','de','DE',''],
        ['Nebengewerbler','audience',78,'business','nebenjob','de','DE',''],
        ['Existenzgründer','audience',84,'business','gründung','de','DE',''],
        ['Jungunternehmer','audience',74,'business','gründung','de','DE',''],
    ])
    total += append_csv('audiences/audiences_pets_de.csv', [
        ['Hundehalter','audience',92,'haustiere','hunde','de','DE',''],
        ['Ersthundbesitzer','audience',88,'haustiere','hunde','de','DE',''],
        ['Katzenhalter','audience',86,'haustiere','katzen','de','DE',''],
        ['Tierliebhaber','audience',78,'haustiere','allgemein','de','DE',''],
        ['Aquarianer','audience',64,'haustiere','aquarium','de','DE',''],
    ])
    total += append_csv('audiences/audiences_health_de.csv', [
        ['Menschen mit Bluthochdruck','audience',84,'gesundheit','herz-kreislauf','de','DE',''],
        ['Menschen mit Diabetes','audience',84,'gesundheit','stoffwechsel','de','DE',''],
        ['Menschen mit chronischen Schmerzen','audience',82,'gesundheit','schmerz','de','DE',''],
        ['Menschen mit Schlafstörungen','audience',82,'gesundheit','schlaf','de','DE',''],
        ['Menschen mit Angststörungen','audience',80,'gesundheit','psyche','de','DE',''],
        ['Menschen mit Depression','audience',80,'gesundheit','psyche','de','DE',''],
        ['Menschen mit Demenz','audience',82,'gesundheit','neurologie','de','DE',''],
        ['Reha-Patienten','audience',76,'gesundheit','reha','de','DE',''],
    ])

    # ── PROFESSIONS ──
    total += append_csv('professions/professions_craft_de.csv', [
        ['Elektriker','profession',82,'handwerk','elektro','de','DE',''],
        ['Tischler','profession',78,'handwerk','holz','de','DE',''],
        ['Maler','profession',74,'handwerk','ausbau','de','DE',''],
        ['Dachdecker','profession',72,'handwerk','dach','de','DE',''],
        ['Installateur','profession',76,'handwerk','sanitär','de','DE',''],
        ['Fliesenleger','profession',70,'handwerk','ausbau','de','DE',''],
        ['Maurer','profession',70,'handwerk','bau','de','DE',''],
        ['Zimmerer','profession',72,'handwerk','holz','de','DE',''],
        ['Glaser','profession',66,'handwerk','glas','de','DE',''],
        ['Steinmetz','profession',62,'handwerk','stein','de','DE',''],
        ['Betonbauer','profession',64,'handwerk','bau','de','DE',''],
        ['Straßenbauer','profession',62,'handwerk','tiefbau','de','DE',''],
        ['Schornsteinfeger','profession',68,'handwerk','gebäude','de','DE',''],
        ['Gerüstbauer','profession',64,'handwerk','bau','de','DE',''],
        ['Schreiner','profession',76,'handwerk','holz','de','DE',''],
    ])
    total += append_csv('professions/professions_health_de.csv', [
        ['Pflegefachkraft','profession',96,'gesundheit','pflege','de','DE',''],
        ['Physiotherapeut','profession',84,'gesundheit','therapie','de','DE',''],
        ['Ergotherapeut','profession',80,'gesundheit','therapie','de','DE',''],
        ['Logopäde','profession',74,'gesundheit','sprache','de','DE',''],
        ['Podologe','profession',68,'gesundheit','fuß','de','DE',''],
        ['Hebamme','profession',88,'gesundheit','geburt','de','DE',''],
        ['Notfallsanitäter','profession',86,'gesundheit','notfall','de','DE',''],
        ['Rettungsassistent','profession',76,'gesundheit','notfall','de','DE',''],
        ['Zahntechniker','profession',66,'gesundheit','zahn','de','DE',''],
        ['Medizinische Fachangestellte','profession',74,'gesundheit','praxis','de','DE',''],
        ['Operationstechnischer Assistent','profession',72,'gesundheit','op','de','DE',''],
        ['Diätassistent','profession',66,'gesundheit','ernährung','de','DE',''],
    ])
    total += append_csv('professions/professions_it_de.csv', [
        ['Fachinformatiker','profession',92,'it','software','de','DE',''],
        ['Softwareentwickler','profession',90,'it','software','de','DE',''],
        ['Webdesigner','profession',74,'it','web','de','DE',''],
        ['Webentwickler','profession',76,'it','web','de','DE',''],
        ['Datenanalyst','profession',72,'it','daten','de','DE',''],
        ['Systemadministrator','profession',70,'it','infrastruktur','de','DE',''],
        ['Netzwerktechniker','profession',68,'it','netzwerk','de','DE',''],
        ['IT-Sicherheitsexperte','profession',74,'it','sicherheit','de','DE',''],
        ['UX-Designer','profession',66,'it','design','de','DE',''],
        ['Grafikdesigner','profession',68,'it','design','de','DE',''],
        ['Datenbankentwickler','profession',66,'it','daten','de','DE',''],
    ])
    total += append_csv('professions/professions_education_de.csv', [
        ['Nachhilfelehrer','profession',74,'bildung','nachhilfe','de','DE',''],
        ['Dozent','profession',72,'bildung','hochschule','de','DE',''],
        ['Trainer','profession',68,'bildung','weiterbildung','de','DE',''],
        ['Coach','profession',66,'beratung','coaching','de','DE',''],
        ['Erzieher','profession',84,'bildung','kita','de','DE',''],
        ['Sozialpädagoge','profession',78,'bildung','soziales','de','DE',''],
        ['Bildungsberater','profession',64,'bildung','beratung','de','DE',''],
    ])
    total += append_csv('professions/professions_service_de.csv', [
        ['Fahrlehrer','profession',68,'dienstleistung','transport','de','DE',''],
        ['Immobilienmakler','profession',72,'dienstleistung','immobilien','de','DE',''],
        ['Versicherungsmakler','profession',68,'dienstleistung','finanzen','de','DE',''],
        ['Personalberater','profession',66,'dienstleistung','personal','de','DE',''],
        ['Eventmanager','profession',62,'dienstleistung','events','de','DE',''],
        ['Hochzeitsplaner','profession',58,'dienstleistung','events','de','DE',''],
        ['Reinigungsfachkraft','profession',60,'dienstleistung','reinigung','de','DE',''],
        ['Sicherheitsdienst','profession',56,'dienstleistung','sicherheit','de','DE',''],
    ])
    total += append_csv('professions/professions_gastro_de.csv', [
        ['Koch','profession',76,'gastronomie','küche','de','DE',''],
        ['Gastronom','profession',68,'gastronomie','führung','de','DE',''],
        ['Kellner','profession',62,'gastronomie','service','de','DE',''],
        ['Barkeeper','profession',60,'gastronomie','bar','de','DE',''],
        ['Barista','profession',58,'gastronomie','kaffee','de','DE',''],
        ['Bäcker','profession',68,'handwerk','bäckerei','de','DE',''],
        ['Konditor','profession',66,'handwerk','konditorei','de','DE',''],
        ['Fleischer','profession',64,'handwerk','fleischerei','de','DE',''],
    ])
    total += append_csv('professions/professions_beauty_de.csv', [
        ['Friseur','profession',70,'dienstleistung','beauty','de','DE',''],
        ['Kosmetikerin','profession',66,'dienstleistung','beauty','de','DE',''],
        ['Visagistin','profession',58,'dienstleistung','beauty','de','DE',''],
        ['Nageldesignerin','profession',56,'dienstleistung','beauty','de','DE',''],
        ['Masseurin','profession',64,'dienstleistung','gesundheit','de','DE',''],
        ['Wellnessberater','profession',54,'dienstleistung','beauty','de','DE',''],
    ])
    total += append_csv('professions/professions_transport_de.csv', [
        ['LKW-Fahrer','profession',68,'transport','lkw','de','DE',''],
        ['Busfahrer','profession',64,'transport','personen','de','DE',''],
        ['Berufskraftfahrer','profession',68,'transport','gewerblich','de','DE',''],
        ['Taxifahrer','profession',56,'transport','personen','de','DE',''],
        ['Lokführer','profession',64,'transport','bahn','de','DE',''],
        ['Zugbegleiter','profession',54,'transport','bahn','de','DE',''],
        ['Pilot','profession',68,'transport','luft','de','DE',''],
        ['Flugbegleiter','profession',58,'transport','luft','de','DE',''],
        ['Kurierfahrer','profession',56,'transport','kep','de','DE',''],
        ['Postbote','profession',52,'transport','post','de','DE',''],
    ])

    # ── EXAMS ──
    total += append_csv('exams/exams_vocational_de.csv', [
        ['AEVO Prüfung','exam',85,'beruf','ausbildung','de','DE',''],
        ['IHK Abschlussprüfung','exam',94,'beruf','ihk','de','DE',''],
        ['Fachinformatiker Abschlussprüfung','exam',88,'it','fachinformatik','de','DE',''],
        ['Industriekaufmann Prüfung','exam',72,'beruf','kaufmännisch','de','DE',''],
        ['Bürokaufmann Prüfung','exam',74,'beruf','kaufmännisch','de','DE',''],
        ['Sachkundeprüfung 34a','exam',66,'lizenz','sicherheit','de','DE',''],
        ['Scrum Master Zertifizierung','exam',68,'it','agil','de','DE',''],
        ['Google Ads Zertifizierung','exam',62,'marketing','online','de','DE',''],
        ['Projektmanagement Zertifizierung','exam',72,'beruf','management','de','DE',''],
        ['Steuerfachangestelltenprüfung','exam',74,'finanzen','steuer','de','DE',''],
    ])

    # ── PROBLEMS ──
    total += append_csv('problems/problems_organization_de.csv', [
        ['Zeitmangel','problem',88,'organisation','zeit','de','DE',''],
        ['Unordnung','problem',84,'organisation','ordnung','de','DE',''],
        ['Überforderung','problem',89,'organisation','stress','de','DE',''],
        ['fehlende Struktur','problem',91,'organisation','struktur','de','DE',''],
        ['Prokrastination','problem',82,'organisation','aufschub','de','DE',''],
        ['Perfektionismus','problem',76,'organisation','psyche','de','DE',''],
        ['Digitale Ablenkung','problem',78,'organisation','digital','de','DE',''],
    ])
    total += append_csv('problems/problems_business_de.csv', [
        ['Kundenkommunikation verbessern','problem',78,'buero','kommunikation','de','DE',''],
        ['Angebote schreiben','problem',72,'buero','verkauf','de','DE',''],
        ['Rechnungen schreiben','problem',70,'buero','abrechnung','de','DE',''],
        ['Steuerunterlagen sortieren','problem',76,'buero','steuer','de','DE',''],
        ['Homeoffice Organisation','problem',74,'buero','organisation','de','DE',''],
        ['Kaltakquise','problem',68,'buero','verkauf','de','DE',''],
        ['Preiskalkulation','problem',72,'buero','finanzen','de','DE',''],
        ['E-Mail-Flut','problem',74,'buero','kommunikation','de','DE',''],
    ])
    total += append_csv('problems/problems_household_de.csv', [
        ['Haushaltsbudget planen','problem',78,'haushalt','finanzen','de','DE',''],
        ['Einkaufsplanung','problem',74,'haushalt','organisation','de','DE',''],
        ['Wäsche organisieren','problem',66,'haushalt','routine','de','DE',''],
        ['Keller aufräumen','problem',64,'haushalt','ordnung','de','DE',''],
        ['Dachboden ausmisten','problem',62,'haushalt','ordnung','de','DE',''],
        ['Umzug planen','problem',74,'haushalt','wohnen','de','DE',''],
    ])
    total += append_csv('problems/problems_seniors_de.csv', [
        ['Pflegeantrag verstehen','problem',88,'senioren','pflege','de','DE',''],
        ['Pflegegrad beantragen','problem',90,'senioren','pflege','de','DE',''],
        ['Behördenpost verstehen','problem',84,'senioren','verwaltung','de','DE',''],
        ['Hausnotruf einrichten','problem',76,'senioren','sicherheit','de','DE',''],
        ['Seniorenheim suchen','problem',78,'senioren','pflege','de','DE',''],
        ['Treppenlift planen','problem',68,'senioren','wohnen','de','DE',''],
    ])
    total += append_csv('problems/problems_pets_de.csv', [
        ['Hund zieht an der Leine','problem',88,'haustiere','hunde','de','DE',''],
        ['Hund bleibt nicht alleine','problem',86,'haustiere','hunde','de','DE',''],
        ['Welpe stubenrein bekommen','problem',84,'haustiere','hunde','de','DE',''],
        ['Katze frisst schlecht','problem',72,'haustiere','katzen','de','DE',''],
        ['Katze kratzt Möbel','problem',70,'haustiere','katzen','de','DE',''],
        ['Tierarztkosten planen','problem',68,'haustiere','finanzen','de','DE',''],
    ])

    # ── TOPICS ──
    total += append_csv('topics/topics_health_trackers_de.csv', [
        ['Blutdrucktagebuch','topic',93,'gesundheit','tracker','de','DE',''],
        ['Blutzuckertagebuch','topic',88,'gesundheit','tracker','de','DE',''],
        ['Schmerztagebuch','topic',80,'gesundheit','tracker','de','DE',''],
        ['Medikamentenplan','topic',86,'gesundheit','organisation','de','DE',''],
        ['Arztbesuch Notizbuch','topic',80,'gesundheit','organisation','de','DE',''],
        ['Schlaftagebuch','topic',82,'gesundheit','tracker','de','DE',''],
        ['Symptomtagebuch','topic',76,'gesundheit','tracker','de','DE',''],
        ['Stimmungstagebuch','topic',78,'gesundheit','tracker','de','DE',''],
        ['Ernährungstagebuch','topic',82,'gesundheit','tracker','de','DE',''],
        ['Fitness Tagebuch','topic',76,'sport','tracker','de','DE',''],
        ['ADHS Planer','topic',88,'gesundheit','planer','de','DE',''],
        ['Migräne Tagebuch','topic',78,'gesundheit','tracker','de','DE',''],
        ['Allergietagebuch','topic',72,'gesundheit','tracker','de','DE',''],
        ['Wechseljahrestagebuch','topic',70,'gesundheit','tracker','de','DE',''],
        ['Reha Tagebuch','topic',72,'gesundheit','tracker','de','DE',''],
    ])
    total += append_csv('topics/topics_business_de.csv', [
        ['Nebengewerbe starten','topic',88,'business','gründung','de','DE',''],
        ['Kleinunternehmen gründen','topic',84,'business','gründung','de','DE',''],
        ['Buchhaltung für Kleinunternehmer','topic',84,'business','buchhaltung','de','DE',''],
        ['Steuerunterlagen organisieren','topic',78,'business','steuer','de','DE',''],
        ['Kundengewinnung','topic',82,'business','marketing','de','DE',''],
        ['Social Media für Selbstständige','topic',78,'business','marketing','de','DE',''],
        ['Preiskalkulation','topic',74,'business','finanzen','de','DE',''],
        ['Angebote schreiben','topic',76,'business','verkauf','de','DE',''],
        ['Businessplan erstellen','topic',80,'business','strategie','de','DE',''],
    ])
    total += append_csv('topics/topics_ai_de.csv', [
        ['KI für Handwerker','topic',88,'ki','handwerk','de','DE',''],
        ['KI für Pflegekräfte','topic',80,'ki','pflege','de','DE',''],
        ['KI für Immobilienmakler','topic',78,'ki','immobilien','de','DE',''],
        ['KI für Coaches','topic',76,'ki','coaching','de','DE',''],
        ['KI für Lehrer','topic',82,'ki','bildung','de','DE',''],
        ['ChatGPT für Senioren','topic',80,'ki','senioren','de','DE',''],
        ['ChatGPT für Selbstständige','topic',84,'ki','business','de','DE',''],
        ['ChatGPT für Studenten','topic',82,'ki','bildung','de','DE',''],
        ['KI für Friseure','topic',74,'ki','handwerk','de','DE',''],
        ['KI für Gastronomen','topic',72,'ki','gastronomie','de','DE',''],
        ['KI für Architekten','topic',74,'ki','bau','de','DE',''],
        ['KI für Steuerberater','topic',76,'ki','finanzen','de','DE',''],
        ['KI für Anwälte','topic',72,'ki','recht','de','DE',''],
        ['KI für Ärzte','topic',74,'ki','medizin','de','DE',''],
    ])
    total += append_csv('topics/topics_household_de.csv', [
        ['Haushaltsbuch','topic',84,'haushalt','planer','de','DE',''],
        ['Putzplan','topic',78,'haushalt','planer','de','DE',''],
        ['Essensplan','topic',82,'haushalt','planer','de','DE',''],
        ['Familienkalender','topic',76,'haushalt','planer','de','DE',''],
        ['Notfallordner','topic',82,'haushalt','organisation','de','DE',''],
        ['Dokumentenmappe','topic',80,'haushalt','organisation','de','DE',''],
        ['Behördenpost organisieren','topic',84,'haushalt','organisation','de','DE',''],
        ['Passwörter organisieren','topic',72,'haushalt','digital','de','DE',''],
        ['Minimalismus zu Hause','topic',76,'haushalt','lifestyle','de','DE',''],
    ])
    total += append_csv('topics/topics_seniors_de.csv', [
        ['Pflegegrad Antrag','topic',90,'senioren','pflege','de','DE',''],
        ['Patientenverfügung','topic',84,'senioren','recht','de','DE',''],
        ['Vorsorgevollmacht','topic',82,'senioren','recht','de','DE',''],
        ['Testament verfassen','topic',80,'senioren','recht','de','DE',''],
        ['Altersvorsorge','topic',80,'senioren','finanzen','de','DE',''],
        ['Rente beantragen','topic',82,'senioren','verwaltung','de','DE',''],
        ['Seniorenheim finden','topic',78,'senioren','pflege','de','DE',''],
        ['Sturzprävention','topic',80,'senioren','gesundheit','de','DE',''],
        ['Seniorengymnastik','topic',76,'senioren','sport','de','DE',''],
        ['Treppenlift','topic',68,'senioren','wohnen','de','DE',''],
        ['Hausnotruf','topic',74,'senioren','sicherheit','de','DE',''],
        ['Pflegetagebuch','topic',80,'senioren','tracker','de','DE',''],
    ])
    total += append_csv('topics/topics_pets_de.csv', [
        ['Hundetraining Tagebuch','topic',78,'haustiere','tracker','de','DE',''],
        ['Welpen Tagebuch','topic',80,'haustiere','tracker','de','DE',''],
        ['Hundeführerschein','topic',72,'haustiere','prüfung','de','DE',''],
        ['Hundepflege','topic',68,'haustiere','pflege','de','DE',''],
        ['Hundeernährung','topic',74,'haustiere','ernährung','de','DE',''],
        ['Katzen Gesundheitstagebuch','topic',72,'haustiere','tracker','de','DE',''],
        ['Katzenpflege','topic',66,'haustiere','pflege','de','DE',''],
    ])
    total += append_csv('topics/topics_hobbies_de.csv', [
        ['Balkongarten','topic',82,'hobby','garten','de','DE',''],
        ['Hochbeet','topic',76,'hobby','garten','de','DE',''],
        ['Kräutergarten','topic',78,'hobby','garten','de','DE',''],
        ['Meal Prep','topic',78,'hobby','kochen','de','DE',''],
        ['Fermentieren','topic',64,'hobby','kochen','de','DE',''],
        ['Fotografie für Anfänger','topic',76,'hobby','fotografie','de','DE',''],
        ['Aquarell malen','topic',68,'hobby','kunst','de','DE',''],
        ['Zeichnen lernen','topic',72,'hobby','kunst','de','DE',''],
        ['Stricken lernen','topic',66,'hobby','handarbeit','de','DE',''],
        ['Nähen lernen','topic',72,'hobby','handarbeit','de','DE',''],
        ['Häkeln lernen','topic',64,'hobby','handarbeit','de','DE',''],
        ['Brot backen','topic',80,'hobby','backen','de','DE',''],
        ['Wandern','topic',82,'hobby','outdoor','de','DE',''],
        ['Camping','topic',78,'hobby','outdoor','de','DE',''],
        ['Angeln','topic',74,'hobby','outdoor','de','DE',''],
    ])
    total += append_csv('topics/topics_learning_de.csv', [
        ['Lernplaner','topic',80,'lernen','planer','de','DE',''],
        ['Prüfungsvorbereitung','topic',86,'lernen','prüfung','de','DE',''],
        ['Vokabeltrainer','topic',72,'lernen','sprache','de','DE',''],
        ['Mathe Übungsbuch','topic',68,'lernen','mathe','de','DE',''],
        ['Sprachen lernen','topic',80,'lernen','sprache','de','DE',''],
        ['Lerntechniken','topic',78,'lernen','methodik','de','DE',''],
        ['Gedächtnistraining','topic',78,'lernen','gehirn','de','DE',''],
        ['Mind Mapping','topic',70,'lernen','methodik','de','DE',''],
        ['Klassenarbeit Vorbereitung','topic',74,'lernen','prüfung','de','DE',''],
    ])
    total += append_csv('topics/topics_home_garden_de.csv', [
        ['Gemüsegarten','topic',80,'garten','gemüse','de','DE',''],
        ['Zimmerpflanzen','topic',74,'garten','indoor','de','DE',''],
        ['Gartenteich','topic',66,'garten','teich','de','DE',''],
        ['Rasenpflege','topic',64,'garten','rasen','de','DE',''],
        ['Kompostieren','topic',66,'garten','kompost','de','DE',''],
        ['Balkon begrünen','topic',72,'garten','balkon','de','DE',''],
        ['Gartenplanung','topic',70,'garten','planung','de','DE',''],
    ])
    total += append_csv('topics/topics_career_de.csv', [
        ['Bewerbung schreiben','topic',84,'karriere','bewerbung','de','DE',''],
        ['Vorstellungsgespräch','topic',82,'karriere','interview','de','DE',''],
        ['Gehaltsverhandlung','topic',80,'karriere','finanzen','de','DE',''],
        ['Karrierewechsel','topic',78,'karriere','umstieg','de','DE',''],
        ['LinkedIn Profil','topic',68,'karriere','netzwerk','de','DE',''],
        ['Weiterbildung planen','topic',74,'karriere','lernen','de','DE',''],
        ['Arbeitszeugnis verstehen','topic',66,'karriere','dokument','de','DE',''],
    ])

    # ── COMPATIBILITY ──
    compat_new += append_compat('compatibility/topic_audience_compatibility.csv', [
        ('KI für Handwerker','Handwerker',95,'compatible','direkte Zielgruppe'),
        ('KI für Pflegekräfte','Pflegekräfte',95,'compatible','direkte Zielgruppe'),
        ('KI für Immobilienmakler','Immobilienmakler',95,'compatible','direkte Zielgruppe'),
        ('KI für Coaches','Coach',90,'compatible','direkte Zielgruppe'),
        ('KI für Lehrer','Lehrer',92,'compatible','direkte Zielgruppe'),
        ('ChatGPT für Senioren','Senioren',92,'compatible','Technik für Ältere'),
        ('ChatGPT für Selbstständige','Selbstständige',92,'compatible','Business-Tool'),
        ('ChatGPT für Studenten','Studenten',90,'compatible','Lerntool'),
        ('ADHS Planer','Erwachsene mit ADHS',95,'compatible','direktes Hilfsmittel'),
        ('ADHS Planer','Eltern',88,'compatible','Eltern von ADHS-Kindern'),
        ('Blutdrucktagebuch','Senioren',95,'compatible','klassischer Tracker'),
        ('Blutdrucktagebuch','Menschen mit Bluthochdruck',95,'compatible','direkter Use Case'),
        ('Blutzuckertagebuch','Menschen mit Diabetes',95,'compatible','direkter Use Case'),
        ('Hundetraining Tagebuch','Hundehalter',95,'compatible','direkte Zielgruppe'),
        ('Welpen Tagebuch','Ersthundbesitzer',95,'compatible','direkter Use Case'),
        ('Buchhaltung','Kleinunternehmer',95,'compatible','Pflichtthema'),
        ('Buchhaltung','Selbstständige',95,'compatible','Pflichtthema'),
        ('Buchhaltung','Freelancer',92,'compatible','Pflichtthema'),
        ('Steuerunterlagen','Selbstständige',92,'compatible','starker Use Case'),
        ('Steuerunterlagen','Freelancer',90,'compatible','Steuerthema'),
        ('Pflegegrad Antrag','Angehörige',95,'compatible','Angehörige beantragen'),
        ('Pflegegrad Antrag','Senioren',92,'compatible','direkter Use Case'),
        ('Patientenverfügung','Senioren',95,'compatible','Vorsorge'),
        ('Patientenverfügung','Angehörige',88,'compatible','Vorsorge für Familie'),
        ('Vorsorgevollmacht','Senioren',92,'compatible','Vorsorge'),
        ('Testament','Senioren',88,'compatible','Nachlassplanung'),
        ('Balkongarten','Stadtbewohner',88,'compatible','Urban Gardening'),
        ('Balkongarten','Anfänger',86,'compatible','Einsteiger'),
        ('Meal Prep','Berufstätige',90,'compatible','Essensplanung'),
        ('Meal Prep','Schichtarbeiter',88,'compatible','Schichtarbeit Ernährung'),
        ('Nebengewerbe','Selbstständige',88,'compatible','Existenzgründung'),
        ('Nebengewerbe','Kleinunternehmer',86,'compatible','Business Start'),
        ('Wandern','Naturfreunde',86,'compatible','Outdoor'),
        ('Wandern','Senioren',84,'compatible','sanfte Bewegung'),
        ('Camping','Familien',88,'compatible','Familienurlaub'),
        ('Camping','Paare',84,'compatible','Paarurlaub'),
        ('Fotografie','Anfänger',88,'compatible','Einsteiger'),
        ('Fotografie','Reisende',78,'compatible','Reisefotografie'),
        ('Stricken','Anfänger',84,'compatible','Handarbeit lernen'),
        ('Nähen','Anfänger',86,'compatible','Handarbeit lernen'),
        ('Lernplaner','Studenten',92,'compatible','Lernhilfe'),
        ('Lernplaner','Schüler',88,'compatible','Lernhilfe'),
        ('Bewerbung','Berufstätige',88,'compatible','Karriere'),
        ('Bewerbung','Studenten',86,'compatible','Berufseinstieg'),
        ('Vorstellungsgespräch','Berufstätige',86,'compatible','Karriere'),
        ('Gehaltsverhandlung','Berufstätige',84,'compatible','Karriere'),
    ])

    # ── INCOMPATIBLE ──
    incompat_new += append_incompat('compatibility/incompatible_combinations.csv', [
        ('KI im Handwerk','Pflegekräfte','domain_mismatch','hard_block'),
        ('KI im Handwerk','Senioren','domain_mismatch','hard_block'),
        ('KI für Pflegekräfte','Handwerker','domain_mismatch','hard_block'),
        ('Pflegegrad','Kleinunternehmer','domain_mismatch','hard_block'),
        ('Pflegegrad','Schüler','life_stage_mismatch','hard_block'),
        ('Pflegeantrag','Studenten','life_stage_mismatch','hard_block'),
        ('Babyschlaf','Senioren','life_stage_mismatch','hard_block'),
        ('Welpentraining','Senioren','domain_mismatch','soft_block'),
        ('Buchhaltung','Kinder','domain_mismatch','hard_block'),
        ('Buchhaltung','Schüler','domain_mismatch','hard_block'),
        ('Rente beantragen','Schüler','life_stage_mismatch','hard_block'),
        ('Rente beantragen','Studenten','life_stage_mismatch','hard_block'),
        ('Patientenverfügung','Kinder','life_stage_mismatch','hard_block'),
        ('Patientenverfügung','Schüler','life_stage_mismatch','hard_block'),
        ('Testament','Kinder','life_stage_mismatch','hard_block'),
        ('Testament','Studenten','life_stage_mismatch','hard_block'),
        ('Altersvorsorge','Kinder','life_stage_mismatch','hard_block'),
        ('Altersvorsorge','Schüler','life_stage_mismatch','hard_block'),
        ('Gehaltsverhandlung','Rentner','life_stage_mismatch','hard_block'),
        ('Vorstellungsgespräch','Rentner','life_stage_mismatch','hard_block'),
        ('Existenzgründung','Rentner','life_stage_mismatch','hard_block'),
        ('Existenzgründung','Schüler','life_stage_mismatch','hard_block'),
        ('Hundetraining','Kleinunternehmer','domain_mismatch','hard_block'),
        ('Hundetraining','Senioren','domain_mismatch','hard_block'),
        ('Welpen Tagebuch','Kleinunternehmer','domain_mismatch','hard_block'),
    ])

    # ── RISK RULES ──
    risk_new += append_risk('compatibility/risk_rules.csv', [
        ('dosierung','restricted','dosage_content','False'),
        ('zyklus','restricted','dosage_content','False'),
        ('cycle','restricted','dosage_content','False'),
        ('steroide','high','substance_related','False'),
        ('anabol','high','substance_related','False'),
        ('blutdruck','high','health_sensitive','False'),
        ('blutzucker','high','health_sensitive','False'),
        ('diabetes','high','health_sensitive','False'),
        ('adhs','high','health_sensitive','False'),
        ('depression','high','health_sensitive','False'),
        ('angststörung','high','health_sensitive','False'),
        ('demenz','high','health_sensitive','False'),
        ('alzheimer','high','health_sensitive','False'),
        ('medikament','high','health_sensitive','False'),
        ('diagnose','high','health_sensitive','False'),
        ('therapie','high','health_sensitive','False'),
        ('behandlung','high','health_sensitive','False'),
        ('steuer','high','legal_sensitive','False'),
        ('recht','high','legal_sensitive','False'),
        ('investment','high','financial_sensitive','False'),
        ('aktien','high','financial_sensitive','False'),
        ('krypto','high','financial_sensitive','False'),
        ('rendite','high','financial_sensitive','False'),
        ('patientenverfügung','high','legal_sensitive','False'),
        ('vorsorgevollmacht','high','legal_sensitive','False'),
        ('testament','high','legal_sensitive','False'),
        ('erbrecht','high','legal_sensitive','False'),
        ('sorgerecht','high','legal_sensitive','False'),
        ('beschaffung','blocked','illegal_content','False'),
        ('darknet','blocked','illegal_content','False'),
    ])

    # ── REPORT ──
    all_csvs = list(_glob.glob(str(BASE / "**/*.csv"), recursive=True))
    total_rows = sum(count_rows(Path(f)) for f in all_csvs)
    print(f"Seed files: {len(all_csvs)}")
    print(f"Total seed rows: {total_rows}")
    print(f"New rows added: {total}")
    print(f"Compatibility pairs: {count_rows(csv_path('compatibility/topic_audience_compatibility.csv'))}")
    print(f"  New: {compat_new}")
    print(f"Incompatible pairs: {count_rows(csv_path('compatibility/incompatible_combinations.csv'))}")
    print(f"  New: {incompat_new}")
    print(f"Risk rules: {count_rows(csv_path('compatibility/risk_rules.csv'))}")
    print(f"  New: {risk_new}")

if __name__ == "__main__":
    main()
