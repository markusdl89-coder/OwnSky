import math
from config import USER_SHIPS, START_PORT

class GameCore:
    @staticmethod
    def init_ship(chat_id, name="Стартовый Цеппелин"):
        USER_SHIPS[chat_id] = {
            "name": name,
            "status": "docked",
            "x": START_PORT["x"],
            "y": START_PORT["y"],
            "target_x": None,
            "target_y": None,
            "fuel": 100.0,
            "max_fuel": 100.0,
            "speed": 10.0,
            "fuel_consumption": 0.5
        }

    @staticmethod
    def calculate_distance(x1, y1, x2, y2):
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

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

        ship["fuel"] = max(0.0, ship["fuel"] - ship["fuel_consumption"])
        return "moving"

