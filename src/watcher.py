#!/usr/bin/env python3
"""
watcher.py  — stateless

Attaches to qBittorrent's /api/v2/sync/maindata and triggers guard.TorrentGuard
when new torrents appear. No disk state is kept; only an in-memory set of
hashes seen during the current process lifetime.

Behavior:
- On first snapshot:
  - If WATCH_PROCESS_EXISTING_AT_START=1, process all currently present torrents.
  - Otherwise, just index them (skip processing).
- During runtime:
  - Process a torrent the first time we see its infohash.
  - If qB reports torrents_removed, we forget those hashes so a future re-add
    will be processed again.
- Optional: force a rescan if category or tags contain WATCH_RESCAN_KEYWORD
  (default 'rescan'), even if we've already processed it in this session.
"""

import os, sys, json, time, signal, logging, urllib.parse as uparse
from typing import Dict, Set, Tuple

# Your class-based guard + clients
from guard import Config, HttpClient, QbitClient, TorrentGuard

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("qbit-guard-watcher")

POLL_SEC = float(os.getenv("WATCH_POLL_SECONDS", "3.0"))
PROCESS_EXISTING_AT_START = os.getenv("WATCH_PROCESS_EXISTING_AT_START", "0") == "1"
RESCAN_KEYWORD = os.getenv("WATCH_RESCAN_KEYWORD", "rescan").strip().lower()  # in category/tags -> force

def qb_sync_maindata(http: HttpClient, cfg: Config, rid: int) -> Dict:
    url = f"{cfg.qbit_host}/api/v2/sync/maindata"
    if rid:
        url += "?" + uparse.urlencode({"rid": rid})
    raw = http.get(url)
    return {} if not raw else json.loads(raw.decode("utf-8"))

def _should_process(h: str, t: Dict, seen: Set[str]) -> Tuple[bool, str]:
    # Manual rescan via keyword in category or tags
    cat = (t.get("category") or "").strip().lower()
    tags = (t.get("tags") or "").strip().lower()
    if RESCAN_KEYWORD and (RESCAN_KEYWORD in cat or RESCAN_KEYWORD in tags):
        return True, "manual-rescan"
    if h not in seen:
        return True, "new"
    return False, "already-seen"

def main():
    cfg = Config()
    http = HttpClient(cfg.ignore_tls, cfg.user_agent)
    qb = QbitClient(cfg, http)
    guard = TorrentGuard(cfg)

    # graceful shutdown
    stop = {"flag": False}
    def _sig(*_): stop["flag"] = True
    for s in (signal.SIGINT, signal.SIGTERM):
        signal.signal(s, _sig)

    # login
    try:
        qb.login()
    except Exception as e:
        log.error("qB login failed: %s", e)
        sys.exit(2)

    seen: Set[str] = set()
    rid = 0
    first_snapshot = True
    log.info(
        "Watcher (stateless) started. poll=%.1fs, process_existing_at_start=%s, rescan-keyword='%s'",
        POLL_SEC, PROCESS_EXISTING_AT_START, RESCAN_KEYWORD or "(disabled)"
    )

    while not stop["flag"]:
        try:
            data = qb_sync_maindata(http, cfg, rid)
            if not data:
                time.sleep(POLL_SEC)
                continue

            rid = data.get("rid", rid)
            torrents = data.get("torrents") or {}
            removed = data.get("torrents_removed") or []

            # First snapshot behavior
            if first_snapshot:
                first_snapshot = False
                present = set(torrents.keys())
                if PROCESS_EXISTING_AT_START:
                    log.info("Initial snapshot: processing %d existing torrents.", len(present))
                    # fall through: they will be processed below (since not in 'seen' yet)
                else:
                    seen |= present
                    log.info("Initial snapshot: indexed %d existing torrents (not processing).", len(present))
                    time.sleep(POLL_SEC)
                    continue

            # Forget hashes for removed torrents so re-adds will trigger again
            for h in removed:
                if h in seen:
                    seen.discard(h)

            # Handle new/changed torrents in this delta
            for h, t in torrents.items():
                name = t.get("name") or ""
                category = (t.get("category") or "").strip()
                ok, reason = _should_process(h, t, seen)
                if not ok:
                    log.debug("Skip %s | %s", h, reason)
                    continue

                log.info("Processing %s | reason=%s | category='%s' | name='%s'", h, reason, category, name)
                try:
                    guard.run(h, category)
                except Exception as e:
                    log.error("Guard run failed for %s: %s", h, e)
                finally:
                    seen.add(h)

        except Exception as e:
            log.error("Watcher loop error: %s", e)

        time.sleep(POLL_SEC)

    log.info("Watcher stopping...")

if __name__ == "__main__":
    main()
