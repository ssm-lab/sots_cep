from app.core.source.EventSource import EventSource
import time

class ExperimentEventSource(EventSource):

    def __init__(self, *args, clock=None, scenario=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.clock = clock
        self.scenario = scenario

    def emit_ground_truth(self, params):
        event = self.generate_event(params)
        event["event_status"] = "ground_truth"
        event["partition"] = "ground_truth"

        state = self.lifecycle.get_state(self.id)
        extras = event["extras"]
        extras["health"] = state["health_main"]
        extras["belonging_main"] = state["belonging_main"]
        extras["belonging_sub"] = state["belonging_sub"]

        event["extras"] = extras
        
        self.stream.add_event(event, "ground_truth", self.id)

        return event

    def emit_event(self, params):
        return super().emit_event(params)