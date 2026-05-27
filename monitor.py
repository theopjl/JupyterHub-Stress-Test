import csv
import os
import time
import threading
import subprocess
import psutil
from datetime import datetime


def _get_gpu_stats() -> dict:
    """Interroge nvidia-smi et retourne un dict de métriques GPU."""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        vals = [v.strip() for v in result.stdout.strip().split(",")]
        return {
            "gpu_util":     int(vals[0]),
            "gpu_mem_used": int(vals[1]),
            "gpu_mem_total":int(vals[2]),
            "gpu_temp":     int(vals[3]),
        }
    except Exception:
        return {"gpu_util": 0, "gpu_mem_used": 0, "gpu_mem_total": 0, "gpu_temp": 0}


CSV_HEADER = [
    "timestamp", "gabarit", "nb_users",
    "cpu_percent",
    "ram_used_gb", "ram_total_gb", "ram_percent",
    "gpu_util_percent", "gpu_mem_used_mb", "gpu_mem_total_mb", "gpu_temp_c",
]


class ResourceMonitor:
    """Moniteur de ressources écrivant en continu dans un fichier CSV."""

    def __init__(self, output_file: str, gabarit: str, nb_users: int, interval: float = 1.0):
        self.output_file = output_file
        self.gabarit     = gabarit
        self.nb_users    = nb_users
        self.interval    = interval
        self._stop       = threading.Event()
        self._thread     = None

    def _ensure_header(self):
        """Écrit l'en-tête CSV si le fichier est vide ou nouveau."""
        try:
            with open(self.output_file, "x", newline="") as f:
                csv.writer(f).writerow(CSV_HEADER)
        except FileExistsError:
            if os.path.getsize(self.output_file) == 0:
                with open(self.output_file, "w", newline="") as f:
                    csv.writer(f).writerow(CSV_HEADER)

    def _sample_loop(self):
        while not self._stop.is_set():
            ts  = datetime.now().isoformat(timespec="seconds")
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory()
            gpu = _get_gpu_stats()

            row = [
                ts,
                self.gabarit,
                self.nb_users,
                cpu,
                round(ram.used   / 1e9, 2),
                round(ram.total  / 1e9, 2),
                ram.percent,
                gpu["gpu_util"],
                gpu["gpu_mem_used"],
                gpu["gpu_mem_total"],
                gpu["gpu_temp"],
            ]

            with open(self.output_file, "a", newline="") as f:
                csv.writer(f).writerow(row)

            time.sleep(self.interval)

    def start(self):
        self._ensure_header()
        self._thread = threading.Thread(target=self._sample_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)