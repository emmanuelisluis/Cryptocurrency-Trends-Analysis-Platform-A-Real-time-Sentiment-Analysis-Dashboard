import asyncio
import logging
from typing import Any, List

from sqlalchemy.exc import SQLAlchemyError

from backend.app.core.config import settings
from backend.app.services.exchange_clients.binance_client import BinanceWebSocketClient
from backend.app.models.exchange_data import TradeData as PydanticTradeData, \
                                            OrderBookData as PydanticOrderBookData, \
                                            TickerData as PydanticTickerData
from backend.app.db.session import create_session # Use this for background tasks
from backend.app.db.models import TradeDB, OrderBookSnapshotDB, TickerDB

logger = logging.getLogger(__name__)

class DataIngestionService:
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self.clients = []
        self.binance_client = BinanceWebSocketClient(symbols=self.symbols, callback=self.db_data_handler)
        self.clients.append(self.binance_client)
        self._is_running = False

    def db_data_handler(self, data_item: Any):
        """
        Handles incoming data items from exchange clients and writes them to the database.
        Manages its own database session.
        """
        session = create_session()
        try:
            if isinstance(data_item, PydanticTradeData):
                db_trade = TradeDB(
                    timestamp=data_item.timestamp,
                    symbol=data_item.symbol.lower(), # Ensure consistent case
                    exchange=data_item.exchange.lower(),
                    price=data_item.price,
                    volume=data_item.volume,
                    side=data_item.side.lower(),
                    trade_id=data_item.trade_id,
                    aggressor_side=data_item.aggressor_side.lower() if data_item.aggressor_side else None # Add this line
                )
                session.add(db_trade)
                # logger.debug(f"Added TradeDB: {db_trade.symbol} {db_trade.trade_id}")

            elif isinstance(data_item, PydanticOrderBookData):
                # Convert list[OrderBookLevel] to JSON serializable list of dicts
                bids_json = [{"price": level.price, "volume": level.volume} for level in data_item.bids]
                asks_json = [{"price": level.price, "volume": level.volume} for level in data_item.asks]

                db_order_book = OrderBookSnapshotDB(
                    timestamp=data_item.timestamp,
                    symbol=data_item.symbol.lower(),
                    exchange=data_item.exchange.lower(),
                    bids=bids_json,
                    asks=asks_json,
                    last_update_id=data_item.last_update_id
                )
                session.add(db_order_book)
                # logger.debug(f"Added OrderBookSnapshotDB: {db_order_book.symbol} {data_item.timestamp}")

            elif isinstance(data_item, PydanticTickerData):
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
                # logger.debug(f"Added TickerDB: {db_ticker.symbol} {data_item.timestamp}")
            else:
                logger.warning(f"Received unknown data item type: {type(data_item)}")
                return

            session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Database error processing data item {type(data_item)} for {data_item.symbol if hasattr(data_item, 'symbol') else 'N/A'}: {e}")
            session.rollback()
        except Exception as e:
            logger.error(f"Unexpected error processing data item {type(data_item)} for {data_item.symbol if hasattr(data_item, 'symbol') else 'N/A'}: {e}")
            session.rollback()
        finally:
            session.close()

    async def start_ingestion(self):
        if self._is_running:
            logger.warning("Data ingestion is already running.")
            return

        logger.info(f"Starting data ingestion for symbols: {self.symbols}")
        self._is_running = True

        start_tasks = []
        for client in self.clients:
            start_tasks.append(client.start())

        await asyncio.gather(*start_tasks)
        logger.info("All exchange clients started.")

    async def stop_ingestion(self):
        if not self._is_running:
            logger.warning("Data ingestion is not running.")
            return

        logger.info("Stopping data ingestion...")
        stop_tasks = []
        for client in self.clients:
            # Ensure client has a stop method and it's awaitable
            if hasattr(client, 'stop') and asyncio.iscoroutinefunction(client.stop):
                stop_tasks.append(client.stop())
            else:
                logger.warning(f"Client {type(client).__name__} does not have an async stop method.")

        if stop_tasks:
            await asyncio.gather(*stop_tasks)

        self._is_running = False
        logger.info("Data ingestion stopped.")

    def get_all_clients_status(self) -> List[Dict[str, Any]]:
        """
        Aggregates status from all managed exchange clients.
        Returns a list of status dictionaries, one for each client.
        """
        all_statuses = []
        for client in self.clients:
            if hasattr(client, 'get_status') and callable(client.get_status):
                status = client.get_status() # This should be a dictionary
                all_statuses.append(status)
            else:
                logger.warning(f"Client {type(client).__name__} does not have a get_status method.")
                # Optionally, add a placeholder status for such clients
                if hasattr(client, 'EXCHANGE_NAME'):
                    exchange_name = client.EXCHANGE_NAME
                else:
                    exchange_name = type(client).__name__

                all_statuses.append({
                    "exchange_name": exchange_name,
                    "client_connection_status": "unknown",
                    "client_error_message": "Client does not support status reporting.",
                    "symbols": []
                })
        return all_statuses


# Example Usage (for testing purposes, will be integrated into main.py or run_ingestion.py)
async def main_test_ingestion():
    logging.basicConfig(level=logging.DEBUG) # Use DEBUG for more verbose logs from service
    logger.info("Starting main_test_ingestion...")

    if not settings.SYMBOLS:
        logger.error("No symbols configured. Please set SYMBOLS in core.config")
        return

    # Initialize DB (for testing purposes, in real app this is separate)
    # from backend.app.db.init_db import initialize_database
    # logger.info("Initializing database for test...")
    # initialize_database() # This would try to connect to DB. Ensure DB is running.
    # logger.info("Database initialization for test completed.")

    ingestion_service = DataIngestionService(symbols=settings.SYMBOLS[:1]) # Test with one symbol
    try:
        await ingestion_service.start_ingestion()
        # In a real test, you might want to check status periodically
        for _ in range(5): # Check status a few times
            await asyncio.sleep(10) # Wait for connections and some data
            status_report = ingestion_service.get_all_clients_status()
            logger.info(f"Ingestion Service Status: {json.dumps(status_report, indent=2, default=str)}")

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping ingestion service...")
    except Exception as e:
        logger.error(f"Error during main_test_ingestion: {e}", exc_info=True)
    finally:
        await ingestion_service.stop_ingestion()

if __name__ == "__main__":
    import json # Make sure json is imported for the test part
    # This part is for direct testing of the service.
    # Note: DATABASE_URL must be correctly set in .env for this to write to a DB.
    # If DB is not available, it will log errors but try to continue.
    asyncio.run(main_test_ingestion())
