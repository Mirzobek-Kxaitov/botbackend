from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, UniqueConstraint, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bookings.db")

# SQLite uchun check_same_thread, PostgreSQL uchun yo'q
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Barber(Base):
    """Sartaroshlar jadvali"""
    __tablename__ = "barbers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # Sartarosh ismi
    bot_token = Column(String, unique=True, nullable=False)  # Telegram bot token
    admin_telegram_id = Column(String, nullable=True)  # Sartaroshning Telegram ID (notification uchun)
    phone = Column(String, nullable=True)  # Telefon raqam
    image_url = Column(String, nullable=True)  # Rasm URL
    work_start = Column(String, default="09:00")  # Ish boshlanishi
    work_end = Column(String, default="21:00")  # Ish tugashi
    is_active = Column(Boolean, default=True)  # Faolmi
    gender_category = Column(String, default="both")  # male, female, both
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    services = relationship("Service", back_populates="barber", cascade="all, delete-orphan")
    users = relationship("User", back_populates="barber")
    bookings = relationship("Booking", back_populates="barber")

class Service(Base):
    """Xizmatlar jadvali"""
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    barber_id = Column(Integer, ForeignKey('barbers.id'), nullable=False)
    name = Column(String, nullable=False)  # Xizmat nomi
    price = Column(Float, nullable=False)  # Narx
    duration = Column(Integer, default=1)  # Davomiylik (soatda)
    gender_category = Column(String, default="both")  # male, female, both
    is_active = Column(Boolean, default=True)  # Faolmi
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    barber = relationship("Barber", back_populates="services")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, index=True)  # unique emas - bitta user bir nechta sartaroshda bo'lishi mumkin
    name = Column(String)
    phone = Column(String)
    barber_id = Column(Integer, ForeignKey('barbers.id'), nullable=True)  # Qaysi sartarosh mijozi
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    barber = relationship("Barber", back_populates="users")

    __table_args__ = (
        UniqueConstraint('telegram_id', 'barber_id', name='unique_user_per_barber'),
    )

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    barber_id = Column(Integer, ForeignKey('barbers.id'), nullable=True)  # Qaysi sartarosh
    user_telegram_id = Column(String)
    user_name = Column(String)
    user_phone = Column(String)
    booking_date = Column(String)  # YYYY-MM-DD format
    booking_time = Column(String)  # HH:00 format
    total_duration = Column(Integer, default=1)  # Jami soat
    total_price = Column(Float, default=0)  # Jami summa
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    barber = relationship("Barber", back_populates="bookings")
    services = relationship("BookingService", back_populates="booking", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('barber_id', 'booking_date', 'booking_time', 'is_active', name='unique_active_booking_per_barber_slot'),
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
