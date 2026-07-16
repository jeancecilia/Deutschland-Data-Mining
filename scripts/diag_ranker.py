"""Test ranker against known-good and known-bad candidates."""
from app.services.discovery.candidate_ranker import (
    _score_naturalness, _score_specificity, _score_intent,
    _score_domain_fit, _score_audience_fit, _score_format_style
)
from app.services.discovery.format_fit_rules import score_format_fit

tests = [
    ("Blutdrucktagebuch für Senioren", {"macro_domain": "gesundheit", "audience_hint": "senioren", "format_hint": "tagebuch"}),
    ("Pflegegrad Antrag Checkliste für Angehörige", {"macro_domain": "pflege", "audience_hint": "pflegende_angehoerige", "format_hint": "checkliste"}),
    ("Umzugscheckliste für Familien", {"macro_domain": "reise_umzug", "audience_hint": "familien", "format_hint": "checkliste"}),
    ("Excel Arbeitsbuch für Anfänger", {"macro_domain": "software", "audience_hint": "anfaenger", "format_hint": "arbeitsbuch"}),
    ("Rückruftraining Hund für Ersthundbesitzer", {"macro_domain": "haustiere", "audience_hint": "tierhalter", "format_hint": "trainingsjournal"}),
    ("Buchhaltung Arbeitsbuch für Kleinunternehmer", {"macro_domain": "business", "audience_hint": "kleinunternehmer", "format_hint": "arbeitsbuch"}),
    ("Smartphone Ratgeber für Senioren", {"macro_domain": "senioren", "audience_hint": "senioren", "format_hint": "ratgeber"}),
    ("ADHS Ernährung Kochbuch", {"macro_domain": "adhs", "audience_hint": "erwachsene", "format_hint": "kochbuch"}),
    # bad ones
    ("Schule Organisation für Einsteiger trainingsjournal", {"macro_domain": "schule", "audience_hint": "einsteiger", "format_hint": "trainingsjournal"}),
    ("Reise Umzug Beratung für Schueler leitfaden", {"macro_domain": "reise_umzug", "audience_hint": "schueler", "format_hint": "leitfaden"}),
]

print(f"{'Candidate':<55} {'Nat':>4} {'Spe':>4} {'Int':>4} {'Dom':>4} {'Fmt':>4} {'Aud':>4} {'Sty':>4} {'TOT':>4} {'Status':>12}")
print("-" * 115)

for name, meta in tests:
    nat = _score_naturalness(name)
    spec = _score_specificity(name, meta)
    intent = _score_intent(name, meta)
    dom = _score_domain_fit(meta)
    fmt = score_format_fit(name, meta.get("macro_domain", ""), "")
    aud = _score_audience_fit(meta)
    sty = _score_format_style(name, meta)
    total = int(nat * 0.15 + spec * 0.20 + intent * 0.15 + dom * 0.10 + fmt * 0.10 + aud * 0.10 + sty * 0.10)
    status = "queued" if total >= 80 else ("manual_review" if total >= 70 else "rejected")
    print(f"{name:<55} {nat:>4} {spec:>4} {intent:>4} {dom:>4} {fmt:>4} {aud:>4} {sty:>4} {total:>4} {status:>12}")
