import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from database import engine, User, Booking, create_tables
from datetime import datetime, timedelta
from google_sheets import export_booking_to_sheets, export_all_bookings_to_sheets, get_sheets_url
import json

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
WEBAPP_URL = "https://mirzobek-kxaitov.github.io/botfront/"  # Bu URL frontendni deploy qilgandan keyin o'zgartiriladi

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "yo'q"
    logger.info(f"Start command from user: ID={user_id}, Username=@{username}")
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
            # Admin uchun maxsus tugmalar
            if user_id == ADMIN_CHAT_ID:
                keyboard = [
                    [KeyboardButton("📅 Bugungi Bronlar")],
                    [KeyboardButton("📋 Barcha Bronlar")],
                    [KeyboardButton("📊 Google Sheets")]
                ]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                
                await update.message.reply_text(
                    f"Admin paneli - Xush kelibsiz, {existing_user.name}! 👨‍💼\n\n"
                    "Quyidagi tugmalardan birini tanlang:",
                    reply_markup=reply_markup
                )
            else:
                # Oddiy foydalanuvchilar uchun
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
        
        # Admin tugmalarini handle qilish
        elif user_id == ADMIN_CHAT_ID:
            if text == "📅 Bugungi Bronlar":
                await bookings_today(update, context)
                return
            elif text == "📋 Barcha Bronlar":
                await all_bookings(update, context)
                return  
            elif text == "📊 Google Sheets":
                await sheets_url_command(update, context)
                return
    
    finally:
        db.close()


async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = None
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
        
        # Yangi bron yaratish (database-level constraint bilan himoyalangan)
        new_booking = Booking(
            user_telegram_id=user_id,
            user_name=user.name,
            user_phone=user.phone,
            booking_date=booking_date,
            booking_time=booking_time
        )
        
        try:
            db.add(new_booking)
            db.commit()
        except IntegrityError as e:
            # Database constraint violation - bu slot allaqachon band
            db.rollback()
            await update.message.reply_text(
                f"❌ Kechirasiz, {booking_date} kuni soat {booking_time} allaqachon band!\n\n"
                "Boshqa vaqtni tanlang."
            )
            logger.info(f"Conflict detected for {booking_date} {booking_time} by user {user_id}")
            return
        
        # Google Sheets'ga export qilish
        try:
            export_booking_to_sheets(new_booking)
            logger.info(f"Bron #{new_booking.id} Google Sheets'ga export qilindi")
        except Exception as e:
            logger.error(f"Google Sheets export xatoligi: {e}")
        
        # Admin'ga xabar yuborish
        if ADMIN_CHAT_ID:
            try:
                admin_message = (
                    f"🎉 **YANGI BRON QILINDI!**\n\n"
                    f"👤 **Mijoz:** {user.name}\n"
                    f"📱 **Telefon:** {user.phone}\n"
                    f"📅 **Sana:** {booking_date}\n"
                    f"⏰ **Vaqt:** {booking_time}\n"
                    f"🆔 **Bron ID:** #{new_booking.id}\n\n"
                    f"📊 Barcha bronlar: /all_bookings\n"
                    f"📋 Google Sheets: /sheets_url"
                )
                await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID, 
                    text=admin_message,
                    parse_mode='Markdown'
                )
                logger.info(f"Admin'ga yangi bron haqida xabar yuborildi: #{new_booking.id}")
            except Exception as e:
                logger.error(f"Admin'ga xabar yuborishda xatolik: {e}")
        
        # Foydalanuvchiga ham batafsil ma'lumot
        await update.message.reply_text(
            f"✅ **BRON MUVAFFAQIYATLI TASDIQLANDI!** 🎉\n\n"
            f"📋 **Bron ma'lumotlari:**\n"
            f"🆔 Bron raqami: #{new_booking.id}\n"
            f"📅 Sana: {booking_date}\n"
            f"⏰ Vaqt: {booking_time}\n"
            f"👤 Ism: {user.name}\n\n"
            f"📝 **Eslatma:**\n"
            f"• Belgilangan vaqtda sartaroshxonaga tashrif buyuring\n"
            f"• Telefon raqamingiz: {user.phone}\n"
            f"• Bron raqamini eslab qoling: #{new_booking.id}\n\n"
            f"❓ Savollar bo'lsa admin bilan bog'laning.",
            parse_mode='Markdown'
        )
    
    except Exception as e:
        logger.error(f"Web app data error: {e}")
        await update.message.reply_text("❌ Bron qilishda xatolik yuz berdi.")
    finally:
        if db:
            db.close()

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    
    # Faqat admin foydalana oladi
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Sizga bu komandani ishlatishga ruxsat yo'q.")
        return
    
    db = SessionLocal()
    try:
        # Bugungi va ertangi kunning bronlarini ko'rsatish
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        today_bookings = db.query(Booking).filter(
            Booking.booking_date == today.strftime('%Y-%m-%d'),
            Booking.is_active == True
        ).order_by(Booking.booking_time).all()
        
        tomorrow_bookings = db.query(Booking).filter(
            Booking.booking_date == tomorrow.strftime('%Y-%m-%d'),
            Booking.is_active == True
        ).order_by(Booking.booking_time).all()
        
        # Barcha aktiv bronlar soni
        total_bookings = db.query(Booking).filter(Booking.is_active == True).count()
        
        message = f"📊 **ADMIN PANEL**\n\n"
        message += f"📈 Jami aktiv bronlar: **{total_bookings}**\n\n"
        
        # Bugungi bronlar
        message += f"📅 **BUGUNGI BRONLAR** ({today.strftime('%d.%m.%Y')}):\n"
        if today_bookings:
            for booking in today_bookings:
                message += f"⏰ {booking.booking_time} - {booking.user_name} ({booking.user_phone})\n"
        else:
            message += "Bronlar yo'q\n"
        
        message += "\n"
        
        # Ertangi bronlar
        message += f"📅 **ERTANGI BRONLAR** ({tomorrow.strftime('%d.%m.%Y')}):\n"
        if tomorrow_bookings:
            for booking in tomorrow_bookings:
                message += f"⏰ {booking.booking_time} - {booking.user_name} ({booking.user_phone})\n"
        else:
            message += "Bronlar yo'q\n"
        
        message += f"\n📋 Batafsil ma'lumot uchun: /bookings_today, /bookings_tomorrow, /all_bookings"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    finally:
        db.close()

