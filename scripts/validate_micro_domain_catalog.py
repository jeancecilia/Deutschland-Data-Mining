"""Validate the micro-domain catalog CSV."""
import csv, sys, argparse
from pathlib import Path

VALID_RISK = {"low", "medium", "high", "restricted", "blocked"}

def validate(path: str) -> bool:
    p = Path(path)
    if not p.exists():
        print(f"FAIL: file not found: {path}")
        return False

    with open(p, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    errors = []
    macros = set()
    subdomains = set()
    micros = set()

    for i, row in enumerate(rows, start=2):
        md = row.get("macro_domain", "").strip()
        sd = row.get("subdomain", "").strip()
        mic = row.get("micro_domain", "").strip()
        aud = row.get("audience_hint", "").strip()
        prob = row.get("problem_hint", "").strip()
        fmt = row.get("format_hint", "").strip()
        risk = row.get("risk_level", "").strip()
        prio = row.get("priority", "").strip()
        lang = row.get("language", "").strip()

        if not md: errors.append(f"Row {i}: empty macro_domain")
        if not sd: errors.append(f"Row {i}: empty subdomain")
        if not mic: errors.append(f"Row {i}: empty micro_domain")
        if not aud: errors.append(f"Row {i}: empty audience_hint")
        if not prob: errors.append(f"Row {i}: empty problem_hint")
        if not fmt: errors.append(f"Row {i}: empty format_hint")
        if risk not in VALID_RISK: errors.append(f"Row {i}: invalid risk_level '{risk}'")
        if not prio.isdigit() or not (1 <= int(prio) <= 100): errors.append(f"Row {i}: invalid priority '{prio}'")
        if lang != "de": errors.append(f"Row {i}: language not 'de'")

        macros.add(md)
        subdomains.add(sd)
        if mic in micros: errors.append(f"Row {i}: duplicate micro_domain '{mic}'")
        micros.add(mic)

    if len(rows) != 10000:
        errors.append(f"Row count: {len(rows)} (expected 10000)")
    if len(macros) != 100:
        errors.append(f"Macro domains: {len(macros)} (expected 100)")
    if len(subdomains) != 1000:
        errors.append(f"Subdomains: {len(subdomains)} (expected 1000)")

    if errors:
        print("FAIL")
        for e in errors[:20]:
            print(f"  {e}")
        if len(errors) > 20:
            print(f"  ... and {len(errors)-20} more")
        return False

    print("VALID")
    print(f"  Rows: {len(rows)}")
    print(f"  Macro domains: {len(macros)}")
    print(f"  Subdomains: {len(subdomains)}")
    print(f"  Micro-domains: {len(micros)}")
    print(f"  Duplicates: 0")
    return True

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    args = p.parse_args()
    ok = validate(args.file)
    sys.exit(0 if ok else 1)
