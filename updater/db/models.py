from sqlalchemy import String, ForeignKey, DateTime, Table, Column, Float, Boolean, ForeignKeyConstraint, Interval, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, validates
from datetime import datetime, timedelta
from typing import List

class Base(DeclarativeBase):
  pass

class SerializerMixin:
  def to_dict(self):
    return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class Timeframe (Base, SerializerMixin):
  __tablename__="timeframe"
  name: Mapped[str] = mapped_column(String(10), primary_key=True)
  datetime_interval: Mapped[timedelta] = mapped_column(Interval, nullable=False)
  
  candles: Mapped[List["Candle"]] = relationship("Candle", back_populates="timeframe")
  swings: Mapped[List["Swing"]] = relationship("Swing", back_populates="timeframe", cascade="all, delete-orphan")
  

class Tradepair (Base, SerializerMixin):
  __tablename__="tradepair"
  
  name: Mapped[str] = mapped_column(String(20), primary_key=True)
  tracking: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
  delisted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
  
  candles: Mapped[List["Candle"]] = relationship("Candle", back_populates="tradepair", cascade="all, delete-orphan")
  swings: Mapped[List["Swing"]] = relationship("Swing", back_populates="tradepair", cascade="all, delete-orphan")

  
class Candle (Base, SerializerMixin):
  __tablename__="candle"
  
  tradepair_name: Mapped[str] = mapped_column(ForeignKey("tradepair.name"), primary_key=True)
  timeframe_name: Mapped[str] = mapped_column(ForeignKey("timeframe.name"), primary_key=True)
  datetime_open: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
  datetime_close: Mapped[datetime] = mapped_column(DateTime, nullable=False)
  high: Mapped[float] = mapped_column(Float, nullable=False)
  low: Mapped[float] = mapped_column(Float, nullable=False)
  open: Mapped[float] = mapped_column(Float, nullable=False)
  close: Mapped[float] = mapped_column(Float, nullable=False)
  
  tradepair: Mapped["Tradepair"] = relationship("Tradepair", back_populates="candles")
  timeframe: Mapped["Timeframe"] = relationship("Timeframe", back_populates="candles")
  swings: Mapped[List["Swing"]] = relationship("Swing", secondary="swing_candle_link", back_populates="candles")

swing_candle_link = Table(
  "swing_candle_link", Base.metadata,
  Column("swing_id", ForeignKey("swing.id"), primary_key=True),
  Column("candle_tradepair", String(20), primary_key=True),
  Column("candle_timeframe", String(10), primary_key=True),
  Column("candle_datetime_open", DateTime, primary_key=True),
  ForeignKeyConstraint(
    ["candle_tradepair", "candle_timeframe", "candle_datetime_open"],
    ["candle.tradepair_name", "candle.timeframe_name", "candle.datetime_open"]
  )
)
  
class Swing(Base, SerializerMixin):
  __tablename__ = "swing"
  id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
  tradepair_name: Mapped[str] = mapped_column(ForeignKey("tradepair.name"), nullable=False)
  timeframe_name: Mapped[str] = mapped_column(ForeignKey("timeframe.name"), nullable=False)
  orientation_up: Mapped[bool] = mapped_column(Boolean, nullable=False)
    
  tradepair: Mapped["Tradepair"] = relationship("Tradepair", back_populates="swings")
  timeframe: Mapped["Timeframe"] = relationship("Timeframe", back_populates="swings")
  
  candles: Mapped[List["Candle"]] = relationship("Candle", secondary="swing_candle_link", back_populates="swings")
