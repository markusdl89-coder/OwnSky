import math
from config import USER_SHIPS, START_PORT, CITIES, RESOURCE_WEIGHTS

class GameCore:
    @staticmethod
    def init_ship(chat_id, name="Стартовый Цеппелин"):
        """Создание корабля с кошельком и пустым трюмом"""
        USER_SHIPS[chat_id] = {
            "name": name,
            "status": "docked",
            "current_city_id": "gorn", # Изначально стоим в Горне
            "x": START_PORT["x"],
            "y": START_PORT["y"],
            "target_x": None,
            "target_y": None,
            "fuel": 100.0,
            "max_fuel": 100.0,
            "speed": 15.0,
            "fuel_consumption": 0.5,
            "credits": 1000,           # Стартовый капитал Адмирала
            "max_cargo_weight": 500,   # Лимит грузоподъемности (500 кг)
            "cargo": {"coal": 0, "iron_ore": 0, "steel": 0, "tools": 0} # Пустой трюм
        }

    @staticmethod
    def calculate_distance(x1, y1, x2, y2):
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    @staticmethod
    def get_cargo_weight(ship):
        """Вычисление общего веса груза в трюме"""
        total_weight = 0
        for resource, amount in ship["cargo"].items():
            total_weight += amount * RESOURCE_WEIGHTS.get(resource, 0)
        return total_weight

    @classmethod
    def update_world_production(cls):
        """Пассивное производство в городах. Вызывается каждый тик игры"""
        # 1. Шахта в Горне добывает ресурсы
        gorn = CITIES["gorn"]
        gorn["stockpile"]["coal"] += int(2 * gorn["production_speed"])
        gorn["stockpile"]["iron_ore"] += int(1 * gorn["production_speed"])

        # 2. Завод в Пар-Сити плавит сталь из угля и руды
        pc = CITIES["steam_city"]
        # Для 1 стали нужно 2 угля и 2 руды
        if pc["stockpile"]["coal"] >= 2 and pc["stockpile"]["iron_ore"] >= 2:
            pc["stockpile"]["coal"] -= 2
            pc["stockpile"]["iron_ore"] -= 2
            pc["stockpile"]["steel"] += int(1 * pc["production_speed"])

    @classmethod
    def process_flight_tick(cls, chat_id):
        ship = USER_SHIPS.get(chat_id)
        if not ship or ship["status"] != "in_flight":
            return "not_moving"

        if ship["target_x"] is None or ship["target_y"] is None:
            return "error"

        distance = cls.calculate_distance(ship["x"], ship["y"], ship["target_x"], ship["target_y"])

        if ship["fuel"] <= 0:
            ship["status"] = "wrecked"
            return "no_fuel_crash"

        if distance <= ship["speed"]:
            ship["x"] = ship["target_x"]
            ship["y"] = ship["target_y"]
            ship["status"] = "docked"
            ship["target_x"] = None
            ship["target_y"] = None
            return "arrived"

        dx = ship["target_x"] - ship["x"]
        dy = ship["target_y"] - ship["y"]
        ratio = ship["speed"] / distance
        
        ship["x"] += dx * ratio
        ship["y"] += dy * ratio

        # Если корабль загружен, он тратит чуть больше топлива (эффект веса)
        weight_factor = 1.0 + (cls.get_cargo_weight(ship) / ship["max_cargo_weight"]) * 0.5
        ship["fuel"] = max(0.0, ship["fuel"] - (ship["fuel_consumption"] * weight_factor))
        return "moving"
