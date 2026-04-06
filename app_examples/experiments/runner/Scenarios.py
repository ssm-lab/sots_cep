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
    


class ProgressiveDegradationScenario(BaseScenario):
    def __init__(self, seed=42):
        self.random = random.Random(seed)

        self.health_schedule = [
            (0, "ideal"),
            (100, "defective"),
            (200, "faulty"),
            (300, "erroneous"),
            (350, "malfunctioning"),
            (400, "erroneous"),
            (415, "faulty"),
            (445, "defective"),
            (465, "ideal"),
        ]

        self.belonging_schedule = [
            (0, "disengaged"),
            (5, "prepared"),
            (10, "available"),     # passive
            (20, "full_role"),     # active
        ]

        self.drop_map = {
            "ideal": 0.0,
            "defective": 0.025,
            "faulty": 0.05,
            "erroneous": 0.25,
            "malfunctioning": 0.35,
        }

    def name(self):
        return "ProgressiveDegradation"

    def get_health(self, t, current_health, source_id):

        health = "ideal"

        for ts, h in self.health_schedule:
            if t >= ts:
                health = h

        return health
    
    def get_belonging(self, t, current_sub, source_id):
        sub = "disengaged"

        for ts, s in self.belonging_schedule:
            if t >= ts:
                sub = s

        return sub

    def get_observation(self, t, value, source_id):
        health = self.get_health(t, None, source_id)
        drop_prob = self.drop_map.get(health, 0.0)

        if self.random.random() < drop_prob:
            return None

        return value




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













# class ExperimentScenario(BaseScenario):
#     def __init__(self, seed=42):
#         self.random = random.Random(seed)

#         self.drop_map = {
#             "ideal": 0.0,
#             "erroneous": 0.5,
#             "malfunctioning": 0.8,
#             "failed": 1.0,
#         }

#     def name(self):
#         return "ExperimentScenario"

#     # -----------------------------
#     # HEALTH (EXPLICIT PHASES)
#     # -----------------------------
#     def get_health(self, t, current_health, source_id):
#         if source_id == "signal-1":
#             if t < 100:
#                 return "ideal"
#             elif t < 350:
#                 return "erroneous"
#             else:
#                 return "ideal"

#         elif source_id == "signal-2":
#             if t < 100:
#                 return "ideal"
#             elif t < 350:
#                 return "malfunctioning"
#             else:
#                 return "ideal"

#         elif source_id == "signal-3":
#             if t < 100:
#                 return "ideal"
#             elif t < 200:
#                 return "faulty"
#             elif t < 350:
#                 return "erroneous"
#             else:
#                 return "ideal"

#     # -----------------------------
#     # BELONGING
#     # -----------------------------
#     def get_belonging(self, t, current_sub, source_id):

#         # Initial ramp-up
#         if t < 5:
#             return "disengaged"
#         elif t < 10:
#             return "prepared"
#         elif t < 20:
#             return "available"

#         # Always try to participate after
#         if current_sub not in ["full_role", "restricted_role"]:
#             return "participating"

#         return current_sub

#     # -----------------------------
#     # OBSERVATION DROPS
#     # -----------------------------
#     def get_observation(self, t, value, source_id):
#         health = self.get_health(t, None, source_id)
#         drop_prob = self.drop_map.get(health, 0.0)

#         if self.random.random() < drop_prob:
#             return None

#         return value

    
# class PeriodicDropScenario(BaseScenario):
#     def __init__(self, drop_every=5, offset=0):
#         self.drop_every = drop_every
#         self.offset = offset

#     def get_observation(self, t, value, source_id):
#         if (t + self.offset) % self.drop_every == 0:
#             return None 
#         return value
    
# class RandomDropScenario(BaseScenario):

#     def __init__(self, drop_prob=0.2, seed=42):
#         self.drop_prob = drop_prob
#         self.random = random.Random(seed)

#     def name(self):
#         return f"RandomDrop_p{self.drop_prob}"

#     def get_observation(self, t, value, source_id):
#         if self.random.random() < self.drop_prob:
#             return None
#         return value