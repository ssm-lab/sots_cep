import logging
import logging
import os
import shutil
import subprocess

__author__ = "Feyi Adesanya"

# mvn clean package -DskipTests
class EventProcessor:
    def __init__(self, pattern_cfg, run_dir,
                 jar_name="sots-uncertainty-aware-cep-0.0.1-SNAPSHOT.jar",
                 java_dir="app/java", rebuild=True, log_matches: str = "True"):
        self.pattern_cfg = pattern_cfg
        self.run_dir = run_dir
        self.jar_name = jar_name
        self.java_dir = java_dir
        self.rebuild = rebuild
        self.log_matches = log_matches
        self.proc = None
        self.pid = None

    def start(self):
        """Start the Java CEP engine as a subprocess."""
        logging.info("[JavaCEPBridge] Starting Java process")
        self.proc = start_java(
            main_class="app.Main",
            jar_name=self.jar_name,
            java_dir=self.java_dir,
            args=[self.pattern_cfg, self.run_dir, self.log_matches],
            rebuild=self.rebuild
        )
        self.pid = self.proc.pid
        logging.info(f"[JavaCEPBridge] Started Java PID={self.pid}")

    def stop(self):
        """Stop the Java CEP engine subprocess."""
        if self.proc:
            logging.info("[JavaCEPBridge] Stopping Java process")
            stop_java(self.proc, self.pid)
            self.proc = None


# Utility functions for starting and stopping a Java process.
def build_java(
    java_dir: str = os.path.join(os.getcwd(), "app/java"),
    clean: bool = False
):
    logging.info(f"[BUILD] Running mvn {'clean ' if clean else ''}package in {java_dir}")

    mvn_cmd = shutil.which("mvn")
    if mvn_cmd is None:
        logging.error("[BUILD] Maven not found on PATH")
        raise RuntimeError("Maven not found")

    cmd = [mvn_cmd]
    if clean:
        cmd.append("clean")
    cmd.extend(["package", "-DskipTests"])

    result = subprocess.run(
        cmd,
        cwd=java_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=True,
    )

    if result.returncode != 0:
        logging.error("[BUILD] Maven build failed")
        logging.error(result.stderr)
        raise RuntimeError("Maven build failed")
    else:
        logging.info("[BUILD] Maven build succeeded")


def start_java(
    main_class: str = "app.Main",
    jar_name: str = "sots-uncertainty-aware-cep-0.0.1-SNAPSHOT.jar",
    java_dir: str = os.path.join(os.getcwd(), "app/java"),
    args: list[str] = None,
    rebuild: bool = False
):
    jar_path = os.path.join(java_dir, "target", jar_name)

    if rebuild or not os.path.exists(jar_path):
        build_java(java_dir=java_dir, clean=rebuild)

    if not os.path.exists(jar_path):
        logging.error(f"[MAIN] Could not find JAR at {jar_path}")
        return None

    cmd = ["java", "-cp", jar_path, main_class]
    if args:
        cmd.extend(args)

    logging.info(f"[MAIN] Starting subprocess with: {' '.join(cmd)}")
    return subprocess.Popen(cmd)


def stop_java(proc, pid=None):
    if not proc:
        return
    try:
        logging.info("[MAIN] Attempting to stop Java process...")
        proc.terminate()
        try:
            proc.wait(timeout=8)
            logging.info("[MAIN] Java stopped.")
        except subprocess.TimeoutExpired:
            logging.warning("[MAIN] unresponsive — forcing kill.")
            proc.kill()
            proc.wait()
    except Exception as e:
        logging.error(f"[MAIN] Failed to stop Java process: {e}")

    # kill all leftover Java processes
    subprocess.run(
    ["taskkill", "/IM", "java.exe", "/F"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)