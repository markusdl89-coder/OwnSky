from crew_core import CrewMember, Trait, StressCalculator

class CrewManager:
    def __init__(self):
        self.officers = []
        self._spawn_mvp_crew()

    def _spawn_mvp_crew(self):
        hamlet = CrewMember("Гамлет", "Капитан", "EIE", extraversion=True, ethics=True)
        hamlet.add_trait(Trait("Король Драмы", "Раздувает трагедию из любой мелочи", work_modifier=0.0, social_modifier=1.3))
        hamlet.add_trait(Trait("Идейный Вдохновитель", "Пафосные речи мотивируют в критический момент", work_modifier=10.0, social_modifier=1.0))

        dostoevsky = CrewMember("Достоевский", "Инженер", "EII", extraversion=False, ethics=True)
        dostoevsky.add_trait(Trait("Вселенская Обида", "Остро переживает критику и давление", work_modifier=0.0, social_modifier=1.0))
        dostoevsky.add_trait(Trait("Тихий Гений", "С головой уходит в работу, спасаясь от криков", work_modifier=15.0, social_modifier=0.9))

        maxim = CrewMember("Максим Горький", "Второй пилот", "LSI", extraversion=False, ethics=False)
        maxim.add_trait(Trait("Душный Перфекционист", "Пилит команду за нарушение регламента", work_modifier=5.0, social_modifier=1.2))
        maxim.add_trait(Trait("Каменные Нервы", "Игнорирует чужую панику и эмоции", work_modifier=0.0, social_modifier=0.8))

        self.officers = [hamlet, dostoevsky, maxim]

    def update_tick(self, is_in_flight):
        if is_in_flight:
            StressCalculator.calculate_flight_tick(self.officers)
        else:
            StressCalculator.calculate_port_tick(self.officers)

    def get_all_officers(self):
        return self.officers

    def get_officer_by_role(self, role):
        for officer in self.officers:
            if officer.role == role:
                return officer
        return None
