import logging
from app.core.bridge.JavaProcessManager import start_java, stop_java

__author__ = "Feyi Adesanya"

class JavaCEPBridge:
    def __init__(self, pattern_cfg, run_dir,
                 jar_name="sots-uncertainty-aware-cep-0.0.1-SNAPSHOT.jar",
                 java_dir="app/java", rebuild=True):
        self.pattern_cfg = pattern_cfg
        self.run_dir = run_dir
        self.jar_name = jar_name
        self.java_dir = java_dir
        self.rebuild = rebuild
        self.proc = None

    def start(self):
        """Start the Java CEP engine as a subprocess."""
        logging.info("[JavaCEPBridge] Starting Java process")
        self.proc = start_java(
            main_class="app.Main",
            jar_name=self.jar_name,
            java_dir=self.java_dir,
            args=[self.pattern_cfg, self.run_dir],
            rebuild=self.rebuild
        )

    def stop(self):
        """Stop the Java CEP engine subprocess."""
        if self.proc:
            logging.info("[JavaCEPBridge] Stopping Java process")
            stop_java(self.proc)
            self.proc = None
