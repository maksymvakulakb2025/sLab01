import csv
import json
import logging
import re
import socket
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

HOST_PATTERN = re.compile(
    r"^("
    r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}"
    r"|"
    r"(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"
    r")$"
)


@dataclass
class ServiceTarget:
    host: str
    port: int
    service: str = "UNKNOWN"


@dataclass
class ScanResult:
    host: str
    port: int
    service: str
    status: str
    response_time_ms: float
    notes: str


def validate_host(host: str) -> bool:
    return bool(HOST_PATTERN.match(host))


def scan_target(target: ServiceTarget, timeout: float = 2.0) -> ScanResult:
    if not validate_host(target.host):
        return ScanResult(
            host=target.host,
            port=target.port,
            service=target.service,
            status="INVALID",
            response_time_ms=0.0,
            notes="Invalid host syntax",
        )

    start_time = time.perf_counter()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)

    try:
        sock.connect((target.host, target.port))
        elapsed = (time.perf_counter() - start_time) * 1000
        sock.close()
        return ScanResult(
            host=target.host,
            port=target.port,
            service=target.service,
            status="ONLINE",
            response_time_ms=round(elapsed, 1),
            notes="OK",
        )
    except TimeoutError:
        return ScanResult(
            host=target.host,
            port=target.port,
            service=target.service,
            status="OFFLINE",
            response_time_ms=0.0,
            notes="Connection timed out",
        )
    except OSError as e:
        return ScanResult(
            host=target.host,
            port=target.port,
            service=target.service,
            status="OFFLINE",
            response_time_ms=0.0,
            notes=str(e),
        )


def run_availability_scan(
    targets_file: Path, timeout: float, out_csv: Path, verbose: bool
):
    logger.info(
        f"Starting service availability scan from target list {targets_file}..."
    )

    if not targets_file.exists():
        logger.error(f"File not found: {targets_file}")
        return

    with open(targets_file, "r", encoding="utf-8") as f:
        raw_targets = json.load(f)

    targets = [
        ServiceTarget(
            host=t["host"],
            port=int(t["port"]),
            service=t.get("service", "UNKNOWN"),
        )
        for t in raw_targets
    ]

    results: list[ScanResult] = []
    online_count = 0

    print(
        f"\n{'Target Host':<18} {'Port':<6} {'Service':<8} {'Status':<8} {'Response Time':<15} {'Notes'}"
    )
    print("-" * 75)

    for target in targets:
        res = scan_target(target, timeout)
        results.append(res)

        if res.status == "ONLINE":
            online_count += 1
            resp_str = f"{res.response_time_ms} ms"
        else:
            resp_str = "TIMEOUT" if "timed out" in res.notes else "N/A"

        print(
            f"{res.host:<18} {res.port:<6} {res.service:<8} {res.status:<8} {resp_str:<15} {res.notes}"
        )

        if verbose:
            logger.debug(f"Scanned {res.host}:{res.port} -> {res.status}")

    total = len(results)
    offline_count = total - online_count
    online_pct = (online_count / total * 100) if total > 0 else 0
    offline_pct = (offline_count / total * 100) if total > 0 else 0

    print("\n=== Scan Statistics ===")
    print(f"Total Scanned : {total}")
    print(f"Online        : {online_count} ({online_pct:.1f}%)")
    print(f"Offline       : {offline_count} ({offline_pct:.1f}%)\n")

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["Host", "Port", "Service", "Status", "ResponseTimeMs", "Notes"]
        )
        for r in results:
            writer.writerow(
                [r.host, r.port, r.service, r.status, r.response_time_ms, r.notes]
            )

    logger.info(f"Detailed scan report saved to {out_csv}")
