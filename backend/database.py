from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, UniqueConstraint, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bookings.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True)
    name = Column(String)
    phone = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_telegram_id = Column(String)
    user_name = Column(String)
    user_phone = Column(String)
    booking_date = Column(String)  # YYYY-MM-DD format
    booking_time = Column(String)  # HH:00 format
    total_duration = Column(Integer, default=1)  # Jami soat
    total_price = Column(Float, default=0)  # Jami summa
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationship
    services = relationship("BookingService", back_populates="booking", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('booking_date', 'booking_time', 'is_active', name='unique_active_booking_per_slot'),
    )

class BookingService(Base):
    __tablename__ = "booking_services"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey('bookings.id'))
    service_name = Column(String)
    service_code = Column(String)
    price = Column(Float)
    duration = Column(Integer)  # Soatlarda
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    booking = relationship("Booking", back_populates="services")

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()