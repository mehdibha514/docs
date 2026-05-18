"""
PolyBot v2 — Feed prix BTC (Binance.US)
Surveillance BTC en temps réel via le flux aggTrade Binance.US.
Émet un signal instantané quand le prix bouge de >= CANDLE_THRESHOLD_PCT
sur une fenêtre glissante de WINDOW_SECONDS (~1s) — pour exploiter le lag
de l'oracle Polymarket (1-2s) avant l'ajustement du prix du marché.

HISTORIQUE / CHOIX DE LA SOURCE :
  - Binance.com bloque les IP US (HTTP 451) : INACCESSIBLE depuis un VPS US,
    impossible à contourner en code (blocage côté Binance, sur l'IP).
  - Binance.US ne diffuse PAS les klines 1s (WS connecté mais aucune donnée).
  - Binance.US btcusdt@aggTrade est quasi mort (~1 trade / 36s) : fenêtre 1s
    famélique → move toujours 0 % → quasi aucun signal.
  - Binance.US BTCUSD (sans T) est la paire liquide : flux aggTrade dense,
    on reste sur Binance, et ça fonctionne depuis un VPS US.
Pour utiliser le vrai Binance.com (source exacte de règlement Polymarket), il
faut faire tourner le bot depuis un VPS hors US — c'est une décision infra,
pas un changement de code (cf. BINANCE_SYMBOL / PRICE_WS_URL via .env).

La signature de on_signal est INCHANGÉE : le reste du bot n'a pas à bouger.
Le nom de classe BinanceWatcher est conservé pour ne pas casser les imports
existants (simulate.py / main.py).
"""

import asyncio
import collections
import json
import logging
import os
import time
from typing import Callable

import aiohttp

import config

logger = logging.getLogger("polybot.binance")

# Binance.US — paire BTCUSD (liquide). Surchargeable via .env si un jour le
# bot tourne hors US (ex: PRICE_WS_URL=wss://stream.binance.com:9443,
# BINANCE_SYMBOL=btcusdt).
BINANCE_WS_BASE = os.getenv("PRICE_WS_URL", "wss://stream.binance.us:9443")
BINANCE_SYMBOL = os.getenv("BINANCE_SYMBOL", "btcusd").lower()
WS_URL = f"{BINANCE_WS_BASE}/ws/{BINANCE_SYMBOL}@aggTrade"

# Fenêtre glissante du détecteur de move (secondes). 1.0 = équivalent "bougie 1s".
WINDOW_SECONDS = float(os.getenv("MOVE_WINDOW_SECONDS", "1.0"))

# Délai max de reconnexion
MAX_RECONNECT_DELAY = 30


