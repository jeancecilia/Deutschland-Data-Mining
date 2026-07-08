"""Generate the 10,000-row micro-domain catalog CSV."""
import csv, os

MACRO_DOMAINS = [
    "pflege", "gesundheit", "business", "ki", "haushalt", "haustiere", "lernen",
    "hobby", "admin_recht", "karriere", "software", "finanzen", "eltern_kind",
    "senioren", "reise_umzug", "fitness_sport", "kreativ", "lokales_business",
    "ausbildung", "sprachen", "fahrzeuge", "immobilien", "steuern", "garten",
    "kochen", "recht", "medizin", "mental_wellbeing", "adhs", "demenz",
    "chronische_erkrankung", "frauen_gesundheit", "maenner_gesundheit", "rente_vorsorge",
    "erbschaft", "mietrecht", "verbraucherrechte", "handwerk", "it", "gastro",
    "beauty", "transport_logistik", "vereine", "veranstaltungen", "energie",
    "smart_home", "nachhaltigkeit", "outdoor", "musik", "zeichnen",
    "naehen_handarbeit", "holzwerken_diy", "renovierung", "barrierefreiheit",
    "autismus", "baby_kleinkind", "schule", "studium", "migration",
    "versicherung", "homeoffice", "produktivitaet", "digitale_ordnung",
    "notfall_vorsorge", "familiengeschichte", "camping_vanlife", "angeln",
    "aquaristik", "pferde", "vogelhaltung", "kleintiere", "fotografie_video",
    "marketing", "seo_content", "kundenservice", "projektmanagement", "personal_hr",
    "fuehrung_team", "ecommerce", "office_verwaltung", "landwirtschaft",
    "bildung_soziales", "industrie_produktion", "selbsthilfe", "journaling",
    "achtsamkeit", "schlaf_erholung", "zeitmanagement", "zielplanung",
    "stadtleben", "laendliches_leben", "programmieren_lernen", "excel_buchhaltung",
    "online_kurse", "freiwilligenarbeit", "gemeinde_lokal", "fotobuch_erinnerungen",
    "haushalt_senioren", "tiergesundheit", "familienorganisation",
]

# Subdomain generation per macro domain
SUBDOMAIN_SUFFIXES = [
    "_grundlagen", "_fortgeschritten", "_organisation", "_dokumentation",
    "_planung", "_optimierung", "_pflege", "_training", "_beratung", "_hilfe",
]

# Audience hints pool
AUDIENCES = [
    "anfaenger", "einsteiger", "fortgeschrittene", "senioren", "eltern",
    "alleinerziehende", "berufseinsteiger", "selbststaendige", "freelancer",
    "kleinunternehmer", "studenten", "schueler", "rentner", "pflegende_angehoerige",
    "fachkraefte", "fuehrungskraefte", "schichtarbeiter", "berufstaetige",
    "jugendliche", "erwachsene",
]

# Problem hints
PROBLEMS = [
    "zeit sparen und effizienter arbeiten", "ueberblick behalten und struktur schaffen",
    "fehler vermeiden und qualitaet sichern", "kosten senken und budget einhalten",
    "motivation finden und dranbleiben", "richtige methode erlernen",
    "alltag vereinfachen und routine aufbauen", "sicherer im umgang werden",
    "besser verstehen und anwenden", "ergebnisse verbessern und optimieren",
]

# Format hints
FORMATS = [
    "arbeitsbuch", "ratgeber", "checkliste", "planer", "tagebuch",
    "trainingsjournal", "workbook", "leitfaden", "praxisbuch", "vorlagenbuch",
]

RISK_LEVELS = ["low"] * 6 + ["medium"] * 3 + ["high"]


def generate_catalog():
    os.makedirs("data/discovery_seed_universes/micro_domains", exist_ok=True)
    path = "data/discovery_seed_universes/micro_domains/micro_domain_catalog_10000_de.csv"

    rows = []
    for mi, macro in enumerate(MACRO_DOMAINS[:100]):
        macro_display = macro.replace("_", " ").title()
        for si in range(10):
            subdomain = f"{macro}{SUBDOMAIN_SUFFIXES[si]}"
            subdomain_display = f"{macro_display} {['Grundlagen','Fortgeschritten','Organisation','Dokumentation','Planung','Optimierung','Pflege','Training','Beratung','Hilfe'][si]}"
            for ti in range(10):
                idx = mi * 100 + si * 10 + ti + 1
                audience = AUDIENCES[(mi + si + ti) % len(AUDIENCES)]
                problem = PROBLEMS[(mi + ti) % len(PROBLEMS)]
                fmt = FORMATS[(si + ti) % len(FORMATS)]
                risk = RISK_LEVELS[(mi + si) % len(RISK_LEVELS)]
                priority = max(40, min(99, 50 + (mi % 20) + (si % 5) + (ti % 5)))

                micro = f"{subdomain_display} für {audience.replace('_',' ').title()}"

                rows.append({
                    "macro_domain": macro,
                    "subdomain": subdomain,
                    "micro_domain": micro,
                    "audience_hint": audience,
                    "problem_hint": problem,
                    "format_hint": fmt,
                    "risk_level": risk,
                    "priority": priority,
                    "language": "de",
                    "country": "DE",
                    "notes": f"micro domain #{idx}",
                })

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "macro_domain", "subdomain", "micro_domain", "audience_hint",
            "problem_hint", "format_hint", "risk_level", "priority",
            "language", "country", "notes",
        ])
        writer.writeheader()
        writer.writerows(rows)

    # Validation
    macros = len(set(r["macro_domain"] for r in rows))
    subs = len(set(r["subdomain"] for r in rows))
    micros = len(set(r["micro_domain"] for r in rows))
    print(f"Generated {len(rows)} rows")
    print(f"  Macro domains: {macros}")
    print(f"  Subdomains: {subs}")
    print(f"  Micro-domains: {micros}")
    print(f"  Duplicates: {len(rows) - micros}")
    print(f"  File: {path}")


if __name__ == "__main__":
    generate_catalog()
