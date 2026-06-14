### 🗃️ ПАСПОРТ МОДУЛЯ: database.py (Слой данных)
* **Роль в игре:** Переводчик между ботом (на Render) и базой данных (на Neon).
* **Связь с базой:** Библиотека `pg8000`, использует переменную среды `DATABASE_URL`.
* **Функции (API модуля):** `get_player_data(user_id)`, `update_inventory(...)`, `register_new_player(user_id, username)`.

### 📊 СХЕМА СТРУКТУРЫ ТАБЛИЦ В NEON DB
1. **Таблица `players` (Капитаны)**
   * `user_id` (BIGINT, PRIMARY KEY) — Telegram ID игрока.
   * `username` (TEXT) — Игровой никнейм.
   * `credits` (INT, DEFAULT 5000) — Стартовый баланс.
   * `ship_type` (TEXT, DEFAULT 'Старатель') — Начальный корабль.
   * `fuel` (INT, 100) | `x`, `y` (INT, 0) | `status` (TEXT, 'В порту').
2. **Таблица `locations` (Города-порты)**
   * Порты: `'Горн'` (0, 0), `'Пар-Сити'` (400, 500), `'Ветроград'` (-200, 300).
3. **Таблица `inventories` (Трюмы и Магазины)**
   * Поля: `owner_type` ('player' или 'location'), `owner_id`, `item_name`, `quantity`.
4. **🚀 ЗАМОРОЖЕННЫЙ СЛОЙ: Автономные Полетные Планы флота**
   * **Таблица `flight_plans`** — Инструкции («если-то») для торговли в фоновом режиме.
   * **Таблицы `routes` и `route_points`** — Трассы между городами.
5. **Таблица `player_journals`** — Системный лог действий игрока.
