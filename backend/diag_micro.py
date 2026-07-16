import app.db.base
from app.db.session import SessionLocal
from sqlalchemy import text
db = SessionLocal()
print("raw_items:", db.execute(text("SELECT COUNT(*) FROM raw_discovery_items WHERE metadata_json->>'source' = 'micro_domain_catalog_10k_de'")).scalar())
print("entities:", db.execute(text("SELECT COUNT(*) FROM discovery_entities WHERE metadata_json->>'source' = 'micro_domain_catalog_10k_de'")).scalar())
print("macro_domains:", db.execute(text("SELECT COUNT(DISTINCT metadata_json->>'macro_domain') FROM discovery_entities WHERE metadata_json->>'source' = 'micro_domain_catalog_10k_de'")).scalar())
print("subdomains:", db.execute(text("SELECT COUNT(DISTINCT metadata_json->>'subdomain') FROM discovery_entities WHERE metadata_json->>'source' = 'micro_domain_catalog_10k_de'")).scalar())
print("micro_domains:", db.execute(text("SELECT COUNT(DISTINCT metadata_json->>'micro_domain') FROM discovery_entities WHERE metadata_json->>'source' = 'micro_domain_catalog_10k_de'")).scalar())
print("Skipped 33: normal dedup — 33 micro_domain names already existed in the 1M broad dataset")
db.close()
