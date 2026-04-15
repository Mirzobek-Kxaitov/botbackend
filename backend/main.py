from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, Booking, User, BookingService, Barber, Service, create_tables
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import os
import logging
import httpx
from sqlalchemy.exc import IntegrityError
import pytz
import pathlib

app = FastAPI()

# Mount static files (frontend and admin) - use absolute path
FRONTEND_DIR = pathlib.Path(__file__).parent.parent / "frontend"
ADMIN_DIR = pathlib.Path(__file__).parent.parent / "admin"

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # ngrok bilan ishlaganda False bo'lishi kerak
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

class ServiceRequest(BaseModel):
    name: str
    service: str
    price: float
    duration: int

class BookingRequest(BaseModel):
    date: str
    time: str
    user_telegram_id: str
    user_name: str
    user_phone: str
    services: List[ServiceRequest] = []
    total_price: float = 0
    total_duration: int = 1

class ServiceResponse(BaseModel):
    service_name: str
    service_code: str
    price: float
    duration: int

class BookingResponse(BaseModel):
    id: int
    date: str
    time: str
    user_name: str
    user_phone: str
    total_price: float
    total_duration: int
    services: List[ServiceResponse] = []

# Barber Pydantic Models
class BarberCreate(BaseModel):
    name: str
    bot_token: str
    phone: Optional[str] = None
    image_url: Optional[str] = None
    work_start: str = "09:00"
    work_end: str = "21:00"
    gender_category: str = "both"  # male, female, both
    is_active: bool = True

class BarberUpdate(BaseModel):
    name: Optional[str] = None
    bot_token: Optional[str] = None
    phone: Optional[str] = None
    image_url: Optional[str] = None
    work_start: Optional[str] = None
    work_end: Optional[str] = None
    gender_category: Optional[str] = None
    is_active: Optional[bool] = None

class BarberResponse(BaseModel):
    id: int
    name: str
    bot_token: str
    phone: Optional[str]
    image_url: Optional[str]
    work_start: str
    work_end: str
    gender_category: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Service Pydantic Models
class ServiceCreate(BaseModel):
    barber_id: int
    name: str
    price: float
    duration: int = 1
    gender_category: str = "both"  # male, female, both
    is_active: bool = True

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    duration: Optional[int] = None
    gender_category: Optional[str] = None
    is_active: Optional[bool] = None

class ServiceResponseDetailed(BaseModel):
    id: int
    barber_id: int
    name: str
    price: float
    duration: int
    gender_category: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Admin va Super Admin chat ID lar
ADMIN_CHAT_IDS = []
if os.getenv("ADMIN_CHAT_ID"):
    ADMIN_CHAT_IDS = [int(id.strip()) for id in os.getenv("ADMIN_CHAT_ID").split(",")]

SUPER_ADMIN_CHAT_IDS = []
if os.getenv("SUPER_ADMIN_CHAT_ID"):
    SUPER_ADMIN_CHAT_IDS = [int(id.strip()) for id in os.getenv("SUPER_ADMIN_CHAT_ID").split(",")]

# Barcha adminlar (Admin + Super Admin)
ALL_ADMIN_IDS = ADMIN_CHAT_IDS + SUPER_ADMIN_CHAT_IDS

@app.on_event("startup")
async def startup():
    create_tables()

@app.get("/")
async def root():
    """Root endpoint - redirect to webapp"""
    return {"message": "Rustam Barber Booking System", "webapp": "/webapp", "status": "running"}

@app.get("/webapp")
async def serve_webapp():
    """Serve the frontend Web App"""
    return FileResponse(str(FRONTEND_DIR / "index.html"))

@app.get("/api")
async def api_root():
    return {"message": "Barbershop Booking API"}

@app.get("/available-times/today")
async def get_today_available_times(
    duration: Optional[int] = Query(1, description="Jami kerakli soatlar"),
    db: Session = Depends(get_db)
):
    today = datetime.now().strftime("%Y-%m-%d")
    return await get_available_times_internal(today, duration, db)

