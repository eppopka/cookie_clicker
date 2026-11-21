import tkinter as tk
from tkinter import messagebox

from economy import format_number

class Upgrades:
    def __init__(self, parent, game):
        self.game = game

        self.frame = tk.LabelFrame(
            parent,
            text="Upgrades",
            font=("Arial", 12, "bold"),
            bg="#f5e6c8",
            fg="#5c3317",
            padx=10,
            pady=8
        )
        self.frame.pack(fill="x", padx=20, pady=8)
        self.upgrades = [
            {
                "id": "double_click",
                "name": "Reinforced Index Finger",
                "description": "Cookies per click x2",
                "cost": 100,
                "unlock_at": 50,          # appears when you reach 50 cookies
                "effect": "click_x2",
                "bought": False
            },
            {
                "id": "click_x5",
                "name": "Carpal Tunnel Prevention Cream",
                "description": "Cookies per click x5",
                "cost": 500,
                "unlock_at": 300,
                "effect": "click_x5",
                "bought": False
            },
            {
                "id": "click_x10",
                "name": "Ambidextrous",
                "description": "Cookies per click x10",
                "cost": 2500,
                "unlock_at": 1500,
                "effect": "click_x10",
                "bought": False
            },
            {
                "id": "cps_boost",
                "name": "Forwards from Grandma",
                "description": "All buildings produce +10% more",
                "cost": 1000,
                "unlock_at": 800,
                "effect": "cps_10pct",
                "bought": False
            },
        ]

        self.buttons = {}
        self.create_buttons()

    def create_buttons(self):
        for upgrade in self.upgrades:
            btn = tk.Button(
                self.frame,
                text="",
                font=("Arial", 9),
                command=lambda u=upgrade: self.buy(u),
                width=46,
                anchor="w",
                state="disabled"
            )
            btn.pack(pady=2)
            self.buttons[upgrade["id"]] = btn

        self.update_buttons()

    def buy(self, upgrade):
        if upgrade["bought"]:
            return

        if self.game.cookies >= upgrade["cost"]:
            self.game.cookies -= upgrade["cost"]
            upgrade["bought"] = True
            self.apply_effect(upgrade)
            self.update_buttons()
            self.game.update_display()
        else:
            messagebox.showinfo("Not enough cookies", f"You need {format_number(upgrade['cost'])} cookies!")

    def apply_effect(self, upgrade):
        effect = upgrade["effect"]

        if effect == "click_x2":
            self.game.click_power *= 2
        elif effect == "click_x5":
            self.game.click_power *= 5
        elif effect == "click_x10":
            self.game.click_power *= 10
        elif effect == "cps_10pct":
            self.game.cps_multiplier *= 1.10
            self.game.recalculate_cps()

    def update_buttons(self):
        for upgrade in self.upgrades:
            btn = self.buttons[upgrade["id"]]

            # Show the upgrade only when the player has reached the unlock amount
            if self.game.cookies < upgrade["unlock_at"] and not upgrade["bought"]:
                btn.config(text="???", state="disabled")
                continue

            if upgrade["bought"]:
                btn.config(
                    text=f"✓ {upgrade['name']}  (owned)",
                    state="disabled",
                    bg="#d4edda"
                )
            else:
                btn.config(
                    text=f"{upgrade['name']}  |  {upgrade['description']}  |  Cost: {format_number(upgrade['cost'])}",
                    state="normal",
                    bg="SystemButtonFace"
                )

    def get_bought(self):
        return {u["id"]: u["bought"] for u in self.upgrades}

    def load_bought(self, bought_dict):
        for upgrade in self.upgrades:
            # Saved click_power and cps_multiplier already include the
            # effects of bought upgrades, so only restore the flags here.
            upgrade["bought"] = bool(bought_dict.get(upgrade["id"], False))
        self.update_buttons()