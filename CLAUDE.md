# BrewCalc — Home Brewing Recipe Calculator & Fermentation Controller

## Project Overview

A Flask web application for designing, calculating, and managing home brewing beer recipes at the 1.75-gallon small-batch scale. Includes BJCP style guidelines, brew day timers with per-step equipment lists, batch scaling, fermentation profile editor, and a Raspberry Pi fermentation temperature controller with live monitoring dashboard.

## Architecture

```
brewcalc/
├── app/                                 # Flask recipe web app (port 5000)
│   ├── __init__.py                      # App factory, srm_to_hex helper
│   ├── config.py                        # Config classes (dev, test)
│   ├── models.py                        # SQLAlchemy ORM models (8 tables)
│   ├── extensions.py                    # db, migrate instances
│   ├── calc/                            # Brewing calculation engine
│   │   ├── gravity.py                   # OG/FG from fermentable inputs
│   │   ├── ibu.py                       # Tinseth IBU formula
│   │   ├── color.py                     # SRM via Morey equation
│   │   ├── abv.py                       # ABV from OG/FG
│   │   └── scaling.py                   # Batch size scaling with recalculation
│   ├── data/                            # JSON seed catalogs
│   │   ├── fermentables.json            # 22 extracts, grains, sugars
│   │   ├── hops.json                    # 30 hop varieties
│   │   ├── yeast.json                   # 10 yeast strains
│   │   └── bjcp_styles.json             # 12 BJCP style guidelines
│   ├── routes/
│   │   ├── recipes.py                   # Recipe CRUD + AJAX API + scale + profile
│   │   ├── brewday.py                   # Brew day timer/checklist with equipment
│   │   ├── styles.py                    # BJCP style reference page
│   │   ├── fermentation.py              # Proxy to Pi controller API
│   │   └── admin.py                     # Ingredient/style CRUD admin UI
│   ├── templates/                       # Jinja2 + Bootstrap 5 (dark theme)
│   │   ├── recipes/                     # list, detail, builder, new
│   │   ├── brewday/                     # timer with equipment tags
│   │   ├── fermentation/               # dashboard proxied from Pi
│   │   ├── styles/                      # BJCP style reference
│   │   └── admin/                       # fermentables, hops, yeasts, styles
│   └── static/
│       ├── css/app.css
│       └── js/
│           ├── calculator.js            # Live recalc, scaling, profile editor
│           └── timer.js                 # Brew day countdown timers
├── fermctl/                             # Raspberry Pi controller (port 5001)
│   ├── fermctl/
│   │   ├── config.py                    # GPIO pins, hysteresis, safety params
│   │   ├── sensor.py                    # DS18B20 reading, median filter, spike reject
│   │   ├── relay.py                     # GPIO relay control (heat/cool)
│   │   ├── controller.py               # Bang-bang control loop with watchdog
│   │   ├── profile.py                   # Temp profile interpolation
│   │   ├── logger.py                    # SQLite logging (WAL mode)
│   │   └── api.py                       # Flask REST API
│   ├── templates/dashboard.html         # Real-time Chart.js dashboard
│   ├── static/js/dashboard.js           # Dashboard polling and charts
│   ├── systemd/fermctl.service          # Auto-start on boot
│   ├── tests/test_fermctl.py            # 14 unit tests
│   ├── requirements.txt
│   └── run.py                           # Entry point (hardware or simulation)
├── tests/
│   └── test_calculations.py             # 21 unit tests for calc module
├── data/                                # SQLite database directory
├── seed_data.py                         # Database seeder script
├── requirements.txt                     # Recipe app dependencies
├── run.py                               # Recipe app entry point
├── EQUIPMENT_LIST.txt                   # Full procurement list with retailers
└── RASPBERRY_PI_SETUP.txt              # Step-by-step Pi integration guide
```

## Key Files

| File | Purpose |
|------|---------|
| `app/models.py` | 8 SQLAlchemy models: Style, Fermentable, Hop, Yeast, Recipe, RecipeFermentable, RecipeHop, RecipeAdjunct |
| `app/calc/ibu.py` | Tinseth IBU calculation — most complex formula, core of recipe accuracy |
| `app/calc/gravity.py` | OG/FG calculations — handles extract vs grain efficiency correctly |
| `app/routes/recipes.py` | Recipe CRUD + REST API for builder, batch scaling, fermentation profiles |
| `app/routes/brewday.py` | Generates brew day steps with per-step equipment lists |
| `app/routes/fermentation.py` | Proxies requests to Pi controller, handles offline gracefully |
| `app/routes/admin.py` | Admin CRUD for all ingredient types and styles |
| `app/static/js/calculator.js` | Client-side AJAX, batch scaling, fermentation profile editor with Chart.js |
| `fermctl/fermctl/controller.py` | Bang-bang temperature control with hysteresis and watchdog safety |
| `fermctl/fermctl/sensor.py` | DS18B20 reading with median filtering and spike rejection |
| `fermctl/fermctl/api.py` | Flask REST API for runs, readings, profiles, overrides |
| `seed_data.py` | Populates database from JSON catalogs (only inserts if table is empty) |

