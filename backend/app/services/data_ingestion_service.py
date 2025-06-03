"""
Service for managing data ingestion from multiple exchange clients.

This module defines the `DataIngestionService` class, which is responsible for
orchestrating data collection from various cryptocurrency exchange WebSocket APIs.
It initializes clients (like `BinanceWebSocketClient`), manages their lifecycle
(start/stop), and processes the data they stream by converting Pydantic models
to SQLAlchemy database models and committing them to the database.
"""
import asyncio
import logging
from typing import Any, List, Dict

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session # Used for type hinting, actual session created by create_session

from backend.app.core.config import settings
from backend.app.db.models import OrderBookSnapshotDB, TickerDB, TradeDB
from backend.app.db.session import create_session # Factory for creating DB sessions for background tasks
from backend.app.models.exchange_data import (
    OrderBookData as PydanticOrderBookData,
    TickerData as PydanticTickerData,
    TradeData as PydanticTradeData,
)
# Specific exchange client imports. More can be added here.
from backend.app.services.exchange_clients.binance_client import BinanceWebSocketClient

logger = logging.getLogger(__name__)


class DataIngestionService:
    """
    Orchestrates data ingestion from various exchange clients.

    This service initializes configured exchange clients (e.g., for Binance),
    starts them to begin receiving real-time market data, and stops them gracefully.
    It uses a callback mechanism (`db_data_handler`) to process incoming data,
    which involves mapping it to database models and saving it to the database.
    The service also provides a way to get status reports from all managed clients.

    Attributes:
        symbols (List[str]): A list of lowercased trading symbols (e.g., 'btcusdt')
            for which data should be ingested.
        clients (List[Any]): A list that holds instances of initialized exchange
            clients (e.g., `BinanceWebSocketClient`). This allows for managing
            multiple clients for different exchanges or purposes.
        binance_client (Optional[BinanceWebSocketClient]): A specific attribute to hold
            the Binance client instance if initialized. This could be generalized if
            many exchange clients are managed.
        _is_running (bool): A private flag indicating whether the ingestion service
            (and by extension, its clients) is currently active or trying to run.
    """
    def __init__(self, symbols: List[str]):
        """
        Initializes the DataIngestionService.

        Sets up the service with the specified symbols and initializes exchange clients
        based on application settings (e.g., `settings.ACTIVE_EXCHANGES`).

        Args:
            symbols (List[str]): A list of trading symbols (e.g., ['BTCUSDT', 'ETHBTC'])
                to manage data ingestion for. These will be standardized to lowercase.
        """
        self.symbols: List[str] = [s.lower() for s in symbols]
        self.clients: List[Any] = []
        self.binance_client: Optional[BinanceWebSocketClient] = None # Explicitly define for clarity

        # Client initialization logic based on settings.
        # This section can be extended to dynamically load and initialize clients
        # for multiple exchanges based on the `settings.ACTIVE_EXCHANGES` list.
        if "binance" in settings.ACTIVE_EXCHANGES:
            logger.info(f"Initializing BinanceWebSocketClient for symbols: {self.symbols}")
            # The db_data_handler is passed as the callback to process incoming data.
            self.binance_client = BinanceWebSocketClient(symbols=self.symbols, callback=self.db_data_handler)
            self.clients.append(self.binance_client)
        else:
            # Example: Log if a configured exchange is not supported or if no exchanges are active.
            if settings.ACTIVE_EXCHANGES: # If list is not empty but 'binance' is not in it
                 logger.warning(f"Binance exchange is not listed in ACTIVE_EXCHANGES. Binance client will not be initialized.")
            else: # If ACTIVE_EXCHANGES is empty or not defined
                 logger.warning("No exchanges listed in ACTIVE_EXCHANGES. No clients will be initialized.")
            # Retained the original fallback for now, but ideally, it should only init if configured.
            # Consider removing this else block if strict configuration is desired.
            # logger.info(f"Defaulting to initialize BinanceWebSocketClient for symbols: {self.symbols} (no specific exchanges in ACTIVE_EXCHANGES or setting not used).")
            # self.binance_client = BinanceWebSocketClient(symbols=self.symbols, callback=self.db_data_handler)
            # self.clients.append(self.binance_client)


        self._is_running: bool = False
        logger.info(f"DataIngestionService initialized with {len(self.clients)} client(s) for symbols: {self.symbols}.")

    def db_data_handler(self, data_item: Any):
        """
        Callback function to handle incoming data items from exchange clients.

        This method is responsible for:
        1. Identifying the type of the incoming Pydantic data model (Trade, OrderBook, Ticker).
        2. Converting the Pydantic model to its corresponding SQLAlchemy database model.
        3. Adding the SQLAlchemy model to a new database session.
        4. Committing the session to save the data to the database.
        5. Handling potential database errors and rolling back in case of failure.
        6. Closing the database session.

        This handler is designed to be called by exchange clients from their own
        asyncio tasks or threads, so it creates and manages its own database session
        per invocation to ensure thread safety and proper session lifecycle.

        Args:
            data_item (Any): The data item received from an exchange client. This is
                expected to be an instance of a Pydantic model defined in
                `backend.app.models.exchange_data` (e.g., `PydanticTradeData`).
        """
        session: Session = create_session() # Obtain a new DB session for this operation.
        try:
            logger.debug(f"Received data item of type: {type(data_item)} for DB processing.")

            # Determine the type of data item and map it to the appropriate DB model.
            if isinstance(data_item, PydanticTradeData):
                # Map Pydantic TradeData to SQLAlchemy TradeDB model.
                db_trade = TradeDB(
                    timestamp=data_item.timestamp,
                    symbol=data_item.symbol.lower(), # Ensure lowercase consistency
                    exchange=data_item.exchange.lower(), # Ensure lowercase consistency
                    price=data_item.price,
                    volume=data_item.volume,
                    side=data_item.side.lower(), # Ensure lowercase consistency
                    trade_id=data_item.trade_id,
                    aggressor_side=data_item.aggressor_side.lower() if data_item.aggressor_side else None # Handle optional field
                )
                session.add(db_trade)
                logger.debug(f"Added TradeDB to session: Symbol {db_trade.symbol}, Trade ID {db_trade.trade_id}")

            elif isinstance(data_item, PydanticOrderBookData):
                # Convert lists of Pydantic OrderBookLevel models to JSONB compatible list of dicts.
                bids_json = [{"price": level.price, "volume": level.volume} for level in data_item.bids]
                asks_json = [{"price": level.price, "volume": level.volume} for level in data_item.asks]
                # Map Pydantic OrderBookData to SQLAlchemy OrderBookSnapshotDB model.
                db_order_book = OrderBookSnapshotDB(
                    timestamp=data_item.timestamp,
                    symbol=data_item.symbol.lower(),
                    exchange=data_item.exchange.lower(),
                    bids=bids_json, # Store as JSON
                    asks=asks_json, # Store as JSON
                    last_update_id=data_item.last_update_id
                )
                session.add(db_order_book)
                logger.debug(f"Added OrderBookSnapshotDB to session: Symbol {db_order_book.symbol} @ {data_item.timestamp}")

            elif isinstance(data_item, PydanticTickerData):
                # Map Pydantic TickerData to SQLAlchemy TickerDB model.
                db_ticker = TickerDB(
                    timestamp=data_item.timestamp,
                    symbol=data_item.symbol.lower(),
                    exchange=data_item.exchange.lower(),
                    last_price=data_item.last_price,
                    volume_24h=data_item.volume_24h,
                    high_24h=data_item.high_24h,
                    low_24h=data_item.low_24h,
                    price_change_percent_24h=data_item.price_change_percent_24h
                )
                session.add(db_ticker)
                logger.debug(f"Added TickerDB to session: Symbol {db_ticker.symbol} @ {data_item.timestamp}")
            else:
                # Log a warning if an unrecognized data type is received.
                logger.warning(f"Received unknown data item type for DB handling: {type(data_item)}. Data: {data_item}")
                return # Do not proceed to commit if the type is unknown.

            session.commit() # Attempt to save the record(s) to the database.
            # Log successful commit, including symbol if available.
            symbol_info = data_item.symbol if hasattr(data_item, 'symbol') else 'N/A'
            logger.debug(f"Committed data item for {symbol_info} (Type: {type(data_item).__name__})")
        except SQLAlchemyError as e:
            # Log database-specific errors (e.g., connection issues, constraint violations).
            symbol_info = data_item.symbol if hasattr(data_item, 'symbol') else 'N/A'
            logger.error(f"Database error processing data item for {symbol_info}: {e}", exc_info=True)
            session.rollback() # Rollback the transaction on error.
        except Exception as e:
            # Log any other unexpected errors during data handling.
            symbol_info = data_item.symbol if hasattr(data_item, 'symbol') else 'N/A'
            logger.error(f"Unexpected error in db_data_handler for {symbol_info}: {e}", exc_info=True)
            session.rollback() # Ensure rollback on any exception.
        finally:
            session.close() # Always close the session to free up resources.
            logger.debug("Database session closed for db_data_handler.")

    async def start_ingestion(self):
        """
        Starts the data ingestion process for all configured and initialized clients.

        This method sets the service's running flag to True and then iterates through
        all managed clients, calling their asynchronous `start()` method. These calls
        are gathered and run concurrently using `asyncio.gather`.
        If no clients are initialized, or if clients lack a `start` method,
        appropriate warnings are logged.
        """
        if self._is_running:
            logger.warning("Data ingestion service is already running. Start request ignored.")
            return

        if not self.clients:
            logger.warning("No exchange clients initialized. Data ingestion cannot start.")
            return

        logger.info(f"Starting data ingestion for symbols: {self.symbols} across {len(self.clients)} client(s).")
        self._is_running = True

        # Collect tasks for starting each client. Assumes clients have an async `start()` method.
        start_tasks = [client.start() for client in self.clients if hasattr(client, 'start') and asyncio.iscoroutinefunction(client.start)]

        if not start_tasks:
            logger.warning("No clients found with a valid async start method. Ingestion may not proceed.")
            self._is_running = False # Reset running status if no tasks can be started.
            return

        await asyncio.gather(*start_tasks) # Execute all client start tasks concurrently.
        logger.info("All exchange client start methods have been initiated by the ingestion service.")
        # Note: This method returns after initiating client starts. The clients themselves
        # run their data fetching loops independently. The actual data flow begins once
        # clients successfully connect and start invoking the `db_data_handler` callback.

    async def stop_ingestion(self):
        """
        Stops the data ingestion process for all managed clients.

        This method sets the service's running flag to False and then iterates through
        all managed clients, calling their asynchronous `stop()` method. These calls
        are gathered and run concurrently. It handles cases where clients might not
        have a proper `stop` method.
        """
        if not self._is_running:
            logger.warning("Data ingestion service is not currently running. Stop request ignored.")
            return

        logger.info("Stopping data ingestion for all clients...")
        self._is_running = False # Set running flag to false immediately to signal intent.

        stop_tasks = []
        for client in self.clients:
            if hasattr(client, 'stop') and asyncio.iscoroutinefunction(client.stop):
                stop_tasks.append(client.stop()) # Add the coroutine to the list of tasks.
            else:
                logger.warning(f"Client {type(client).__name__} does not have an appropriate async stop method or is not a coroutine.")

        if stop_tasks:
            try:
                # Wait for all client stop methods to complete.
                await asyncio.gather(*stop_tasks)
                logger.info("All exchange client stop methods have been successfully called.")
            except Exception as e:
                # Log if any error occurs during the stopping of clients.
                logger.error(f"Error occurred during client stop procedures: {e}", exc_info=True)
        else:
            logger.info("No clients with async stop methods were found to stop.")

        logger.info("Data ingestion service has been commanded to stop.")

    def get_all_clients_status(self) -> List[Dict[str, Any]]:
        """
        Aggregates and returns the operational status from all managed exchange clients.

        Iterates through each client, calls its `get_status()` method (if available),
        and compiles a list of status reports. Handles clients that might not implement
        status reporting or encounter errors during status retrieval.

        Returns:
            List[Dict[str, Any]]: A list of status dictionaries. Each dictionary
                represents the status of one exchange client, typically conforming to
                the structure defined by that client's `get_status()` method (e.g.,
                matching a Pydantic model like `ExchangeClientStatus`).
                If a client fails to report status, a placeholder error status is included.
        """
        all_statuses: List[Dict[str, Any]] = []
        if not self.clients:
            logger.info("No clients are currently managed by the ingestion service to get status from.")
            return all_statuses # Return empty list if no clients.

        for client_idx, client in enumerate(self.clients):
            client_name = type(client).__name__
            exchange_identifier = getattr(client, 'EXCHANGE_NAME', client_name) # Use EXCHANGE_NAME if available

            if hasattr(client, 'get_status') and callable(client.get_status):
                try:
                    status = client.get_status()
                    all_statuses.append(status)
                except Exception as e:
                    logger.error(f"Error getting status from client {client_name} (Exchange: {exchange_identifier}): {e}", exc_info=True)
                    # Provide a standardized error status structure for this client.
                    all_statuses.append({
                        "exchange_name": exchange_identifier,
                        "client_connection_status": "error_reporting",
                        "client_error_message": f"Failed to retrieve status: {str(e)}",
                        "symbols": [] # Empty symbols list as status is unavailable.
                    })
            else:
                logger.warning(f"Client {client_name} (Exchange: {exchange_identifier}) does not implement a callable get_status method.")
                # Provide a status indicating lack of reporting capability.
                all_statuses.append({
                    "exchange_name": exchange_identifier,
                    "client_connection_status": "unknown_no_reporting",
                    "client_error_message": "Client does not support status reporting.",
                    "symbols": []
                })
        return all_statuses


