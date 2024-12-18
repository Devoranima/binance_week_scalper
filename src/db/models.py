from sqlalchemy import Column, String, ForeignKey, DateTime, PrimaryKeyConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from typing import List

class Base(DeclarativeBase):
  pass

class Timeframe (Base):
  __tablename__="timeframe"
  type: Mapped[str] = mapped_column(primary_key=True)
  
  candles: Mapped[List["Candle"]] = relationship()
  

class Tradepair (Base):
  __tablename__="tradepair"
  
  name: Mapped[str] = mapped_column(String(20), primary_key=True)
  tracking: Mapped[bool] = mapped_column(default=True)
  last_updated: Mapped[datetime] = mapped_column(default=datetime.now())
  
  candles: Mapped[List["Candle"]] = relationship()
  
class Candle (Base):
  __tablename__="candle"
  
  tradepair_name: Mapped[str] = mapped_column(ForeignKey("tradepair.name"))
  timeframe: Mapped[str] = mapped_column(ForeignKey("timeframe.type"))
  datetime_open: Mapped[datetime] = mapped_column()
  datetime_close: Mapped[datetime] = mapped_column()
  value_max: Mapped[float] = mapped_column()
  value_min: Mapped[float] = mapped_column() 
  value_open: Mapped[float] = mapped_column()
  value_close: Mapped[float] = mapped_column()
  
  __table_args__ = (
    PrimaryKeyConstraint(tradepair_name, timeframe, datetime_open),
    {}
  )

