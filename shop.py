import tkinter as tk
from tkinter import messagebox

from economy import bulk_cost, format_number, total_cps

# Batch sizes offered in the shop.
BUY_AMOUNTS = (1, 10, 100)

class Shop:
    def __init__(self, parent, game):
        self.game = game
        self.buy_amount = 1
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

        amount_row = tk.Frame(self.frame, bg="#f5e6c8")
        amount_row.pack(fill="x", pady=(0, 4))

        tk.Label(
            amount_row, text="Buy:", font=("Arial", 10, "bold"),
            bg="#f5e6c8", fg="#5c3317"
        ).pack(side="left")

        self.amount_buttons = {}
        for amount in BUY_AMOUNTS:
            btn = tk.Button(
                amount_row, text=f"x{amount}", font=("Arial", 9), width=4,
                command=lambda a=amount: self.set_buy_amount(a)
            )
            btn.pack(side="left", padx=3)
            self.amount_buttons[amount] = btn

        self._highlight_amount()

        self.buildings = {
            "Cursor":      {"base_cost": 15,        "cps": 0.1,     "owned": 0},
            "Grandma":     {"base_cost": 100,       "cps": 1.0,     "owned": 0},
            "Farm":        {"base_cost": 1_100,     "cps": 8.0,     "owned": 0},
            "Mine":        {"base_cost": 12_000,    "cps": 47.0,    "owned": 0},
            "Factory":     {"base_cost": 130_000,   "cps": 260.0,   "owned": 0},
            "Shipment":    {"base_cost": 1_400_000, "cps": 2_600.0, "owned": 0},
            "Alchemy Lab": {"base_cost": 20_000_000, "cps": 16_000.0, "owned": 0},
            "Portal":      {"base_cost": 330_000_000, "cps": 100_000.0, "owned": 0},
        }

        self.buttons = {}
        for name in self.buildings:
            btn = tk.Button(
                self.frame,
                text="",
                font=("Arial", 9),
                command=lambda n=name: self.buy(n),
                width=46,
                anchor="w"
            )
            btn.pack(pady=2)
            self.buttons[name] = btn

        self.update_buttons()

    def get_cost(self, name, amount=None):
        """Price of the next ``amount`` copies (default: the selected batch)."""
        if amount is None:
            amount = self.buy_amount
        b = self.buildings[name]
        return bulk_cost(b["base_cost"], b["owned"], amount)

    def buy(self, name):
        amount = self.buy_amount
        cost = self.get_cost(name, amount)
        if self.game.cookies >= cost:
            self.game.cookies -= cost
            self.buildings[name]["owned"] += amount
            self.game.recalculate_cps()
            self.update_buttons()
            self.game.update_display()
        else:
            messagebox.showinfo("Not enough cookies", f"You need {format_number(cost)} cookies!")

    def set_buy_amount(self, amount):
        self.buy_amount = amount
        self._highlight_amount()
        self.update_buttons()

    def _highlight_amount(self):
        for amount, btn in self.amount_buttons.items():
            selected = amount == self.buy_amount
            btn.config(
                relief="sunken" if selected else "raised",
                bg="#d4edda" if selected else "SystemButtonFace"
            )

    def recalculate_cps(self):
        return total_cps(self.buildings)

    def update_buttons(self):
        for name, b in self.buildings.items():
            cost = self.get_cost(name)
            text = (f"{name}  |  Owned: {b['owned']}  |  "
                    f"+{format_number(b['cps'])} cps each  |  "
                    f"x{self.buy_amount}: {format_number(cost)}")
            self.buttons[name].config(text=text)

    def get_owned(self):
        return {name: b["owned"] for name, b in self.buildings.items()}

    def load_owned(self, owned_dict):
        for name, owned in owned_dict.items():
            if name in self.buildings:
                self.buildings[name]["owned"] = owned
        self.update_buttons()