@app.get("/available-times/tomorrow")
async def get_tomorrow_available_times(
    duration: Optional[int] = Query(1, description="Jami kerakli soatlar"),
    db: Session = Depends(get_db)
):
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    return await get_available_times_internal(tomorrow, duration, db)

@app.get("/available-times/{date}")
async def get_available_times(
    date: str,
    duration: Optional[int] = Query(1, description="Jami kerakli soatlar"),
    db: Session = Depends(get_db)
):
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    return await get_available_times_internal(date, duration, db)

async def get_available_times_internal(date: str, duration: int, db: Session):
    all_times = [f"{hour:02d}:00" for hour in range(9, 22)]

    # Hozirgi vaqtni olish (real-time validation) - Tashkent timezone
    tashkent_tz = pytz.timezone('Asia/Tashkent')
    now = datetime.now(tashkent_tz)
    current_date = now.strftime("%Y-%m-%d")
    current_hour = now.hour

    # Agar bugun tanlangan bo'lsa, faqat kelajakdagi vaqtlarni ko'rsatish
    if date == current_date:
        # Hozirgi vaqtdan keyingi vaqtlarni filtrlash
        all_times = [time for time in all_times if int(time.split(':')[0]) > current_hour]

    # Band qilingan vaqtlarni olish
    bookings = db.query(Booking).filter(
        Booking.booking_date == date,
        Booking.is_active == True
    ).all()

    # Har bir bron uchun band qilingan barcha soatlarni hisoblash
    # Agar 10:00 da 2 soatlik bron bo'lsa, 10:00-12:00 band (10:00, 11:00, 12:00)
    booked_hours = set()
    for booking in bookings:
        start_hour = int(booking.booking_time.split(':')[0])
        end_hour = start_hour + booking.total_duration
        # Boshlanish vaqtidan tugash vaqtigacha barcha soatlarni band qilish
        for hour in range(start_hour, end_hour + 1):
            if hour <= 22:  # Maksimal ish vaqti
                booked_hours.add(f"{hour:02d}:00")

    # Mavjud vaqtlarni topish (duration soatlik ketma-ket bo'sh oraliq kerak)
    available_times = []
    for time in all_times:
        start_hour = int(time.split(':')[0])
        # Kerakli davomiylikdagi barcha soatlar bo'shligini tekshirish
        is_available = True
        for i in range(duration):
            check_time = f"{start_hour + i:02d}:00"
            if check_time in booked_hours or start_hour + i >= 22:
                is_available = False
                break
        if is_available:
            available_times.append(time)

    print(f"Date: {date}, Duration: {duration}")
    print(f"Booked hours: {booked_hours}")
    print(f"Available times: {available_times}")

    return {"available_times": available_times, "date": date, "duration": duration}

@app.get("/bookings/{date}")
async def get_bookings(date: str, db: Session = Depends(get_db)):
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    bookings = db.query(Booking).filter(
        Booking.booking_date == date,
        Booking.is_active == True
    ).all()

    return [
        BookingResponse(
            id=booking.id,
            date=booking.booking_date,
            time=booking.booking_time,
            user_name=booking.user_name,
            user_phone=booking.user_phone,
            total_price=booking.total_price,
            total_duration=booking.total_duration,
            services=[
                ServiceResponse(
                    service_name=service.service_name,
                    service_code=service.service_code,
                    price=service.price,
                    duration=service.duration
                )
                for service in booking.services
            ]
        )
        for booking in bookings
    ]

