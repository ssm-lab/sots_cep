import logging
import time
from ...state_charts.yakindu.timer.timer_service import TimerService

class ConstituentController:

    HEALTH_ORDER = [
        "ideal",
        "defective",
        "faulty",
        "erroneous",
        "malfunctioning",
        "degraded",
        "failed"
    ]

    HEALTH_STATE_MAP = {
        "constituent_lifecycle_orthogonal_states_health_ideal": "ideal",
        "constituent_lifecycle_orthogonal_states_health_defective": "defective",
        "constituent_lifecycle_orthogonal_states_health_faulty": "faulty",
        "constituent_lifecycle_orthogonal_states_health_erroneous": "erroneous",
        "constituent_lifecycle_orthogonal_states_health_malfunctioning": "malfunctioning",
        "constituent_lifecycle_orthogonal_states_health_degraded": "degraded",
        "constituent_lifecycle_orthogonal_states_health_failed": "failed",
    }

    BELONGING_STATE_MAP = {
        "constituent_lifecycle_orthogonal_states_belonging_passive_region0negotiating": "negotiating",
        "constituent_lifecycle_orthogonal_states_belonging_passive_region0avaliable": "available",
        "constituent_lifecycle_orthogonal_states_belonging_active_region0pending_entry": "pending_entry",
        "constituent_lifecycle_orthogonal_states_belonging_active_region0participating_region0full_role": "full_role",
        "constituent_lifecycle_orthogonal_states_belonging_active_region0participating_region0restricted_role": "restricted_role",
        "constituent_lifecycle_orthogonal_states_belonging_active_region0pending_exit": "pending_exit",
        "constituent_lifecycle_orthogonal_states_belonging_disengaged": "disengaged",
        "constituent_lifecycle_orthogonal_states_belonging_prepared": "prepared",
    }

    def __init__(self, statechart_cls, constituent_id, lifecycle_logger=None):

        self.id = constituent_id
        self.sm = statechart_cls()

        self.timer_service = TimerService()
        self.sm.timer_service = self.timer_service
        self.lifecycle_logger = lifecycle_logger

        self.sm.enter()


        self.announce_stream = self.sm.announce_observable

        self.emit_observed = self.sm.emit_observed_observable
        self.emit_validated = self.sm.emit_validated_observable
        self.enable_compensation = self.sm.compensation_enabled_observable

        self.belonging_changed = self.sm.belonging_changed_observable
        self.health_changed = self.sm.health_changed_observable

        self.state = None
        self.update_snapshot()

    # change state
    def _raise(self, event, goal=None):
        before = self.state_snapshot()
        from_state = f"{before['belonging_main']}/{before['belonging_sub']}"

        transition = event
        getattr(self.sm, transition)()
        self.sm.run_cycle()

        self.update_snapshot()
        after = self.state_snapshot()

        final_state = f"{after['belonging_main']}/{after['belonging_sub']}"
        after_health = after["health_main"]

        result = "made" if from_state != final_state else "no_change"
        goal_match = (goal == final_state)

        ts = time.time()

        logging.info(
            f"[LIFECYCLE] {self.id} "
            f"{from_state} --({transition})--> {final_state} "
            f"[goal={goal}, result={result}, goal_match={goal_match}]"
        )

        # log state change
        if self.lifecycle_logger:
            self.lifecycle_logger.consume_event({
                "type": "lifecycle_decision",
                "ts": ts,
                "constituent_id": self.id,
                "from_state": from_state,
                "target_state": goal,
                "transition": transition,
                "result": result,
                "final_state": final_state,
                "health": after_health,
                "goal_match": goal_match,
                "trigger_event": transition,
            })
        

    def health_name(self):

        sm = self.sm
        state_vector = sm._Statechart__state_vector
        state = state_vector[1]
        S = sm.State

        for attr, name in self.HEALTH_STATE_MAP.items():
            if state == getattr(S, attr):
                return name

        return "unknown"

    def belonging_substate(self):

        sm = self.sm
        state_vector = sm._Statechart__state_vector
        state = state_vector[0]
        S = sm.State

        for attr, name in self.BELONGING_STATE_MAP.items():
            if state == getattr(S, attr):
                return name

        return "unknown"


    def belonging_main(self):
        sub = self.belonging_substate()

        if sub in {"negotiating", "available"}:
            return "passive"

        if sub in {"pending_entry", "full_role", "restricted_role", "pending_exit"}:
            return "active"

        return sub


    def update_snapshot(self):
        self.state = {
            "id": self.id,
            "belonging_main": self.belonging_main(),
            "belonging_sub": self.belonging_substate(),
            "health_main": self.health_name(),
        }

    def state_snapshot(self):
        return self.state


    # Belonging events
    def prepare(self, goal=None): self._raise("raise_prepare_for_so_s", goal=goal)
    def disengage(self, goal=None): self._raise("raise_disengage_from_so_s", goal=goal)
    def join_sos(self, goal=None): self._raise("raise_join_so_s", goal=goal)
    def leave_sos(self, goal=None): self._raise("raise_leave_so_s", goal=goal)

    def join_invitation(self, goal=None): self._raise("raise_join_invitation", goal=goal)
    def join_request(self, goal=None): self._raise("raise_join_request", goal=goal)
    def admission_rejected(self, goal=None): self._raise("raise_admission_rejected", goal=goal)
    def exit_denied(self, goal=None): self._raise("raise_exit_denied", goal=goal)
    def join_constellation(self, goal=None): self._raise("raise_join_constellation", goal=goal)
    def constellation_stable(self, goal=None): self._raise("raise_constellation_stable", goal=goal)
    def leave_request(self, goal=None): self._raise("raise_leave_request", goal=goal)
    def leave_constellation(self, goal=None): self._raise("raise_leave_constellation", goal=goal)

    def uncertainty_threshold_exceeded(self):
        self._raise("raise_uncertainty_threshold_exceeded")


    # Health events
    def degrade(self, goal=None):
        self._raise("raise_degrade", goal=goal)

    def improve(self, goal=None):
        self._raise("raise_improve", goal=goal)

    def full_recovery(self, goal=None):
        self._raise("raise_full_recovery", goal=goal)


    # Navigation
    def ensure_health(self, goal, max_steps=10):
        if goal not in self.HEALTH_ORDER:
            raise ValueError(f"Unknown health state: {goal}")

        for _ in range(max_steps):

            current = self.health_name()

            if current == goal:
                return True

            if goal == "ideal":
                self.full_recovery(goal=goal)
                continue

            current_idx = self.HEALTH_ORDER.index(current)
            goal_idx = self.HEALTH_ORDER.index(goal)

            if goal_idx > current_idx:
                self.degrade(goal=goal)
            else:
                self.improve(goal=goal)

        raise RuntimeError(f"Failed to reach health state '{goal}'")

    def ensure_ideal(self): return self.ensure_health("ideal")
    def ensure_defective(self): return self.ensure_health("defective")
    def ensure_faulty(self): return self.ensure_health("faulty")
    def ensure_erroneous(self): return self.ensure_health("erroneous")
    def ensure_malfunctioning(self): return self.ensure_health("malfunctioning")
    def ensure_degraded(self): return self.ensure_health("degraded")
    def ensure_failed(self): return self.ensure_health("failed")


    BELONGING_POLICY = {
        "disengaged": {
            "disengaged": None,
            "prepared": "disengage",

            "available": "leave_sos",
            "negotiating": "leave_sos",

            "pending_entry": "leave_request",
            "full_role": "leave_request",
            "restricted_role": "leave_request",
            "pending_exit": "leave_constellation",
        },
        "prepared": {
            "disengaged": "prepare",
            "prepared": None,

            "available": "leave_sos",
            "negotiating": "leave_sos",

            "pending_entry": "leave_request",
            "full_role": "leave_request",
            "restricted_role": "leave_request",
            "pending_exit": "leave_constellation",
        },
        "available": {
            "prepared": "join_sos",
            "disengaged": "prepare",

            "available": None,
            "negotiating": "admission_rejected",

            "pending_entry": "leave_request",
            "full_role": "leave_request",
            "restricted_role": "leave_request",
            "pending_exit": "leave_constellation",
        },
        "negotiating": {
            "prepared": "join_sos",
            "disengaged": "prepare",

            "available": "join_invitation",
            "negotiating": None,

            "pending_entry": "leave_request",
            "full_role": "leave_request",
            "restricted_role": "leave_request",
            "pending_exit": "leave_constellation",
        },
        "pending_entry": {
            "prepared": "join_sos",
            "disengaged": "prepare",

            "available": "join_invitation",
            "negotiating": "join_constellation",

            "pending_entry": None,
            "full_role": "leave_request",
            "restricted_role": "leave_request",
            "pending_exit": "leave_constellation",
        },
        "participating": {
            "prepared": "join_sos",
            "disengaged": "prepare",

            "available": "join_invitation",
            "negotiating": "join_constellation",

            "pending_entry": "constellation_stable",

            "restricted_role": None,
            "pending_exit": "exit_denied",

            "full_role": None, 
        },
        "full_role": {
            "prepared": "join_sos",
            "disengaged": "prepare",

            "available": "join_invitation",
            "negotiating": "join_constellation",

            "pending_entry": "constellation_stable",

            "restricted_role": None,
            "pending_exit": "exit_denied",

            "full_role": None, 
        },
        "restricted_role": {
            "prepared": "join_sos",
            "disengaged": "prepare",

            "available": "join_invitation",
            "negotiating": "join_constellation",

            "pending_entry": "constellation_stable",

            "restricted_role": None,
            "pending_exit": "exit_denied",

            "full_role": None, 
        },
        "pending_exit": {
            "prepared": "join_sos",
            "disengaged": "prepare",

            "available": "join_invitation",
            "negotiating": "join_constellation",

            "pending_entry": "leave_request",
            "full_role": "leave_request",
            "restricted_role": "leave_request",
            "pending_exit": None,
        },
    }


    def ensure_belonging(self, goal, max_steps=15):

        valid_states = set(self.BELONGING_STATE_MAP.values()) | {"participating"}

        if goal not in valid_states:
            raise ValueError(f"Unknown belonging state: {goal}")

        for _ in range(max_steps):

            current = self.belonging_substate()

            if goal == "participating":
                if current in {"full_role", "restricted_role"}:
                    return True
            else:
                if current == goal:
                    return True

            try:
                action = self.BELONGING_POLICY[goal][current]
            except KeyError:
                raise RuntimeError(
                    f"No policy defined for ({current} → {goal})"
                )

            if action is None:
                return True

            before = current

            getattr(self, action)(goal=goal)

            after = self.belonging_substate()

            if after == before:
                return False   # blocked by guard / constraint

        return False  # couldn't reach after max steps
    

    def step_towards_belonging(self, goal):
        current = self.belonging_substate()

        if goal == "participating":
            if current in {"full_role", "restricted_role"}:
                return True
        else:
            if current == goal:
                return True
        try:
            action = self.BELONGING_POLICY[goal][current]
        except KeyError:
            return False

        if action is None:
            return True

        before = current
        getattr(self, action)(goal=goal)
        after = self.belonging_substate()
        if after == before:
            return False
        return True

    def ensure_disengaged(self): 
        return self.ensure_belonging("disengaged")

    def ensure_prepared(self): 
        return self.ensure_belonging("prepared")

    def ensure_available(self): 
        return self.ensure_belonging("available")

    def ensure_negotiating(self): 
        return self.ensure_belonging("negotiating")

    def ensure_pending_entry(self): 
        return self.ensure_belonging("pending_entry")

    def ensure_participating(self): 
        return self.ensure_belonging("participating")

    def ensure_pending_exit(self): 
        return self.ensure_belonging("pending_exit")