async def bookings_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Sizga bu komandani ishlatishga ruxsat yo'q.")
        return
    
    db = SessionLocal()
    try:
        today = datetime.now().date()
        bookings = db.query(Booking).filter(
            Booking.booking_date == today.strftime('%Y-%m-%d'),
            Booking.is_active == True
        ).order_by(Booking.booking_time).all()
        
        message = f"📅 **BUGUNGI BRONLAR** ({today.strftime('%d.%m.%Y')}):\n\n"
        
        if bookings:
            for i, booking in enumerate(bookings, 1):
                message += f"{i}. ⏰ **{booking.booking_time}**\n"
                message += f"   👤 {booking.user_name}\n"
                message += f"   📱 {booking.user_phone}\n"
                message += f"   🆔 ID: {booking.id}\n\n"
        else:
            message += "Bugun uchun bronlar yo'q 📭"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    finally:
        db.close()

async def bookings_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Sizga bu komandani ishlatishga ruxsat yo'q.")
        return
    
    db = SessionLocal()
    try:
        tomorrow = datetime.now().date() + timedelta(days=1)
        bookings = db.query(Booking).filter(
            Booking.booking_date == tomorrow.strftime('%Y-%m-%d'),
            Booking.is_active == True
        ).order_by(Booking.booking_time).all()
        
        message = f"📅 **ERTANGI BRONLAR** ({tomorrow.strftime('%d.%m.%Y')}):\n\n"
        
        if bookings:
            for i, booking in enumerate(bookings, 1):
                message += f"{i}. ⏰ **{booking.booking_time}**\n"
                message += f"   👤 {booking.user_name}\n"
                message += f"   📱 {booking.user_phone}\n"
                message += f"   🆔 ID: {booking.id}\n\n"
        else:
            message += "Ertaga uchun bronlar yo'q 📭"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    finally:
        db.close()

