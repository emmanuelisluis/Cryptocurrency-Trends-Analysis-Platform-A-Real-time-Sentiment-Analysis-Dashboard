import asyncio
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import List, Callable, Any, Dict, Optional, Tuple

import websockets
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from backend.app.models.exchange_data import TradeData, OrderBookData, OrderBookLevel, TickerData
from backend.app.core.config import settings

logger = logging.getLogger(__name__)
# BasicConfig should ideally be called once at application startup (e.g. in run_ingestion.py or main.py)
# If multiple modules call it, it might not behave as expected or be overridden.
# For now, ensuring it's here for standalone testing if __name__ == "__main__".
if not logger.hasHandlers(): # Avoid duplicate handlers if already configured
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


StreamKey = Tuple[str, str] # (symbol, stream_type like 'trade', 'depth', 'ticker')

class BinanceWebSocketClient:
    BASE_URL = "wss://stream.binance.com:9443/ws"
    EXCHANGE_NAME = "binance"
    STALENESS_THRESHOLD_SECONDS = 60 # Mark as stale if no message for this long

    def __init__(self, symbols: List[str], callback: Callable[[Any], None]):
        self.symbols = [s.lower() for s in symbols]
        self.callback = callback
        self._running = False
        self._tasks: List[asyncio.Task] = []

        # Status tracking attributes
        self.overall_connection_status: str = "initializing" # "connected", "connecting", "disconnected", "error", "stopped"
        self.connection_error_message: Optional[str] = None

        # Per-stream status: Dict[StreamKey, Dict[str, Any]]
        self.stream_statuses: Dict[StreamKey, Dict[str, Any]] = {}
        for symbol in self.symbols:
            for stream_type_suffix in ["trade", "depth", "ticker"]: # Corresponds to @trade, @depth, @ticker
                stream_key = (symbol, stream_type_suffix)
                self.stream_statuses[stream_key] = {
                    "status": "initializing", # "connected", "connecting", "disconnected", "error", "stale"
                    "last_message_timestamp": None,
                    "error_message": None,
                    "stream_name": f"{symbol}@{stream_type_suffix}" # Store for easy access
                }
        self.overall_connection_status = "initialized"

    def _update_stream_status(self, symbol: str, stream_type_suffix: str, status: str,
                              timestamp: Optional[datetime] = None, error_message: Optional[str] = None):
        stream_key = (symbol.lower(), stream_type_suffix)
        if stream_key in self.stream_statuses:
            self.stream_statuses[stream_key]["status"] = status
            if timestamp: # Only update timestamp if provided (i.e., on new message)
                self.stream_statuses[stream_key]["last_message_timestamp"] = timestamp
            if status in ["error", "disconnected"] and error_message: # Store error message
                 self.stream_statuses[stream_key]["error_message"] = error_message
            elif status == "connected": # Clear previous error on successful connect
                 self.stream_statuses[stream_key]["error_message"] = None
        else:
            logger.warning(f"Attempted to update status for unknown stream: {symbol}@{stream_type_suffix}")

    async def _connect_and_listen(self, symbol:str, stream_type_suffix: str, parser: Callable[[Dict[str, Any]], Any]):
        stream_name = f"{symbol}@{stream_type_suffix}"
        url = f"{self.BASE_URL}/{stream_name}"
        reconnect_delay = 5

        self._update_stream_status(symbol, stream_type_suffix, "connecting")

        while self._running:
            try:
                async with websockets.connect(url) as websocket:
                    self._update_stream_status(symbol, stream_type_suffix, "connected")
                    self.overall_connection_status = "connected" # If at least one stream connects
                    self.connection_error_message = None # Clear global error on successful connect
                    logger.info(f"Connected to Binance {stream_type_suffix} stream: {stream_name}")
                    reconnect_delay = 5
                    async for message_raw in websocket:
                        try:
                            data = json.loads(message_raw)
                            if "result" in data and data["result"] is None:
                                logger.info(f"Subscription confirmed for {stream_name}: {data}")
                                continue
                            if "e" in data and data["e"] == "error": # Should be caught by websockets library raising exception?
                                logger.error(f"Error message from {stream_name}: {data}")
                                self._update_stream_status(symbol, stream_type_suffix, "error", error_message=str(data))
                                continue # Or break and reconnect depending on error type

                            parsed_data = parser(data)
                            if parsed_data:
                                self._update_stream_status(symbol, stream_type_suffix, "connected", timestamp=datetime.now(timezone.utc))
                                self.callback(parsed_data)
                        except json.JSONDecodeError:
                            logger.error(f"Error decoding JSON from {stream_name}: {message_raw}")
                            # Status remains 'connected' but error could be logged or handled
                        except Exception as e:
                            logger.error(f"Error processing message from {stream_name}: {e} - Data: {message_raw}")
                            # Status remains 'connected'

            except (ConnectionClosedError, ConnectionClosedOK, ConnectionRefusedError, asyncio.TimeoutError) as e:
                err_msg = f"Connection to {stream_name} closed/failed: {type(e).__name__}. Reconnecting in {reconnect_delay}s..."
                logger.warning(err_msg)
                self._update_stream_status(symbol, stream_type_suffix, "disconnected", error_message=str(e))
                self.overall_connection_status = "error" # Or "degraded"
                self.connection_error_message = err_msg
            except Exception as e: # Broad exception catch for unexpected issues during connect/listen
                err_msg = f"Unexpected error with {stream_name}: {e}. Reconnecting in {reconnect_delay}s..."
                logger.error(err_msg)
                self._update_stream_status(symbol, stream_type_suffix, "error", error_message=str(e))
                self.overall_connection_status = "error"
                self.connection_error_message = err_msg

            if self._running:
                self._update_stream_status(symbol, stream_type_suffix, "connecting") # Set to connecting before sleep
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, 60)
            else:
                self._update_stream_status(symbol, stream_type_suffix, "stopped")
                logger.info(f"Listener for {stream_name} stopping as client is no longer running.")
                break

        if not self._running: # if loop exited due to _running being false
             self._update_stream_status(symbol, stream_type_suffix, "stopped")
        # If loop exited for other reasons (e.g. max retries, unrecoverable error - not implemented yet)
        # then status might remain 'error' or 'disconnected'.
        logger.info(f"Listener for {stream_name} fully stopped.")


    def _parse_trade_data(self, data: Dict[str, Any]) -> Optional[TradeData]:
        try:
            # Determine aggressor side:
            # If 'm' is true (isBuyerMaker), the buyer placed a passive order (was on the book),
            # so the seller was the aggressor (taker) by hitting that bid. Aggressor is 'sell'.
            # If 'm' is false, the buyer was the taker (aggressor). Aggressor is 'buy'.
            aggressor_side = 'sell' if data.get('m', False) else 'buy' # Default to 'buy' aggressor if 'm' is missing, though it should be there

            # The 'side' of the trade from Binance's perspective often refers to the taker's action.
            # If buyer is maker (m=true), it was a sell hitting a bid. So trade side is 'sell'.
            # If buyer is not maker (m=false, buyer is taker), it was a buy hitting an ask. So trade side is 'buy'.
            # This matches our aggressor_side logic.
            # The `side` field in TradeData should represent the taker's side.
            trade_side = aggressor_side

            return TradeData(
                timestamp=datetime.fromtimestamp(data['T'] / 1000, tz=timezone.utc),
                price=float(data['p']),
                volume=float(data['q']),
                side=trade_side, # This is the taker's side
                exchange=self.EXCHANGE_NAME,
                symbol=data['s'].lower(),
                trade_id=str(data['t']),
                aggressor_side=aggressor_side # Explicitly store the aggressor
            )
        except KeyError as e:
            logger.error(f"KeyError parsing trade data: {e} - Data: {data}")
            return None
        except Exception as e: # Catch any other parsing errors
            logger.error(f"General error parsing trade data: {e} - Data: {data}")
            return None

    def _parse_order_book_data(self, data: Dict[str, Any]) -> Optional[OrderBookData]:
        # ... (parser code remains the same, ensure symbol is from data['s'])
        try:
            bids = [OrderBookLevel(price=float(p), volume=float(v)) for p, v in data['b']]
            asks = [OrderBookLevel(price=float(p), volume=float(v)) for p, v in data['a']]
            return OrderBookData(
                timestamp=datetime.fromtimestamp(data['E'] / 1000, tz=timezone.utc),
                symbol=data['s'].lower(), exchange=self.EXCHANGE_NAME,
                bids=bids, asks=asks, last_update_id=data.get('u')
            )
        except KeyError as e: logger.error(f"KeyError parsing order book data: {e} - Data: {data}"); return None

    def _parse_ticker_data(self, data: Dict[str, Any]) -> Optional[TickerData]:
        # ... (parser code remains the same, ensure symbol is from data['s'])
        try:
            return TickerData(
                timestamp=datetime.fromtimestamp(data['E'] / 1000, tz=timezone.utc),
                symbol=data['s'].lower(), exchange=self.EXCHANGE_NAME,
                last_price=float(data['c']), volume_24h=float(data['v']),
                high_24h=float(data['h']), low_24h=float(data['l']),
                price_change_percent_24h=float(data['P'])
            )
        except KeyError as e: logger.error(f"KeyError parsing ticker data: {e} - Data: {data}"); return None
        except TypeError as e: logger.error(f"TypeError parsing ticker data: {e} - Data: {data}"); return None

    async def _create_subscription_tasks(self):
        self._tasks.clear() # Clear any old tasks if this is called multiple times (e.g. restart)
        stream_configs = [
            ("trade", self._parse_trade_data),
            ("depth", self._parse_order_book_data), # L2 depth
            ("ticker", self._parse_ticker_data)
        ]
        for symbol in self.symbols:
            for stream_type_suffix, parser in stream_configs:
                task = asyncio.create_task(self._connect_and_listen(symbol, stream_type_suffix, parser))
                self._tasks.append(task)
        logger.info(f"All ({len(self._tasks)}) subscription tasks created for symbols: {self.symbols}")

    async def start(self):
        if self._running:
            logger.warning("Client is already running.")
            return
        self._running = True
        self.overall_connection_status = "starting"
        logger.info("BinanceWebSocketClient starting...")
        await self._create_subscription_tasks()
        # overall_connection_status will be updated by _connect_and_listen
        # For now, start() is non-blocking. If all tasks fail immediately, status might not reflect "connected".

    async def stop(self):
        if not self._running and not self._tasks: # Check tasks too in case it was never fully started
            logger.warning("Client is not running or already stopped.")
            return

        logger.info("BinanceWebSocketClient stopping...")
        self._running = False
        self.overall_connection_status = "stopping"

        for task in self._tasks:
            if not task.done():
                task.cancel()

        results = await asyncio.gather(*self._tasks, return_exceptions=True)
        for i, result in enumerate(results): # Logging for any errors during task cancellation
            original_task_name = self._tasks[i].get_name() if hasattr(self._tasks[i], 'get_name') else f"Task-{i}"
            if isinstance(result, asyncio.CancelledError):
                logger.info(f"{original_task_name} was cancelled successfully.")
            elif isinstance(result, Exception):
                logger.error(f"{original_task_name} raised an exception during stop: {result}")

        self._tasks.clear()
        # Update all stream statuses to "stopped"
        for symbol in self.symbols:
            for stream_type_suffix in ["trade", "depth", "ticker"]:
                 self._update_stream_status(symbol, stream_type_suffix, "stopped")
        self.overall_connection_status = "stopped"
        logger.info("BinanceWebSocketClient stopped and all tasks cancelled/completed.")

    def get_status(self) -> Dict[str, Any]:
        """ Returns a summary of the client's health for all its subscribed symbols/streams. """
        symbol_statuses = {}
        now = datetime.now(timezone.utc)

        # Determine overall client connection status based on stream statuses
        # If any stream is 'connected' or 'connecting', client might be considered 'connected' or 'degraded'.
        # If all are 'disconnected' or 'error', client is 'error' or 'disconnected'.
        # This is a simple heuristic.
        client_level_status = self.overall_connection_status
        if self.overall_connection_status == "connected" and not any(s["status"] == "connected" for s in self.stream_statuses.values()):
             if any(s["status"] == "connecting" for s in self.stream_statuses.values()):
                 client_level_status = "connecting"
             elif any(s["status"] in ["error", "disconnected"] for s in self.stream_statuses.values()):
                 client_level_status = "degraded" # Some streams down

        for symbol in self.symbols:
            symbol_status_summary = {
                "symbol": symbol,
                "streams": [],
                "error": None # Placeholder for symbol-level specific errors if any in future
            }

            symbol_has_active_stream = False
            symbol_has_error = False

            for stream_type_suffix in ["trade", "depth", "ticker"]:
                stream_key = (symbol, stream_type_suffix)
                status_info = self.stream_statuses.get(stream_key)
                if not status_info: continue

                current_status = status_info["status"]
                last_msg_ts = status_info["last_message_timestamp"]

                # Check for staleness
                if current_status == "connected" and last_msg_ts:
                    if (now - last_msg_ts) > timedelta(seconds=self.STALENESS_THRESHOLD_SECONDS):
                        current_status = "stale"

                symbol_status_summary["streams"].append({
                    "stream_type": stream_type_suffix, # e.g. "trade", "depth", "ticker"
                    "status": current_status,
                    "last_message_at": last_msg_ts.isoformat() if last_msg_ts else None,
                    "error_message": status_info["error_message"]
                })
                if current_status == "connected": symbol_has_active_stream = True
                if current_status == "error": symbol_has_error = True

            # Determine overall status for the symbol
            # This is a simple heuristic for the symbol's "overall_connection_status" for the Pydantic model
            # It might differ from the client_level_status which is more global.
            if any(s["status"] == "connected" for s in symbol_status_summary["streams"]):
                symbol_status_summary["overall_symbol_status"] = "connected"
            elif any(s["status"] == "stale" for s in symbol_status_summary["streams"]):
                 symbol_status_summary["overall_symbol_status"] = "stale"
            elif any(s["status"] == "connecting" for s in symbol_status_summary["streams"]):
                symbol_status_summary["overall_symbol_status"] = "connecting"
            elif symbol_has_error:
                symbol_status_summary["overall_symbol_status"] = "error"
            else: # disconnected, stopped, initializing
                # Prioritize "disconnected" if any stream is disconnected
                if any(s["status"] == "disconnected" for s in symbol_status_summary["streams"]):
                     symbol_status_summary["overall_symbol_status"] = "disconnected"
                else: # Pick the status of the first stream or a sensible default.
                    symbol_status_summary["overall_symbol_status"] = symbol_status_summary["streams"][0]["status"] if symbol_status_summary["streams"] else "unknown"


            symbol_statuses[symbol] = symbol_status_summary

        return {
            "exchange_name": self.EXCHANGE_NAME,
            "client_connection_status": client_level_status, # Global status of the client itself
            "client_error_message": self.connection_error_message,
            "symbols": list(symbol_statuses.values())
        }