async def send_admin_notification(booking: Booking):
    """Admin va Super Adminga yangi bron haqida xabar yuborish"""
    if not BOT_TOKEN or not ALL_ADMIN_IDS:
        return False

    try:
        # Xizmatlar ro'yxatini yaratish
        services_text = ""
        if booking.services:
            services_text = "\n\n💼 **Xizmatlar:**\n"
            for service in booking.services:
                services_text += f"   • {service.service_name} - {service.price:,.0f} so'm ({service.duration} soat)\n"

        # Super Admin uchun maxsus xabar (ko'proq ma'lumot bilan)
        super_admin_message = (
            f"👑 **YANGI BRON QILINDI!** (Super Admin)\n\n"
            f"👤 **Mijoz:** {booking.user_name}\n"
            f"📱 **Telefon:** {booking.user_phone}\n"
            f"🆔 **Telegram ID:** {booking.user_telegram_id}\n"
            f"📅 **Sana:** {booking.booking_date}\n"
            f"⏰ **Vaqt:** {booking.booking_time}\n"
            f"⏱ **Davomiyligi:** {booking.total_duration} soat"
            f"{services_text}\n"
            f"💰 **Jami summa:** {booking.total_price:,.0f} so'm\n"
            f"🆔 **Bron ID:** #{booking.id}\n\n"
            f"📋 Bugungi mijozlar: /mijozlar\n"
            f"📊 Statistika: /statistika"
        )

        # Oddiy Admin uchun xabar
        admin_message = (
            f"🎉 **YANGI BRON QILINDI!**\n\n"
            f"👤 **Mijoz:** {booking.user_name}\n"
            f"📱 **Telefon:** {booking.user_phone}\n"
            f"📅 **Sana:** {booking.booking_date}\n"
            f"⏰ **Vaqt:** {booking.booking_time}\n"
            f"⏱ **Davomiyligi:** {booking.total_duration} soat"
            f"{services_text}\n"
            f"💰 **Jami summa:** {booking.total_price:,.0f} so'm\n"
            f"🆔 **Bron ID:** #{booking.id}\n\n"
            f"📋 Bugungi mijozlar: /mijozlar\n"
            f"📊 Statistika: /statistika"
        )

        telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        success = True

        async with httpx.AsyncClient() as client:
            # Super Admin larga yuborish
            if SUPER_ADMIN_CHAT_IDS:
                for super_admin_id in SUPER_ADMIN_CHAT_IDS:
                    try:
                        payload = {
                            "chat_id": super_admin_id,
                            "text": super_admin_message,
                            "parse_mode": "Markdown"
                        }
                        response = await client.post(telegram_url, json=payload)
                        if response.status_code != 200:
                            success = False
                            print(f"Super Admin {super_admin_id} ga xabar yuborishda xatolik")
                    except Exception as e:
                        print(f"Super Admin {super_admin_id} ga xabar yuborishda xatolik: {e}")
                        success = False

            # Oddiy Admin larga yuborish (Super Adminlarni chiqarib tashlash)
            if ADMIN_CHAT_IDS:
                for admin_id in ADMIN_CHAT_IDS:
                    # Agar bu admin Super Admin bo'lmasa, faqat shunda yuborish
                    if not SUPER_ADMIN_CHAT_IDS or admin_id not in SUPER_ADMIN_CHAT_IDS:
                        try:
                            payload = {
                                "chat_id": admin_id,
                                "text": admin_message,
                                "parse_mode": "Markdown"
                            }
                            response = await client.post(telegram_url, json=payload)
                            if response.status_code != 200:
                                success = False
                                print(f"Admin {admin_id} ga xabar yuborishda xatolik")
                        except Exception as e:
                            print(f"Admin {admin_id} ga xabar yuborishda xatolik: {e}")
                            success = False

        return success
    except Exception as e:
        print(f"Admin'ga xabar yuborishda xatolik: {e}")
        return False

