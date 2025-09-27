import logging
import os
import shutil
import signal
import subprocess

logging.basicConfig(
    format="[%(levelname)s] %(message)s",
    level=logging.DEBUG
)


def build_java(
    java_dir: str = os.path.join(os.getcwd(), "app/java"),
    clean: bool = False
):
    """Run mvn package (with optional clean)."""
    logging.info(f"[BUILD] Running mvn {'clean ' if clean else ''}package in {java_dir}")

    mvn_cmd = shutil.which("mvn")
    if mvn_cmd is None:
        logging.error("[BUILD] Maven not found on PATH. Please install Maven or add it to PATH.")
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
    """Start a Java subprocess"""
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
    """Stop a Java subprocess"""
    if proc:
        logging.info("[MAIN] Terminating subprocess...")
        proc.send_signal(signal.SIGTERM)
        proc.wait()
        logging.info("[MAIN] Subprocess stopped")
