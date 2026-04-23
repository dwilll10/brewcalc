from datetime import datetime, timezone

from .extensions import db


class Style(db.Model):
    __tablename__ = "styles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(10))  # e.g. "21A"
    og_low = db.Column(db.Float)
    og_high = db.Column(db.Float)
    fg_low = db.Column(db.Float)
    fg_high = db.Column(db.Float)
    ibu_low = db.Column(db.Integer)
    ibu_high = db.Column(db.Integer)
    srm_low = db.Column(db.Float)
    srm_high = db.Column(db.Float)
    abv_low = db.Column(db.Float)
    abv_high = db.Column(db.Float)
    description = db.Column(db.Text)

    recipes = db.relationship("Recipe", backref="style", lazy=True)


class Fermentable(db.Model):
    __tablename__ = "fermentables"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(20))  # extract_liquid, extract_dry, grain, sugar
    ppg = db.Column(db.Float)  # points per pound per gallon
    srm = db.Column(db.Float)  # color contribution
    notes = db.Column(db.Text)


class Hop(db.Model):
    __tablename__ = "hops"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    alpha_acid = db.Column(db.Float)  # % AA
    type = db.Column(db.String(20))  # bittering, aroma, dual
    notes = db.Column(db.Text)


class Yeast(db.Model):
    __tablename__ = "yeasts"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    lab = db.Column(db.String(60))  # Fermentis, White Labs, etc.
    code = db.Column(db.String(20))  # US-05, WLP001
    attenuation = db.Column(db.Float)  # avg apparent attenuation (0-1)
    temp_low = db.Column(db.Float)  # recommended ferm temp low (F)
    temp_high = db.Column(db.Float)  # recommended ferm temp high (F)
    type = db.Column(db.String(10))  # ale, lager
    notes = db.Column(db.Text)


class Recipe(db.Model):
    __tablename__ = "recipes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    style_id = db.Column(db.Integer, db.ForeignKey("styles.id"))
    batch_size = db.Column(db.Float, default=1.75)  # gallons
    boil_time = db.Column(db.Integer, default=60)  # minutes
    efficiency = db.Column(db.Float, default=1.0)  # 1.0 for extract
    yeast_id = db.Column(db.Integer, db.ForeignKey("yeasts.id"))
    og = db.Column(db.Float)
    fg = db.Column(db.Float)
    ibu = db.Column(db.Float)
    srm = db.Column(db.Float)
    abv = db.Column(db.Float)
    notes = db.Column(db.Text)
    ferm_profile = db.Column(db.Text)  # JSON: [{hours, temp_f}, ...]
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    brewed_at = db.Column(db.DateTime, nullable=True)

    yeast = db.relationship("Yeast", backref="recipes", lazy=True)
    fermentables = db.relationship(
        "RecipeFermentable", backref="recipe", lazy=True, cascade="all, delete-orphan"
    )
    hops = db.relationship(
        "RecipeHop", backref="recipe", lazy=True, cascade="all, delete-orphan"
    )
    adjuncts = db.relationship(
        "RecipeAdjunct", backref="recipe", lazy=True, cascade="all, delete-orphan"
    )


class RecipeFermentable(db.Model):
    __tablename__ = "recipe_fermentables"

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)
    fermentable_id = db.Column(db.Integer, db.ForeignKey("fermentables.id"), nullable=False)
    amount_oz = db.Column(db.Float)  # weight in ounces
    use = db.Column(db.String(20))  # steep, boil, late

    fermentable = db.relationship("Fermentable", lazy=True)


class RecipeHop(db.Model):
    __tablename__ = "recipe_hops"

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)
    hop_id = db.Column(db.Integer, db.ForeignKey("hops.id"), nullable=False)
    amount_oz = db.Column(db.Float)  # weight in ounces
    boil_time_min = db.Column(db.Integer)  # 0 = flameout/whirlpool
    use = db.Column(db.String(20))  # boil, flameout, dryhop

    hop = db.relationship("Hop", lazy=True)


class RecipeAdjunct(db.Model):
    __tablename__ = "recipe_adjuncts"

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)
    name = db.Column(db.String(120))
    amount = db.Column(db.String(60))  # free-text: "1 oz", "1 bean"
    add_time = db.Column(db.String(60))  # "boil 15 min", "secondary 5 days"
    notes = db.Column(db.Text)
