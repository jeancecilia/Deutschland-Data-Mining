"""Generate v2 micro-domain catalog with concrete KDP-ready concepts."""
import csv, os
from collections import OrderedDict

# Concrete use-case pools per macro domain
USE_CASE_POOLS = {
    "gesundheit": [
        ("blutdrucktagebuch für senioren", "senioren", "blutdruckwerte dokumentieren", "tagebuch", "medium", 90),
        ("blutzuckertagebuch für diabetiker", "diabetiker", "werte regelmäßig dokumentieren", "tagebuch", "medium", 88),
        ("medikamentenplan für senioren", "senioren", "medikamente richtig einnehmen", "planer", "medium", 85),
        ("schmerztagebuch für chronische schmerzen", "erwachsene", "schmerzverlauf dokumentieren", "tagebuch", "medium", 82),
        ("migräne tagebuch für erwachsene", "erwachsene", "trigger identifizieren", "tagebuch", "low", 78),
        ("schlafprotokoll für schlafprobleme", "erwachsene", "schlafqualität verbessern", "tagebuch", "low", 76),
        ("arzttermin planer für patienten", "erwachsene", "termine und befunde organisieren", "planer", "low", 74),
        ("symptomtagebuch für arztbesuche", "erwachsene", "symptome vor arzttermin notieren", "tagebuch", "low", 72),
        ("notfallordner für gesundheit", "senioren", "wichtige dokumente griffbereit", "arbeitsbuch", "medium", 80),
        ("blutdruck messen anleitung für anfänger", "anfaenger", "richtig messen lernen", "ratgeber", "low", 70),
    ],
    "pflege": [
        ("pflegegrad antrag checkliste für angehörige", "pflegende_angehoerige", "antrag richtig stellen", "checkliste", "high", 92),
        ("md begutachtung vorbereitung für angehörige", "pflegende_angehoerige", "begutachtung vorbereiten", "checkliste", "high", 90),
        ("pflegeordner für angehörige", "pflegende_angehoerige", "unterlagen organisieren", "planer", "medium", 88),
        ("demenz alltag planer für familien", "familien", "alltag mit demenz strukturieren", "planer", "medium", 85),
        ("pflegekosten übersicht für senioren", "senioren", "kosten im blick behalten", "arbeitsbuch", "medium", 82),
        ("pflegekasse briefvorlagen für angehörige", "pflegende_angehoerige", "anträge korrekt formulieren", "vorlagenbuch", "medium", 80),
        ("verhinderungspflege planer für familien", "familien", "ersatzpflege organisieren", "planer", "low", 75),
        ("entlastungsbetrag checkliste für angehörige", "pflegende_angehoerige", "leistungen ausschöpfen", "checkliste", "low", 72),
        ("pflegeheim vergleich für familien", "familien", "richtiges heim finden", "checkliste", "medium", 78),
        ("hausnotruf checkliste für senioren", "senioren", "sicherheit zuhause erhöhen", "checkliste", "low", 70),
    ],
    "haustiere": [
        ("rückruftraining hund für ersthundbesitzer", "tierhalter", "hund kommt zuverlässig zurück", "trainingsjournal", "low", 85),
        ("leinenführigkeit training für hundehalter", "tierhalter", "entspannt an der leine gehen", "trainingsjournal", "low", 82),
        ("welpentraining plan für welpenbesitzer", "tierhalter", "welpen richtig sozialisieren", "planer", "low", 80),
        ("angsthund tagebuch für hundehalter", "tierhalter", "fortschritte dokumentieren", "tagebuch", "low", 75),
        ("futtertagebuch hund für tierhalter", "tierhalter", "unverträglichkeiten erkennen", "tagebuch", "low", 72),
        ("katzeneingewöhnung checkliste für katzenhalter", "tierhalter", "katze stressfrei eingewöhnen", "checkliste", "low", 78),
        ("tierarzt notizbuch für hundehalter", "tierhalter", "befunde und impfungen notieren", "notizbuch", "low", 70),
        ("hundebegegnungen trainingsjournal für hundehalter", "tierhalter", "begegnungen trainieren", "trainingsjournal", "low", 74),
        ("alleine bleiben training für hunde", "tierhalter", "trennungsangst überwinden", "trainingsjournal", "low", 76),
        ("katzenklo training für katzenhalter", "tierhalter", "unsauberkeit lösen", "ratgeber", "low", 68),
    ],
    "software": [
        ("excel arbeitsbuch für anfänger", "anfaenger", "grundfunktionen sicher beherrschen", "arbeitsbuch", "low", 88),
        ("excel haushaltsbuch für familien", "familien", "finanzen im griff behalten", "vorlagenbuch", "low", 82),
        ("notion planer für selbstständige", "selbststaendige", "projekte und aufgaben organisieren", "planer", "low", 80),
        ("canva vorlagen für kleinunternehmer", "kleinunternehmer", "social media grafiken erstellen", "vorlagenbuch", "low", 78),
        ("wordpress checkliste für anfänger", "anfaenger", "website selbst erstellen", "checkliste", "low", 76),
        ("google kalender organisation für berufstätige", "berufstaetige", "termine und deadlines managen", "planer", "low", 74),
        ("outlook inbox zero für büro", "berufstaetige", "e-mail flut bewältigen", "arbeitsbuch", "low", 72),
        ("chatgpt prompts für selbstständige", "selbststaendige", "ki für business nutzen", "arbeitsbuch", "medium", 84),
        ("shopify checkliste für online händler", "kleinunternehmer", "shop richtig einrichten", "checkliste", "low", 76),
        ("powerpoint vorlagen für berufseinsteiger", "berufseinsteiger", "professionelle präsentationen erstellen", "vorlagenbuch", "low", 72),
    ],
    "business": [
        ("buchhaltung arbeitsbuch für kleinunternehmer", "kleinunternehmer", "belege und rechnungen organisieren", "arbeitsbuch", "medium", 86),
        ("rechnung schreiben vorlage für selbstständige", "selbststaendige", "korrekte rechnungen erstellen", "vorlagenbuch", "low", 82),
        ("businessplan vorlage für gründer", "kleinunternehmer", "businessplan strukturiert erstellen", "vorlagenbuch", "medium", 84),
        ("steuererklärung checkliste für freelancer", "freelancer", "alle belege rechtzeitig sammeln", "checkliste", "medium", 80),
        ("kundengewinnung arbeitsbuch für selbstständige", "selbststaendige", "neue kunden systematisch gewinnen", "arbeitsbuch", "medium", 78),
        ("preiskalkulation arbeitsbuch für kleinunternehmer", "kleinunternehmer", "preise richtig kalkulieren", "arbeitsbuch", "low", 76),
        ("social media planer für kleinunternehmer", "kleinunternehmer", "posts und content planen", "planer", "low", 74),
        ("zeitmanagement arbeitsbuch für selbstständige", "selbststaendige", "effizienter arbeiten", "arbeitsbuch", "low", 72),
        ("angebotsvorlage für handwerker", "fachkraefte", "professionelle angebote schreiben", "vorlagenbuch", "low", 70),
        ("geschäftskonto checkliste für gründer", "kleinunternehmer", "richtiges konto wählen", "checkliste", "low", 68),
    ],
    "finanzen": [
        ("haushaltsbudget planer für familien", "familien", "monatliche ausgaben kontrollieren", "planer", "low", 84),
        ("haushaltsbuch für anfänger", "anfaenger", "einnahmen und ausgaben tracken", "arbeitsbuch", "low", 80),
        ("schuldenfrei planer für erwachsene", "erwachsene", "schulden systematisch abbauen", "planer", "medium", 78),
        ("altersvorsorge ratgeber für berufseinsteiger", "berufseinsteiger", "frühzeitig vorsorgen", "ratgeber", "medium", 76),
        ("etf sparplan für anfänger", "anfaenger", "mit etfs vermögen aufbauen", "ratgeber", "medium", 82),
        ("steuererklärung checkliste für arbeitnehmer", "berufstaetige", "nichts vergessen bei der steuer", "checkliste", "low", 78),
        ("geld sparen challenge für familien", "familien", "sparpotentiale im alltag finden", "planer", "low", 72),
        ("kontoauszug verstehen für jugendliche", "jugendliche", "erste eigene finanzen verstehen", "arbeitsbuch", "low", 68),
        ("nebenkostenabrechnung prüfen für mieter", "erwachsene", "nebenkosten richtig kontrollieren", "checkliste", "low", 70),
        ("gehaltsverhandlung vorbereitung für berufstätige", "berufstaetige", "mehr gehalt durchsetzen", "arbeitsbuch", "low", 74),
    ],
    "schule": [
        ("schulstart checkliste für eltern", "eltern", "nichts vergessen zum schulbeginn", "checkliste", "low", 82),
        ("hausaufgabenplaner für grundschüler", "eltern", "hausaufgaben strukturiert erledigen", "planer", "low", 78),
        ("mathe lernplan für realschüler", "schueler", "mathe systematisch üben", "lernplaner", "low", 76),
        ("vokabeltrainer für gymnasium", "schueler", "vokabeln effizient lernen", "arbeitsbuch", "low", 74),
        ("zeugnis verbessern planer für schüler", "schueler", "noten gezielt verbessern", "planer", "low", 72),
        ("referat vorbereitung checkliste für schüler", "schueler", "perfektes referat halten", "checkliste", "low", 70),
        ("lehrerplaner für referendare", "fachkraefte", "unterricht und stunden planen", "planer", "low", 68),
        ("einschulung tagebuch für eltern", "eltern", "ersten schultag dokumentieren", "tagebuch", "low", 66),
        ("schulwechsel checkliste für eltern", "eltern", "schulwechsel organisieren", "checkliste", "low", 64),
        ("klassenarbeit vorbereitung für schüler", "schueler", "gezielt für arbeiten lernen", "arbeitsbuch", "low", 72),
    ],
    "karriere": [
        ("lebenslauf vorlage für berufseinsteiger", "berufseinsteiger", "perfekten lebenslauf erstellen", "vorlagenbuch", "low", 84),
        ("vorstellungsgespräch vorbereitung für berufseinsteiger", "berufseinsteiger", "sicher im gespräch überzeugen", "workbook", "low", 82),
        ("bewerbungsschreiben vorlagen für fachkräfte", "fachkraefte", "anschreiben die überzeugen", "vorlagenbuch", "low", 80),
        ("gehaltsverhandlung training für berufstätige", "berufstaetige", "selbstbewusst verhandeln", "arbeitsbuch", "low", 78),
        ("linkedin profil optimierung für berufstätige", "berufstaetige", "online sichtbar werden", "arbeitsbuch", "low", 76),
        ("jobwechsel planer für berufstätige", "berufstaetige", "beruflichen wechsel planen", "planer", "low", 74),
        ("homeoffice einrichtung checkliste für berufstätige", "berufstaetige", "produktives homeoffice gestalten", "checkliste", "low", 72),
        ("netzwerken lernen für berufseinsteiger", "berufseinsteiger", "kontakte strategisch aufbauen", "arbeitsbuch", "low", 70),
        ("arbeitszeugnis prüfen für arbeitnehmer", "berufstaetige", "zeugnis korrekt bewerten", "checkliste", "low", 68),
        ("seitenwechsel in die selbstständigkeit", "selbststaendige", "schritt für schritt selbstständig", "ratgeber", "medium", 76),
    ],
    "senioren": [
        ("smartphone ratgeber für senioren", "senioren", "grundfunktionen sicher verstehen", "ratgeber", "low", 86),
        ("tablet einrichtung für senioren", "senioren", "erste schritte mit dem tablet", "ratgeber", "low", 82),
        ("online banking für senioren", "senioren", "sicher online überweisungen tätigen", "ratgeber", "medium", 80),
        ("videotelefonie lernen für senioren", "senioren", "mit enkeln in kontakt bleiben", "ratgeber", "low", 76),
        ("fitness zuhause für senioren", "senioren", "beweglich bleiben im alter", "arbeitsbuch", "low", 74),
        ("ernährungsplan für senioren", "senioren", "gesund essen im alter", "planer", "low", 72),
        ("gedächtnistraining für senioren", "senioren", "geistig fit bleiben", "arbeitsbuch", "low", 70),
        ("seniorengerechtes wohnen checkliste", "senioren", "wohnung altersgerecht umbauen", "checkliste", "low", 68),
        ("rentenantrag checkliste für rentner", "rentner", "rente richtig beantragen", "checkliste", "medium", 78),
        ("vollmacht und patientenverfügung für senioren", "senioren", "für den ernstfall vorsorgen", "ratgeber", "high", 84),
    ],
    "kochen": [
        ("meal prep planer für berufstätige", "berufstaetige", "essen für die woche vorkochen", "planer", "low", 80),
        ("schnelle gerichte kochbuch für familien", "familien", "in 30 minuten auf dem tisch", "kochbuch", "low", 78),
        ("backen für anfänger", "anfaenger", "grundrezepte einfach erklärt", "kochbuch", "low", 76),
        ("zuckerfrei kochbuch für einsteiger", "einsteiger", "zucker im alltag reduzieren", "kochbuch", "low", 74),
        ("vegetarisch kochen für familien", "familien", "fleischlos und lecker", "kochbuch", "low", 72),
        ("einkaufsplaner für wochenmärkte", "familien", "saisonal und regional einkaufen", "planer", "low", 66),
        ("vorratshaltung checkliste für haushalte", "erwachsene", "vorräte richtig lagern", "checkliste", "low", 64),
        ("kräuter anbauen für die küche", "anfaenger", "frische kräuter selbst ziehen", "ratgeber", "low", 62),
        ("grillrezepte für anfänger", "anfaenger", "perfekt grillen lernen", "kochbuch", "low", 70),
        ("brotdosen ideen für kinder", "eltern", "gesunde pausenbrote kreativ gestalten", "kochbuch", "low", 68),
    ],
    "adhs": [
        ("adhs alltag strukturieren für erwachsene", "erwachsene", "routinen und ordnung schaffen", "arbeitsbuch", "medium", 84),
        ("adhs ernährung kochbuch", "erwachsene", "ernährung bei adhs optimieren", "kochbuch", "low", 76),
        ("adhs studium planer für studenten", "studenten", "mit adhs erfolgreich studieren", "planer", "medium", 80),
        ("adhs haushalt organisieren für erwachsene", "erwachsene", "haushalt trotz adhs im griff", "arbeitsbuch", "low", 74),
        ("adhs berufsalltag für berufstätige", "berufstaetige", "produktiv trotz adhs", "arbeitsbuch", "medium", 78),
        ("adhs kind unterstützen für eltern", "eltern", "kind mit adhs besser verstehen", "ratgeber", "medium", 82),
        ("adhs medikamenten tagebuch", "erwachsene", "wirkung dokumentieren", "tagebuch", "medium", 72),
        ("adhs schlaf verbessern für erwachsene", "erwachsene", "besser schlafen mit adhs", "arbeitsbuch", "low", 70),
        ("adhs beziehungen pflegen für erwachsene", "erwachsene", "beziehungen trotz adhs stärken", "ratgeber", "low", 68),
        ("adhs zeitblindheit überwinden", "erwachsene", "zeitgefühl verbessern", "arbeitsbuch", "low", 72),
    ],
    "fitness_sport": [
        ("fitness tagebuch für anfänger", "anfaenger", "fortschritte dokumentieren", "tagebuch", "low", 78),
        ("yoga für anfänger arbeitsbuch", "anfaenger", "grundhaltungen sicher lernen", "arbeitsbuch", "low", 76),
        ("laufplan für anfänger", "anfaenger", "von 0 auf 5 kilometer", "trainingsjournal", "low", 74),
        ("krafttraining plan für einsteiger", "einsteiger", "muskelaufbau systematisch", "trainingsjournal", "low", 72),
        ("dehnübungen für büroberufe", "berufstaetige", "rückenschmerzen vorbeugen", "arbeitsbuch", "low", 70),
        ("ernährungstagebuch für sportler", "erwachsene", "makros und kalorien tracken", "tagebuch", "low", 68),
        ("heimtraining ohne geräte für anfänger", "anfaenger", "fitness zuhause aufbauen", "arbeitsbuch", "low", 66),
        ("marathon trainingsplan für fortgeschrittene", "fortgeschrittene", "auf den marathon vorbereiten", "trainingsjournal", "low", 64),
        ("schwimmtechnik verbessern für anfänger", "anfaenger", "effizienter schwimmen lernen", "arbeitsbuch", "low", 62),
        ("rückenschule arbeitsbuch für büro", "berufstaetige", "rücken gesund halten", "arbeitsbuch", "low", 68),
    ],
    "reise_umzug": [
        ("umzugscheckliste für familien", "familien", "umzug ohne chaos planen", "checkliste", "low", 82),
        ("umzugsfirmen vergleich checkliste", "erwachsene", "beste umzugsfirma finden", "checkliste", "low", 76),
        ("karton beschriftung system für umzüge", "erwachsene", "kartons richtig beschriften", "arbeitsbuch", "low", 70),
        ("wohnungsübergabe protokoll für mieter", "erwachsene", "mängel korrekt dokumentieren", "checkliste", "low", 72),
        ("nachsendeauftrag checkliste für umziehende", "erwachsene", "nichts vergessen nach dem umzug", "checkliste", "low", 68),
        ("urlaubsplaner für familien", "familien", "reise organisieren und planen", "planer", "low", 74),
        ("packliste urlaub für familien", "familien", "nichts vergessen beim packen", "checkliste", "low", 66),
        ("wohnmobil reise tagebuch", "erwachsene", "vanlife erlebnisse dokumentieren", "tagebuch", "low", 64),
        ("auslandsumzug checkliste für expats", "erwachsene", "ins ausland umziehen", "checkliste", "medium", 72),
        ("möbel abbau anleitung für umzüge", "erwachsene", "möbel richtig zerlegen", "ratgeber", "low", 60),
    ],
    "garten": [
        ("gemüsegarten planer für anfänger", "anfaenger", "eigenes gemüse anbauen", "planer", "low", 78),
        ("hochbeet bauanleitung für einsteiger", "einsteiger", "hochbeet selbst bauen", "ratgeber", "low", 74),
        ("rasenpflege kalender für hausbesitzer", "erwachsene", "perfekter rasen das ganze jahr", "planer", "low", 70),
        ("balkongarten für anfänger", "anfaenger", "auf kleinem raum gärtnern", "ratgeber", "low", 72),
        ("kompost anlegen für einsteiger", "einsteiger", "eigenen kompost herstellen", "ratgeber", "low", 66),
        ("pflanzplan für schnittblumen", "erwachsene", "blumen für die vase anbauen", "planer", "low", 64),
        ("schädlingsbekämpfung natürlich", "erwachsene", "ohne chemie gegen schädlinge", "ratgeber", "low", 68),
        ("gartengeräte pflege checkliste", "erwachsene", "werkzeuge richtig warten", "checkliste", "low", 62),
        ("kräuterspirale bauen anleitung", "erwachsene", "kräuterspirale selbst bauen", "ratgeber", "low", 60),
        ("gartenbewässerung planen für trockene sommer", "erwachsene", "bewässerungssystem planen", "planer", "low", 66),
    ],
    "steuern": [
        ("steuererklärung checkliste für arbeitnehmer", "berufstaetige", "alle belege für die steuer", "checkliste", "low", 82),
        ("umsatzsteuer voranmeldung für selbstständige", "selbststaendige", "ustva richtig abgeben", "arbeitsbuch", "medium", 78),
        ("steuerklassen wechsel checkliste für ehepaare", "familien", "beste steuerklasse wählen", "checkliste", "low", 74),
        ("freibeträge checkliste für arbeitnehmer", "berufstaetige", "alle freibeträge nutzen", "checkliste", "low", 72),
        ("elster einrichtung für anfänger", "anfaenger", "elster online nutzen", "ratgeber", "low", 70),
        ("fahrtenbuch vorlage für selbstständige", "selbststaendige", "dienstfahrten korrekt dokumentieren", "vorlagenbuch", "low", 68),
        ("arbeitszimmer absetzen für homeoffice", "berufstaetige", "homeoffice steuerlich geltend machen", "checkliste", "low", 76),
        ("spendenquittung organiser für spenden", "erwachsene", "spenden steuerlich absetzen", "planer", "low", 64),
        ("kindergeld checkliste für eltern", "eltern", "kindergeld richtig beantragen", "checkliste", "low", 70),
        ("steuerberater wechsel checkliste", "selbststaendige", "den richtigen steuerberater finden", "checkliste", "low", 66),
    ],
    "ecommerce": [
        ("amazon fba einstieg für anfänger", "anfaenger", "produkte über amazon verkaufen", "ratgeber", "medium", 80),
        ("ebay kleinanzeigen verkaufstipps", "erwachsene", "erfolgreich auf ebay verkaufen", "ratgeber", "low", 72),
        ("etsy shop eröffnen für kreative", "kleinunternehmer", "handmade produkte verkaufen", "checkliste", "low", 76),
        ("dropshipping einstieg für anfänger", "anfaenger", "ohne lager verkaufen", "ratgeber", "medium", 74),
        ("produktfotografie für online shops", "kleinunternehmer", "produkte richtig fotografieren", "ratgeber", "low", 70),
        ("verpackung und versand optimieren", "kleinunternehmer", "versandkosten senken", "checkliste", "low", 66),
        ("retouren management für online händler", "kleinunternehmer", "retouren effizient bearbeiten", "arbeitsbuch", "low", 64),
        ("shopify themes auswahl guide", "kleinunternehmer", "perfektes design wählen", "ratgeber", "low", 68),
        ("google shopping feed optimierung", "kleinunternehmer", "produkte bei google listen", "arbeitsbuch", "low", 72),
        ("kundenbewertungen sammeln strategie", "kleinunternehmer", "mehr positive bewertungen", "arbeitsbuch", "low", 70),
    ],
    "smart_home": [
        ("alexa einrichtung für senioren", "senioren", "sprachassistent einfach nutzen", "ratgeber", "low", 78),
        ("smart home einstieg für anfänger", "anfaenger", "erste smart home geräte", "ratgeber", "low", 74),
        ("smarte heizungssteuerung einrichten", "erwachsene", "heizkosten sparen", "ratgeber", "low", 72),
        ("wlan optimierung für zuhause", "erwachsene", "besseres internet in jedem raum", "ratgeber", "low", 70),
        ("sicherheitskameras einrichten für hausbesitzer", "erwachsene", "haus smarter überwachen", "ratgeber", "low", 68),
        ("philips hue licht einrichtung", "erwachsene", "smarte beleuchtung planen", "ratgeber", "low", 66),
        ("saugroboter vergleich und einrichtung", "erwachsene", "richtigen saugroboter wählen", "ratgeber", "low", 64),
        ("smart home mit home assistant", "fortgeschrittene", "eigene smart home zentrale", "arbeitsbuch", "medium", 72),
        ("stromverbrauch messen mit smart steckdosen", "erwachsene", "stromfresser identifizieren", "ratgeber", "low", 70),
        ("gartengeräte smart steuern", "erwachsene", "bewässerung automatisieren", "ratgeber", "low", 66),
    ],
    "demenz": [
        ("demenz alltag planer für angehörige", "pflegende_angehoerige", "alltag mit demenz strukturieren", "planer", "medium", 84),
        ("demenz beschäftigung ideen für senioren", "pflegende_angehoerige", "sinnvolle beschäftigung finden", "arbeitsbuch", "low", 76),
        ("demenz ernährung ratgeber für angehörige", "pflegende_angehoerige", "richtig ernähren bei demenz", "ratgeber", "low", 72),
        ("demenz tagesablauf planer", "pflegende_angehoerige", "geregelten tagesablauf schaffen", "planer", "low", 70),
        ("erinnerungsalbum für demenzkranke", "pflegende_angehoerige", "erinnerungen wachhalten", "arbeitsbuch", "low", 68),
        ("demenz wohngestaltung checkliste", "pflegende_angehoerige", "wohnung demenzgerecht einrichten", "checkliste", "low", 74),
        ("kommunikation mit demenzkranken", "pflegende_angehoerige", "besser kommunizieren lernen", "ratgeber", "low", 70),
        ("pflegetagebuch für demenz", "pflegende_angehoerige", "verlauf und maßnahmen dokumentieren", "tagebuch", "medium", 72),
        ("demenz und rechtliche vorsorge", "pflegende_angehoerige", "vollmachten und verfügungen", "ratgeber", "high", 80),
        ("selbstfürsorge für pflegende angehörige", "pflegende_angehoerige", "auf sich selbst achten", "arbeitsbuch", "medium", 76),
    ],
    "lernen": [
        ("vokabeltrainer englisch für anfänger", "anfaenger", "englisch vokabeln effizient lernen", "arbeitsbuch", "low", 76),
        ("lernplaner für abiturienten", "schueler", "abi-vorbereitung strukturieren", "lernplaner", "low", 74),
        ("speed reading training für studenten", "studenten", "schneller lesen und verstehen", "arbeitsbuch", "low", 70),
        ("gedächtnistechniken für berufstätige", "berufstaetige", "sich mehr merken können", "arbeitsbuch", "low", 68),
        ("sprachlernplan für auswanderer", "erwachsene", "neue sprache systematisch lernen", "planer", "low", 72),
        ("notiztechnik für meetings", "berufstaetige", "bessere notizen im beruf", "arbeitsbuch", "low", 64),
        ("prüfungsangst überwinden für studenten", "studenten", "ruhig in die prüfung gehen", "arbeitsbuch", "low", 70),
        ("mnemotechniken für schüler", "schueler", "mit eselsbrücken besser lernen", "arbeitsbuch", "low", 66),
        ("online kurs selbstdisziplin arbeitsbuch", "erwachsene", "online kurse erfolgreich abschließen", "arbeitsbuch", "low", 68),
        ("lerntyp test und strategien für erwachsene", "erwachsene", "eigenen lerntyp finden", "arbeitsbuch", "low", 64),
    ],
}


