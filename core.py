from config import FEATURE_TOGGLES, USER_SHIPS

class GameCore:
    @staticmethod
    def is_module_active(module_name: str) -> bool:
        return FEATURE_TOGGLES.get(module_name, False)

    @staticmethod
    def init_player_ship(user_id: int):
        USER_SHIPS[user_id] = {
            "name": "Цеппелин-1",
            "altitude": 100,
            "speed": 0,
            "hull": 100,
            "gas_leak": False
        }

    @staticmethod
    def get_ship(user_id: int) -> dict:
        return USER_SHIPS.get(user_id)
