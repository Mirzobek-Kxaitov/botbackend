from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, Booking, create_tables
from datetime import datetime, timedelta
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BookingRequest(BaseModel):
    date: str
    time: str

class BookingResponse(BaseModel):
    id: int
    date: str
    time: str
    user_name: str
    user_phone: str

@app.on_event("startup")
async def startup():
    create_tables()

@app.get("/")
async def root():
    return {"message": "Barbershop Booking API"}

@app.get("/available-times/{date}")
async def get_available_times(date: str, db: Session = Depends(get_db)):
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    all_times = [f"{hour:02d}:00" for hour in range(9, 22)]
    
    booked_times = db.query(Booking.booking_time).filter(
        Booking.booking_date == date,
        Booking.is_active == True
    ).all()
    
    booked_times_list = [time[0] for time in booked_times]
    available_times = [time for time in all_times if time not in booked_times_list]
    
    return {"available_times": available_times}

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
            user_phone=booking.user_phone
        )
        for booking in bookings
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)