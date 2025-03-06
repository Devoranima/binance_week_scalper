from server.db.engine import engine
from server.db.models import Tradepair, Candle, Swing
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from contextlib import contextmanager
from datetime import datetime
from collections.abc import Callable


@contextmanager
def getSession():
    session = Session(engine, expire_on_commit=False)
    #session.begin()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def returnDict(func: Callable[..., list]):
    def inner(*args, **kwargs):
        rows = func(*args, **kwargs)
        return [row.to_dict() for row in rows]
    return inner


@returnDict
def selectTradepairs(tracking: bool = None) -> list[Tradepair]:
    with getSession() as session:
        stmt = select(Tradepair).order_by(Tradepair.name)
        if tracking != None:
            stmt = stmt.where(Tradepair.tracking == tracking)
        return session.scalars(stmt).all()


@returnDict
def selectCandles(tradepair_name: str = None, timeframe: str = None) -> list[Candle]:
    with getSession() as session:
        stmt = select(Candle).order_by(Candle.datetime_open.desc())

        if tradepair_name:
            stmt = stmt.where(Candle.tradepair_name == tradepair_name)
        if timeframe:
            stmt = stmt.where(Candle.timeframe_type == timeframe)
            
        return session.scalars(stmt).all()

@returnDict
def selectSwings(tradepair_name: str, timeframe: str, amount: int = 5) -> list[Swing]:
    with getSession() as session:
        stmt = (
            select(Swing)
            .where(Swing.tradepair_name == tradepair_name, Swing.timeframe_type == timeframe)
            .order_by(Swing.id.desc())
            .limit(amount)
        )
        return session.scalars(stmt).all()

@returnDict
def addTradepairs(tradepairs: list[str]) -> list[Tradepair]:
    added_tradepairs = []

    with getSession() as session:
        existing_tradepairs = session.scalars(select(Tradepair.name)).all()
        for tradepair_name in tradepairs:
            if tradepair_name not in existing_tradepairs:
                tradepair = Tradepair(name=tradepair_name)
                session.add(tradepair)
                added_tradepairs.append(tradepair)
        
        #? untrack delisted tradepairs
        stmt = (
            update(Tradepair)
            .where(Tradepair.name.not_in(tradepairs))
            .values(delisted=True)
            .returning(Tradepair)
        )
        untracked_tradepairs = session.scalars(stmt).all()

    return added_tradepairs, untracked_tradepairs

@returnDict
def switchTradepairsTrackingStatus(tracking: bool, selected_tradepairs: list[str]) -> list[Tradepair]:
    with getSession() as session:
        stmt = (
            update(Tradepair)
            .where(Tradepair.name.in_(selected_tradepairs))
            .values(tracking=tracking)
            .returning(Tradepair)  # Fetch updated rows
        )
        return session.scalars(stmt).all()

@returnDict
def addCandles(klines: list) -> list[Candle]:
    added_candles = []

    with getSession() as session:
        for kline in klines:
            stmt = select(Candle.tradepair_name, Candle.timeframe, Candle.datetime_open).where(
                (Candle.tradepair_name == kline['tradepair_name']) &
                (Candle.timeframe == kline['timeframe']) &
                (Candle.datetime_open == kline['datetime_open'])
            )
            exists = session.execute(stmt).first()
            if not exists:
                candle = Candle(**kline)
                session.add(candle)
                added_candles.append(candle)

        if added_candles:
            updated_tradepairs = {candle.tradepair_name for candle in added_candles}
            stmt = (
                update(Tradepair)
                .where(Tradepair.name.in_(updated_tradepairs))
                .values(last_updated=datetime.now())
            )
            session.execute(stmt)

    return added_candles

