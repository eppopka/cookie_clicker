from upgrades import Upgrades
import tkinter as tk
from tkinter import messagebox
import json
import os
import time

from economy import click_upgrade_cost, offline_earnings
from shop import Shop

SAVE_FILE = "cookie_clicker_save.json"

class Game:
    def __init__(self, root):
        self.root = root
        self.root.title("Cookie Clicker")
        self.root.geometry("500x750")
        self.root.resizable(False, False)
        self.root.configure(bg="#f5e6c8")

        # Game state
        self.cookies = 0.0
        self.cps = 0.0
        self.click_power = 1.0
        self.cps_multiplier = 1.0

        self.create_widgets()
        self.shop = Shop(self.root, self)
        self.upgrades = Upgrades(self.root, self)   # ← created after shop

        self.load_game()
        self.update_loop()

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
            self.root, text="🍪", font=("Arial", 80),
            bg="#d2691e", activebackground="#b85c1a",
            command=self.click_cookie, relief="raised", bd=8
        )
        self.cookie_btn.pack(pady=15)

        # Old simple upgrade button (you can remove this later if you want)
        self.upgrade_btn = tk.Button(
            self.root,
            text="",
            font=("Arial", 11),
            command=self.upgrade_click,
            bg="#ffe4b5"
        )
        self.upgrade_btn.pack(pady=8)

        # Controls
        control_frame = tk.Frame(self.root, bg="#f5e6c8")
        control_frame.pack(pady=8)

        tk.Button(control_frame, text="Save", command=self.save_game).pack(side="left", padx=5)
        tk.Button(control_frame, text="Reset Game", command=self.reset_game).pack(side="left", padx=5)

    def click_cookie(self):
        self.cookies += self.click_power
        self.update_display()

    def upgrade_click(self):
        cost = click_upgrade_cost(self.click_power)
        if self.cookies >= cost:
            self.cookies -= cost
            self.click_power += 1
            self.update_display()
        else:
            messagebox.showinfo("Not enough cookies", f"You need {cost} cookies!")

    def recalculate_cps(self):
        base_cps = self.shop.recalculate_cps()
        self.cps = base_cps * self.cps_multiplier

    def update_display(self):
        self.cookie_label.config(text=f"{self.cookies:,.1f} cookies")
        self.cps_label.config(text=f"per second: {self.cps:,.1f}")

        upgrade_cost = click_upgrade_cost(int(self.click_power))
        self.upgrade_btn.config(
            text=f"Upgrade Click Power (x{self.click_power:.0f}) - Cost: {upgrade_cost}"
        )

        self.shop.update_buttons()
        self.upgrades.update_buttons()

    def update_loop(self):
        self.cookies += self.cps * 0.1
        self.update_display()
        self.root.after(100, self.update_loop)

    def save_game(self):
        data = {
            "cookies": self.cookies,
            "click_power": self.click_power,
            "cps_multiplier": self.cps_multiplier,
            "buildings": self.shop.get_owned(),
            "upgrades": self.upgrades.get_bought(),
            "timestamp": time.time()
        }
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f)
        messagebox.showinfo("Saved", "Game saved!")

    def load_game(self):
        if not os.path.exists(SAVE_FILE):
            self.update_display()
            return

        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)

            self.cookies = data.get("cookies", 0)
            self.click_power = data.get("click_power", 1)
            self.cps_multiplier = data.get("cps_multiplier", 1.0)

            self.shop.load_owned(data.get("buildings", {}))
            self.upgrades.load_bought(data.get("upgrades", {}))

            self.recalculate_cps()

            # Offline progress (capped inside the helper)
            offline = offline_earnings(self.cps, time.time() - data.get("timestamp", time.time()))
            self.cookies += offline

        except Exception as e:
            print("Failed to load save:", e)

        self.update_display()

    def reset_game(self):
        if messagebox.askyesno("Reset", "Are you sure you want to reset all progress?"):
            self.cookies = 0
            self.click_power = 1
            self.cps_multiplier = 1.0

            # Reset buildings
            self.shop.load_owned({name: 0 for name in self.shop.buildings})

            # Reset upgrades
            self.upgrades.load_bought({u["id"]: False for u in self.upgrades.upgrades})

            self.recalculate_cps()

            if os.path.exists(SAVE_FILE):
                os.remove(SAVE_FILE)

            self.update_display()