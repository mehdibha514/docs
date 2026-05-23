"""
PolyBot v2 — Paper Trader (fill réaliste sur carnet réel)
Simule les ordres BUY/SELL sans argent réel.

Interface identique à Trader — remplacement drop-in.
is_paper_mode = True — jamais d'argent réel touché.

RÉALISME (objectif : zéro surprise au passage en réel) :
  - Le fill n'est PLUS un slippage forfaitaire. On récupère le VRAI carnet
    d'ordres Polymarket (CLOB /book) et on le "marche" niveau par niveau :
      * plus la mise est grosse, plus on paie cher (impact de profondeur réel) ;
      * si la liquidité manque → FILL PARTIEL (on ne reçoit que le dispo) ;
      * on est preneur (taker) : on paie l'ask / on vend au bid réels.
  - Slippage de latence : petite dégradation conservatrice pour modéliser le
    carnet qui bouge pendant les 1-2 s de latence (PAPER_LATENCY_SLIPPAGE).
  - But : le PnL paper est un PLANCHER réaliste, jamais au-dessus du réel.
"""

import asyncio
import logging
import os
import time
from typing import Optional

import requests

from bot.trader import OrderResult

logger = logging.getLogger("polybot.paper_trader")

CLOB_API = "https://clob.polymarket.com"

# Dégradation conservatrice pour le carnet qui bouge pendant la latence (1-2 s).
# 0.001 = 0.1%. Surchargeable via .env si tu veux plus/moins pessimiste.
LATENCY_SLIPPAGE = float(os.getenv("PAPER_LATENCY_SLIPPAGE", "0.001"))

# Slippage de repli UNIQUEMENT si le carnet est indisponible (API down).
FALLBACK_SLIPPAGE = 0.005


