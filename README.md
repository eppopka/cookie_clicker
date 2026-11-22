# 🍪 Cookie Clicker

[![Tests](https://github.com/eppopka/cookie_clicker/actions/workflows/tests.yml/badge.svg)](https://github.com/eppopka/cookie_clicker/actions/workflows/tests.yml)

A small desktop cookie clicker written in Python with tkinter: click the
cookie, buy buildings, unlock upgrades and watch the numbers grow — even
while the game is closed.

## Features

- Click the big cookie (or press <kbd>Space</kbd>) to bake.
- Eight buildings — from Cursor to Portal — each 15% more expensive per
  copy owned.
- Buy buildings one at a time or in batches of 10 and 100. A batch you
  cannot fully afford still buys as many copies as your balance covers.
- Four upgrades, from Reinforced Index Finger to Forwards from Grandma.
- Offline earnings while the game is closed, capped at 8 hours.
- Autosave every minute, a manual **Save** button, and a final save when
  the window is closed.
- Compact counters (`1.5K`, `2.3M`, `1.5Qa`) so the UI never overflows.
- Versioned, defensive save format: a corrupted file is reported instead of
  crashing the game.

## Requirements

- Python 3.9 or newer.
- tkinter. It ships with the official Windows and macOS installers; on
  Debian/Ubuntu install it with `sudo apt install python3-tk`.

## Running the game

```bash
git clone https://github.com/eppopka/cookie_clicker.git
cd cookie_clicker
python3 main.py
```

Progress is stored in `cookie_clicker_save.json` next to `game.py`, so the
game finds the same save no matter which directory it was started from.

## Controls

| Action        | How                          |
| ------------- | ---------------------------- |
| Bake a cookie | Click the cookie or press Space |
| Buy a building| Click it in the **Buildings** list |
| Choose a batch| Click **x1**, **x10** or **x100** above the building list |
| Buy an upgrade| Click it in the **Upgrades** list (appears once unlocked) |
| Save          | **Save** button, the autosave, or closing the window |
| Reset         | **Reset Game** button        |

## Project layout

| File          | Responsibility                                  |
| ------------- | ----------------------------------------------- |
| `main.py`     | Entry point: creates the window and starts the game |
| `game.py`     | Game state, UI wiring, saving and loading       |
| `shop.py`     | Building list and purchase logic                |
| `upgrades.py` | Upgrade list, unlocking and effects             |
| `economy.py`  | Pure cost/cps/offline math (no tkinter)         |
| `save.py`     | Save-file schema and legacy-save handling       |
| `tests/`      | Pytest suite for `economy.py` and `save.py`     |
| `CHANGELOG.md`| Release notes for each version                  |

## Running the tests

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e . pytest
python -m pytest
```

The suite runs on Python 3.9–3.13 in GitHub Actions on every push and pull
request.

## Save data

Progress is stored in `cookie_clicker_save.json` next to `main.py`. The file
is versioned (`SAVE_VERSION` in `save.py`), ignored by git, and written
atomically, so an interrupted save cannot corrupt it. The game also saves
when you close the window, so quitting never loses a purchase. Deleting the
file is the same as starting over.
