class CampManager:
    """
    Менеджер Тайного Лагеря дирижабля OWNSKY.
    Управляет подпольным производством, притоком беженцев и симулирует два древа развития (Стелс/Промышленность).
    """
    def __init__(self):
        self.suitability = 50.0          # Общая пригодность лагеря (0 - 100%)
        self.refugees = 5                # Всего беженцев (доступное население)
        self.assigned_workers = 0        # Назначено рабочих в Цех Инструментов
        
        # Внутренний склад лагеря (Сталь привозит дирижабль, Инструменты производятся)
        self.stockpile = {
            "steel": 10.0,
            "tools": 0.0
        }
        
        # Переключатель древа развития для демонстрации MVP:
        # "none" - не выбрано, "surface" - Промышленный сектор, "underground" - Подземный бункер
        self.development_path = "none"

    def add_worker(self):
        """Назначает свободного беженца в цех."""
        if self.assigned_workers < self.refugees:
            self.assigned_workers += 1
            return True
        return False

    def remove_worker(self):
        """Забирает рабочего из цеха обратно в резерв."""
        if self.assigned_workers > 0:
            self.assigned_workers -= 1
            return True
        return False

    def change_path(self, path_name):
        """Переключает древо развития для демонстрации на собеседовании."""
        if path_name in ["surface", "underground"]:
            self.development_path = path_name
            return True
        return False

    def update_camp_tick(self):
        """
        Один системный тик лагеря (вызывается из главного игрового цикла).
        Перерабатывает Сталь в Инструменты, регулирует пригодность и приток беженцев.
        """
        # 1. Логика производства: 1 рабочий перерабатывает 2 Стали в 1 Инструмент за тик
        if self.assigned_workers > 0 and self.stockpile["steel"] >= (self.assigned_workers * 2):
            consumption = self.assigned_workers * 2
            production = self.assigned_workers * 1
            
            # Модификаторы эффективности в зависимости от древа развития
            if self.development_path == "underground":
                production *= 0.5 # Подземная мастерская работает на 50% слабее
                
            self.stockpile["steel"] -= consumption
            self.stockpile["tools"] += production
            
            # Успешное производство поднимает пригодность лагеря
            self.suitability = min(100.0, self.suitability + 0.5)
        else:
            # Если производство простаивает или нет сырья, пригодность плавно падает
            self.suitability = max(0.0, self.suitability - 0.2)

        # 2. Логика притока беженцев: зависит от пригодности и выбранного древа
        if self.suitability > 60.0:
            # Шанс прихода нового беженца (в подземный бункер люди идут неохотно)
            growth_modifier = 0.05 if self.development_path == "underground" else 0.1
            self.refugees += growth_modifier


class CampViewer:
    """Визуальный модуль Тайного Лагеря. Формирует текстовые экраны и приписки о стелс-механиках."""
    
    @staticmethod
    def _generate_bar(current_value, max_value=100.0):
        total_blocks = 10
        filled_blocks = int((current_value / max_value) * total_blocks)
        filled_blocks = max(0, min(total_blocks, filled_blocks))
        empty_blocks = total_blocks - filled_blocks
        return f"[{'█' * filled_blocks}{'░' * empty_blocks}]"

    @classmethod
    def get_camp_report(cls, camp_manager):
        """Формирует главный текстовый экран лагеря со всеми пояснениями концепции стелса."""
        bar = cls._generate_bar(camp_manager.suitability)
        free_workers = int(camp_manager.refugees) - camp_manager.assigned_workers
        
        # Определяем текстовый статус древа развития
        path_text = "❌ Не выбрано (Доступны варианты развития ниже)"
        stealth_status = "🟢 ПОЛНАЯ МАСКИРОВКА (Начальный лагерь незаметен для радаров)"
        
        if camp_manager.development_path == "surface":
            path_text = "🏭 ПРОМЫШЛЕННЫЙ СЕКТОР (Максимум ресурсов, высокий приток людей)"
            stealth_status = "⚠️ ВЫСОКАЯУГРОЗА (База видна на картах других игроков. Риск пиратских налетов!)"
        elif camp_manager.development_path == "underground":
            path_text = "🧱 ПОДЗЕМНЫЙ БУНКЕР (Ограниченное производство, слабый приток людей)"
            stealth_status = "🛡️ АБСОЛЮТНЫЙ СТЕЛС (Обнаружение возможно только сканированием георадаром спец-класса)"

        text = (
            "⛺ **ТАЙНЫЙ ЛАГЕРЬ АДМИРАЛА (ПОДПОЛЬНОЕ ПРОИЗВОДСТВО)**\n"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"📈 **Пригодность лагеря:** `{bar}` **{int(camp_manager.suitability)}%**\n"
            f"👥 **Население:** `{int(camp_manager.refugees)}` выживших (`{camp_manager.assigned_workers}` в цеху, `{free_workers}` в резерве)\n"
            f"👁‍🗨 **Статус маскировки:** {stealth_status}\n\n"
            
            f"🛠 **ЦЕХ ИНСТРУМЕНТОВ:**\n"
            f" ├ Статус: {'🟢 РАБОТАЕТ' if camp_manager.assigned_workers > 0 and camp_manager.stockpile['steel'] >= 2 else '🔴 ПРОСТОЙ'}\n"
            f" └ Рецепт: `2 Стали ➔ 1 Инструмент` (Зависит от числа рабочих)\n\n"
            
            f"📦 **СКЛАД ЛАГЕРЯ:**\n"
            f" ├ 📦 Сталь (Сырьё): `{int(camp_manager.stockpile['steel'])} ед.`\n"
            f" └ 🛠 Инструменты (Итог): `{int(camp_manager.stockpile['tools'])} ед.`\n\n"
            
            f"📐 **ТЕКУЩЕЕ ДРЕВО РАЗВИТИЯ БАЗЫ:**\n"
            f" {path_text}\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"📢 **СПРАВКА MVP (ДИЛЕМА СКРЫТНОСТИ):**\n"
            f" В полной версии игры вы сможете развернуть эту точку в любом месте карты. "
            f"Развитие на поверхности (🏭) откроет полноценный город, но привлечет пиратов. "
            f"Заглубление под землю (🧱) защитит от грабежей, но потребует георадары для поиска ваших пустот."
        )
        return text