async def all_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Sizga bu komandani ishlatishga ruxsat yo'q.")
        return
    
    db = SessionLocal()
    try:
        # So'nggi 7 kunlik bronlar
        start_date = datetime.now().date() - timedelta(days=7)
        end_date = datetime.now().date() + timedelta(days=30)
        
        bookings = db.query(Booking).filter(
            Booking.booking_date >= start_date.strftime('%Y-%m-%d'),
            Booking.booking_date <= end_date.strftime('%Y-%m-%d'),
            Booking.is_active == True
        ).order_by(Booking.booking_date, Booking.booking_time).all()
        
        if not bookings:
            await update.message.reply_text("📭 Hozircha bronlar yo'q.")
            return
        
        # Sanalar bo'yicha guruhlash
        grouped_bookings = {}
        for booking in bookings:
            date = booking.booking_date
            if date not in grouped_bookings:
                grouped_bookings[date] = []
            grouped_bookings[date].append(booking)
        
        message = "📅 **BARCHA AKTIV BRONLAR**:\n\n"
        
        for date, date_bookings in grouped_bookings.items():
            try:
                formatted_date = datetime.strptime(date, '%Y-%m-%d').strftime('%d.%m.%Y')
            except:
                formatted_date = date
                
            message += f"📆 **{formatted_date}**:\n"
            for booking in date_bookings:
                message += f"  ⏰ {booking.booking_time} - {booking.user_name} ({booking.user_phone})\n"
            message += "\n"
        
        # Telegram message uzunligi chegarasi
        if len(message) > 4000:
            # Bo'lib yuborish
            chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
            for chunk in chunks:
                await update.message.reply_text(chunk, parse_mode='Markdown')
        else:
            await update.message.reply_text(message, parse_mode='Markdown')
        
    finally:
        db.close()

async def export_sheets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Barcha bronlarni Google Sheets'ga export qilish"""
    user_id = str(update.effective_user.id)
    
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Sizga bu komandani ishlatishga ruxsat yo'q.")
        return
    
    try:
        await update.message.reply_text("📊 Google Sheets'ga export qilinmoqda...")
        
        success = export_all_bookings_to_sheets()
        
        if success:
            sheets_url = get_sheets_url()
            message = "✅ Barcha bronlar Google Sheets'ga muvaffaqiyatli export qilindi!"
            
            if sheets_url:
                message += f"\n\n🔗 Google Sheets'ni ochish: {sheets_url}"
            
            await update.message.reply_text(message)
        else:
            await update.message.reply_text(
                "❌ Google Sheets'ga export qilishda xatolik yuz berdi.\n"
                "credentials.json fayli va GOOGLE_SHEET_ID sozlamalarini tekshiring."
            )
    
    except Exception as e:
        logger.error(f"Export sheets error: {e}")
        await update.message.reply_text("❌ Export qilishda xatolik yuz berdi.")

async def sheets_url_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Google Sheets linkini olish"""
    user_id = str(update.effective_user.id)
    
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Sizga bu komandani ishlatishga ruxsat yo'q.")
        return
    
    try:
        sheets_url = get_sheets_url()
        
        if sheets_url:
            await update.message.reply_text(
                f"🔗 **Google Sheets havolasi:**\n\n{sheets_url}\n\n"
                "Bu havola orqali barcha bronlarni ko'rishingiz mumkin.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ Google Sheets ulanmagan.\n"
                "credentials.json va GOOGLE_SHEET_ID sozlamalarini tekshiring."
            )
    
    except Exception as e:
        logger.error(f"Sheets URL error: {e}")
        await update.message.reply_text("❌ Google Sheets havolasini olishda xatolik.")

def main() -> None:
    create_tables()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("bookings_today", bookings_today))
    application.add_handler(CommandHandler("bookings_tomorrow", bookings_tomorrow))
    application.add_handler(CommandHandler("all_bookings", all_bookings))
    application.add_handler(CommandHandler("export_sheets", export_sheets))
    application.add_handler(CommandHandler("sheets_url", sheets_url_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.CONTACT, handle_message))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()