from updater.db.engine import engine
from updater.db.models import Tradepair, Candle, Swing, Timeframe,swing_candle_link
from sqlalchemy import select, update, func
from sqlalchemy.orm import Session
from contextlib import contextmanager
from datetime import datetime, timedelta
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


def returnDict(func: Callable):
    def inner(*args, **kwargs):
        result = func(*args, **kwargs)
        if result == None:
            return []
        if type(result) == list:            
            return [row.to_dict() for row in result]
        return result.to_dict()
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
            stmt = stmt.where(Candle.timeframe_name == timeframe)
            
        return session.scalars(stmt).all()

@returnDict
def selectSwings(tradepair_name: str, timeframe: str, amount: int = 5) -> list[Swing]:
    with getSession() as session:
        stmt = (
            select(Swing)
            .where(Swing.tradepair_name == tradepair_name, Swing.timeframe_name == timeframe)
            .order_by(Swing.id.desc())
            .limit(amount)
        )
        return session.scalars(stmt).all()

@returnDict
def addTradepairs(tradepairs: list[str]):
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
                (Candle.timeframe_name == kline['timeframe_name']) &
                (Candle.datetime_open == kline['datetime_open'])
            )
            exists = session.execute(stmt).first()
            if not exists:
                candle = Candle(**kline)
                session.add(candle)
                added_candles.append(candle)

    return added_candles

@returnDict
def addSwing(tradepair_name: str, timeframe: str, candles: list[dict], orientation_up: bool) -> Swing:
    """
    Adds a new Swing to the database if it does not already exist.
    
    Parameters
    ----------
    tradepair_name : str 
        The name of the tradepair.
    timeframe : str
        The timeframe name of the candles.
    candles : list[dict] 
        A list of candle dictionaries from `returnDict()`.
    orientation_up : bool
        True for swing high, False for swing low.
        
    Returns
    -------
    Swing
        The created Swing object.
    """
    new_swing = None
    with getSession() as session:
        # Ensure the tradepair exists
        tradepair = session.scalar(select(Tradepair).where(Tradepair.name == tradepair_name))
        if not tradepair:
            raise ValueError(f"Tradepair {tradepair_name} does not exist")
        
        timeframe_obj = session.scalar(select(Timeframe).where(Timeframe.name == timeframe))
        if not timeframe_obj:
            raise ValueError(f"Timeframe {timeframe} does not exist")
        
        # Fetch actual Candle objects from DB using the primary keys
        candle_objects = session.scalars(
            select(Candle).where(
                (Candle.tradepair_name == tradepair_name) &
                (Candle.timeframe_name == timeframe) &
                (Candle.datetime_open.in_([c["datetime_open"] for c in candles]))
            )
        ).all()
        
        if len(candle_objects) != len(candles):
            raise ValueError(f"Candles not found")

        # Check if a swing already exists for this tradepair and these candles

        existing_swing = session.scalar(
            select(Swing)
            .where(
                (Swing.tradepair_name == tradepair_name),
                (Swing.orientation_up == orientation_up),
                (Swing.timeframe_name == timeframe)
            ).where(
                session.scalar(
                    select(func.count(swing_candle_link.c.swing_id))
                    .where(
                        (swing_candle_link.c.candle_datetime_open.in_([c["datetime_open"] for c in candles])),
                        (swing_candle_link.c.swing_id == Swing.id)  # Ensure link exists
                    )
                )
                == len(candles)
            )
        )

        if not existing_swing:

            # Create the swing
            new_swing = Swing(
                tradepair_name=tradepair_name,
                timeframe_name=timeframe,
                orientation_up=orientation_up,
                candles=candle_objects
            )
            session.add(new_swing)
            
    return new_swing


def addTimeframe(name, datetime_interval):
    with getSession() as session:
        session.add(Timeframe(name=name, datetime_interval=datetime_interval))