class PaperTrader:
    """
    Paper Trading — fill simulé sur le carnet d'ordres CLOB Polymarket réel.

    is_paper_mode = True → les fonctions qui vérifient ce flag savent que
    c'est une simulation.
    """

    is_paper_mode: bool = True

    def __init__(self):
        self._initialized = True
        self._init_error = None
        self._trade_count = 0

    async def initialize(self) -> bool:
        logger.info(
            "[PaperTrader] ✅ Paper Trader actif — AUCUN argent réel, "
            f"fill réaliste sur carnet CLOB (latence {LATENCY_SLIPPAGE*100:.2f}%)"
        )
        return True

    @property
    def is_ready(self) -> bool:
        return True

    # ── Carnet d'ordres réel ─────────────────────────────────────────────────

    async def get_order_book(self, token_id: str) -> Optional[dict]:
        """Carnet complet (bids/asks avec tailles) depuis le CLOB Polymarket."""
        try:
            resp = await asyncio.wait_for(
                asyncio.to_thread(
                    requests.get,
                    f"{CLOB_API}/book",
                    params={"token_id": token_id},
                    timeout=10,
                ),
                timeout=12,
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.warning(
                f"[PaperTrader] Carnet indisponible pour {token_id[:20]}…: {e}"
            )
        return None

    @staticmethod
    def _levels(raw, reverse: bool):
        """Normalise et trie les niveaux [(price, size), …].

        reverse=False → ASKS, tri croissant (meilleur = plus bas en premier).
        reverse=True  → BIDS, tri décroissant (meilleur = plus haut en premier).
        """
        out = []
        for lvl in raw or []:
            try:
                px = float(lvl["price"])
                sz = float(lvl["size"])
            except (KeyError, TypeError, ValueError):
                continue
            if px > 0 and sz > 0:
                out.append((px, sz))
        out.sort(key=lambda x: x[0], reverse=reverse)
        return out

    # ── BUY simulé (on marche les ASKS) ──────────────────────────────────────

    async def bet(
        self,
        market: dict,
        side: str,
        amount_usdc: float,
        price_override: Optional[float] = None,
    ) -> OrderResult:
        token_id = (
            market.get("yes_token_id") if side == "UP"
            else market.get("no_token_id")
        )
        ref_price = (
            price_override if (price_override and price_override > 0)
            else (market["yes_price"] if side == "UP" else market["no_price"])
        )
        if ref_price <= 0:
            return OrderResult(
                success=False,
                error=f"[PAPER] Prix invalide ({ref_price}) — ordre simulé annulé",
            )

        book = await self.get_order_book(token_id) if token_id else None
        asks = self._levels(book.get("asks") if book else None, reverse=False)

        if asks:
            spent = 0.0
            tokens = 0.0
            remaining = amount_usdc
            for px, sz in asks:
                if remaining <= 1e-9:
                    break
                level_usdc = px * sz
                take = min(remaining, level_usdc)
                tokens += take / px
                spent += take
                remaining -= take

            if tokens <= 0:
                return OrderResult(
                    success=False,
                    error="[PAPER] Aucune liquidité au carnet — ordre annulé",
                )

            avg_price = spent / tokens
            # latence : le carnet bouge contre nous pendant 1-2 s
            fill_price = round(min(avg_price * (1 + LATENCY_SLIPPAGE), 0.999), 4)
            tokens = round(spent / fill_price, 2)
            cost = round(spent, 4)
            partial = remaining > 0.01
            src = f"carnet réel ({len(asks)} niveaux)"
        else:
            # Repli : carnet indisponible → slippage forfaitaire conservateur
            fill_price = round(min(ref_price * (1 + FALLBACK_SLIPPAGE), 0.99), 4)
            cost = round(amount_usdc, 4)
            tokens = round(amount_usdc / fill_price, 2)
            partial = False
            src = "REPLI (carnet indispo)"

        self._trade_count += 1
        order_id = f"PAPER-{self._trade_count:04d}-{int(time.time() * 1000) % 100000}"

        flag = " ⚠️ FILL PARTIEL" if partial else ""
        logger.info(
            f"[PaperTrader] 📝 PAPER BUY {side}{flag} | "
            f"demandé={ref_price:.4f} | fill={fill_price:.4f} ({src}) | "
            f"voulu={amount_usdc:.2f}$ rempli={cost:.2f}$ | "
            f"{tokens:.2f} tokens | id={order_id}"
        )

        result = OrderResult(
            success=True,
            order_id=order_id,
            filled_amount=cost,
            avg_price=fill_price,
            tokens_received=tokens,
        )
        result.is_paper = True
        return result

    # ── SELL simulé (on marche les BIDS) ─────────────────────────────────────

    async def exit_position(self, position: dict, current_price: float) -> OrderResult:
        tokens = position.get("tokens", 0.0)
        token_id = position.get("token_id")

        book = await self.get_order_book(token_id) if token_id else None
        bids = self._levels(book.get("bids") if book else None, reverse=True)

        # ANTI-BUG : on ne vend JAMAIS au-dessus du bid réellement actionnable
        # (current_price, confirmé par le WS). Le /book REST contient des ordres
        # limites fantômes très au-dessus du vrai marché (bids périmés) — les
        # prendre simulait des ventes à des prix qui ne s'exécuteraient jamais
        # (ex : stop-loss qui ressortait en "profit"). On les filtre.
        cap = current_price if (current_price and current_price > 0) else None
        if cap is not None:
            bids = [(px, sz) for (px, sz) in bids if px <= cap * 1.001]

        if bids:
            usdc = 0.0
            sold = 0.0
            remaining = tokens
            for px, sz in bids:
                if remaining <= 1e-9:
                    break
                take = min(remaining, sz)
                usdc += take * px
                sold += take
                remaining -= take

            if sold <= 0:
                fill_price = round(max(current_price * (1 - FALLBACK_SLIPPAGE), 0.01), 4)
                usdc_out = round(tokens * fill_price, 4)
                src = "REPLI (aucun bid)"
                partial = False
            else:
                avg_price = usdc / sold
                fill_price = round(max(avg_price * (1 - LATENCY_SLIPPAGE), 0.01), 4)
                usdc_out = round(sold * fill_price, 4)
                partial = remaining > 1e-6
                src = f"carnet réel ({len(bids)} niveaux)"
        else:
            fill_price = round(max(current_price * (1 - FALLBACK_SLIPPAGE), 0.01), 4)
            usdc_out = round(tokens * fill_price, 4)
            src = "REPLI (carnet indispo)"
            partial = False

        order_id = f"PAPER-EXIT-{int(time.time() * 1000) % 100000}"
        flag = " ⚠️ VENTE PARTIELLE" if partial else ""
        logger.info(
            f"[PaperTrader] 📝 PAPER SELL{flag} | tokens={tokens:.4f} "
            f"vendus={(sold if bids else tokens):.4f} | "
            f"fill={fill_price:.4f} ({src}) | USDC out={usdc_out:.4f}$ | id={order_id}"
        )

        result = OrderResult(
            success=True,
            order_id=order_id,
            filled_amount=usdc_out,
            avg_price=fill_price,
        )
        result.is_paper = True
        return result

    # ── Prix réels CLOB (inchangé) ───────────────────────────────────────────

    async def get_current_price(self, token_id: str) -> Optional[float]:
        """Prix ASK (côté achat) depuis le CLOB en temps réel."""
        try:
            resp = await asyncio.wait_for(
                asyncio.to_thread(
                    requests.get,
                    f"{CLOB_API}/price",
                    params={"token_id": token_id, "side": "BUY"},
                    timeout=10,
                ),
                timeout=12,
            )
            if resp.status_code == 200:
                return float(resp.json().get("price", 0)) or None
        except Exception as e:
            logger.debug(f"[PaperTrader] Prix ASK indisponible pour {token_id[:20]}…: {e}")
        return None

    async def get_bid_price(self, token_id: str) -> Optional[float]:
        """Prix BID (côté vente) depuis le CLOB en temps réel."""
        try:
            resp = await asyncio.wait_for(
                asyncio.to_thread(
                    requests.get,
                    f"{CLOB_API}/price",
                    params={"token_id": token_id, "side": "SELL"},
                    timeout=10,
                ),
                timeout=12,
            )
            if resp.status_code == 200:
                return float(resp.json().get("price", 0)) or None
        except Exception as e:
            logger.debug(f"[PaperTrader] Prix BID indisponible pour {token_id[:20]}…: {e}")
        return None

    async def get_prices_batch(self, token_ids: list) -> dict:
        prices = {}
        tasks = [self.get_current_price(tid) for tid in token_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for tid, price in zip(token_ids, results):
            if isinstance(price, float) and price > 0:
                prices[tid] = price
        return prices