# Example Usage (for testing purposes, can be removed or kept for standalone tests).
# This section provides a way to test the DataIngestionService independently of the full FastAPI application.
# This section is useful for testing the service independently.
async def main_test_ingestion():
    """Example function to test DataIngestionService independently."""
    # Configure logging for this test run
    logging.basicConfig(
        level=logging.DEBUG, # Use DEBUG for verbose logs during testing
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(module)s.%(funcName)s:%(lineno)d]',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger.info("Starting DataIngestionService test sequence...")

    if not settings.SYMBOLS:
        logger.error("No symbols configured in settings.SYMBOLS. Aborting test.")
        return

    # Example: Initialize database if needed for the test
    # from backend.app.db.init_db import initialize_database
    # logger.info("Initializing database for test...")
    # try:
    #     initialize_database() # Ensure DB is running and accessible
    #     logger.info("Database initialization for test completed.")
    # except Exception as e:
    #     logger.error(f"Database initialization failed for test: {e}", exc_info=True)
    #     return # Stop test if DB init fails

    # Test with a subset of symbols from settings
    test_symbols = settings.SYMBOLS[:1] if settings.SYMBOLS else ["btcusdt"]
    logger.info(f"Testing DataIngestionService with symbols: {test_symbols}")

    ingestion_service = DataIngestionService(symbols=test_symbols)
    try:
        await ingestion_service.start_ingestion()
        logger.info("Ingestion service started. Monitoring for 30 seconds...")

        for i in range(3): # Check status a few times
            await asyncio.sleep(10)
            status_report = ingestion_service.get_all_clients_status()
            # `json.dumps` requires `default=str` if status_report contains non-serializable objects like datetime
            try:
                import json
                logger.info(f"Ingestion Service Status (check {i+1}): {json.dumps(status_report, indent=2, default=str)}")
            except ImportError:
                logger.info(f"Ingestion Service Status (check {i+1}): {status_report} (json module not available for pretty print)")


    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received during test, stopping ingestion service...")
    except Exception as e:
        logger.error(f"Error during DataIngestionService test: {e}", exc_info=True)
    finally:
        logger.info("Stopping DataIngestionService as part of test cleanup...")
        await ingestion_service.stop_ingestion()
        logger.info("DataIngestionService test sequence finished.")

if __name__ == "__main__":
    # This allows running `python -m backend.app.services.data_ingestion_service`
    # Note: DATABASE_URL must be correctly set in .env for db_data_handler to work.
    # If DB is not available, it will log errors.
    # Ensure any ACTIVE_EXCHANGES setting in config.py is appropriate for this test.

    # To run this test, ensure you have a .env file in the `backend` directory, or relevant
    # environment variables are set for DATABASE_URL.
    # Also, the `run_ingestion.py` script at project root might be a better way to test full app functionality.

    # Example: Add a setting for active exchanges if not already present
    if not hasattr(settings, 'ACTIVE_EXCHANGES'):
        settings.ACTIVE_EXCHANGES = ['binance'] # Default to binance for this test
        logger.info("Temporarily set ACTIVE_EXCHANGES to ['binance'] for testing.")

    asyncio.run(main_test_ingestion())
