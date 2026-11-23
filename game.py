from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import tkinter as tk
from tkinter import messagebox

from economy import click_upgrade_cost, format_number, offline_earnings
from save import deserialize_state, serialize_state
from shop import Shop
from upgrades import Upgrades


# Keep the save next to the game script, not next to the shell that launched it
SAVE_FILE = Path(__file__).resolve().parent / "cookie_clicker_save.json"
AUTOSAVE_INTERVAL_MS = 60_000          # 60 seconds
TICK_MS = 100                          # game tick every 100 ms


class Game:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Cookie Clicker")
        self.root.geometry("540x840")
        self.root.minsize(540, 840)
        self.root.configure(bg="#f5e6c8")

        # Core state
        self.cookies: float = 0.0
        self.cps: float = 0.0
        self.click_power: float = 1.0
        self.click_level: int = 1
        self.cps_multiplier: float = 1.0
        self.total_baked: float = 0.0   # lifetime cookies (never decreases)

        self._autosave_job: str | None = None

        self.create_widgets()
        self.shop = Shop(self.root, self)
        self.upgrades = Upgrades(self.root, self)

        self.load_game()
        self.update_loop()
        self._schedule_autosave()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    # ------------------------------------------------------------------ UI
    def create_widgets(self) -> None:
        self.cookie_label = tk.Label(
            self.root,
            text="0 cookies",
            font=("Arial", 24, "bold"),
            bg="#f5e6c8",
            fg="#5c3317",
        )
        self.cookie_label.pack(pady=10)

        self.cps_label = tk.Label(
            self.root,
            text="per second: 0",
            font=("Arial", 12),
            bg="#f5e6c8",
            fg="#8b5a2b",
        )
        self.cps_label.pack()

        self.cookie_btn = tk.Button(
            self.root,
            text="🍪",
            font=("Arial", 64),
            bg="#d2691e",
            activebackground="#b85c1a",
            command=self.click_cookie,
            relief="raised",
            bd=8,
        )
        self.cookie_btn.pack(pady=15)

        # Legacy single-button click upgrade (safe to remove once Upgrades panel is complete)
        self.upgrade_btn = tk.Button(
            self.root,
            text="",
            font=("Arial", 10),
            command=self.upgrade_click,
            bg="#ffe4b5",
        )
        self.upgrade_btn.pack(pady=8)

        control_frame = tk.Frame(self.root, bg="#f5e6c8")
        control_frame.pack(pady=8)

        tk.Button(control_frame, text="Save", command=self.save_game).pack(side="left", padx=5)
        tk.Button(control_frame, text="Reset Game", command=self.reset_game).pack(side="left", padx=5)

        tk.Label(
            self.root,
            text="Tip: press Space to bake",
            font=("Arial", 9),
            bg="#f5e6c8",
            fg="#a07850",
        ).pack(pady=(4, 0))

        self.root.bind("<space>", self._on_space_key)

    def _on_space_key(self, event: tk.Event | None = None) -> None:
        """Bake with Space unless a button currently has focus."""
        if isinstance(self.root.focus_get(), tk.Button):
            return
        self.click_cookie()

    # ------------------------------------------------------------- Game logic
    def click_cookie(self) -> None:
        self.cookies += self.click_power
        self.total_baked += self.click_power
        self.update_display()

    def upgrade_click(self) -> None:
        cost = click_upgrade_cost(self.click_level)
        if self.cookies < cost:
            messagebox.showinfo(
                "Not enough cookies",
                f"You need {format_number(cost)} cookies!",
            )
            return
        self.cookies -= cost
        self.click_level += 1
        self.click_power += 1
        self.update_display()

    def recalculate_cps(self) -> None:
        base_cps = self.shop.recalculate_cps()
        self.cps = base_cps * self.cps_multiplier

    def update_display(self) -> None:
        self.cookie_label.config(text=f"{format_number(self.cookies)} cookies")
        self.cps_label.config(text=f"per second: {format_number(self.cps)}")

        cost = click_upgrade_cost(self.click_level)
        self.upgrade_btn.config(
            text=f"Upgrade Click Power (x{self.click_power:g}) – Cost: {format_number(cost)}"
        )

        self.shop.update_buttons()
        self.upgrades.update_buttons()

    def update_loop(self) -> None:
        baked = self.cps * (TICK_MS / 1000.0)
        self.cookies += baked
        self.total_baked += baked
        self.update_display()
        self.root.after(TICK_MS, self.update_loop)

    # --------------------------------------------------------------- Saving
    def _write_save(self) -> None:
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
        tmp = SAVE_FILE.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        tmp.replace(SAVE_FILE)

    def save_game(self) -> None:
        try:
            self._write_save()
            messagebox.showinfo("Saved", "Game saved!")
        except OSError as e:
            messagebox.showerror("Save failed", str(e))

    def _schedule_autosave(self) -> None:
        self._autosave_job = self.root.after(AUTOSAVE_INTERVAL_MS, self._autosave)

    def _autosave(self) -> None:
        try:
            self._write_save()
        except OSError as e:
            print("Autosave failed:", e)
        self._schedule_autosave()

    def close(self) -> None:
        if self._autosave_job is not None:
            self.root.after_cancel(self._autosave_job)
            self._autosave_job = None
        try:
            self._write_save()
        except OSError as e:
            print("Save on exit failed:", e)
        self.root.destroy()

    def load_game(self) -> None:
        if not SAVE_FILE.exists():
            self.update_display()
            return

        try:
            with SAVE_FILE.open("r", encoding="utf-8") as f:
                raw = json.load(f)
            state = deserialize_state(raw)
        except (OSError, ValueError, json.JSONDecodeError) as e:
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

        # Offline progress
        if state.get("timestamp") is not None:
            earned = offline_earnings(self.cps, time.time() - state["timestamp"])
            self.cookies += earned
            self.total_baked += earned

        self.update_display()

    def reset_game(self) -> None:
        if not messagebox.askyesno("Reset", "Are you sure you want to reset all progress?"):
            return

        self.cookies = 0.0
        self.click_power = 1.0
        self.click_level = 1
        self.cps_multiplier = 1.0
        self.total_baked = 0.0

        self.shop.load_owned({name: 0 for name in self.shop.buildings})
        self.upgrades.load_bought({u["id"]: False for u in self.upgrades.upgrades})
        self.recalculate_cps()

        if SAVE_FILE.exists():
            try:
                SAVE_FILE.unlink()
            except OSError as e:
                print("Could not delete save file:", e)

        self.update_display()


# Example entry point (keep your existing one if you already have it)
if __name__ == "__main__":
    root = tk.Tk()
    game = Game(root)
    root.mainloop()