class BinanceWatcher:
    """
    Connexion WebSocket Coinbase — reçoit chaque trade BTC-USD en temps réel.

    Le callback on_signal(direction, open_price, close_price, move_pct) est
    appelé dès que le prix bouge de >= config.CANDLE_THRESHOLD_PCT sur les
    WINDOW_SECONDS dernières secondes.
      direction   = "UP" (hausse) | "DOWN" (baisse)
      open_price  = prix de référence (~WINDOW_SECONDS en arrière)
      close_price = dernier prix
      move_pct    = amplitude du move (ex: 0.0003 = 0.03%)
    """

    def __init__(self, on_signal: Callable):
        self.on_signal = on_signal
        self._running = False
        self._reconnect_delay = 1  # secondes, double à chaque échec
        self._tick_count = 0
        self._last_hb_tick_count = 0
        self._max_move_pct = 0.0
        self._last_heartbeat = 0.0
        self._last_minute_heartbeat = 0.0
        # buffer glissant (timestamp_s, price) limité à WINDOW_SECONDS
        self._window: collections.deque = collections.deque()
        # edge-trigger : un signal par mouvement, ré-armé seulement quand le
        # move repasse sous le seuil (évite de spammer on_signal et d'enchaîner
        # des ordres en boucle sur un même mouvement).
        self._armed = True
        self._signal_tasks: set = set()  # références fortes anti-GC

    async def start(self):
        self._running = True
        logger.info(
            f"[Binance] Démarrage — source: Binance.US {BINANCE_SYMBOL}@aggTrade | "
            f"seuil: {config.CANDLE_THRESHOLD_PCT*100:.2f}% "
            f"sur fenêtre glissante {WINDOW_SECONDS:.1f}s"
        )
        while self._running:
            try:
                await self._connect()
                self._reconnect_delay = 1  # reset après connexion réussie
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    f"[Binance] Connexion perdue: {e} — "
                    f"reconnexion dans {self._reconnect_delay}s"
                )
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(
                    self._reconnect_delay * 2, MAX_RECONNECT_DELAY
                )

    async def stop(self):
        self._running = False

    async def _connect(self):
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                WS_URL,
                heartbeat=20,
                receive_timeout=60,
            ) as ws:
                # Binance : le stream est dans l'URL, pas de souscription à envoyer.
                logger.info(
                    f"[Binance] ✅ Connecté — Binance.US {BINANCE_SYMBOL}@aggTrade actif"
                )
                async for msg in ws:
                    if not self._running:
                        break
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        await self._handle(msg.data)
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        logger.warning(f"[Binance] Erreur WS: {ws.exception()}")
                        break
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        logger.warning("[Binance] Connexion fermée par le feed")
                        break

    async def _handle(self, raw: str):
        try:
            data = json.loads(raw)

            # flux aggTrade Binance : prix du trade dans "p"
            price = float(data.get("p", 0))
            if price <= 0:
                return

            now = time.time()

            # alimente le buffer glissant et purge ce qui dépasse la fenêtre
            self._window.append((now, price))
            cutoff = now - WINDOW_SECONDS
            while self._window and self._window[0][0] < cutoff:
                self._window.popleft()

            # prix de référence = le plus ancien encore dans la fenêtre
            ref_price = self._window[0][1]
            move_pct = abs(price - ref_price) / ref_price

            self._tick_count += 1
            if move_pct > self._max_move_pct:
                self._max_move_pct = move_pct

            # Heartbeat — INFO toutes les 60s. Affiche le DÉBIT du feed
            # (trades/s) pour qu'une famine de données soit immédiatement
            # visible (c'est ce qui avait été masqué avec Binance.US).
            if now - self._last_heartbeat >= 1:
                logger.debug(
                    f"[Binance] BTC: {price:.1f} | "
                    f"Move {WINDOW_SECONDS:.0f}s: {self._max_move_pct*100:.4f}% | "
                    f"Seuil: {config.CANDLE_THRESHOLD_PCT*100:.4f}%"
                )
                if now - self._last_minute_heartbeat >= 60:
                    span = now - self._last_minute_heartbeat
                    n = self._tick_count - self._last_hb_tick_count
                    rate = n / span if span > 0 else 0.0
                    logger.info(
                        f"[Binance] ❤️ Actif | BTC: {price:.1f} | "
                        f"Max move {WINDOW_SECONDS:.0f}s: {self._max_move_pct*100:.4f}% | "
                        f"débit: {rate:.1f} trades/s ({self._tick_count} total)"
                    )
                    self._last_minute_heartbeat = now
                    self._last_hb_tick_count = self._tick_count
                self._last_heartbeat = now
                self._max_move_pct = 0.0  # reset chaque seconde

            # Détecteur edge-triggered : UN signal par mouvement.
            if move_pct < config.CANDLE_THRESHOLD_PCT:
                self._armed = True
                return
            if not self._armed:
                return  # déjà signalé pour ce mouvement, on attend qu'il retombe
            self._armed = False

            direction = "UP" if price > ref_price else "DOWN"
            logger.info(
                f"[Binance] SIGNAL | "
                f"BTC {'↑' if direction == 'UP' else '↓'} {move_pct*100:.4f}% "
                f"({ref_price:.1f} -> {price:.1f}) en {WINDOW_SECONDS:.0f}s | "
                f"Direction: {direction}"
            )
            task = asyncio.create_task(
                self.on_signal(direction, ref_price, price, move_pct)
            )
            self._signal_tasks.add(task)

            def _signal_done(t: asyncio.Task):
                self._signal_tasks.discard(t)
                if not t.cancelled() and t.exception():
                    logger.error(
                        f"[Binance] Exception non-catchée dans on_signal : "
                        f"{type(t.exception()).__name__}: {t.exception()}",
                        exc_info=t.exception(),
                    )

            task.add_done_callback(_signal_done)

        except Exception as e:
            logger.warning(f"[Binance] Erreur parsing message: {e}")
