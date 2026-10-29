"""Завдання 2 (варіант 5): сканер доступності мережевих сервісів."""

import csv
import json
import logging
import re
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import astuple, dataclass, fields
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_WORKERS = 20

_OCTET = r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
IPV4_PATTERN = re.compile(rf"{_OCTET}(?:\.{_OCTET}){{3}}")
_LABEL = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
HOSTNAME_PATTERN = re.compile(rf"{_LABEL}(?:\.{_LABEL})*")
NUMERIC_LIKE_PATTERN = re.compile(r"[\d.]+")


class ScanInputError(Exception):
    """Вхідний файл цілей неможливо прочитати або він некоректний."""


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
    status: str  # ONLINE / OFFLINE / INVALID
    response_time_ms: float
    notes: str
    timed_out: bool = False


def validate_host(host: str) -> bool:
    """IPv4-адреса або доменне ім'я (включно з односкладовим, як localhost)."""
    if not isinstance(host, str) or len(host) > 253:
        return False
    if NUMERIC_LIKE_PATTERN.fullmatch(host):
        return IPV4_PATTERN.fullmatch(host) is not None
    return HOSTNAME_PATTERN.fullmatch(host) is not None


def _result(
    target: ServiceTarget,
    status: str,
    ms: float,
    notes: str,
    timed_out: bool = False,
) -> ScanResult:
    return ScanResult(
        target.host, target.port, target.service, status, ms, notes, timed_out
    )


def scan_target(target: ServiceTarget, timeout: float = 2.0) -> ScanResult:
    if not validate_host(target.host):
        return _result(target, "INVALID", 0.0, "Invalid host syntax")
    if not 1 <= target.port <= 65535:
        return _result(target, "INVALID", 0.0, "Port out of range (1-65535)")

    start = time.perf_counter()
    try:
        with socket.create_connection((target.host, target.port), timeout=timeout):
            elapsed = (time.perf_counter() - start) * 1000
    except TimeoutError:
        return _result(target, "OFFLINE", 0.0, "Connection timed out", timed_out=True)
    except ConnectionRefusedError:
        return _result(target, "OFFLINE", 0.0, "Connection refused")
    except socket.gaierror:
        return _result(target, "OFFLINE", 0.0, "Host name not resolved")
    except OSError as e:
        return _result(target, "OFFLINE", 0.0, str(e))
    return _result(target, "ONLINE", round(elapsed, 1), "OK")


def _record_to_target(record: object) -> ServiceTarget:
    if not isinstance(record, dict):
        raise TypeError("record is not an object")
    rec = {str(k).strip().lower(): v for k, v in record.items()}
    if "host" not in rec or "port" not in rec:
        raise ValueError("missing 'host' or 'port'")
    service = rec.get("service") or "UNKNOWN"
    return ServiceTarget(str(rec["host"]).strip(), int(rec["port"]), str(service))


def load_targets(path: Path) -> list[ServiceTarget]:
    """Читає цілі з JSON або CSV. Некоректні записи пропускаються з помилкою в лог."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise ScanInputError(f"Targets file not found: {path}") from e
    except (PermissionError, IsADirectoryError, UnicodeDecodeError) as e:
        raise ScanInputError(f"Cannot read targets file {path}: {e}") from e

    if path.suffix.lower() == ".csv":
        raw = list(csv.DictReader(text.splitlines()))
    else:
        try:
            raw = json.loads(text)
        except json.JSONDecodeError as e:
            raise ScanInputError(f"Invalid JSON in {path}: {e}") from e
        if isinstance(raw, dict) and isinstance(raw.get("targets"), list):
            raw = raw["targets"]
    if not isinstance(raw, list):
        raise ScanInputError("Targets file must contain a list of records")

    targets: list[ServiceTarget] = []
    for index, record in enumerate(raw, start=1):
        try:
            targets.append(_record_to_target(record))
        except (TypeError, ValueError) as e:
            logger.error("Skipping record #%d: %s", index, e)
    return targets


def _print_table(results: list[ScanResult]) -> None:
    header = (
        f"{'Target Host':<22} {'Port':<6} {'Service':<10} "
        f"{'Status':<8} {'Response Time':<14} Notes"
    )
    print(f"\n{header}")
    print("-" * 85)
    for r in results:
        if r.status == "ONLINE":
            resp = f"{r.response_time_ms} ms"
        elif r.timed_out:
            resp = "TIMEOUT"
        else:
            resp = "N/A"
        print(
            f"{r.host:<22} {r.port:<6} {r.service:<10} "
            f"{r.status:<8} {resp:<14} {r.notes}"
        )


def _print_stats(results: list[ScanResult]) -> None:
    total = len(results)
    online = sum(r.status == "ONLINE" for r in results)
    offline = sum(r.status == "OFFLINE" for r in results)
    invalid = sum(r.status == "INVALID" for r in results)

    def pct(n: int) -> float:
        return n / total * 100 if total else 0.0

    print("\n=== Scan Statistics ===")
    print(f"Total Scanned : {total}")
    print(f"Online        : {online} ({pct(online):.1f}%)")
    print(f"Offline       : {offline} ({pct(offline):.1f}%)")
    print(f"Invalid       : {invalid} ({pct(invalid):.1f}%)\n")


def save_csv(results: list[ScanResult], out_csv: Path) -> None:
    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([fld.name for fld in fields(ScanResult)])
        writer.writerows(astuple(r) for r in results)


def run_availability_scan(
    targets_file: Path, timeout: float, out_csv: Path
) -> list[ScanResult]:
    """Виконує скан. Кидає ScanInputError, якщо вхідні дані непридатні."""
    logger.info("Starting service availability scan from %s...", targets_file)
    targets = load_targets(targets_file)
    if not targets:
        raise ScanInputError("No valid targets to scan")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        results = list(pool.map(lambda t: scan_target(t, timeout), targets))

    for r in results:
        if r.status == "ONLINE":
            logger.debug(
                "%s:%d is ONLINE (%.1f ms)", r.host, r.port, r.response_time_ms
            )
        elif r.status == "OFFLINE":
            logger.warning("%s:%d is OFFLINE: %s", r.host, r.port, r.notes)
        else:
            logger.error("%s:%d is INVALID: %s", r.host, r.port, r.notes)

    _print_table(results)
    _print_stats(results)

    try:
        save_csv(results, out_csv)
    except OSError as e:
        logger.error("Failed to save CSV report to %s: %s", out_csv, e)
    else:
        logger.info("Detailed scan report saved to %s", out_csv)
    return results