def generate_v2():
    os.makedirs("data/discovery_seed_universes/micro_domains", exist_ok=True)
    path = "data/discovery_seed_universes/micro_domains/micro_domain_catalog_10000_de_v2.csv"

    rows = []
    used_micros = set()
    row_idx = 0

    # First: concrete use-case pools (20 domains × 10 rows = 200)
    macro_count = 0
    for macro, concepts in USE_CASE_POOLS.items():
        sub_prefix = macro
        for si in range(10):
            subdomain = f"{sub_prefix}_sub_{si+1}"
            # Fill remaining slots with improved generic-but-concrete entries
            if si < len(concepts):
                micro, audience, problem, fmt, risk, priority = concepts[si]
            else:
                continue
            if micro in used_micros:
                continue
            used_micros.add(micro)
            rows.append({
                "macro_domain": macro, "subdomain": subdomain,
                "micro_domain": micro, "audience_hint": audience,
                "problem_hint": problem, "format_hint": fmt,
                "risk_level": risk, "priority": priority,
                "language": "de", "country": "DE",
                "notes": f"curated v2 #{len(rows)+1}",
            })
            row_idx += 1
        macro_count += 1

    curated_count = len(rows)
    print(f"Curated rows: {curated_count}")

    # Fill remaining to 10,000 with improved logic (concrete concepts from remaining macros)
    MACRO_DOMAINS = list(USE_CASE_POOLS.keys()) + [
        "admin_recht", "ausbildung", "baby_kleinkind", "chronische_erkrankung",
        "digitale_ordnung", "eltern_kind", "energie", "familiengeschichte",
        "fotografie_video", "haushalt", "hobby", "homeoffice",
        "immobilien", "lokales_business", "marketing", "medizin",
        "mental_wellbeing", "migration", "musik", "naehen_handarbeit",
        "nachhaltigkeit", "notfall_vorsorge", "office_verwaltung", "personal_hr",
        "produktivitaet", "programmieren_lernen", "projektmanagement", "recht",
        "renovierung", "schlaf_erholung", "sprachen", "stadtleben",
        "studium", "transport_logistik", "veranstaltungen", "vereine",
        "versicherung", "zeichnen", "zeitmanagement", "zielplanung",
        "aquaristik", "barrierefreiheit", "beauty", "camping_vanlife",
        "erbschaft", "excel_buchhaltung", "fahrzeuge", "freiwilligenarbeit",
        "fuehrung_team", "gastro", "gemeinde_lokal", "holzwerken_diy",
        "industrie_produktion", "it", "journaling", "kleintiere",
        "kundenservice", "laendliches_leben", "landwirtschaft", "maenner_gesundheit",
        "online_kurse", "outdoor", "pferde", "rente_vorsorge",
        "seo_content", "selbsthilfe", "tiergesundheit", "verbraucherrechte",
        "vogelhaltung", "angeln", "autismus", "bildung_soziales",
        "frauen_gesundheit", "fotobuch_erinnerungen", "haushalt_senioren", "familienorganisation",
        "mietrecht",
    ]

    # Better audiences, problems, formats for auto-gen
    BETTER_AUDIENCES = ["anfaenger", "einsteiger", "erwachsene", "familien", "berufstaetige",
                        "studenten", "senioren", "eltern", "kleinunternehmer", "jugendliche"]
    BETTER_PROBLEMS = ["schritt für schritt erklärt", "praktisch umsetzen",
                       "einfach und verständlich", "mit übungen und checklisten",
                       "für den alltag optimiert", "schnell und effektiv umsetzen",
                       "keine vorkenntnisse nötig", "mit vielen beispielen"]
    BETTER_FORMATS = ["arbeitsbuch", "ratgeber", "checkliste", "planer", "tagebuch",
                      "workbook", "leitfaden", "vorlagenbuch", "praxisbuch"]

    remaining = 10000 - len(rows)
    for i, macro in enumerate(MACRO_DOMAINS):
        if len(rows) >= 10000:
            break
        for si in range(10):
            if len(rows) >= 10000:
                break
            subdomain = f"{macro}_v2_sub_{si+1}"
            for ti in range(10):
                if len(rows) >= 10000:
                    break
                aud = BETTER_AUDIENCES[(i + si + ti) % len(BETTER_AUDIENCES)]
                prob = BETTER_PROBLEMS[(i + ti) % len(BETTER_PROBLEMS)]
                fmt = BETTER_FORMATS[(si + ti) % len(BETTER_FORMATS)]
                risk = "low"
                priority = max(40, min(85, 50 + (i % 15) + (si % 5) + (ti % 5)))

                # Make concrete micro_domain name
                macro_display = macro.replace("_", " ").title()
                micro = f"{macro_display} {fmt} für {aud.replace('_',' ').title()}"

                if micro in used_micros:
                    continue
                used_micros.add(micro)

                rows.append({
                    "macro_domain": macro, "subdomain": subdomain,
                    "micro_domain": micro, "audience_hint": aud,
                    "problem_hint": prob, "format_hint": fmt,
                    "risk_level": risk, "priority": priority,
                    "language": "de", "country": "DE",
                    "notes": f"auto v2 #{len(rows)+1}",
                })

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "macro_domain", "subdomain", "micro_domain", "audience_hint",
            "problem_hint", "format_hint", "risk_level", "priority",
            "language", "country", "notes",
        ])
        writer.writeheader()
        writer.writerows(rows)

    macros = len(set(r["macro_domain"] for r in rows))
    subs = len(set(r["subdomain"] for r in rows))
    micros = len(set(r["micro_domain"] for r in rows))
    print(f"Generated {len(rows)} rows ({curated_count} curated + {len(rows)-curated_count} auto)")
    print(f"  Macro domains: {macros}")
    print(f"  Subdomains: {subs}")
    print(f"  Micro-domains: {micros}")
    print(f"  Duplicates: {len(rows) - micros}")
    print(f"  File: {path}")


if __name__ == "__main__":
    generate_v2()
