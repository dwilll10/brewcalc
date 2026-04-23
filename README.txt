BrewCalc - Home Brewing Recipe Calculator
=========================================

A web application for designing, calculating, and managing home brewing
beer recipes. Built for small-batch brewing (1.75 gallon default) with
support for extract and partial-mash brewing methods.

Features
--------
- Recipe builder with live calculation of OG, FG, IBU, SRM, and ABV
- BJCP style guidelines with in-range/out-of-range indicators
- Ingredient database: 22 fermentables, 30 hops, 10 yeasts, 12 styles
- Admin UI for adding/editing/deleting ingredients and styles
- Brew day timer with countdown timers and step checklist
- Batch size scaling with automatic recalculation
- Dark theme UI (Bootstrap 5)

Brewing Calculations
--------------------
- Original Gravity (OG): from fermentable PPG values and batch size
- Final Gravity (FG): from OG and yeast attenuation
- IBU: Tinseth formula accounting for gravity and boil time
- SRM: Morey equation for beer color
- ABV: Standard (OG - FG) * 131.25

Quick Start
-----------
1. Install Python 3.9 or newer

2. Install dependencies:
   python3 -m pip install -r requirements.txt

3. Seed the ingredient database (first time only):
   python3 seed_data.py

4. Start the development server:
   python3 run.py

5. Open http://127.0.0.1:5000 in your browser

Usage
-----
- Click "New Recipe" to create a recipe
- Use the Builder page to add fermentables, hops, and adjuncts
- Stats (OG, FG, ABV, IBU, SRM) update live as you change ingredients
- Select a BJCP style to see if your recipe is within style guidelines
- Use the Brew Day page for step-by-step instructions with timers
- Use Admin (nav bar) to add new hops, yeasts, fermentables, or styles

Project Structure
-----------------
brewcalc/
  app/              Flask application package
    calc/           Brewing calculation engine
    data/           JSON ingredient catalogs
    routes/         Flask route blueprints
    templates/      Jinja2 HTML templates
    static/         CSS and JavaScript
  tests/            Unit tests (21 tests)
  data/             SQLite database
  seed_data.py      Database seeder
  run.py            Application entry point
  requirements.txt  Python dependencies

Running Tests
-------------
python3 -m unittest tests.test_calculations -v

Tech Stack
----------
- Backend: Python, Flask, SQLAlchemy, SQLite
- Frontend: Bootstrap 5 (dark theme), vanilla JavaScript
- No npm/node required - CSS and JS libraries loaded via CDN

Planned Features
----------------
- Raspberry Pi fermentation temperature controller
- Live fermentation temperature monitoring dashboard
- Temperature profile management
- Print-friendly brew day sheets

License
-------
Personal use.