# Example Usage (for testing status - can be removed or kept for standalone tests)
async def main_test_status():
    def dummy_callback(data):
        # In a real scenario, this callback would process data (e.g., write to DB)
        # logger.info(f"Callback received: {type(data)} for {data.symbol if hasattr(data, 'symbol') else 'N/A'}")
        pass

    client = BinanceWebSocketClient(symbols=["btcusdt", "ethusdt"], callback=dummy_callback)

    try:
        await client.start()
        for i in range(15): # Print status every few seconds for a short period
            await asyncio.sleep(5)
            status = client.get_status()
            logger.info(f"Client Status (iteration {i+1}): {json.dumps(status, indent=2)}")
            # Simulate a stream going stale for testing (by not updating its timestamp)
            if i == 2 and ("btcusdt", "ticker") in client.stream_statuses:
                 logger.warning("Simulating btcusdt ticker going stale for testing get_status()...")
                 # To make it stale, we'd need to prevent its last_message_timestamp from updating
                 # This is hard to do from outside without direct manipulation or message interception
                 # The staleness check in get_status() itself will handle real scenarios.

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received.")
    finally:
        logger.info("Stopping client...")
        await client.stop()
        logger.info("Client stopped. Final status:")
        logger.info(json.dumps(client.get_status(), indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s [%(module)s.%(funcName)s:%(lineno)d]')
    # To test the status changes, you might need to simulate disconnections or stop your internet.
    asyncio.run(main_test_status())
