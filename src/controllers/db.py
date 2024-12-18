from ..db.engine import engine
from ..db.models import Tradepair, Candle
from ..utils.types import Kline
from sqlalchemy import select, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session
from typing import List
from contextlib import contextmanager


@contextmanager
def getSession():
    session = Session(engine)
    session.begin()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def selectAllTradepairs():
    with getSession() as session:    
        stmt = select(Tradepair.name).order_by(Tradepair.name)
        return session.execute(stmt).all()

    
def selectFilteredTradepairs(tracking: bool):
    with getSession() as session:
        stmt = select(Tradepair.name).where(Tradepair.tracking == tracking)
        return session.execute(stmt).all()


def updateTradepairs(tradepairs: List[str]):
    with getSession() as session:
        for tradepair_name in tradepairs:
            tradepair = Tradepair(name = tradepair_name)
            session.add(tradepair)
    return tradepairs


def switchTradepairsTrackingStatus(tracking:bool, selected_tradepairs: list[str]):
    with getSession() as session:
        stmt = update(Tradepair)
        return session.execute(stmt, list({'name': tradepair, 'tracking': tracking} for tradepair in selected_tradepairs)).all()


def addCandles(klines: dict[str, list[Kline]]):
    with getSession() as session:
        candles_to_add = []
        
        for tradepair_name, klines in klines.items():
            for kline in klines:
                candle = Candle(tradepair_name, **kline)
                candles_to_add.append(candle)
        
        stmt = sqlite_insert(Candle).values(candles_to_add).on_conflict_do_nothing(index_elements=['tradepair_name', 'timeframe', 'datetime_open'])
        result = session.execute(stmt).all()
        return result

        
        
            
