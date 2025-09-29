import logging
from app.core.utils.JavaRunner import start_java, stop_java

class EsperCEPEngine:
    def __init__(self, pattern_file, run_dir,
                 jar_name="sots-uncertainty-aware-cep-0.0.1-SNAPSHOT.jar",
                 java_dir="app/java", rebuild=True):
        self.pattern_file = pattern_file
        self.run_dir = run_dir
        self.jar_name = jar_name
        self.java_dir = java_dir
        self.rebuild = rebuild
        self.proc = None

    def start(self):
        logging.info("[EsperCEPEngine] Starting Esper process")
        self.proc = start_java(
            main_class="app.Main",
            jar_name=self.jar_name,
            java_dir=self.java_dir,
            args=[self.pattern_file, self.run_dir],
            rebuild=self.rebuild
        )

    def stop(self):
        if self.proc:
            logging.info("[EsperCEPEngine] Stopping Esper process")
            stop_java(self.proc)
            self.proc = None
