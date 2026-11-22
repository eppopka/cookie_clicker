from upgrades import Upgrades
import tkinter as tk
from tkinter import messagebox
import json
import os
import time

from economy import click_upgrade_cost, format_number, offline_earnings
from save import deserialize_state, serialize_state
from shop import Shop

SAVE_FILE = "cookie_clicker_save.json"
AUTOSAVE_INTERVAL_MS = 60 * 1000

class Game:
    def __init__(self, root):
        self.root = root
        self.root.title("Cookie Clicker")
        self.root.geometry("540x840")
        self.root.minsize(540, 840)
        self.root.configure(bg="#f5e6c8")

        # Game state
        self.cookies = 0.0
        self.cps = 0.0
        self.click_power = 1.0
        self.click_level = 1
        self.cps_multiplier = 1.0
        # Lifetime cookies, never reduced by purchases. Upgrades unlock
        # from this counter so spending never hides them again.
        self.total_baked = 0.0

        self.create_widgets()
        self.shop = Shop(self.root, self)
        self.upgrades = Upgrades(self.root, self)   # ← created after shop

        self.load_game()
        self.update_loop()
        self._autosave_job = self.root.after(AUTOSAVE_INTERVAL_MS, self._autosave)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def create_widgets(self):
        self.cookie_label = tk.Label(
            self.root, text="0 cookies", font=("Arial", 24, "bold"),
            bg="#f5e6c8", fg="#5c3317"
        )
        self.cookie_label.pack(pady=10)

        self.cps_label = tk.Label(
            self.root, text="per second: 0", font=("Arial", 12),
            bg="#f5e6c8", fg="#8b5a2b"
        )
        self.cps_label.pack()

        self.cookie_btn = tk.Button(
            self.root, text="🍪", font=("Arial", 64),
            bg="#d2691e", activebackground="#b85c1a",
            command=self.click_cookie, relief="raised", bd=8
        )
        self.cookie_btn.pack(pady=15)

        # Old simple upgrade button (you can remove this later if you want)
        self.upgrade_btn = tk.Button(
            self.root,
            text="",
            font=("Arial", 10),
            command=self.upgrade_click,
            bg="#ffe4b5"
        )
        self.upgrade_btn.pack(pady=8)

        # Controls
        control_frame = tk.Frame(self.root, bg="#f5e6c8")
        control_frame.pack(pady=8)

        tk.Button(control_frame, text="Save", command=self.save_game).pack(side="left", padx=5)
        tk.Button(control_frame, text="Reset Game", command=self.reset_game).pack(side="left", padx=5)

        tk.Label(
            self.root, text="Tip: press Space to bake", font=("Arial", 9),
            bg="#f5e6c8", fg="#a07850"
        ).pack(pady=(4, 0))

        self.root.bind("<space>", self._on_space_key)

    def _on_space_key(self, event=None):
        """Bake with the space bar, unless a button already has focus."""
        if isinstance(self.root.focus_get(), tk.Button):
            return
        self.click_cookie()

    def click_cookie(self):
        self.cookies += self.click_power
        self.total_baked += self.click_power
        self.update_display()

    def upgrade_click(self):
        cost = click_upgrade_cost(self.click_level)
        if self.cookies >= cost:
            self.cookies -= cost
            self.click_level += 1
            self.click_power += 1
            self.update_display()
        else:
            messagebox.showinfo("Not enough cookies", f"You need {format_number(cost)} cookies!")

    def recalculate_cps(self):
        base_cps = self.shop.recalculate_cps()
        self.cps = base_cps * self.cps_multiplier

    def update_display(self):
        cookie_text = f"{format_number(self.cookies)} cookies"
        if self.cookie_label.cget("text") != cookie_text:
            self.cookie_label.config(text=cookie_text)

        cps_text = f"per second: {format_number(self.cps)}"
        if self.cps_label.cget("text") != cps_text:
            self.cps_label.config(text=cps_text)

        upgrade_cost = click_upgrade_cost(self.click_level)
        upgrade_text = (f"Upgrade Click Power (x{self.click_power:g}) - "
                        f"Cost: {format_number(upgrade_cost)}")
        if self.upgrade_btn.cget("text") != upgrade_text:
            self.upgrade_btn.config(text=upgrade_text)

        self.shop.update_buttons()
        self.upgrades.update_buttons()

    def update_loop(self):
        baked = self.cps * 0.1
        self.cookies += baked
        self.total_baked += baked
        self.update_display()
        self.root.after(100, self.update_loop)

    def save_game(self):
        try:
            self._write_save()
        except OSError as e:
            messagebox.showerror("Save failed", str(e))
            return
        messagebox.showinfo("Saved", "Game saved!")

    def _write_save(self):
        """Write the current state to disk, replacing the old save atomically."""
        data = serialize_state(
            cookies=self.cookies,
            click_power=self.click_power,
            click_level=self.click_level,
            cps_multiplier=self.cps_multiplier,
            total_baked=self.total_baked,
            buildings=self.shop.get_owned(),
            upgrades=self.upgrades.get_bought(),
            timestamp=time.time(),
        )
        temp_file = SAVE_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(temp_file, SAVE_FILE)

    def _autosave(self):
        try:
            self._write_save()
        except OSError as e:
            print("Autosave failed:", e)
        self._autosave_job = self.root.after(AUTOSAVE_INTERVAL_MS, self._autosave)

    def close(self):
        """Flush the save and stop the background jobs before closing."""
        if self._autosave_job is not None:
            self.root.after_cancel(self._autosave_job)
            self._autosave_job = None
        try:
            self._write_save()
        except OSError as e:
            print("Save on exit failed:", e)
        self.root.destroy()

    def load_game(self):
        if not os.path.exists(SAVE_FILE):
            self.update_display()
            return

        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                state = deserialize_state(json.load(f))
        except (OSError, ValueError) as e:
            print("Failed to load save:", e)
            self.update_display()
            return

        self.cookies = state["cookies"]
        self.click_power = state["click_power"]
        self.click_level = state["click_level"]
        self.cps_multiplier = state["cps_multiplier"]
        self.total_baked = state["total_baked"]

        self.shop.load_owned(state["buildings"])
        self.upgrades.load_bought(state["upgrades"])

        self.recalculate_cps()

        # Offline progress (capped inside the helper)
        if state["timestamp"] is not None:
            earned = offline_earnings(self.cps, time.time() - state["timestamp"])
            self.cookies += earned
            self.total_baked += earned

        self.update_display()

    def reset_game(self):
        if messagebox.askyesno("Reset", "Are you sure you want to reset all progress?"):
            self.cookies = 0
            self.click_power = 1
            self.click_level = 1
            self.cps_multiplier = 1.0
            self.total_baked = 0.0

            # Reset buildings
            self.shop.load_owned({name: 0 for name in self.shop.buildings})

            # Reset upgrades
            self.upgrades.load_bought({u["id"]: False for u in self.upgrades.upgrades})

            self.recalculate_cps()

            if os.path.exists(SAVE_FILE):
                os.remove(SAVE_FILE)

            self.update_display()