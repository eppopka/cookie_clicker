import tkinter as tk
from tkinter import messagebox

from economy import building_cost, format_number, total_cps

class Shop:
    def __init__(self, parent, game):
        self.game = game
        self.frame = tk.LabelFrame(
            parent,
            text="Buildings",
            font=("Arial", 12, "bold"),
            bg="#f5e6c8",
            fg="#5c3317",
            padx=10,
            pady=10
        )
        self.frame.pack(fill="x", padx=20, pady=10)

        self.buildings = {
            "Cursor":  {"base_cost": 15,     "cps": 0.1,   "owned": 0},
            "Grandma": {"base_cost": 100,    "cps": 1.0,   "owned": 0},
            "Farm":    {"base_cost": 1100,   "cps": 8.0,   "owned": 0},
            "Mine":    {"base_cost": 12000,  "cps": 47.0,  "owned": 0},
            "Factory": {"base_cost": 130000, "cps": 260.0, "owned": 0},
        }

        self.buttons = {}
        for name in self.buildings:
            btn = tk.Button(
                self.frame,
                text="",
                font=("Arial", 10),
                command=lambda n=name: self.buy(n),
                width=42,
                anchor="w"
            )
            btn.pack(pady=3)
            self.buttons[name] = btn

        self.update_buttons()

    def get_cost(self, name):
        b = self.buildings[name]
        return building_cost(b["base_cost"], b["owned"])

    def buy(self, name):
        cost = self.get_cost(name)
        if self.game.cookies >= cost:
            self.game.cookies -= cost
            self.buildings[name]["owned"] += 1
            self.game.recalculate_cps()
            self.update_buttons()
            self.game.update_display()
        else:
            messagebox.showinfo("Not enough cookies", f"You need {format_number(cost)} cookies!")

    def recalculate_cps(self):
        return total_cps(self.buildings)

    def update_buttons(self):
        for name, b in self.buildings.items():
            cost = self.get_cost(name)
            text = (f"{name}  |  Owned: {b['owned']}  |  "
                    f"+{format_number(b['cps'])} cps  |  "
                    f"Cost: {format_number(cost)}")
            self.buttons[name].config(text=text)

    def get_owned(self):
        return {name: b["owned"] for name, b in self.buildings.items()}

    def load_owned(self, owned_dict):
        for name, owned in owned_dict.items():
            if name in self.buildings:
                self.buildings[name]["owned"] = owned
        self.update_buttons()