class CrewViewer:
    """
    Визуальный модуль для отображения экипажа в кабинете Адмирала.
    Формирует текстовые интерфейсы для Telegram-бота с заделом на масштабирование флота.
    """
    
    @staticmethod
    def _generate_bar(current_value, max_value=100.0):
        """Внутренний метод для сборки графической текстовой шкалы из кубиков."""
        total_blocks = 10
        # Вычисляем, сколько кубиков из 10 должны быть заполнены
        filled_blocks = int((current_value / max_value) * total_blocks)
        filled_blocks = max(0, min(total_blocks, filled_blocks))
        empty_blocks = total_blocks - filled_blocks
        
        return f"[{'█' * filled_blocks}{'░' * empty_blocks}]"

    @classmethod
    def get_fleet_menu(cls):
        """Уровень 1: Главное меню 'Флот'. Симуляция масштабирования на эскадру."""
        text = (
            "🛸 **УПРАВЛЕНИЕ ФЛОТОМ АДМИРАЛА**\n"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            "*Выберите боевую единицу для инспекции:*\n\n"
            "🔘 **[Дирижабль «Ownsky»]** — *В строю (Экипаж: 3/3)*\n\n"
            "📢 _Примечание: Для расширения флота и найма новых офицеров постройте Таверну в Тайном Лагере._"
        )
        return text

    @classmethod
    def get_bridge_menu(cls, crew_manager):
        """Уровень 2: Мостик Дирижабля. Сводка по состоянию всей команды."""
        officers = crew_manager.get_all_officers()
        
        text = (
            "⚓️ **БОЕВОЙ ДИРИЖАБЛЬ «OWNSKY»**\n"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            "*Текущий статус экипажа:*\n\n"
        )
        
        for officer in officers:
            bar = cls._generate_bar(officer.stress)
            text += (
                f"🔸 **[{officer.role}] {officer.name}**\n"
                f"Стресс: `{bar}` **{int(officer.stress)}%** | "
                f"Работоспособность: **{int(officer.work_efficiency)}%**\n\n"
            )
            
        text += "*(Выберите офицера в меню бота, чтобы открыть личное досье и отдать директивы)*"
        return text

    @classmethod
    def get_officer_dossier(cls, officer):
        """Уровень 3: Личное досье офицера с заглушками будущих механик лагеря."""
        if not officer:
            return "Ошибка: Офицер не найден."
            
        bar = cls._generate_bar(officer.stress)
        
        text = (
            f"🗂 **ЛИЧНОЕ ДЕЛО: {officer.role} {officer.name}**\n"
            f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            f"Соционический тип: **{officer.sociotype}**\n\n"
            f"📉 **Психический стресс:** `{bar}` **{int(officer.stress)}%**\n"
            f"⚙️ **Текущая эффективность:** **{int(officer.work_efficiency)}%**\n\n"
            f"🧠 **Активные черты характера:**\n"
        )
        
        if officer.traits:
            for trait in officer.traits:
                text += f"• `{trait.name}` — _{trait.description}_\n"
        else:
            text += "• _Черты характера отсутствуют_\n"
            
        text += (
            "\n📑 **ДОСТУПНЫЕ ДИРЕКТИВЫ АДМИРАЛА:**\n"
            "❌ `[Списать в Портовый Лазарет]` — _Заблокировано в вылете (Требуется: База и 100 кредитов)_\n"
            "❌ `[Назначить комендантом Тайного Лагеря]` — _Офицер занят на боевом посту до конца сессии_"
        )
        return text
