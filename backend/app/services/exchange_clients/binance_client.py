import asyncio
import json
import logging
# import time # time module was imported but not used. # No longer relevant, time was removed.
from datetime import datetime, timezone, timedelta
from typing import List, Callable, Any, Dict, Optional, Tuple

import websockets
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK, WebSocketException

from backend.app.models.exchange_data import TradeData, OrderBookData, OrderBookLevel, TickerData
# from backend.app.core.config import settings # settings is not used in this file currently.

logger = logging.getLogger(__name__)

# Ensure basic logging is configured if this module is run standalone or if no other config is set.
# This basicConfig should ideally be called once at the application's entry point.
# The check `if not logger.hasHandlers()` prevents adding multiple handlers if already configured.
if not logger.hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(module)s.%(funcName)s:%(lineno)d]'
    )

# Type alias for identifying a stream uniquely (symbol, stream_type_suffix)
StreamKey = Tuple[str, str]


class BinanceWebSocketClient:
    """
    A WebSocket client for Binance, handling connections, subscriptions,
    data parsing, and status reporting for multiple symbols and stream types.
    """
    BASE_URL = "wss://stream.binance.com:9443/ws"
    EXCHANGE_NAME = "binance"
    STALENESS_THRESHOLD_SECONDS = 60  # Time in seconds to mark a stream as stale if no messages arrive.
    MAX_RECONNECT_DELAY = 60  # Maximum delay in seconds for exponential backoff.

    def __init__(self, symbols: List[str], callback: Callable[[Any], None]):
        """
        Initializes the BinanceWebSocketClient.

        Args:
            symbols (List[str]): A list of trading symbols to subscribe to
                (e.g., ['btcusdt', 'ethusdt']). Symbols will be lowercased.
            callback (Callable[[Any], None]): A callback function that will be
                invoked with parsed data models (TradeData, OrderBookData, TickerData)
                as they are received from the WebSocket streams.
        """
        self.symbols: List[str] = [s.lower() for s in symbols]  # Standardize symbols
        self.callback: Callable[[Any], None] = callback
        self._running: bool = False
        self._tasks: List[asyncio.Task] = []

        # --- Status Tracking Attributes ---
        self.overall_connection_status: str = "initializing"
        self.connection_error_message: Optional[str] = None

        # Per-stream status, keyed by (symbol, stream_type_suffix)
        self.stream_statuses: Dict[StreamKey, Dict[str, Any]] = {}
        for symbol_str in self.symbols: # Renamed to avoid conflict with 'symbol' var in _connect_and_listen
            for stream_type_suffix_str in ["trade", "depth", "ticker"]:
                stream_key: StreamKey = (symbol_str, stream_type_suffix_str)
                self.stream_statuses[stream_key] = {
                    "status": "initializing",
                    "last_message_timestamp": None,
                    "error_message": None,
                    "stream_name": f"{symbol_str}@{stream_type_suffix_str}"
                }
        self.overall_connection_status = "initialized"
        logger.info(f"BinanceWebSocketClient initialized for symbols: {self.symbols}")

    def _update_stream_status(self,
                              symbol: str,
                              stream_type_suffix: str,
                              status: str,
                              timestamp: Optional[datetime] = None,
                              error_message: Optional[str] = None):
        """
        Helper method to update the operational status of a specific data stream.

        This method centralizes status updates for individual streams (e.g., 'btcusdt@trade').
        It logs the status change and updates the `stream_statuses` dictionary.

        Args:
            symbol (str): The market symbol of the stream (e.g., 'btcusdt').
            stream_type_suffix (str): The type of the stream ('trade', 'depth', 'ticker').
            status (str): The new status (e.g., "connecting", "connected", "error", "stale").
            timestamp (Optional[datetime]): The timestamp of the event causing the status change
                (typically the arrival of a new message). Defaults to None.
            error_message (Optional[str]): An error message if the status indicates an error
                or disconnection. Defaults to None.
        """
        stream_key = (symbol.lower(), stream_type_suffix)
        if stream_key in self.stream_statuses:
            current_status_info = self.stream_statuses[stream_key]
            current_status_info["status"] = status
            if timestamp:  # Update timestamp only if one is provided (i.e., on new message)
                current_status_info["last_message_timestamp"] = timestamp

            # Store error message if status indicates an error or disconnection
            if status in ["error", "disconnected", "stale"] and error_message: # Added "stale"
                 current_status_info["error_message"] = error_message
            elif status == "connected": # Clear previous error on successful (re)connection
                 current_status_info["error_message"] = None

            logger.debug(f"Status update for {self.EXCHANGE_NAME} {symbol}@{stream_type_suffix}: {status}" + (f" Error: {error_message}" if error_message else ""))
        else:
            logger.warning(f"Attempted to update status for unknown stream key: {stream_key} ({self.EXCHANGE_NAME})")

    async def _connect_and_listen(self,
                                  symbol: str,
                                  stream_type_suffix: str,
                                  parser: Callable[[Dict[str, Any]], Any]):
        """
        Connects to a specific Binance WebSocket stream, listens for messages,
        parses them, and handles reconnection logic.

        This is the core method for each individual WebSocket connection. It runs in an
        infinite loop (as long as `self._running` is True), attempting to connect,
        receive messages, and then reconnect on disconnections or errors.

        Args:
            symbol (str): The trading symbol for this stream (e.g., 'btcusdt').
            stream_type_suffix (str): The type of stream ('trade', 'depth', 'ticker').
            parser (Callable[[Dict[str, Any]], Any]): The function responsible for parsing
                the raw JSON message from this stream into a Pydantic model.
        """
        stream_name = f"{symbol}@{stream_type_suffix}"
        url = f"{self.BASE_URL}/{stream_name}"
        reconnect_delay = 5  # Initial reconnect delay in seconds, increases exponentially.

        self._update_stream_status(symbol, stream_type_suffix, "connecting")
        logger.info(f"Attempting to connect to {self.EXCHANGE_NAME} stream: {stream_name} at {url}")

        while self._running:
            try:
                # `websockets.connect` is an async context manager for WebSocket connections.
                # ping_interval and ping_timeout help keep the connection alive and detect dead connections.
                async with websockets.connect(url, ping_interval=20, ping_timeout=20) as websocket:
                    self._update_stream_status(symbol, stream_type_suffix, "connected", timestamp=datetime.now(timezone.utc))
                    # Update overall client status if this is the first successful connection or recovers from an error state.
                    if self.overall_connection_status != "connected":
                        if any(s_info["status"] == "connected" for s_info in self.stream_statuses.values()):
                             self.overall_connection_status = "connected"
                    self.connection_error_message = None # Clear global error on any successful stream connection

                    logger.info(f"Successfully connected to {self.EXCHANGE_NAME} stream: {stream_name}")
                    reconnect_delay = 5  # Reset reconnect delay on successful connection

                    # Listen for messages on the WebSocket
                    async for message_raw in websocket:
                        try:
                            data = json.loads(message_raw) # Messages are expected to be JSON strings.

                            # Binance may send confirmation/result messages (though often just starts data flow).
                            if "result" in data and data.get("id") is not None:
                                logger.info(f"Subscription confirmation or response for {stream_name}: {data}")
                                continue # Skip further processing for these messages.

                            # Check for explicit error messages within the stream data (format may vary).
                            if isinstance(data, dict) and data.get("e") == "error": # Example error format
                                error_detail = data.get('m', 'Unknown stream error')
                                logger.error(f"Error message received from stream {stream_name}: {error_detail}")
                                self._update_stream_status(symbol, stream_type_suffix, "error", error_message=error_detail)
                                continue

                            parsed_data = parser(data) # Parse the raw data using the provided parser function.
                            if parsed_data:
                                # Update last message timestamp for this specific stream upon successful parsing.
                                self._update_stream_status(symbol, stream_type_suffix, "connected", timestamp=datetime.now(timezone.utc))
                                self.callback(parsed_data) # Pass the parsed Pydantic model to the main callback.
                        except json.JSONDecodeError:
                            logger.error(f"JSONDecodeError for stream {stream_name}: Malformed JSON received. Snippet: {message_raw[:200]}...")
                        except Exception as e:
                            logger.error(f"Error processing message from {stream_name}: {e}. Data snippet: {message_raw[:200]}...", exc_info=True)
                            # Note: Stream status remains 'connected' here unless the error is deemed critical for the stream itself.

            except (ConnectionClosedError, ConnectionClosedOK, ConnectionRefusedError, asyncio.TimeoutError, WebSocketException) as e:
                # These exceptions indicate issues with the WebSocket connection itself.
                err_msg_log = f"Connection to {stream_name} closed or failed: {type(e).__name__} - {e}. Reconnecting in {reconnect_delay}s..."
                logger.warning(err_msg_log)
                self._update_stream_status(symbol, stream_type_suffix, "disconnected", error_message=str(e))
                # Update overall client status based on the health of all streams.
                if not any(s_info["status"] == "connected" for s_info in self.stream_statuses.values()):
                    self.overall_connection_status = "error"
                else:
                    self.overall_connection_status = "degraded" # At least one stream is down, but others might be up.
                self.connection_error_message = f"Connection issues with {stream_name} on {self.EXCHANGE_NAME}." # More generic global error
            except Exception as e: # Catch any other unexpected errors during connection setup or management.
                err_msg_log = f"Unexpected error with stream {stream_name}: {type(e).__name__} - {e}. Reconnecting in {reconnect_delay}s..."
                logger.error(err_msg_log, exc_info=True)
                self._update_stream_status(symbol, stream_type_suffix, "error", error_message=str(e))
                self.overall_connection_status = "error" # Assume critical impact on client.
                self.connection_error_message = f"Unexpected error with {stream_name} on {self.EXCHANGE_NAME}."

            if self._running: # Only attempt to reconnect if the client is supposed to be running.
                logger.info(f"Preparing to reconnect stream {stream_name} ({self.EXCHANGE_NAME}) after delay of {reconnect_delay}s.")
                # Preserve the last error message while attempting to reconnect.
                last_err_msg = self.stream_statuses.get((symbol, stream_type_suffix), {}).get("error_message")
                self._update_stream_status(symbol, stream_type_suffix, "connecting", error_message=last_err_msg)
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, self.MAX_RECONNECT_DELAY) # Exponential backoff for reconnection attempts.
            else: # If client was stopped (self._running is False).
                logger.info(f"Listener for {stream_name} ({self.EXCHANGE_NAME}) stopping as client is no longer running.")
                self._update_stream_status(symbol, stream_type_suffix, "stopped")
                break # Exit the while loop, terminating this connection task.

        # After the loop exits (either _running is False or an explicit break occurred).
        if not self._running: # Ensure final status is "stopped" if exited due to client stopping.
             self._update_stream_status(symbol, stream_type_suffix, "stopped")
        logger.info(f"Listener task for stream {stream_name} ({self.EXCHANGE_NAME}) has fully terminated.")


    def _parse_trade_data(self, data: Dict[str, Any]) -> Optional[TradeData]:
        """
        Parses raw trade data from a Binance WebSocket message into a TradeData Pydantic model.

        Handles mapping of Binance-specific fields to the standardized TradeData model.

        Args:
            data (Dict[str, Any]): The raw trade data dictionary from the WebSocket message.
                Expected keys from Binance: 'T' (timestamp), 'p' (price), 'q' (quantity),
                'm' (is_market_maker_sell), 's' (symbol), 't' (trade_id).

        Returns:
            Optional[TradeData]: A TradeData object if parsing is successful, otherwise None.
        """
        try:
            # 'm': true if the buyer is the maker (seller is taker), false if seller is maker (buyer is taker)
            # For our 'side' and 'aggressor_side':
            # If 'm' is true (buyer is maker), then the taker was the seller. So, aggressor_side = 'sell'.
            # If 'm' is false (seller is maker), then the taker was the buyer. So, aggressor_side = 'buy'.
            # The 'side' of the trade is conventionally the taker's side.
            aggressor_side = 'sell' if data.get('m', False) else 'buy' # Default to 'buy' if 'm' is missing for safety.
            trade_side = aggressor_side

            return TradeData(
                timestamp=datetime.fromtimestamp(data['T'] / 1000.0, tz=timezone.utc), # Binance timestamp is in milliseconds.
                price=float(data['p']),
                volume=float(data['q']),
                side=trade_side,
                exchange=self.EXCHANGE_NAME,
                symbol=data['s'].lower(),
                trade_id=str(data['t']), # Trade ID from Binance.
                aggressor_side=aggressor_side
            )
        except KeyError as e:
            logger.error(f"KeyError parsing trade data (Symbol: {data.get('s','N/A')}, Exchange: {self.EXCHANGE_NAME}): Missing key {e}. Data: {data}", exc_info=False)
            return None
        except Exception as e:
            logger.error(f"General error parsing trade data (Symbol: {data.get('s','N/A')}, Exchange: {self.EXCHANGE_NAME}): {e}. Data: {data}", exc_info=True)
            return None

    def _parse_order_book_data(self, data: Dict[str, Any]) -> Optional[OrderBookData]:
        """
        Parses raw order book (depth) data from a Binance WebSocket message
        into an OrderBookData Pydantic model.

        Args:
            data (Dict[str, Any]): The raw order book data dictionary.
                Expected keys from Binance: 'E' (event_time), 's' (symbol),
                'b' (bids as list of [price, volume]), 'a' (asks as list of [price, volume]),
                'u' (final_update_id_in_event).

        Returns:
            Optional[OrderBookData]: An OrderBookData object if successful, otherwise None.
        """
        try:
            bids = [OrderBookLevel(price=float(p_vol[0]), volume=float(p_vol[1])) for p_vol in data['b']]
            asks = [OrderBookLevel(price=float(p_vol[0]), volume=float(p_vol[1])) for p_vol in data['a']]
            return OrderBookData(
                timestamp=datetime.fromtimestamp(data['E'] / 1000.0, tz=timezone.utc), # Event time.
                symbol=data['s'].lower(),
                exchange=self.EXCHANGE_NAME,
                bids=bids,
                asks=asks,
                last_update_id=data.get('u') # Final update ID in this event.
            )
        except KeyError as e:
            logger.error(f"KeyError parsing order book data (Symbol: {data.get('s','N/A')}, Exchange: {self.EXCHANGE_NAME}): Missing key {e}. Data: {data}", exc_info=False)
            return None
        except Exception as e:
            logger.error(f"General error parsing order book data (Symbol: {data.get('s','N/A')}, Exchange: {self.EXCHANGE_NAME}): {e}. Data: {data}", exc_info=True)
            return None


    def _parse_ticker_data(self, data: Dict[str, Any]) -> Optional[TickerData]:
        """
        Parses raw ticker data from a Binance WebSocket message into a TickerData Pydantic model.

        Args:
            data (Dict[str, Any]): The raw ticker data dictionary.
                Expected keys from Binance for individual symbol ticker stream (@ticker):
                'E' (event_time), 's' (symbol), 'c' (last_price), 'v' (total_traded_base_asset_volume_24h),
                'h' (high_price_24h), 'l' (low_price_24h), 'P' (price_change_percent_24h).

        Returns:
            Optional[TickerData]: A TickerData object if successful, otherwise None.
        """
        try:
            return TickerData(
                timestamp=datetime.fromtimestamp(data['E'] / 1000.0, tz=timezone.utc), # Event time.
                symbol=data['s'].lower(),
                exchange=self.EXCHANGE_NAME,
                last_price=float(data['c']),
                volume_24h=float(data['v']),
                high_24h=float(data['h']),
                low_24h=float(data['l']),
                price_change_percent_24h=float(data['P'])
            )
        except KeyError as e:
            logger.error(f"KeyError parsing ticker data (Symbol: {data.get('s','N/A')}, Exchange: {self.EXCHANGE_NAME}): Missing key {e}. Data: {data}", exc_info=False)
            return None
        except TypeError as e: # Handles cases where a field expected to be numeric is None or wrong type.
            logger.error(f"TypeError parsing ticker data (Symbol: {data.get('s','N/A')}, Exchange: {self.EXCHANGE_NAME}): Possibly None for a numeric field. Error: {e}. Data: {data}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"General error parsing ticker data (Symbol: {data.get('s','N/A')}, Exchange: {self.EXCHANGE_NAME}): {e}. Data: {data}", exc_info=True)
            return None


    async def _create_subscription_tasks(self):
        """
        Creates and stores asyncio tasks for each symbol and stream type subscription.

        This method iterates through the configured symbols and stream types (trade, depth, ticker),
        creating an asyncio task for each combination to run the `_connect_and_listen` method.
        If tasks already exist (e.g., from a previous start attempt), they are cancelled first.
        """
        if self._tasks:
            logger.info(f"Clearing existing {len(self._tasks)} subscription tasks before creating new ones for {self.EXCHANGE_NAME}.")
            for task in self._tasks:
                if not task.done():
                    task.cancel()
            # Wait for all tasks to actually cancel. return_exceptions=True allows gather to complete.
            await asyncio.gather(*self._tasks, return_exceptions=True)
            self._tasks.clear()

        stream_configs = [
            ("trade", self._parse_trade_data),
            ("depth", self._parse_order_book_data),
            ("ticker", self._parse_ticker_data)
        ]
        for symbol_str in self.symbols:
            for stream_type_suffix_str, parser_func in stream_configs:
                # Construct a unique name for the task for better logging and debugging.
                task_name = f"binance_ws_{symbol_str}_{stream_type_suffix_str}"
                task = asyncio.create_task(
                    self._connect_and_listen(symbol_str, stream_type_suffix_str, parser_func),
                    name=task_name # Name the task for easier identification in logs/debug tools.
                )
                self._tasks.append(task)
        logger.info(f"Created {len(self._tasks)} subscription tasks for {self.EXCHANGE_NAME} symbols: {self.symbols}")

    async def start(self):
        """
        Starts the WebSocket client and initiates connections for all configured subscriptions.

        Sets the client to a running state and creates tasks for each WebSocket stream.
        If the client is already running, this method will log a warning and return.
        """
        if self._running:
            logger.warning(f"{self.EXCHANGE_NAME} WebSocketClient is already running.")
            return

        logger.info(f"Starting {self.EXCHANGE_NAME} WebSocketClient for symbols: {self.symbols}...")
        self._running = True # Set the running flag.
        self.overall_connection_status = "starting"

        await self._create_subscription_tasks() # Create and schedule the connection tasks.

        # A brief delay to allow initial connection attempts to establish and update statuses.
        await asyncio.sleep(1)
        # Check if any connections were successful after the initial attempts.
        if self.overall_connection_status == "starting":
            # If no stream has moved to "connected" or "connecting", mark client as having an error.
            if not any(s_info["status"] == "connected" or s_info["status"] == "connecting" for s_info in self.stream_statuses.values()):
                 self.overall_connection_status = "error"
                 self.connection_error_message = "Failed to establish any initial stream connections."
                 logger.warning(f"{self.EXCHANGE_NAME} WebSocketClient started, but no streams appear to be connecting.")
            # If at least one stream is connecting/connected, the status would have been updated by _connect_and_listen.

    async def stop(self):
        """
        Stops the WebSocket client, cancels all active asyncio tasks, and closes connections.

        Sets the client to a non-running state, signals all connection loops to terminate,
        and waits for tasks to complete their cancellation.
        """
        if not self._running and not self._tasks: # If already stopped or never started.
            logger.warning(f"{self.EXCHANGE_NAME} WebSocketClient is not running or has no active tasks to stop.")
            return

        logger.info(f"Stopping {self.EXCHANGE_NAME} WebSocketClient...")
        self._running = False  # Signal all _connect_and_listen loops to terminate.
        self.overall_connection_status = "stopping"

        cancelled_tasks = []
        for task in self._tasks:
            if not task.done():
                task.cancel() # Request cancellation of the task.
                cancelled_tasks.append(task)

        if cancelled_tasks:
            logger.info(f"Waiting for {len(cancelled_tasks)} tasks on {self.EXCHANGE_NAME} to cancel...")
            # Wait for all tasks to acknowledge cancellation.
            results = await asyncio.gather(*cancelled_tasks, return_exceptions=True)
            for i, result in enumerate(results):
                task_name = cancelled_tasks[i].get_name() if hasattr(cancelled_tasks[i], 'get_name') else f"Task {i}"
                if isinstance(result, asyncio.CancelledError):
                    logger.info(f"Task '{task_name}' was successfully cancelled.")
                elif isinstance(result, Exception): # Should ideally not happen if tasks handle CancelledError gracefully.
                    logger.error(f"Task '{task_name}' raised an exception during cancellation: {result}", exc_info=result)
        else:
            logger.info(f"No running tasks needed cancellation for {self.EXCHANGE_NAME}.")

        self._tasks.clear() # Clear the list of tasks after they've been handled.

        # Final status update for all streams to "stopped".
        for symbol_str in self.symbols:
            for stream_type_suffix_str in ["trade", "depth", "ticker"]:
                 self._update_stream_status(symbol_str, stream_type_suffix_str, "stopped")
        self.overall_connection_status = "stopped"
        logger.info(f"{self.EXCHANGE_NAME} WebSocketClient has been stopped.")

    def get_status(self) -> Dict[str, Any]:
        """
        Returns a comprehensive status report of the WebSocket client.

        This includes the overall connection status of the client, any client-level error messages,
        and detailed status for each subscribed symbol and its individual data streams (trade, depth, ticker).
        Stream staleness is checked and reported here.

        Returns:
            Dict[str, Any]: A dictionary structured to be compatible with
                            `ExchangeClientStatus` Pydantic model, containing:
                            - "exchange_name": Name of the exchange.
                            - "client_connection_status": Overall status (e.g., "connected", "degraded", "error").
                            - "client_error_message": Any global error message for the client.
                            - "symbols": A list of status details for each symbol, where each item contains:
                                - "symbol": The market symbol.
                                - "overall_symbol_status": Aggregated status for the symbol.
                                - "streams": List of statuses for individual streams (trade, depth, ticker),
                                  including "stream_type", "status", "last_message_at", "error_message".
        """
        symbol_statuses_list: List[Dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        # Determine overall client connection status based on the current state of individual streams.
        # This logic provides a more dynamic and accurate client status than just relying on overall_connection_status alone.
        current_client_level_status = "unknown" # Default
        # Check if any stream is actively connected.
        any_connected = any(s_info["status"] == "connected" for s_info in self.stream_statuses.values())
        # Check if any stream is in the process of connecting.
        any_connecting = any(s_info["status"] == "connecting" for s_info in self.stream_statuses.values())
        # Check if any stream has an error, is disconnected, or has become stale.
        any_error_or_disconnected_or_stale = any(
            s_info["status"] in ["error", "disconnected", "stale"] for s_info in self.stream_statuses.values()
        )

        if self._running: # If the client is supposed to be active.
            if any_connected and not any_error_or_disconnected_or_stale:
                current_client_level_status = "connected" # All streams are healthy.
            elif any_connected and any_error_or_disconnected_or_stale:
                current_client_level_status = "degraded" # Some streams are up, but some have issues.
            elif any_connecting and not any_connected and not any_error_or_disconnected_or_stale:
                current_client_level_status = "connecting" # No active connections yet, but some are trying.
            elif not any_connected and not any_connecting and any_error_or_disconnected_or_stale:
                 current_client_level_status = "error" # All streams are effectively down or stale.
            elif not self.stream_statuses: # No streams are configured.
                 current_client_level_status = "idle"
            else: # Fallback to the last known major status if other detailed states don't match.
                 current_client_level_status = self.overall_connection_status
        else: # If the client is not running (e.g., stopped, initializing).
            current_client_level_status = self.overall_connection_status


        for symbol_str in self.symbols: # Iterate through each configured symbol.
            streams_for_symbol: List[Dict[str,Any]] = []
            symbol_has_error_or_disconnected_stream = False
            symbol_has_connected_stream = False
            symbol_has_stale_stream = False
            symbol_has_connecting_stream = False

            for stream_type_suffix_str in ["trade", "depth", "ticker"]: # Check each stream type for the symbol.
                stream_key = (symbol_str, stream_type_suffix_str)
                status_info = self.stream_statuses.get(stream_key)

                if not status_info:
                    logger.error(f"Missing status_info for stream_key: {stream_key} ({self.EXCHANGE_NAME})")
                    streams_for_symbol.append({
                        "stream_type": stream_type_suffix_str,
                        "status": "unknown_missing_info",
                        "last_message_at": None,
                        "error_message": "Status info missing in client internal state."
                    })
                    continue # Skip to the next stream type.

                current_stream_status = status_info["status"]
                last_msg_ts = status_info["last_message_timestamp"]

                # Check for staleness if the stream is marked as 'connected' but no message received recently.
                if current_stream_status == "connected" and last_msg_ts:
                    if (now - last_msg_ts) > timedelta(seconds=self.STALENESS_THRESHOLD_SECONDS):
                        current_stream_status = "stale" # Dynamically mark as stale for this status report.
                        # Persistently update the stream's status to stale as well.
                        self._update_stream_status(symbol_str, stream_type_suffix_str, "stale", error_message="No messages received recently.")

                streams_for_symbol.append({
                    "stream_type": stream_type_suffix_str,
                    "status": current_stream_status,
                    "last_message_at": last_msg_ts.isoformat() if last_msg_ts else None,
                    "error_message": status_info["error_message"] # Get the latest error message.
                })

                # Aggregate flags for determining the overall symbol status.
                if current_stream_status == "connected": symbol_has_connected_stream = True
                if current_stream_status == "stale": symbol_has_stale_stream = True
                if current_stream_status == "connecting": symbol_has_connecting_stream = True
                if current_stream_status in ["error", "disconnected"]: symbol_has_error_or_disconnected_stream = True

            # Determine overall status for the symbol based on its individual streams.
            overall_symbol_status_str = "unknown"
            if symbol_has_connected_stream and not symbol_has_error_or_disconnected_stream and not symbol_has_stale_stream:
                overall_symbol_status_str = "connected"
            elif symbol_has_connected_stream: # Some connected, but others might be stale/error/disconnected.
                overall_symbol_status_str = "degraded"
            elif symbol_has_stale_stream and not symbol_has_connected_stream: # No active connections, at least one stale.
                 overall_symbol_status_str = "stale"
            elif symbol_has_connecting_stream and not symbol_has_connected_stream and not symbol_has_stale_stream and not symbol_has_error_or_disconnected_stream:
                 overall_symbol_status_str = "connecting" # Only connecting streams, no fully connected or error/stale.
            elif symbol_has_error_or_disconnected_stream and not symbol_has_connected_stream and not symbol_has_stale_stream:
                 overall_symbol_status_str = "error"
            else: # Fallback if none of the above specific conditions are met (e.g. all initializing/stopped).
                if streams_for_symbol: # If there are stream entries, use the status of the first one as a guess.
                    overall_symbol_status_str = streams_for_symbol[0]["status"]
                # else: remains "unknown"

            symbol_statuses_list.append({
                "symbol": symbol_str,
                "overall_symbol_status": overall_symbol_status_str,
                "streams": streams_for_symbol,
            })

        # Construct the final status dictionary.
        return {
            "exchange_name": self.EXCHANGE_NAME,
            "client_connection_status": current_client_level_status,
            "client_error_message": self.connection_error_message if current_client_level_status in ["error", "degraded"] else None,
            "symbols": symbol_statuses_list
        }

# Example Usage (for testing status - can be removed or kept for standalone tests)
# To run this, you would need to set up an environment where this script can be executed.
async def main_test_binance_client_status():
    """
    Test function for BinanceWebSocketClient status reporting and basic operation.

    This function initializes the client, starts it, monitors its status periodically,
    and then stops it. It's useful for standalone testing of the client's lifecycle
    and status reporting mechanisms.
    """
    logger.info(f"Starting {BinanceWebSocketClient.EXCHANGE_NAME} WebSocketClient status test...")

    def dummy_data_callback(data: Any):
        """A simple callback function to log received data for testing."""
        # logger.debug(f"Dummy callback received data: {type(data)}") # Too verbose for INFO level
        if hasattr(data, 'symbol') and hasattr(data, 'timestamp'):
            logger.info(f"Received {type(data).__name__} for {data.symbol} @ {data.timestamp} on {getattr(data, 'exchange', 'N/A')}")
        elif hasattr(data, 'symbol'): # Fallback if no timestamp
             logger.info(f"Received {type(data).__name__} for {data.symbol} on {getattr(data, 'exchange', 'N/A')}")
        else:
            logger.info(f"Received data of type: {type(data).__name__}")


    # Test with a couple of common symbols.
    test_symbols = ["btcusdt", "ethusdt"]
    client = BinanceWebSocketClient(symbols=test_symbols, callback=dummy_data_callback)

    try:
        await client.start() # Start the client and its connection tasks.
        logger.info(f"Client for {client.EXCHANGE_NAME} started. Monitoring status for a short period (e.g., 30 seconds)...")

        for i in range(6): # Print status report every 5 seconds for 30 seconds.
            await asyncio.sleep(5)
            status_report = client.get_status()
            try:
                # Pretty-print the JSON status report for readability.
                logger.info(f"Client Status (check {i+1}/6): \n{json.dumps(status_report, indent=2, default=str)}")
            except ImportError: # Fallback if json module is somehow not available.
                logger.info(f"Client Status (check {i+1}/6): {status_report}")

            # Example: Simulate a stream going stale manually (for testing staleness detection)
            # This should only be done for specific, controlled testing scenarios.
            # if i == 2 and ("btcusdt", "ticker") in client.stream_statuses: # Check if stream exists
            #     logger.warning("Simulating 'btcusdt@ticker' going stale by manually setting its timestamp far back.")
            #     stale_time = datetime.now(timezone.utc) - timedelta(seconds=client.STALENESS_THRESHOLD_SECONDS + 10)
            #     # Directly modifying internal state like this is only for testing.
            #     client.stream_statuses[("btcusdt", "ticker")]["last_message_timestamp"] = stale_time
            #     client.stream_statuses[("btcusdt", "ticker")]["status"] = "connected" # Ensure it's 'connected' to trigger staleness check in get_status


    except KeyboardInterrupt:
        logger.info(f"Keyboard interrupt received during {client.EXCHANGE_NAME} client status test.")
    except Exception as e:
        logger.error(f"An error occurred during {client.EXCHANGE_NAME} client status test: {e}", exc_info=True)
    finally:
        logger.info(f"Stopping {client.EXCHANGE_NAME} WebSocketClient as part of test cleanup...")
        await client.stop() # Ensure the client is stopped cleanly.
        logger.info(f"Client for {client.EXCHANGE_NAME} stopped. Performing final status check:")
        final_status = client.get_status()
        try:
            logger.info(f"Final Client Status ({client.EXCHANGE_NAME}): \n{json.dumps(final_status, indent=2, default=str)}")
        except ImportError:
            logger.info(f"Final Client Status ({client.EXCHANGE_NAME}): {final_status}")
        logger.info(f"{client.EXCHANGE_NAME} WebSocketClient status test finished.")


if __name__ == "__main__":
    # This basicConfig is intended for when the script is run directly (e.g., for testing).
    # It should not interfere with global logging configuration if this module is imported elsewhere,
    # especially if the global config is set up before this module is imported.
    # The `if not logger.hasHandlers()` check at the top of the file aims to prevent duplicate handlers.
    logging.basicConfig(
        level=logging.INFO, # Set to DEBUG for more verbose output from the client and this test script.
        format='%(asctime)s - %(levelname)s - %(name)s - [%(module)s.%(funcName)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    asyncio.run(main_test_binance_client_status())
