"""
seed_shops.py
-------------
Optional helper script to pre-populate the Hobby Shop list with a few
example entries, so the "pick from pre-determined list" location
option has something to show right after setup.

Run once with:
    python seed_shops.py

Feel free to edit SAMPLE_SHOPS below, or just add real shops later via
the admin panel at /admin/shops instead.
"""

from app import create_app
from extensions import db
from models import HobbyShop

SAMPLE_SHOPS = [
    {"name": "Versus Gamecenter - Lisboa", "region": "Lisboa", "address": "Rua Conselheiro Lopo Vaz, Lote C, Loja A, 1800-142 Lisboa"},
    {"name": "Versus Gamecenter - Algés", "region": "Lisboa", "address": "Av. Bombeiros Voluntários de Algés, 68B,1495-023 Algés"},
    {"name": "Conflux", "region": "Lisboa", "address": "Avenida Carolina Michaelis 4, 2795-047 Linda-a-Velha, Oeiras"},
]

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        for data in SAMPLE_SHOPS:
            exists = HobbyShop.query.filter_by(name=data["name"], region=data["region"]).first()
            if not exists:
                db.session.add(HobbyShop(**data))
        db.session.commit()
        print(f"Seeded {len(SAMPLE_SHOPS)} sample hobby shops (skipping any that already existed).")
