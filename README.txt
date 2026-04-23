BrewCalc - Home Brewing Recipe Calculator & Fermentation Controller
====================================================================

A web application for designing, calculating, and managing home brewing
beer recipes with integrated Raspberry Pi fermentation temperature control.
Built for small-batch brewing (1.75 gallon default) with support for
extract and partial-mash brewing methods.


Features
--------

Recipe App:
  - Recipe builder with live calculation of OG, FG, IBU, SRM, and ABV
  - BJCP style guidelines with in-range/out-of-range indicators
  - Ingredient database: 22 fermentables, 30 hops, 10 yeasts, 12 styles
  - Admin UI for adding/editing/deleting ingredients and styles
  - Brew day timer with countdown timers, step checklist, and
    equipment needed per step
  - Batch size scaling with proportional ingredient adjustment
    and automatic stat recalculation (presets: 1, 1.75, 2.5, 5 gal)
  - Fermentation profile editor with visual Chart.js temperature
    curve, editable waypoints, and preset profiles
  - Dark theme UI (Bootstrap 5)

Fermentation Controller (Raspberry Pi):
  - DS18B20 temperature sensor with median filtering and spike rejection
  - Bang-bang temperature control with configurable hysteresis
  - GPIO relay control for heat wrap and cooling fan
  - Temperature profile interpolation with time-based waypoints
  - Real-time web dashboard with Chart.js temperature chart
  - REST API for remote control and monitoring
  - Watchdog safety shutoff (relays off if sensor fails)
  - Simulation mode for development without hardware
  - Auto-start via systemd service

Integration:
  - Recipe app proxies to Pi controller over local network
  - Start fermentation from the recipe page — profile is pushed to Pi
  - Live temperature monitoring from the recipe app dashboard
  - Manual temperature override from either interface


Brewing Calculations
--------------------
  - Original Gravity (OG): from fermentable PPG values and batch size
  - Final Gravity (FG): from OG and yeast attenuation
  - IBU: Tinseth formula accounting for gravity and boil time
  - SRM: Morey equation for beer color
  - ABV: Standard (OG - FG) * 131.25


Quick Start — Recipe App
-------------------------

1. Install Python 3.9 or newer

2. Install dependencies:
     cd brewcalc
     python3 -m pip install -r requirements.txt

3. Seed the ingredient database (first time only):
     python3 seed_data.py

4. Start the development server:
     python3 run.py

5. Open http://127.0.0.1:5000 in your browser


Quick Start — Fermentation Controller
---------------------------------------

On Raspberry Pi (see RASPBERRY_PI_SETUP.txt for full guide):

1. Clone the repository:
     git clone https://github.com/dwilll10/brewcalc.git

2. Install Flask:
     cd brewcalc/fermctl
     pip3 install flask

3. Start the controller:
     python3 run.py

4. Open http://raspberrypi.local:5001 for the dashboard

For development without a Pi (simulation mode):

     cd brewcalc/fermctl
     FERMCTL_SIMULATE=1 python3 run.py


Usage
-----
  - Click "New Recipe" to create a recipe
  - Use the Builder page to add fermentables, hops, and adjuncts
  - Stats (OG, FG, ABV, IBU, SRM) update live as you change ingredients
  - Select a BJCP style to see if your recipe is within style guidelines
  - Use "Scale Recipe" to resize the batch (ingredients scale proportionally)
  - Use the Fermentation Profile editor to define a temperature schedule
    with waypoints, or select a preset (Standard Ale, Stout, Quick Ale)
  - Use the Brew Day page for step-by-step instructions with timers
    and equipment needed for each step
  - Click "Fermentation" on a recipe to monitor and control temperature
    via the Raspberry Pi
  - Use Admin (nav bar) to add new hops, yeasts, fermentables, or styles


Project Structure
-----------------

brewcalc/
  app/                  Flask recipe web application
    calc/               Brewing calculation engine
    data/               JSON ingredient catalogs
    routes/             Flask route blueprints (recipes, brewday,
                          fermentation, styles, admin)
    templates/          Jinja2 HTML templates
    static/             CSS and JavaScript (Chart.js, timers)
  fermctl/              Raspberry Pi fermentation controller
    fermctl/            Controller Python package (sensor, relay,
                          controller, profile, logger, api)
    templates/          Pi dashboard template
    static/             Pi dashboard JavaScript
    systemd/            systemd service file for auto-start
    tests/              Controller unit tests (14 tests)
  tests/                Recipe app unit tests (21 tests)
  data/                 SQLite database directory
  seed_data.py          Database seeder
  run.py                Recipe app entry point
  requirements.txt      Recipe app Python dependencies


Running Tests
-------------

Recipe app (21 tests):
  cd brewcalc
  python3 -m unittest tests.test_calculations -v

Fermentation controller (14 tests):
  cd brewcalc/fermctl
  FERMCTL_SIMULATE=1 python3 -m unittest tests.test_fermctl -v


Tech Stack
----------
  - Backend: Python 3.9+, Flask, SQLAlchemy, SQLite
  - Frontend: Bootstrap 5 (dark theme), Chart.js, vanilla JavaScript
  - Hardware: Raspberry Pi 4, DS18B20 sensor, GPIO relay module
  - No npm/node required — CSS and JS libraries loaded via CDN


Documentation
-------------

  RASPBERRY_PI_SETUP.txt   Step-by-step Pi setup and integration guide
                           (19 steps across 6 phases, from flashing
                           the SD card through brewing your first batch)

  EQUIPMENT_LIST.txt       Complete equipment procurement list with
                           approximate prices and recommended retailers
                           (brewing, fermentation, Pi hardware, serving,
                           cleaning, optional upgrades)

  CLAUDE.md                Architecture reference and developer guide


License
-------
Personal use.
