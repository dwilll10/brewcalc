"""Seed the database with ingredient catalogs and BJCP styles."""

import json
import os

from app import create_app
from app.extensions import db
from app.models import Fermentable, Hop, Yeast, Style

DATA_DIR = os.path.join(os.path.dirname(__file__), "app", "data")


def load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        # Seed fermentables
        if Fermentable.query.count() == 0:
            for item in load_json("fermentables.json"):
                db.session.add(Fermentable(**item))
            print(f"Seeded {Fermentable.query.count()} fermentables")

        # Seed hops
        if Hop.query.count() == 0:
            for item in load_json("hops.json"):
                db.session.add(Hop(**item))
            print(f"Seeded {Hop.query.count()} hops")

        # Seed yeasts
        if Yeast.query.count() == 0:
            for item in load_json("yeast.json"):
                db.session.add(Yeast(**item))
            print(f"Seeded {Yeast.query.count()} yeasts")

        # Seed styles
        if Style.query.count() == 0:
            for item in load_json("bjcp_styles.json"):
                db.session.add(Style(**item))
            print(f"Seeded {Style.query.count()} styles")

        db.session.commit()
        print("Database seeded successfully.")


if __name__ == "__main__":
    seed()
