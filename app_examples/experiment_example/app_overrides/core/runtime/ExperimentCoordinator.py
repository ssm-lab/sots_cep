import logging
import threading
from app.core.runtime.Coordinator import Coordinator
from ..stream.stream_types.ExperimentStream import EndOfDataset, ExperimentStream

LOG = logging.getLogger(__name__)

class ExperimentCoordinator(Coordinator):
    def __init__(self, *args, on_complete=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._active_streams = 0
        self._lock = threading.Lock()
        self._done_called = False   # 👈 make callback idempotent
        self.running = False
        self.on_complete = on_complete

    def _build_stream(self, stream_id: str, cfg: dict):
        params = cfg.get("params", {})
        return ExperimentStream(
            stream_id=stream_id,
            unit=cfg.get("unit"),
            datatype=cfg.get("datatype", "float"),
            interval=cfg.get("interval", 1.0),
            params=params,
        )

    def start(self):
        """Start all dataset replay threads."""
        self.running = True
        threads = []

        for stream_id, scheduler in self.schedulers.items():
            stream = self.streams[stream_id]
            with self._lock:
                self._active_streams += 1
            t = threading.Thread(
                target=self._run_stream, args=(stream_id, scheduler, stream), daemon=True
            )
            t.start()
            threads.append(t)

        LOG.info(f"[ExperimentCoordinator] Started {len(threads)} dataset threads.")

    def _run_stream(self, stream_id, scheduler, stream):
        LOG.info(f"[ExperimentCoordinator] Starting dataset replay for {stream_id}")
        reconstructor = self.reconstructors.get(stream_id)
        if not reconstructor:
            LOG.warning(f"[ExperimentCoordinator] No reconstructor for {stream_id}")
            with self._lock:
                self._active_streams -= 1
            self._check_completion()
            return
        LOG.info(f"[ExperimentCoordinator] Running loop for {stream_id}")


        try:
            while self.running:
                try:
                    event_time = scheduler.wait_next()
                    event, structural, event_id, obs_value = stream.generate_event()
                except EndOfDataset:
                    LOG.info(f"[ExperimentCoordinator] End of dataset for {stream_id}")
                    break

                if structural:
                    reconstructor.advance_without_event()
                    continue

                if event is None:
                    missing_event = {
                        "stream_id": stream_id,
                        "event_id": event_id,
                        "origin": "missing",
                        "value": None,
                        "event_ts": event_time,
                        "extras": {"ground_truth": obs_value},
                    }
                    reconstructor.handle_timeout(missing_event)
                    continue

                self.event_stream.add_event(event, "observed", stream_id)
                # LOG.debug(f"[ExperimentCoordinator] {stream_id} — step done.")


        except Exception as e:
            LOG.exception(f"[ExperimentCoordinator] Error in {stream_id}: {e}")
        finally:
            with self._lock:
                self._active_streams -= 1
                remaining = self._active_streams
            LOG.info(f"[ExperimentCoordinator] Stream {stream_id} stopped. Remaining: {remaining}")
            self._check_completion()

    def _check_completion(self):
        """Invoke orchestrator callback once all streams finish."""
        with self._lock:
            if self._active_streams <= 0 and not self._done_called:
                self._done_called = True
                LOG.info("[ExperimentCoordinator] All dataset streams completed.")
                if self.on_complete:
                    LOG.info("[ExperimentCoordinator] Triggering orchestrator callback.")
                    threading.Thread(target=self.on_complete, daemon=True).start()
