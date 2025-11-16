from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from zoneinfo import ZoneInfo

from scores24_graphql_client import fetch_match_stats

LOG_FILE = Path("data/recommendations_log.csv")
RESULTS_FILE = Path("data/recommendations_results.csv")

FINISHED_STATUS_CODES = {"100"}


@dataclass
class LogEntry:
    entry_id: str
    timestamp_msk: str
    slug: str
    bet_side: str
    coefficient: Optional[float]


def _parse_coefficient(value: str) -> Optional[float]:
    if not value:
        return None
    try:
        return float(value.replace(",", "."))
    except ValueError:
        return None


def _parse_score(value: Optional[str]) -> Optional[Tuple[int, int]]:
    if not value:
        return None
    clean = value.strip().replace(" ", "")
    for sep in (":", "-"):
        if sep in clean:
            parts = clean.split(sep)
            if len(parts) == 2 and all(p.isdigit() for p in parts):
                return int(parts[0]), int(parts[1])
    return None


def _load_log_entries() -> List[LogEntry]:
    if not LOG_FILE.exists():
        raise FileNotFoundError(f"Log file not found: {LOG_FILE}")

    entries: List[LogEntry] = []
    with LOG_FILE.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            entry_id = f"{row.get('timestamp_msk','')}|{row.get('slug','')}|{row.get('bet_side','')}"
            entries.append(
                LogEntry(
                    entry_id=entry_id,
                    timestamp_msk=row.get("timestamp_msk", ""),
                    slug=row.get("slug", ""),
                    bet_side=row.get("bet_side", ""),
                    coefficient=_parse_coefficient(row.get("coefficient", "")),
                )
            )
    return entries


def _load_processed_ids() -> Dict[str, Dict[str, str]]:
    processed: Dict[str, Dict[str, str]] = {}
    if not RESULTS_FILE.exists():
        return processed

    with RESULTS_FILE.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            entry_id = row.get("entry_id")
            if entry_id:
                processed[entry_id] = row
    return processed


def _ensure_results_file() -> None:
    if RESULTS_FILE.exists():
        return
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "entry_id",
        "timestamp_msk",
        "slug",
        "bet_side",
        "coefficient",
        "final_score",
        "status_code",
        "result",
        "profit_units",
        "processed_at_msk",
    ]
    with RESULTS_FILE.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.writer(fp)
        writer.writerow(header)


def _determine_result(
    bet_side: str,
    home_score: int,
    away_score: int,
) -> str:
    if bet_side == "П1":
        if home_score > away_score:
            return "win"
        if home_score < away_score:
            return "loss"
        return "push"
    if bet_side == "П2":
        if away_score > home_score:
            return "win"
        if away_score < home_score:
            return "loss"
        return "push"
    return "unknown"


def _calculate_profit(result: str, coefficient: Optional[float]) -> float:
    if result == "win":
        if coefficient is None:
            return 0.0
        return coefficient - 1.0
    if result == "loss":
        return -1.0
    if result == "push":
        return 0.0
    return 0.0


def process_results() -> None:
    entries = _load_log_entries()
    processed_rows = _load_processed_ids()

    _ensure_results_file()

    new_rows: List[List[str]] = []

    for entry in entries:
        if entry.entry_id in processed_rows:
            continue

        try:
            details = fetch_match_stats(entry.slug)
        except Exception as exc:
            print(f"Failed to fetch stats for {entry.slug}: {exc}")
            continue

        status_code = (details.get("status") or {}).get("code")
        if status_code not in FINISHED_STATUS_CODES:
            continue

        score = _parse_score(details.get("result_score"))
        if score is None:
            score = _parse_score(details.get("game_state", {}).get("score") if isinstance(details.get("game_state"), dict) else None)
        if score is None:
            continue

        home_score, away_score = score
        result = _determine_result(entry.bet_side, home_score, away_score)
        profit = _calculate_profit(result, entry.coefficient)

        processed_at = datetime.now(ZoneInfo("Europe/Moscow")).strftime("%Y-%m-%d %H:%M:%S")

        new_rows.append(
            [
                entry.entry_id,
                entry.timestamp_msk,
                entry.slug,
                entry.bet_side,
                f"{entry.coefficient:.2f}" if entry.coefficient is not None else "",
                f"{home_score}:{away_score}",
                status_code or "",
                result,
                f"{profit:.2f}",
                processed_at,
            ]
        )

    if not new_rows:
        print("No new finished matches to process.")
        return

    with RESULTS_FILE.open("a", encoding="utf-8", newline="") as fp:
        writer = csv.writer(fp)
        writer.writerows(new_rows)

    wins = sum(1 for row in new_rows if row[7] == "win")
    losses = sum(1 for row in new_rows if row[7] == "loss")
    pushes = sum(1 for row in new_rows if row[7] == "push")
    profit_total = sum(float(row[8]) for row in new_rows)

    print(f"Processed {len(new_rows)} finished matches.")
    print(f"Wins: {wins}, Losses: {losses}, Pushes: {pushes}, Profit: {profit_total:.2f}u")


if __name__ == "__main__":
    process_results()

