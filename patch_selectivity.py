#!/usr/bin/env python3
"""
Patch sélectivité pour /root/polybot/simulate.py.

Ajoute, juste avant le log "DIRECT ENTRY" du handler de signal :
  - filtre move : ne trade que si move_pct >= 1.5 × CANDLE_THRESHOLD_PCT
  - filtre prix : ne trade que si 0.30 <= current_price <= 0.72

Idempotent : si le marqueur est déjà présent, ne fait rien.
"""
import re
import sys
from pathlib import Path

TARGET = Path("/root/polybot/simulate.py")
MARKER = "Sélectivité (filtre bruit)"

INSERT = '''        # ── Sélectivité (filtre bruit) ───────────────────────────────────────
        MIN_MOVE_PCT = config.CANDLE_THRESHOLD_PCT * 1.5   # ~0.045% mini
        if move_pct < MIN_MOVE_PCT:
            _paper_stats["no_edge"] += 1
            logger.info(f"[Sim] Move trop faible ({move_pct*100:.4f}%) — bruit ignoré")
            return
        if not (0.30 <= current_price <= 0.72):
            _paper_stats["no_edge"] += 1
            logger.info(f"[Sim] Prix hors bande ({current_price:.4f}) — entrée extrême évitée")
            return

'''


def main() -> int:
    if not TARGET.exists():
        print(f"ERREUR : {TARGET} introuvable", file=sys.stderr)
        return 2

    src = TARGET.read_text()
    if MARKER in src:
        print("Déjà patché — rien à faire.")
        return 0

    pattern = re.compile(
        r'(        logger\.info\(\n            f"\[Sim\] DIRECT ENTRY)',
        re.MULTILINE,
    )
    new, n = pattern.subn(INSERT + r"\1", src, count=1)
    if n != 1:
        print(
            "ERREUR : ancre 'DIRECT ENTRY' introuvable — patch annulé.",
            file=sys.stderr,
        )
        return 1

    backup = TARGET.with_suffix(".py.bak_selectivity")
    backup.write_text(src)
    TARGET.write_text(new)
    print(f"Patch appliqué ✓ (sauvegarde : {backup})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
