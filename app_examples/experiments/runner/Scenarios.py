import random

class BaseScenario:
    def name(self):
        return self.__class__.__name__

    def get_observation(self, t, value, source_id):
        return value

    def get_health(self, t, current_health, source_id):
        return current_health
    
    def get_belonging(self, t, current_belonging, source_id):
        return current_belonging
    

    
class StableScenario(BaseScenario):
    def get_observation(self, t, value, source_id):
        return value

    def get_health(self, t, current_health, source_id):
        return "ideal"
    


class LifecycleEvaluationScenario(BaseScenario):
    def __init__(self, seed=42):
        self.random = random.Random(seed)
        self.health_schedule = [
            (0, "ideal"),
            (100, "erroneous"),
            (200, "malfunctioning"),
            (375, "degraded"),
            (400, "failed"),
            (440, "ideal"),
        ]

        self.drop_map = {
            "ideal": 0.0,
            "defective": 0.02,
            "faulty": 0.05,
            "erroneous": 0.45,
            "malfunctioning": 0.55,
            "degraded": 0.6,
            "failed": 1.0,
        }

    def name(self):
        return "LifecycleEvaluation"

    def get_health(self, t, current_health, source_id):
        health = "ideal"

        for ts, h in self.health_schedule:
            if t >= ts:
                health = h

        return health

    def get_belonging(self, t, current_sub, source_id):
        # Initial onboarding
        if t < 5:
            return "disengaged"
        elif t < 10:
            return "prepared"
        elif t < 20:
            return "available"

        # After onboarding → always attempt participation
        return "participating"


    def get_observation(self, t, value, source_id):
        health = self.get_health(t, None, source_id)
        drop_prob = self.drop_map.get(health, 0.0)
        if self.random.random() < drop_prob:
            return None
        return value
