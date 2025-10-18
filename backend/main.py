from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, Booking, User, BookingService, create_tables
from datetime import datetime, timedelta
from typing import List, Optional
import os
import httpx
from sqlalchemy.exc import IntegrityError

app = FastAPI()

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

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

@app.on_event("startup")
async def startup():
    create_tables()

@app.get("/")
async def root():
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

    # Hozirgi vaqtni olish (real-time validation)
    now = datetime.now()
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
    """Adminga yangi bron haqida xabar yuborish"""
    if not BOT_TOKEN or not ADMIN_CHAT_ID:
        return False

    try:
        # Xizmatlar ro'yxatini yaratish
        services_text = ""
        if booking.services:
            services_text = "\n\n💼 **Xizmatlar:**\n"
            for service in booking.services:
                services_text += f"   • {service.service_name} - {service.price:,.0f} so'm ({service.duration} soat)\n"

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
        payload = {
            "chat_id": ADMIN_CHAT_ID,
            "text": admin_message,
            "parse_mode": "Markdown"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(telegram_url, json=payload)
            return response.status_code == 200
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)