@app.post("/bookings")
async def create_booking(booking_request: BookingRequest, db: Session = Depends(get_db)):
    try:
        # Sanani tekshirish
        datetime.strptime(booking_request.date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Foydalanuvchini tekshirish/yaratish
    user = db.query(User).filter(User.telegram_id == booking_request.user_telegram_id).first()
    if not user:
        user = User(
            telegram_id=booking_request.user_telegram_id,
            name=booking_request.user_name,
            phone=booking_request.user_phone
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Yangi bron yaratish
    new_booking = Booking(
        user_telegram_id=booking_request.user_telegram_id,
        user_name=booking_request.user_name,
        user_phone=booking_request.user_phone,
        booking_date=booking_request.date,
        booking_time=booking_request.time,
        total_duration=booking_request.total_duration,
        total_price=booking_request.total_price
    )

    try:
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)

        # Xizmatlarni qo'shish
        if booking_request.services:
            for service in booking_request.services:
                booking_service = BookingService(
                    booking_id=new_booking.id,
                    service_name=service.name,
                    service_code=service.service,
                    price=service.price,
                    duration=service.duration
                )
                db.add(booking_service)

            db.commit()
            db.refresh(new_booking)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Bu vaqt allaqachon band. Iltimos, boshqa vaqtni tanlang."
        )

    # Admin'ga xabar yuborish
    await send_admin_notification(new_booking)

    return {
        "success": True,
        "message": "Bron muvaffaqiyatli yaratildi!",
        "booking": {
            "id": new_booking.id,
            "date": new_booking.booking_date,
            "time": new_booking.booking_time,
            "user_name": new_booking.user_name,
            "user_phone": new_booking.user_phone,
            "total_price": new_booking.total_price,
            "total_duration": new_booking.total_duration,
            "services": [
                {
                    "service_name": service.service_name,
                    "service_code": service.service_code,
                    "price": service.price,
                    "duration": service.duration
                }
                for service in new_booking.services
            ]
        }
    }

# ==================== BARBER CRUD ENDPOINTS ====================

@app.get("/api/barbers", response_model=List[BarberResponse])
async def get_barbers(
    skip: int = Query(0, description="Skip N barbers"),
    limit: int = Query(100, description="Limit results"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """Barcha sartaroshlarni olish"""
    query = db.query(Barber)

    if is_active is not None:
        query = query.filter(Barber.is_active == is_active)

    barbers = query.offset(skip).limit(limit).all()
    return barbers

@app.post("/api/barbers", response_model=BarberResponse)
async def create_barber(barber: BarberCreate, db: Session = Depends(get_db)):
    """Yangi sartarosh qo'shish"""
    # Check if bot_token already exists
    existing_barber = db.query(Barber).filter(Barber.bot_token == barber.bot_token).first()
    if existing_barber:
        raise HTTPException(
            status_code=400,
            detail="Bu bot token allaqachon mavjud. Har bir sartarosh uchun alohida bot token kerak."
        )

    # Validate gender_category
    if barber.gender_category not in ["male", "female", "both"]:
        raise HTTPException(
            status_code=400,
            detail="gender_category faqat 'male', 'female' yoki 'both' bo'lishi mumkin"
        )

    new_barber = Barber(
        name=barber.name,
        bot_token=barber.bot_token,
        phone=barber.phone,
        image_url=barber.image_url,
        work_start=barber.work_start,
        work_end=barber.work_end,
        gender_category=barber.gender_category,
        is_active=barber.is_active
    )

    try:
        db.add(new_barber)
        db.commit()
        db.refresh(new_barber)
        return new_barber
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Sartarosh yaratishda xatolik. Bot token unique bo'lishi kerak."
        )

@app.get("/api/barbers/{barber_id}", response_model=BarberResponse)
async def get_barber(barber_id: int, db: Session = Depends(get_db)):
    """Bitta sartaroshni olish"""
    barber = db.query(Barber).filter(Barber.id == barber_id).first()
    if not barber:
        raise HTTPException(status_code=404, detail="Sartarosh topilmadi")
    return barber

@app.put("/api/barbers/{barber_id}", response_model=BarberResponse)
async def update_barber(
    barber_id: int,
    barber_update: BarberUpdate,
    db: Session = Depends(get_db)
):
    """Sartarosh ma'lumotlarini yangilash"""
    barber = db.query(Barber).filter(Barber.id == barber_id).first()
    if not barber:
        raise HTTPException(status_code=404, detail="Sartarosh topilmadi")

    # Check if bot_token is being updated and already exists
    if barber_update.bot_token:
        existing = db.query(Barber).filter(
            Barber.bot_token == barber_update.bot_token,
            Barber.id != barber_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Bu bot token boshqa sartaroshda mavjud"
            )

    # Validate gender_category if provided
    if barber_update.gender_category and barber_update.gender_category not in ["male", "female", "both"]:
        raise HTTPException(
            status_code=400,
            detail="gender_category faqat 'male', 'female' yoki 'both' bo'lishi mumkin"
        )

    # Update only provided fields
    update_data = barber_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(barber, field, value)

    try:
        db.commit()
        db.refresh(barber)
        return barber
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Sartarosh yangilashda xatolik"
        )

