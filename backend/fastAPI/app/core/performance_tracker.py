from collections import defaultdict
import statistics
from typing import Dict, List
from datetime import datetime


class PerformanceTracker:
    def __init__(self):
        self.measurements: Dict[str, List[float]] = defaultdict(list)
        self.request_times: List[float] = []
        self.latest_requests: List[Dict] = []  # Für detailliertere Anfrage-Historie

    def add_measurement(self, name: str, duration: float):
        """Fügt eine neue Zeitmessung hinzu."""
        self.measurements[name].append(duration)
        # Behalte nur die letzten 100 Messungen pro Phase
        if len(self.measurements[name]) > 100:
            self.measurements[name].pop(0)

    def add_request(self, path: str, duration: float, measurements: Dict[str, float]):
        """Speichert Details einer kompletten Anfrage."""
        self.request_times.append(duration)

        # Speichere detaillierte Request-Info
        request_info = {
            "timestamp": datetime.now().isoformat(),
            "path": path,
            "duration": f"{duration:.3f}s",
            "breakdown": measurements
        }
        self.latest_requests.append(request_info)

        # Behalte nur die letzten 50 Requests
        if len(self.latest_requests) > 50:
            self.latest_requests.pop(0)
        if len(self.request_times) > 1000:
            self.request_times.pop(0)

    def get_stats(self) -> Dict:
        """Gibt aktuelle Performance-Statistiken zurück."""
        stats = {
            "overall": {
                "total_requests": len(self.request_times),
                "avg_response_time": (
                    f"{statistics.mean(self.request_times):.3f}s"
                    if self.request_times else "0s"
                ),
                "max_response_time": (
                    f"{max(self.request_times):.3f}s"
                    if self.request_times else "0s"
                )
            },
            "phases": {},
            "latest_requests": self.latest_requests[:5]  # Letzte 5 Anfragen
        }

        # Berechne Statistiken für jede Phase
        for name, times in self.measurements.items():
            if times:  # Nur wenn Messungen vorhanden
                stats["phases"][name] = {
                    "avg": f"{statistics.mean(times):.3f}s",
                    "min": f"{min(times):.3f}s",
                    "max": f"{max(times):.3f}s",
                    "calls": len(times)
                }

        return stats


# Globale Instanz
tracker = PerformanceTracker()