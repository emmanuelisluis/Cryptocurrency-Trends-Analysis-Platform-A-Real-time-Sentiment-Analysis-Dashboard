"""
SQLAlchemy ORM Models for the database schema.

This module defines the structure of database tables using SQLAlchemy's
declarative base. These models are used for creating the schema (via `init_db.py`)
and for all database interactions (queries, insertions) by the services.
All timestamp fields are timezone-aware.
"""
from sqlalchemy import Column, DateTime, Float, String, Integer, Index
from sqlalchemy.dialects.postgresql import JSONB # For storing arrays of bids/asks
from sqlalchemy.orm import declarative_base # Updated import for modern SQLAlchemy

# Base for all ORM models
Base = declarative_base()

class TradeDB(Base):
    """
    Represents a single trade event from an exchange.
    This table is configured as a TimescaleDB hypertable on 'timestamp'.
    """
    __tablename__ = "trades"

    # Composite primary key, suitable for TimescaleDB and uniqueness
    timestamp = Column(DateTime(timezone=True), primary_key=True, nullable=False, comment="Timestamp of the trade execution (UTC). Part of PK.")
    symbol = Column(String, primary_key=True, nullable=False, comment="Trading symbol, e.g., 'btcusdt'. Part of PK.")
    exchange = Column(String, primary_key=True, nullable=False, comment="Exchange name, e.g., 'binance'. Part of PK.")
    trade_id = Column(String, primary_key=True, nullable=False, comment="Unique trade ID from the exchange. Part of PK.")

    price = Column(Float, nullable=False, comment="Execution price of the trade.")
    volume = Column(Float, nullable=False, comment="Volume/quantity of the trade in base asset.")
    side = Column(String, nullable=False, comment="Side of the taker order ('buy' or 'sell').")
    aggressor_side = Column(String, nullable=True, comment="The side that initiated the trade (aggressor), 'buy' or 'sell'. Null if unknown.")

    __table_args__ = (
        # Index for common queries filtering by exchange, symbol, and then time
        Index('ix_trades_exchange_symbol_timestamp', 'exchange', 'symbol', 'timestamp', unique=False),
        # TimescaleDB automatically creates an efficient index on the time column ('timestamp') for hypertables.
        # Additional specialized indexes (e.g., on price, volume, or side) can be added if specific query patterns demand them.
        {"comment": "Stores individual trade data, partitioned by time for TimescaleDB."}
    )

class TickerDB(Base):
    """
    Represents ticker data (price summary) for a symbol from an exchange.
    This table is configured as a TimescaleDB hypertable on 'timestamp'.
    """
    __tablename__ = "tickers"

    # Composite primary key
    timestamp = Column(DateTime(timezone=True), primary_key=True, nullable=False, comment="Timestamp of the ticker data (UTC). Part of PK.")
    symbol = Column(String, primary_key=True, nullable=False, comment="Trading symbol. Part of PK.")
    exchange = Column(String, primary_key=True, nullable=False, comment="Exchange name. Part of PK.")

    last_price = Column(Float, nullable=False, comment="Last traded price.")
    volume_24h = Column(Float, nullable=True, comment="Total traded base asset volume in the last 24 hours.")
    high_24h = Column(Float, nullable=True, comment="Highest price in the last 24 hours.")
    low_24h = Column(Float, nullable=True, comment="Lowest price in the last 24 hours.")
    price_change_percent_24h = Column(Float, nullable=True, comment="Price change percentage in the last 24 hours.")

    __table_args__ = (
        Index('ix_tickers_exchange_symbol_timestamp', 'exchange', 'symbol', 'timestamp', unique=False),
        {"comment": "Stores ticker/summary data for symbols, partitioned by time."}
    )

class OrderBookSnapshotDB(Base):
    """
    Represents a snapshot of the order book for a symbol from an exchange.
    Bids and asks are stored as JSONB arrays of [price, volume] tuples/lists.
    This table is configured as a TimescaleDB hypertable on 'timestamp'.
    """
    __tablename__ = "order_book_snapshots"

    # Composite primary key
    timestamp = Column(DateTime(timezone=True), primary_key=True, nullable=False, comment="Timestamp of the order book snapshot (UTC). Part of PK.")
    symbol = Column(String, primary_key=True, nullable=False, comment="Trading symbol. Part of PK.")
    exchange = Column(String, primary_key=True, nullable=False, comment="Exchange name. Part of PK.")

    # Bids and asks are stored as JSONB. Each is a list of [price, quantity] pairs.
    # Example: [[price1, quant1], [price2, quant2], ...]
    # Bids are typically sorted highest price first. Asks lowest price first.
    bids = Column(JSONB, nullable=False, comment="List of bid levels, each [price, quantity].")
    asks = Column(JSONB, nullable=False, comment="List of ask levels, each [price, quantity].")
    last_update_id = Column(Integer, nullable=True, comment="For exchanges like Binance, the last update ID of the event included in this snapshot.")

    __table_args__ = (
        Index('ix_orderbooks_exchange_symbol_timestamp', 'exchange', 'symbol', 'timestamp', unique=False),
        {"comment": "Stores order book snapshots, partitioned by time."}
    )

# Note: To make these tables TimescaleDB hypertables, specific SQL commands
# (e.g., `SELECT create_hypertable(...)`) must be executed after table creation.
# This is handled in `init_db.py`.