@app.delete("/api/barbers/{barber_id}")
async def delete_barber(barber_id: int, db: Session = Depends(get_db)):
    """Sartaroshni o'chirish"""
    barber = db.query(Barber).filter(Barber.id == barber_id).first()
    if not barber:
        raise HTTPException(status_code=404, detail="Sartarosh topilmadi")

    # Check if barber has any bookings or users
    booking_count = db.query(Booking).filter(Booking.barber_id == barber_id).count()
    user_count = db.query(User).filter(User.barber_id == barber_id).count()

    if booking_count > 0 or user_count > 0:
        # Soft delete - just deactivate
        barber.is_active = False
        db.commit()
        return {
            "success": True,
            "message": f"Sartarosh deaktivatsiya qilindi (mijozlar va bronlar mavjud). Bronlar: {booking_count}, Mijozlar: {user_count}",
            "soft_delete": True
        }
    else:
        # Hard delete - no data associated
        db.delete(barber)
        db.commit()
        return {
            "success": True,
            "message": "Sartarosh butunlay o'chirildi",
            "soft_delete": False
        }

# ==================== SERVICE CRUD ENDPOINTS ====================

@app.get("/api/services", response_model=List[ServiceResponseDetailed])
async def get_services(
    barber_id: Optional[int] = Query(None, description="Filter by barber ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    gender_category: Optional[str] = Query(None, description="Filter by gender category"),
    skip: int = Query(0, description="Skip N services"),
    limit: int = Query(100, description="Limit results"),
    db: Session = Depends(get_db)
):
    """Barcha xizmatlarni olish (filtrlash imkoniyati bilan)"""
    query = db.query(Service)

    if barber_id is not None:
        query = query.filter(Service.barber_id == barber_id)

    if is_active is not None:
        query = query.filter(Service.is_active == is_active)

    if gender_category:
        query = query.filter(Service.gender_category == gender_category)

    services = query.offset(skip).limit(limit).all()
    return services

@app.post("/api/services", response_model=ServiceResponseDetailed)
async def create_service(service: ServiceCreate, db: Session = Depends(get_db)):
    """Yangi xizmat qo'shish"""
    # Check if barber exists
    barber = db.query(Barber).filter(Barber.id == service.barber_id).first()
    if not barber:
        raise HTTPException(status_code=404, detail="Sartarosh topilmadi")

    # Validate gender_category
    if service.gender_category not in ["male", "female", "both"]:
        raise HTTPException(
            status_code=400,
            detail="gender_category faqat 'male', 'female' yoki 'both' bo'lishi mumkin"
        )

    # Validate price and duration
    if service.price <= 0:
        raise HTTPException(status_code=400, detail="Narx 0 dan katta bo'lishi kerak")

    if service.duration <= 0:
        raise HTTPException(status_code=400, detail="Davomiylik 0 dan katta bo'lishi kerak")

    new_service = Service(
        barber_id=service.barber_id,
        name=service.name,
        price=service.price,
        duration=service.duration,
        gender_category=service.gender_category,
        is_active=service.is_active
    )

    try:
        db.add(new_service)
        db.commit()
        db.refresh(new_service)
        return new_service
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Xizmat yaratishda xatolik"
        )

