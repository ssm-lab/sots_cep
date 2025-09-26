from app.core.runtime.EventStream import EventStream
from app.core.stream.StreamManager import StreamManager
from app.core.imputation.ReconstructionManager import ImputerManager
from app.core.logger.Logger import CSVLogger
import logging
from .evaluation.Evaluator import Evaluator


evaluator = Evaluator(filepath="data/logs/all_partitions_20250926-091540_d822ffd1.csv")
metrics = evaluator.compute_basic_metrics()
stats = evaluator.run_statistical_tests()

logging.info("[MAIN] Evaluation finished")
logging.info(f"Metrics: {metrics}")
logging.info(f"Statistical tests: {stats}")