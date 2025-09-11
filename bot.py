import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from sqlalchemy.orm import sessionmaker
from database import engine, User, Booking, create_tables
import json

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
WEBAPP_URL = "https://mirzobek-kxaitov.github.io/botfront/"  # Bu URL frontendni deploy qilgandan keyin o'zgartiriladi

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
        
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            await update.message.reply_text("❌ Xatolik: Foydalanuvchi topilmadi.")
            return
        
        booking_date = data.get('date')
        booking_time = data.get('time')
        
        existing_booking = db.query(Booking).filter(
            Booking.booking_date == booking_date,
            Booking.booking_time == booking_time,
            Booking.is_active == True
        ).first()
        
        if existing_booking:
            await update.message.reply_text(
                f"❌ Kechirasiz, {booking_date} kuni soat {booking_time} allaqachon band!\n\n"
                "Boshqa vaqtni tanlang."
            )
        else:
            new_booking = Booking(
                user_telegram_id=user_id,
                user_name=user.name,
                user_phone=user.phone,
                booking_date=booking_date,
                booking_time=booking_time
            )
            db.add(new_booking)
            db.commit()
            
            await update.message.reply_text(
                f"✅ Bron muvaffaqiyatli qilindi!\n\n"
                f"📅 Sana: {booking_date}\n"
                f"⏰ Vaqt: {booking_time}\n\n"
                "Belgilangan vaqtda sartaroshxonaga tashrif buyuring."
            )
            
            if ADMIN_CHAT_ID:
                admin_message = (
                    f"🆕 Yangi bron!\n\n"
                    f"👤 Ism: {user.name}\n"
                    f"📱 Telefon: {user.phone}\n"
                    f"📅 Sana: {booking_date}\n"
                    f"⏰ Vaqt: {booking_time}"
                )
                await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message)
        
        db.close()
    
    except Exception as e:
        logger.error(f"Web app data error: {e}")
        await update.message.reply_text("❌ Bron qilishda xatolik yuz berdi.")

def main() -> None:
    create_tables()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.CONTACT, handle_message))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()