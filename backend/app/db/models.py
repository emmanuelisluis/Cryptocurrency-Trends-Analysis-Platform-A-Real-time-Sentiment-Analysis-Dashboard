from sqlalchemy import Column, DateTime, Float, String, Integer, Index # Boolean is not needed if storing 'buy'/'sell' as String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
# For TimescaleDB specific function, though create_hypertable is usually done via SQL execution
# from sqlalchemy_timescaledb import TimescaleDB

Base = declarative_base()

class TradeDB(Base):
    __tablename__ = "trades"

    # Composite primary key, suitable for TimescaleDB and uniqueness across exchanges/symbols
    timestamp = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    symbol = Column(String, primary_key=True, nullable=False) # e.g., 'btcusdt'
    exchange = Column(String, primary_key=True, nullable=False) # e.g., 'binance'
    # Assuming trade_id from exchange is unique per symbol per exchange at a given timestamp.
    # For Binance, 't' (tradeId) is unique per symbol.
    trade_id = Column(String, primary_key=True, nullable=False)

    price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    side = Column(String, nullable=False) # 'buy' or 'sell' (taker's side)

    # New column for aggressor side
    aggressor_side = Column(String, nullable=True) # 'buy' or 'sell', represents the TAKER side of the trade

    # __table_args__ can be used for additional indexes or constraints.
    # TimescaleDB automatically creates an index on the time column ('timestamp').
    # Additional useful indexes might be on (exchange, symbol, timestamp) or (symbol, timestamp).
    # The existing index is fine.
    __table_args__ = (
        Index('ix_trades_exchange_symbol_timestamp', 'exchange', 'symbol', 'timestamp', unique=False),
        # No need for BRIN index on timestamp with TimescaleDB, it handles time-based indexing efficiently.
    )

class TickerDB(Base):
    __tablename__ = "tickers"

    timestamp = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    symbol = Column(String, primary_key=True, nullable=False)
    exchange = Column(String, primary_key=True, nullable=False)

    last_price = Column(Float, nullable=False)
    volume_24h = Column(Float)
    high_24h = Column(Float)
    low_24h = Column(Float)
    price_change_percent_24h = Column(Float)

class OrderBookSnapshotDB(Base):
    __tablename__ = "order_book_snapshots"

    timestamp = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    symbol = Column(String, primary_key=True, nullable=False)
    exchange = Column(String, primary_key=True, nullable=False)

    bids = Column(JSONB, nullable=False) # List of [price, volume]
    asks = Column(JSONB, nullable=False) # List of [price, volume]
    last_update_id = Column(Integer, nullable=True) # For exchanges like Binance

# Ensure __init__.py exists for the db directory (already created)
