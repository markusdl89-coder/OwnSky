class CrewMember:
    def __init__(self, name, role, sociotype, extraversion, ethics):
        self.name = name
        self.role = role
        self.sociotype = sociotype
        self.is_extravert = extraversion
        self.is_ethician = ethics
        self.base_stress = 0.0
        self.traits = []

    @property
    def stress(self):
        return self.base_stress

    @stress.setter
    def stress(self, value):
        self.base_stress = max(0.0, min(100.0, value))

    @property
    def work_efficiency(self):
        stress_penalty = (self.stress / 10.0) * 5.0
        efficiency = 100.0 - stress_penalty
        for trait in self.traits:
            efficiency += trait.work_modifier
        return max(0.0, efficiency)

    @property
    def social_friction(self):
        friction = 1.0
        for trait in self.traits:
            friction *= trait.social_modifier
        return friction

    def add_trait(self, trait):
        for existing_trait in self.traits:
            if existing_trait.name == trait.name:
                return
        self.traits.append(trait)


class Trait:
    def __init__(self, name, description, work_modifier, social_modifier):
        self.name = name
        self.description = description
        self.work_modifier = work_modifier
        self.social_modifier = social_modifier


class StressCalculator:
    @staticmethod
    def calculate_port_tick(crew_list):
        for member in crew_list:
            recovery = 1.5 if not member.is_extravert else 1.0
            member.stress -= recovery

    @staticmethod
    def calculate_flight_tick(crew_list):
        member_dict = {m.role: m for m in crew_list}
        hamlet = member_dict.get("Капитан")
        dostoevsky = member_dict.get("Инженер")
        maxim = member_dict.get("Второй пилот")

        for member in crew_list:
            base_growth = 0.5 if not member.is_extravert else 0.2
            member.stress += base_growth

        if not all([hamlet, dostoevsky, maxim]):
            return

        dostoevsky_friction_modifier = 1.0
        hamlet_friction_modifier = 1.0
        maxim_friction_modifier = 1.0

        for trait in dostoevsky.traits:
            if trait.name == "Вселенская Обида":
                dostoevsky.stress += 0.2

        for trait in maxim.traits:
            if trait.name == "Каменные Нервы":
                maxim_friction_modifier = 0.6

        if hamlet.stress >= 70:
            for trait in hamlet.traits:
                if trait.name == "Идейный Вдохновитель":
                    pass

        dostoevsky.stress += (1.2 * maxim.social_friction) * maxim_friction_modifier
        dostoevsky.stress += (0.8 * hamlet.social_friction) * dostoevsky_friction_modifier
        maxim.stress += (0.4 * hamlet.social_friction) * maxim_friction_modifier
        hamlet.stress += 0.3 * dostoevsky.social_friction
        dostoevsky.stress += 0.3 * hamlet.social_friction
