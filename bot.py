import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
from database import engine, User, Booking, BookingService, create_tables
from datetime import datetime, timedelta
import json

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
WEBAPP_URL = "https://barberlocal.uz"  # Bu URL frontendni deploy qilgandan keyin o'zgartiriladi

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    db = SessionLocal()
    
    try:
        existing_user = db.query(User).filter(User.telegram_id == user_id).first()
        
        if not existing_user:
            await update.message.reply_text(
                "Salom! Sartaroshxonaga xush kelibsiz! 👋\n\n"
                "Bron qilish uchun iltimos ismingizni yuboring:"
            )
            context.user_data['registration_step'] = 'name'
        else:
            keyboard = [
                [KeyboardButton("✂️ BRON QILISH", web_app=WebAppInfo(url=WEBAPP_URL))]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                f"Xush kelibsiz, {existing_user.name}! 🎉\n\n"
                "Sartaroshxonaga bron qilish uchun quyidagi tugmani bosing:",
                reply_markup=reply_markup
            )
    finally:
        db.close()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    text = update.message.text
    db = SessionLocal()
    
    try:
        if context.user_data.get('registration_step') == 'name':
            context.user_data['name'] = text
            context.user_data['registration_step'] = 'phone'
            
            keyboard = [[KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            
            await update.message.reply_text(
                f"Rahmat, {text}! 😊\n\n"
                "Endi telefon raqamingizni yuboring:",
                reply_markup=reply_markup
            )
        
            
        elif context.user_data.get('registration_step') == 'phone' and update.message.contact:
            phone = update.message.contact.phone_number
            name = context.user_data.get('name')
            
            new_user = User(telegram_id=user_id, name=name, phone=phone)
            db.add(new_user)
            db.commit()
            
            keyboard = [
                [KeyboardButton("✂️ BRON QILISH", web_app=WebAppInfo(url=WEBAPP_URL))]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                f"Ro'yxatdan o'tish muvaffaqiyatli yakunlandi! ✅\n\n"
                f"Ism: {name}\n"
                f"Telefon: {phone}\n\n"
                "Endi sartaroshxonaga bron qilish uchun quyidagi tugmani bosing:",
                reply_markup=reply_markup
            )
            
            context.user_data.clear()
    
    finally:
        db.close()


async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        data = json.loads(update.effective_message.web_app_data.data)
        user_id = str(update.effective_user.id)
        db = SessionLocal()

        try:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                await update.message.reply_text("❌ Xatolik: Foydalanuvchi topilmadi.")
                return

            booking_date = data.get('date')
            booking_time = data.get('time')
            services = data.get('services', [])
            total_price = data.get('total_price', 0)
            total_duration = data.get('total_duration', 1)

            # Bron qilish
            new_booking = Booking(
                user_telegram_id=user_id,
                user_name=user.name,
                user_phone=user.phone,
                booking_date=booking_date,
                booking_time=booking_time,
                total_price=total_price,
                total_duration=total_duration
            )
            db.add(new_booking)
            db.commit()
            db.refresh(new_booking)

            # Xizmatlarni qo'shish
            for service in services:
                booking_service = BookingService(
                    booking_id=new_booking.id,
                    service_name=service['name'],
                    service_code=service['service'],
                    price=service['price'],
                    duration=service['duration']
                )
                db.add(booking_service)

            db.commit()

            # Mijozga tasdiqlash xabari
            services_text = "\n".join([f"   • {s['name']} - {s['price']:,} so'm" for s in services])
            client_message = (
                f"✅ Bron muvaffaqiyatli qilindi!\n\n"
                f"🆔 Bron raqami: #{new_booking.id}\n"
                f"📅 Sana: {booking_date}\n"
                f"⏰ Vaqt: {booking_time}\n"
                f"⏱ Davomiyligi: {total_duration} soat\n\n"
                f"💼 Xizmatlar:\n{services_text}\n\n"
                f"💰 Jami summa: {total_price:,} so'm\n\n"
                "Belgilangan vaqtda sartaroshxonaga tashrif buyuring!"
            )
            await update.message.reply_text(client_message)

            # Adminga xabar yuborish
            if ADMIN_CHAT_ID:
                admin_message = (
                    f"🎉 YANGI BRON QILINDI!\n\n"
                    f"🆔 Bron raqami: #{new_booking.id}\n"
                    f"👤 Mijoz: {user.name}\n"
                    f"📱 Telefon: {user.phone}\n"
                    f"📅 Sana: {booking_date}\n"
                    f"⏰ Vaqt: {booking_time}\n"
                    f"⏱ Davomiyligi: {total_duration} soat\n\n"
                    f"💼 Xizmatlar:\n{services_text}\n\n"
                    f"💰 Jami summa: {total_price:,} so'm"
                )
                await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message)

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Web app data error: {e}")
        await update.message.reply_text("❌ Bron qilishda xatolik yuz berdi.")

async def mijozlar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bugungi mijozlar ro'yxatini ko'rsatish (faqat admin uchun)"""
    user_id = str(update.effective_user.id)

    if ADMIN_CHAT_ID and user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Bu buyruq faqat admin uchun!")
        return

    db = SessionLocal()
    try:
        today = datetime.now().strftime("%Y-%m-%d")

        bookings = db.query(Booking).filter(
            Booking.booking_date == today,
            Booking.is_active == True
        ).order_by(Booking.booking_time).all()

        if not bookings:
            await update.message.reply_text(f"📅 {today}\n\nBugun hech qanday bron yo'q.")
            return

        message = f"📅 Bugungi mijozlar ({today})\n"
        message += f"Jami: {len(bookings)} ta bron\n\n"

        for idx, booking in enumerate(bookings, 1):
            services_text = ""
            if booking.services:
                services_list = [f"{s.service_name}" for s in booking.services]
                services_text = f"\n   Xizmatlar: {', '.join(services_list)}"

            message += (
                f"{idx}. 🆔 #{booking.id}\n"
                f"   👤 {booking.user_name}\n"
                f"   📱 {booking.user_phone}\n"
                f"   ⏰ {booking.booking_time}"
                f"{services_text}\n"
                f"   💰 {booking.total_price:,} so'm\n\n"
            )

        await update.message.reply_text(message)

    finally:
        db.close()


async def statistika(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Oylik statistikani ko'rsatish (faqat admin uchun)"""
    user_id = str(update.effective_user.id)

    if ADMIN_CHAT_ID and user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Bu buyruq faqat admin uchun!")
        return

    db = SessionLocal()
    try:
        # Bugun
        today = datetime.now().strftime("%Y-%m-%d")
        today_bookings = db.query(Booking).filter(
            Booking.booking_date == today,
            Booking.is_active == True
        ).count()

        today_revenue = db.query(func.sum(Booking.total_price)).filter(
            Booking.booking_date == today,
            Booking.is_active == True
        ).scalar() or 0

        # Bu hafta
        week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
        week_bookings = db.query(Booking).filter(
            Booking.booking_date >= week_start,
            Booking.is_active == True
        ).count()

        week_revenue = db.query(func.sum(Booking.total_price)).filter(
            Booking.booking_date >= week_start,
            Booking.is_active == True
        ).scalar() or 0

        # Bu oy
        month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        month_bookings = db.query(Booking).filter(
            Booking.booking_date >= month_start,
            Booking.is_active == True
        ).count()

        month_revenue = db.query(func.sum(Booking.total_price)).filter(
            Booking.booking_date >= month_start,
            Booking.is_active == True
        ).scalar() or 0

        # Jami
        total_bookings = db.query(Booking).filter(Booking.is_active == True).count()
        total_revenue = db.query(func.sum(Booking.total_price)).filter(
            Booking.is_active == True
        ).scalar() or 0

        message = (
            f"📊 STATISTIKA\n\n"
            f"📅 Bugun ({today}):\n"
            f"   Bronlar: {today_bookings} ta\n"
            f"   Daromad: {today_revenue:,} so'm\n\n"
            f"📅 Bu hafta:\n"
            f"   Bronlar: {week_bookings} ta\n"
            f"   Daromad: {week_revenue:,} so'm\n\n"
            f"📅 Bu oy:\n"
            f"   Bronlar: {month_bookings} ta\n"
            f"   Daromad: {month_revenue:,} so'm\n\n"
            f"📅 Jami:\n"
            f"   Bronlar: {total_bookings} ta\n"
            f"   Daromad: {total_revenue:,} so'm"
        )

        await update.message.reply_text(message)

    finally:
        db.close()


def main() -> None:
    create_tables()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("mijozlar", mijozlar))
    application.add_handler(CommandHandler("statistika", statistika))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.CONTACT, handle_message))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()