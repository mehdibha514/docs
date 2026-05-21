#!/usr/bin/env python3
"""
Patch "edge > coût" pour /root/polybot/simulate.py.

Avant chaque entrée, on récupère le BID réel du token et on calcule le coût
aller-retour immédiat (spread entre l'ask qu'on paie et le bid où on sortirait).
Si ce coût dépasse MAX_ROUNDTRIP_COST, on SKIP le trade : inutile de payer plus
de spread que ce qu'un ajustement peut rapporter.

Ça ne "force" pas le profit (impossible) — ça refuse les trades structurellement
perdants d'avance. Idempotent.
"""
import re
import sys
from pathlib import Path

TARGET = Path("/root/polybot/simulate.py")
MARKER = "Gate edge > cout"

INSERT = '''        # ── Gate edge > cout : skip si le spread aller-retour mange le gain ──
        # On ne peut pas forcer un trade a etre positif, mais on peut refuser
        # ceux ou le cout (ask -> bid) depasse ce qu'un ajustement peut rapporter.
        MAX_ROUNDTRIP_COST = 0.035   # 3.5% : au-dela, le spread mange tout
        _gate_tid = (
            market.get("yes_token_id") if direction == "UP"
            else market.get("no_token_id")
        )
        _gate_bid = await trader.get_bid_price(_gate_tid) if _gate_tid else None
        if _gate_bid and _gate_bid > 0:
            _rt_cost = (current_price - _gate_bid) / current_price
            if _rt_cost > MAX_ROUNDTRIP_COST:
                _paper_stats["no_edge"] += 1
                logger.info(
                    f"[Sim] Skip edge<cout — spread AR {_rt_cost*100:.2f}% "
                    f"> {MAX_ROUNDTRIP_COST*100:.1f}% ({direction} @ {current_price:.4f})"
                )
                return

'''

def main() -> int:
    if not TARGET.exists():
        print(f"ERREUR : {TARGET} introuvable", file=sys.stderr)
        return 2

    src = TARGET.read_text()
    if MARKER in src:
        print("Deja patche — rien a faire.")
        return 0

    pattern = re.compile(
        r'(        logger\.info\(\n            f"\[Sim\] DIRECT ENTRY)',
        re.MULTILINE,
    )
    new, n = pattern.subn(INSERT + r"\1", src, count=1)
    if n != 1:
        print("ERREUR : ancre 'DIRECT ENTRY' introuvable — patch annule.", file=sys.stderr)
        return 1

    TARGET.with_suffix(".py.bak_edgegate").write_text(src)
    TARGET.write_text(new)
    print("Gate edge>cout applique ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
