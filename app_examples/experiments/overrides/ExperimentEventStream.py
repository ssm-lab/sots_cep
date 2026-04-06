from app.core.runtime.EventStream import EventStream


class ExperimentEventStream(EventStream):

    def __init__(self, client_type):

        super().__init__(client_type)

        self.partitions = {
            "observed": self.client_type(partition="observed"),
            "reconstructed": self.client_type(partition="reconstructed"),
            "ground_truth": self.client_type(partition="ground_truth"),
        }

    def dispatch(self, timeout: int = 0.5, once: bool = True):
        for client in list(self.partitions.values()):
            while True:
                had_event = client.poll_once(timeout=timeout)

                if not had_event:
                    break