@app.get("/api/services/{service_id}", response_model=ServiceResponseDetailed)
async def get_service(service_id: int, db: Session = Depends(get_db)):
    """Bitta xizmatni olish"""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Xizmat topilmadi")
    return service

@app.put("/api/services/{service_id}", response_model=ServiceResponseDetailed)
async def update_service(
    service_id: int,
    service_update: ServiceUpdate,
    db: Session = Depends(get_db)
):
    """Xizmat ma'lumotlarini yangilash"""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Xizmat topilmadi")

    # Validate gender_category if provided
    if service_update.gender_category and service_update.gender_category not in ["male", "female", "both"]:
        raise HTTPException(
            status_code=400,
            detail="gender_category faqat 'male', 'female' yoki 'both' bo'lishi mumkin"
        )

    # Validate price if provided
    if service_update.price is not None and service_update.price <= 0:
        raise HTTPException(status_code=400, detail="Narx 0 dan katta bo'lishi kerak")

    # Validate duration if provided
    if service_update.duration is not None and service_update.duration <= 0:
        raise HTTPException(status_code=400, detail="Davomiylik 0 dan katta bo'lishi kerak")

    # Update only provided fields
    update_data = service_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(service, field, value)

    try:
        db.commit()
        db.refresh(service)
        return service
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Xizmat yangilashda xatolik"
        )

@app.delete("/api/services/{service_id}")
async def delete_service(service_id: int, db: Session = Depends(get_db)):
    """Xizmatni o'chirish"""
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Xizmat topilmadi")

    # Check if service is used in any bookings
    booking_service_count = db.query(BookingService).filter(
        BookingService.service_code == str(service.id)  # Assuming service_code stores service ID
    ).count()

    if booking_service_count > 0:
        # Soft delete - just deactivate
        service.is_active = False
        db.commit()
        return {
            "success": True,
            "message": f"Xizmat deaktivatsiya qilindi (bronlarda ishlatilgan: {booking_service_count})",
            "soft_delete": True
        }
    else:
        # Hard delete - no bookings associated
        db.delete(service)
        db.commit()
        return {
            "success": True,
            "message": "Xizmat butunlay o'chirildi",
            "soft_delete": False
        }

# ==================== BOT MANAGEMENT ENDPOINTS ====================

# Bot manager reference (set by bot_manager.py at startup)
_bot_manager = None

def set_bot_manager(manager_module):
    """Bot manager modulini o'rnatish (bot_manager.py dan chaqiriladi)"""
    global _bot_manager
    _bot_manager = manager_module

@app.get("/api/bots/status")
async def get_bots_status():
    """Barcha botlar holatini olish"""
    if not _bot_manager:
        return {"running_bots": [], "total": 0, "manager_active": False}

    running_ids = list(_bot_manager.running_bots.keys())

    db_session = next(get_db())
    try:
        barbers = db_session.query(Barber).filter(Barber.is_active == True).all()
        status_list = []
        for barber in barbers:
            status_list.append({
                "barber_id": barber.id,
                "barber_name": barber.name,
                "is_running": barber.id in running_ids
            })
        return {
            "running_bots": status_list,
            "total": len(running_ids),
            "manager_active": True
        }
    finally:
        db_session.close()

@app.post("/api/bots/{barber_id}/start")
async def start_bot_endpoint(barber_id: int, db: Session = Depends(get_db)):
    """Sartarosh botini ishga tushirish"""
    if not _bot_manager:
        raise HTTPException(status_code=503, detail="Bot manager ishlamayapti")

    barber = db.query(Barber).filter(Barber.id == barber_id).first()
    if not barber:
        raise HTTPException(status_code=404, detail="Sartarosh topilmadi")

    if barber_id in _bot_manager.running_bots:
        return {"success": True, "message": f"{barber.name} boti allaqachon ishlayapti"}

    success = await _bot_manager.start_bot(barber.id, barber.bot_token, barber.name)
    if success:
        return {"success": True, "message": f"{barber.name} boti ishga tushirildi"}
    else:
        raise HTTPException(status_code=500, detail=f"{barber.name} botini ishga tushirishda xatolik")

