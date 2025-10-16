import logging
import os
import shutil
import signal
import subprocess

import psutil

__author__ = "Feyi Adesanya"

"""
Utility functions for starting and stopping a Java process.
"""

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
        shell=True
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
    """ Launches the Java process. """

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


def stop_java(proc):
    """Terminate the Java subprocess safely on Windows and Unix."""
    if not proc:
        return
    try:
        logging.info("[MAIN] Attempting to stop Java process...")
        proc.terminate()  # sends CTRL_BREAK on Windows
        try:
            proc.wait(timeout=8)
            logging.info("[MAIN] Java stopped gracefully.")
        except subprocess.TimeoutExpired:
            logging.warning("[MAIN] Java unresponsive — forcing kill.")
            proc.kill()
            proc.wait()
    except Exception as e:
        logging.error(f"[MAIN] Failed to stop Java process: {e}")

    # Safety net — kill all leftover Java processes (shouldn’t normally happen)
    for p in psutil.process_iter(attrs=["pid", "name"]):
        if "java" in p.info["name"].lower():
            logging.warning(f"[MAIN] Found stray Java process (PID {p.pid}), terminating...")
            p.kill()