## Running

### Recipe App (on Mac/PC)

```bash
cd brewcalc
python3 -m pip install -r requirements.txt
python3 seed_data.py          # seed the database (first time only)
python3 run.py                # starts Flask dev server on http://127.0.0.1:5000
```

### Fermentation Controller (on Raspberry Pi)

```bash
cd brewcalc/fermctl
pip3 install flask
python3 run.py                # starts controller + API on http://0.0.0.0:5001
```

### Simulation Mode (no Pi hardware needed)

```bash
cd brewcalc/fermctl
FERMCTL_SIMULATE=1 python3 run.py    # simulated sensor, no GPIO
```

## Dependencies

- Python 3.9+
- Flask, Flask-SQLAlchemy, Flask-Migrate, requests
- RPi.GPIO (on Raspberry Pi only, auto-detected)
- Frontend: Bootstrap 5 + Chart.js via CDN (no npm/node)
- SQLite (no external database server needed)

## Testing

```bash
# Recipe app calculations (21 tests)
cd brewcalc
python3 -m unittest tests.test_calculations -v

# Fermentation controller (14 tests)
cd brewcalc/fermctl
FERMCTL_SIMULATE=1 python3 -m unittest tests.test_fermctl -v
```

35 total unit tests covering: OG, FG, IBU, SRM, ABV, batch scaling, temperature profiles, sensor simulation, and data logging.

## Key Routes

### Recipe App (port 5000)

| Route | Purpose |
|-------|---------|
| `/` | Recipe list |
| `/recipes/new` | Create new recipe |
| `/recipes/<id>` | Recipe detail with style comparison |
| `/recipes/<id>/builder` | Interactive builder (live recalc, scaling, profile editor) |
| `/brewday/<id>` | Brew day timer/checklist with equipment per step |
| `/fermentation/recipe/<id>` | Fermentation dashboard (proxied from Pi) |
| `/styles/` | BJCP style reference |
| `/admin/fermentables` | Manage fermentables |
| `/admin/hops` | Manage hops |
| `/admin/yeasts` | Manage yeasts |
| `/admin/styles` | Manage BJCP styles |
| `/api/recipes/<id>/*` | REST API for builder AJAX |
| `/api/recipes/<id>/scale` | Batch size scaling endpoint |
| `/api/recipes/<id>/ferm_profile` | Fermentation profile get/update |

### Fermentation Controller (port 5001)

| Route | Purpose |
|-------|---------|
| `/` | Real-time temperature dashboard |
| `/api/status` | Current temp, target, relay states |
| `/api/runs` | List or start fermentation runs |
| `/api/runs/<id>/stop` | Stop a run |
| `/api/readings` | Historical temperature readings |
| `/api/profile` | Get/update active temperature profile |
| `/api/override` | Manual temperature override |

## Brewing Formulas

- **OG:** `sum(amount_lb * PPG * efficiency) / batch_size` — extract efficiency = 1.0
- **FG:** `OG_points * (1 - attenuation)`
- **IBU (Tinseth):** utilization = bigness_factor * boil_time_factor, applied per hop addition
- **SRM (Morey):** `1.4922 * MCU^0.6859`
- **ABV:** `(OG - FG) * 131.25`

## Hardware Integration

See `RASPBERRY_PI_SETUP.txt` for the complete step-by-step guide covering:
- Flashing Pi OS and enabling 1-Wire
- Wiring DS18B20 sensor (GPIO4) and 2-channel relay (GPIO17/27)
- Testing with a desk lamp before connecting heat wrap
- Installing as a systemd service
- Connecting to the recipe app
- Building the insulated fermentation chamber
- Brewing your first batch

## Documentation

| File | Purpose |
|------|---------|
| `RASPBERRY_PI_SETUP.txt` | Step-by-step Pi setup and integration guide (19 steps) |
| `EQUIPMENT_LIST.txt` | Full equipment procurement list with prices and retailers |
| `README.txt` | Project overview and quick start |
| `CLAUDE.md` | Architecture reference and developer guide (this file) |
