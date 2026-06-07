class AirshipBlueprint:
    """
    Класс чертежа дирижабля OWNSKY.
    Управляет состоянием 5 отсеков вместо абстрактной полоски ХП.
    """
    def __init__(self):
        # Базовое состояние отсеков: True - цел (зеленый), False - пробит (красный)
        self.compartments = {
            "Баллон": True,
            "Мостик": True,
            "Орудийная": True,
            "Машинный": True,
            "Трюм": True
        }
        # Внутренние критические узлы в каждом отсеке для симуляции "кубика повреждений"
        self.sub_systems = {
            "Машинный": ["Паровой котел", "Топливная магистраль"],
            "Баллон": ["Левый баллонет", "Клапан давления"],
            "Мостик": ["Штурвальная колонка", "Приборы навигации"],
            "Орудийная": ["Затвор главного калибра", "Снарядный ящик"],
            "Трюм": ["Крепления карго-отсека", "Радиорубка"]
        }
        self.destroyed_nodes = [] # Список уничтоженных критических узлов

    def apply_damage(self, compartment_name, node_index=0):
        """Пробивает отсек и уничтожает в нем конкретный важный узел."""
        if compartment_name in self.compartments:
            self.compartments[compartment_name] = False # Отсек переходит в статус "Пробит"
            
            # Уничтожаем узел по индексу из списка подсистем
            nodes = self.sub_systems.get(compartment_name, [])
            if 0 <= node_index < len(nodes):
                target_node = nodes[node_index]
                if target_node not in self.destroyed_nodes:
                    self.destroyed_nodes.append(target_node)

    def get_ascii_blueprint(self):
        """Генерирует визуальный текстовый чертеж состояния корабля для Telegram."""
        def get_status_icon(name):
            return "🟢 ЦЕЛ" if self.compartments[name] else "🔥 ПРОБИТИЕ!"

        blueprint_text = (
            "📊 **СХЕМА ПОВРЕЖДЕНИЙ ДИРИЖАБЛЯ:**\n"
            f" `🎈 [ ГАЗОВЫЙ БАЛЛОН ]` ── {get_status_icon('Баллон')}\n"
            f" `⚓️ [ МОСТИК КАПИТАНА ]` ── {get_status_icon('Мостик')}\n"
            f" `💥 [ ОРУДИЙНАЯ ПАЛУБА ]` ── {get_status_icon('Орудийная')}\n"
            f" `⚙️ [ МАШИННЫЙ ОТСЕК ]`  ── {get_status_icon('Машинный')}\n"
            f" `📦 [ ГРУЗОВОЙ ТРЮМ ]`   ── {get_status_icon('Трюм')}\n\n"
        )
        
        if self.destroyed_nodes:
            blueprint_text += "⚠️ **КРИТИЧЕСКИЕ ПОВРЕЖДЕНИЯ УЗЛОВ:**\n"
            for node in self.destroyed_nodes:
                blueprint_text += f" ❌ Уничтожен агрегат: `{node}`\n"
        else:
            blueprint_text += "✅ _Все внутренние агрегаты функционируют штатно._"
            
        return blueprint_text


class CombatSimulator:
    """
    Пошаговый диспетчер демонстрационного боя для MVP.
    Проводит игрока по срежиссированным рельсам сражения, связывая баллистику и реплики экипажа.
    """
    def __init__(self, dialogue_manager):
        self.dialogue_manager = dialogue_manager
        self.blueprint = AirshipBlueprint()
        self.current_turn = 0
        self.is_combat_finished = False

    def next_turn(self):
        """Продвигает бой на один шаг вперед и возвращает текстовый лог происходящего."""
        if self.is_combat_finished:
            return "⚔️ _Симуляция боя завершена. Дирижабль возвращается на базу._"

        self.current_turn += 1
        turn_log = f"⚔️ **СИМУЛЯЦИЯ БОЯ: ХОД {self.current_turn}**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"

        if self.current_turn == 1:
            # Ход 1: Сближение и штормовой фронт
            turn_log += "📍 **Дистанция:** `1800 м` | 🔼 **Высота:** `НА ОДНОМ УРОВНЕ`\n\n"
            turn_log += "💨 _Внезапный штормовой порыв бьет по корпусу дирижабля!_\n\n"
            # Вызываем соционическую реакцию на шторм из нашего третьего файла
            crew_reaction = self.dialogue_manager.process_event_reaction("STORM_START")
            turn_log += f"{crew_reaction}\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            turn_log += self.blueprint.get_ascii_blueprint()

        elif self.current_turn == 2:
            # Ход 2: Вражеский залп и точечное пробитие брони с броском "кубика"
            turn_log += "📍 **Дистанция:** `1200 м` | 🔼 **Высота:** `ВЫШЕ ВРАГА (+15% к точности)`\n\n"
            turn_log += "💥 **Вражеский крейсер открыл огонь прямой наводкой!**\n"
            turn_log += "🛑 Снаряд пробивает бронелист! Осколки влетают внутрь конструкции!\n\n"
            
            # Баллистика: ломаем Машинный отсек и кубик решает уничтожить "Паровой котел" (индекс 0)
            self.blueprint.apply_damage("Машинный", node_index=0)
            
            # Вызываем соционическую реакцию на пробитие отсека
            crew_reaction = self.dialogue_manager.process_event_reaction("SECTOR_BREACH")
            turn_log += f"{crew_reaction}\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            turn_log += self.blueprint.get_ascii_blueprint()

        elif self.current_turn == 3:
            # Ход 3: Ответный победный залп и завершение демки
            turn_log += "📍 **Дистанция:** `900 м` | 🔼 **Высота:** `ВЫШЕ ВРАГА`\n\n"
            turn_log += "🔥 **Капитан Франческа отдает приказ на подавление!**\n"
            turn_log += "🎯 Наш главный калибр разносит мостик вражеского крейсера! Нападающий отступает в облака!\n\n"
            turn_log += "🎉 **ПОБЕДА!** Враг отступил. Дирижабль ложится на обратный курс к Тайному Лагерю.\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            turn_log += self.blueprint.get_ascii_blueprint()
            self.is_combat_finished = True

        return turn_log
