# BrewCalc — Home Brewing Recipe Calculator & Fermentation Controller

## Project Overview

A Flask web application for designing, calculating, and managing home brewing beer recipes at the 1.75-gallon small-batch scale. Includes BJCP style guidelines, brew day timers, and is designed to integrate with a Raspberry Pi fermentation temperature controller (Phase 2).

## Architecture

```
brewcalc/
├── app/
│   ├── __init__.py              # Flask app factory, srm_to_hex helper
│   ├── config.py                # Config classes (dev, test)
│   ├── models.py                # SQLAlchemy ORM models (8 tables)
│   ├── extensions.py            # db, migrate instances
│   ├── calc/                    # Brewing calculation engine
│   │   ├── gravity.py           # OG/FG from fermentable inputs
│   │   ├── ibu.py               # Tinseth IBU formula
│   │   ├── color.py             # SRM via Morey equation
│   │   ├── abv.py               # ABV from OG/FG
│   │   └── scaling.py           # Batch size scaling with recalculation
│   ├── data/                    # JSON seed catalogs
│   │   ├── fermentables.json    # 22 extracts, grains, sugars
│   │   ├── hops.json            # 30 hop varieties
│   │   ├── yeast.json           # 10 yeast strains
│   │   └── bjcp_styles.json     # 12 BJCP style guidelines
│   ├── routes/
│   │   ├── recipes.py           # Recipe CRUD + AJAX API for builder
│   │   ├── brewday.py           # Brew day timer/checklist generator
│   │   ├── styles.py            # BJCP style reference page
│   │   ├── fermentation.py      # Pi controller proxy (stub)
│   │   └── admin.py             # Ingredient/style CRUD admin UI
│   ├── templates/               # Jinja2 + Bootstrap 5 (dark theme)
│   └── static/
│       ├���─ css/app.css
│       └── js/
│           ├── calculator.js    # Live recipe recalculation + SRM color
│           └── timer.js         # Brew day countdown timers
├─��� tests/
│   └── test_calculations.py     # 21 unit tests for calc module
├── data/                        # SQLite database directory
├── seed_data.py                 # Database seeder script
├── requirements.txt             # Flask, SQLAlchemy, Migrate, requests
└── run.py                       # Entry point: python3 run.py
```

## Key Files

| File | Purpose |
|------|---------|
| `app/models.py` | 8 SQLAlchemy models: Style, Fermentable, Hop, Yeast, Recipe, RecipeFermentable, RecipeHop, RecipeAdjunct |
| `app/calc/ibu.py` | Tinseth IBU calculation — most complex formula, core of recipe accuracy |
| `app/calc/gravity.py` | OG/FG calculations — handles extract vs grain efficiency correctly |
| `app/routes/recipes.py` | Recipe CRUD + full REST API for the interactive builder |
| `app/routes/admin.py` | Admin CRUD for all ingredient types and styles |
| `app/static/js/calculator.js` | Client-side AJAX — sends ingredient changes to API, updates stats live |
| `seed_data.py` | Populates database from JSON catalogs (only inserts if table is empty) |

## Running

```bash
cd brewcalc
python3 -m pip install -r requirements.txt
python3 seed_data.py          # seed the database (first time only)
python3 run.py                # starts Flask dev server on http://127.0.0.1:5000
```

## Dependencies

- Python 3.9+
- Flask, Flask-SQLAlchemy, Flask-Migrate, requests
- Frontend: Bootstrap 5 + Chart.js via CDN (no npm/node)
- SQLite (no external database server needed)

## Testing

```bash
python3 -m unittest tests.test_calculations -v
```

21 unit tests cover: OG, FG, IBU (Tinseth), SRM (Morey), ABV, and batch scaling.

## Key Routes

| Route | Purpose |
|-------|---------|
| `/` | Recipe list |
| `/recipes/new` | Create new recipe |
| `/recipes/<id>` | Recipe detail with style comparison |
| `/recipes/<id>/builder` | Interactive recipe builder (live recalculation) |
| `/brewday/<id>` | Brew day timer/checklist |
| `/styles/` | BJCP style reference |
| `/admin/fermentables` | Manage fermentables |
| `/admin/hops` | Manage hops |
| `/admin/yeasts` | Manage yeasts |
| `/admin/styles` | Manage BJCP styles |
| `/api/recipes/<id>/*` | REST API for recipe builder AJAX |

## Brewing Formulas

- **OG:** `sum(amount_lb * PPG * efficiency) / batch_size` — extract efficiency = 1.0
- **FG:** `OG_points * (1 - attenuation)`
- **IBU (Tinseth):** utilization = bigness_factor * boil_time_factor, applied per hop addition
- **SRM (Morey):** `1.4922 * MCU^0.6859`
- **ABV:** `(OG - FG) * 131.25`

## Planned Features (Phase 2+)

- Raspberry Pi fermentation temperature controller (`fermctl/`)
- Fermentation dashboard with live temp charting
- Temperature profile push from recipe app to Pi
- Print-friendly brew day sheets
