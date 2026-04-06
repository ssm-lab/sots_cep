from app.core.runtime.ConstituentController import ConstituentController

class ExperimentConstituentController(ConstituentController):

    def __init__(
        self,
        statechart_cls,
        constituent_id,
        lifecycle_logger=None,
        clock=None,
        scenario=None
    ):
        super().__init__(statechart_cls, constituent_id, lifecycle_logger)
        self.clock = clock
        self.scenario = scenario

    def _raise(self, event, goal=None, goal_domain=None):

        before = self.state_snapshot()
        from_state = f"{before['belonging_main']}/{before['belonging_sub']}"

        transition = event
        getattr(self.sm, transition)()
        self.sm.run_cycle()

        self.update_snapshot()

        after = self.state_snapshot()
        final_state = f"{after['belonging_main']}/{after['belonging_sub']}"
        final_health = after["health_main"]

        transition_made = from_state != final_state
        result = "made" if transition_made else "denied"

        if goal_domain is None:
            if goal in ["ideal", "defective", "faulty", "erroneous", "malfunctioning"]:
                goal_domain = "health"
            else:
                goal_domain = "belonging"

        if goal is None:
            goal_match = False
        elif goal_domain == "belonging":
            goal_match = (goal == final_state)
        elif goal_domain == "health":
            goal_match = (goal == final_health)
        else:
            goal_match = False

        ts = self.clock.now() if self.clock else None

        if self.lifecycle_logger:
            self.lifecycle_logger.consume_event({
                "type": "lifecycle_decision",
                "ts": ts,
                "scenario": self.scenario,
                "constituent_id": self.id,
                "from_state": from_state,
                "target_state": goal or from_state,
                "goal_domain": goal_domain,
                "transition": transition,
                "result": result,
                "final_state": final_state,
                "health": final_health,
                "goal_match": goal_match,
                "trigger_event": transition,
            })