@app.post("/api/bots/{barber_id}/stop")
async def stop_bot_endpoint(barber_id: int, db: Session = Depends(get_db)):
    """Sartarosh botini to'xtatish"""
    if not _bot_manager:
        raise HTTPException(status_code=503, detail="Bot manager ishlamayapti")

    barber = db.query(Barber).filter(Barber.id == barber_id).first()
    barber_name = barber.name if barber else f"Barber-{barber_id}"

    if barber_id not in _bot_manager.running_bots:
        return {"success": True, "message": f"{barber_name} boti allaqachon to'xtatilgan"}

    success = await _bot_manager.stop_bot(barber_id, barber_name)
    if success:
        return {"success": True, "message": f"{barber_name} boti to'xtatildi"}
    else:
        raise HTTPException(status_code=500, detail=f"{barber_name} botini to'xtatishda xatolik")

@app.post("/api/bots/restart-all")
async def restart_all_bots():
    """Barcha botlarni qayta ishga tushirish"""
    if not _bot_manager:
        raise HTTPException(status_code=503, detail="Bot manager ishlamayapti")

    await _bot_manager.stop_all_bots()
    await _bot_manager.start_all_bots()
    return {
        "success": True,
        "message": f"{len(_bot_manager.running_bots)} ta bot qayta ishga tushirildi"
    }

# ==================== BROADCAST ENDPOINTS ====================

class BroadcastRequest(BaseModel):
    barber_id: int
    message: str

@app.post("/api/broadcast")
async def broadcast_message(request: BroadcastRequest, db: Session = Depends(get_db)):
    """Sartarosh mijozlariga xabar yuborish"""
    if not _bot_manager:
        raise HTTPException(status_code=503, detail="Bot manager ishlamayapti")

    barber = db.query(Barber).filter(Barber.id == request.barber_id).first()
    if not barber:
        raise HTTPException(status_code=404, detail="Sartarosh topilmadi")

    if request.barber_id not in _bot_manager.running_bots:
        raise HTTPException(status_code=400, detail=f"{barber.name} boti ishlamayapti. Avval botni ishga tushiring.")

    # Bu sartarosh mijozlarini olish
    users = db.query(User).filter(User.barber_id == request.barber_id).all()

    if not users:
        return {"success": False, "sent": 0, "failed": 0, "total": 0, "message": "Mijozlar topilmadi"}

    # Bot application dan bot objectni olish
    application = _bot_manager.running_bots[request.barber_id]
    bot = application.bot

    sent = 0
    failed = 0
    for user in users:
        try:
            await bot.send_message(
                chat_id=int(user.telegram_id),
                text=f"📢 {barber.name} sartaroshxonasidan xabar:\n\n{request.message}",
                parse_mode='Markdown'
            )
            sent += 1
        except Exception as e:
            failed += 1
            logging.getLogger(__name__).error(f"Broadcast failed for user {user.telegram_id}: {e}")

    return {
        "success": True,
        "sent": sent,
        "failed": failed,
        "total": len(users),
        "message": f"{sent} ta mijozga xabar yuborildi" + (f", {failed} ta xatolik" if failed else "")
    }

@app.get("/api/users/count")
async def get_users_count(
    barber_id: Optional[int] = Query(None, description="Filter by barber ID"),
    db: Session = Depends(get_db)
):
    """Mijozlar sonini olish"""
    query = db.query(User)
    if barber_id is not None:
        query = query.filter(User.barber_id == barber_id)
    count = query.count()
    return {"count": count, "barber_id": barber_id}

# ==================== ADMIN PANEL (mount at the end) ====================
# Admin panel mount eng oxirida bo'lishi kerak, chunki u barcha sub-pathlarni ushlab oladi
app.mount("/admin", StaticFiles(directory=str(ADMIN_DIR), html=True), name="admin")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)