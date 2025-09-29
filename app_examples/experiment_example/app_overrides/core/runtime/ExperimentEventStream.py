from app.core.communication import Client
from app.core.runtime.EventStream import EventStream

class ExperimentEventStream(EventStream):
    def __init__(self):
        super().__init__()
        self.partitions["groundtruth"] = Client("groundtruth")
