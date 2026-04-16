import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from database import engine, User, Booking, BookingService, Barber, Service, create_tables
from datetime import datetime, timedelta
from google_sheets import export_booking_to_sheets, export_all_bookings_to_sheets, get_sheets_url
import json
from functools import wraps

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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

WEBAPP_URL = os.getenv("WEB_APP_URL", "https://barberlocal.uz")  # Frontend URL

# Admin decorator (Admin va Super Admin uchun)
def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if ALL_ADMIN_IDS and user_id in ALL_ADMIN_IDS:
            return await func(update, context, *args, **kwargs)
        else:
            await update.message.reply_text(
                "❌ Sizda admin huquqlari yo'q!\n"
                "Bu buyruq faqat adminlar uchun mo'ljallangan."
            )
    return wrapper

# Super Admin decorator (faqat Super Admin uchun)
def super_admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if SUPER_ADMIN_CHAT_IDS and user_id in SUPER_ADMIN_CHAT_IDS:
            return await func(update, context, *args, **kwargs)
        else:
            await update.message.reply_text(
                "❌ Sizda Super Admin huquqlari yo'q!\n"
                "Bu buyruq faqat Super Admin uchun mo'ljallangan."
            )
    return wrapper

def get_barber_id(context):
    """Bot data dan barber_id ni olish"""
    return context.bot_data.get('barber_id')


def get_barber_name(context):
    """Bot data dan barber nomini olish"""
    return context.bot_data.get('barber_name', 'Sartarosh')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "yo'q"
    barber_id = get_barber_id(context)
    barber_name = get_barber_name(context)
    logger.info(f"[{barber_name}] Start command from user: ID={user_id}, Username=@{username}")
    db = SessionLocal()

    try:
        # Bu sartaroshda ro'yxatdan o'tgan usermi?
        existing_user = db.query(User).filter(
            User.telegram_id == user_id,
            User.barber_id == barber_id
        ).first()

        if not existing_user:
            await update.message.reply_text(
                f"Salom! {barber_name} sartaroshxonasiga xush kelibsiz! 👋\n\n"
                "Bron qilish uchun iltimos ismingizni yuboring:"
            )
            context.user_data['registration_step'] = 'name'
        else:
            # Admin uchun maxsus tugmalar
            if ALL_ADMIN_IDS and int(user_id) in ALL_ADMIN_IDS:
                # Super Admin uchun qo'shimcha tugmalar
                if SUPER_ADMIN_CHAT_IDS and int(user_id) in SUPER_ADMIN_CHAT_IDS:
                    keyboard = [
                        [KeyboardButton("📅 Bugungi Bronlar")],
                        [KeyboardButton("📋 Barcha Bronlar")],
                        [KeyboardButton("📊 Google Sheets")],
                        [KeyboardButton("👑 Super Admin Panel")]
                    ]
                    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

                    await update.message.reply_text(
                        f"👑 Super Admin paneli - Xush kelibsiz, {existing_user.name}! \n\n"
                        "Quyidagi tugmalardan birini tanlang:\n\n"
                        "🔹 /mijozlar - Bugungi mijozlar\n"
                        "🔹 /mijozlar_sana - Belgilangan sanadagi mijozlar\n"
                        "🔹 /statistika - Umumiy statistika\n"
                        "🔹 /help - Barcha buyruqlar",
                        reply_markup=reply_markup
                    )
                else:
                    # Oddiy Admin
                    keyboard = [
                        [KeyboardButton("📅 Bugungi Bronlar")],
                        [KeyboardButton("📋 Barcha Bronlar")],
                        [KeyboardButton("📊 Google Sheets")]
                    ]
                    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

                    await update.message.reply_text(
                        f"Admin paneli - Xush kelibsiz, {existing_user.name}! 👨‍💼\n\n"
                        "Quyidagi tugmalardan birini tanlang:\n\n"
                        "🔹 /mijozlar - Bugungi mijozlar\n"
                        "🔹 /mijozlar_sana - Belgilangan sanadagi mijozlar\n"
                        "🔹 /statistika - Umumiy statistika\n"
                        "🔹 /help - Barcha buyruqlar",
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
                    f"{barber_name} sartaroshxonasiga bron qilish uchun quyidagi tugmani bosing:",
                    reply_markup=reply_markup
                )
    finally:
        db.close()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    is_admin = ALL_ADMIN_IDS and user_id in ALL_ADMIN_IDS
    is_super_admin = SUPER_ADMIN_CHAT_IDS and user_id in SUPER_ADMIN_CHAT_IDS

    help_text = """
🔹 *Bot buyruqlari:*

/start - Botni boshlash va ro'yxatdan o'tish
/help - Yordam va buyruqlar ro'yxati

📝 *Bron qilish jarayoni:*
1. "BRON QILISH" tugmasini bosing
2. Web App ochiladi
3. Sana va vaqtni tanlang
4. Bron qilishni tasdiqlang

⏰ *Ish vaqti:* 09:00 dan 22:00 gacha
    """

    if is_admin:
        help_text += """

👑 *Admin buyruqlari:*
/mijozlar - Bugungi mijozlar ro'yxati
/mijozlar_sana - Belgilangan sanadagi mijozlar
/statistika - Umumiy statistika

📊 *Admin paneli uchun maxsus buyruqlar.*
        """

    if is_super_admin:
        help_text += """

🌟 *Super Admin buyruqlari:*
Barcha admin buyruqlari + qo'shimcha huquqlar
        """

    help_text += "\n\n❓ Savollaringiz bo'lsa, admin bilan bog'laning."

    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    text = update.message.text
    barber_id = get_barber_id(context)
    barber_name = get_barber_name(context)
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

            logger.info(f"[{barber_name}] Processing phone registration: name={name}, phone={phone}, user_id={user_id}")

            try:
                # Check if user already exists for this barber
                existing_user = db.query(User).filter(
                    User.telegram_id == user_id,
                    User.barber_id == barber_id
                ).first()
                if not existing_user:
                    new_user = User(telegram_id=user_id, name=name, phone=phone, barber_id=barber_id)
                    db.add(new_user)
                    db.commit()
                    logger.info(f"[{barber_name}] New user created: {user_id}")
                else:
                    # Update existing user
                    existing_user.name = name
                    existing_user.phone = phone
                    db.commit()
                    logger.info(f"[{barber_name}] User updated: {user_id}")

                logger.info(f"WEB_APP_URL: {WEBAPP_URL}")

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

                logger.info(f"Registration complete message sent to {user_id}")
                context.user_data.clear()

            except Exception as e:
                logger.error(f"Error during registration: {e}", exc_info=True)
                await update.message.reply_text("Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.")

        # Admin tugmalarini handle qilish
        elif ALL_ADMIN_IDS and int(user_id) in ALL_ADMIN_IDS:
            if text == "📅 Bugungi Bronlar":
                await mijozlar_command(update, context)
                return
            elif text == "📋 Barcha Bronlar":
                await all_bookings(update, context)
                return
            elif text == "📊 Google Sheets":
                await sheets_url_command(update, context)
                return
            elif text == "👑 Super Admin Panel" and SUPER_ADMIN_CHAT_IDS and int(user_id) in SUPER_ADMIN_CHAT_IDS:
                await super_admin_panel(update, context)
                return

    finally:
        db.close()


async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = None
    barber_id = get_barber_id(context)
    barber_name = get_barber_name(context)
    try:
        data = json.loads(update.effective_message.web_app_data.data)
        user_id = str(update.effective_user.id)
        db = SessionLocal()

        user = db.query(User).filter(
            User.telegram_id == user_id,
            User.barber_id == barber_id
        ).first()
        if not user:
            await update.message.reply_text("❌ Xatolik: Foydalanuvchi topilmadi.")
            return

        booking_date = data.get('date')
        booking_time = data.get('time')
        services = data.get('services', [])
        total_price = data.get('total_price', 0)
        total_duration = data.get('total_duration', 1)

        # Yangi bron yaratish (database-level constraint bilan himoyalangan)
        new_booking = Booking(
            barber_id=barber_id,
            user_telegram_id=user_id,
            user_name=user.name,
            user_phone=user.phone,
            booking_date=booking_date,
            booking_time=booking_time,
            total_duration=total_duration,
            total_price=total_price
        )

        try:
            db.add(new_booking)
            db.commit()
            db.refresh(new_booking)

            # Xizmatlarni qo'shish
            if services:
                for service in services:
                    booking_service = BookingService(
                        booking_id=new_booking.id,
                        service_name=service.get('name'),
                        service_code=service.get('service'),
                        price=service.get('price'),
                        duration=service.get('duration')
                    )
                    db.add(booking_service)
                db.commit()
                db.refresh(new_booking)

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

        # Sartaroshga xabar yuborish (barber'ning o'z admin_telegram_id'siga)
        barber_admin_id = None
        db_session = SessionLocal()
        try:
            barber_obj = db_session.query(Barber).filter(Barber.id == barber_id).first()
            if barber_obj and barber_obj.admin_telegram_id:
                barber_admin_id = barber_obj.admin_telegram_id.strip()
        finally:
            db_session.close()

        if barber_admin_id:
            try:
                # Xizmatlar ro'yxatini yaratish
                services_text = ""
                if new_booking.services:
                    services_text = "\n\n💼 **Xizmatlar:**\n"
                    for service in new_booking.services:
                        services_text += f"   • {service.service_name} - {service.price:,.0f} so'm ({service.duration} soat)\n"

                admin_message = (
                    f"🎉 **YANGI BRON!**\n\n"
                    f"👤 **Mijoz:** {user.name}\n"
                    f"📱 **Telefon:** {user.phone}\n"
                    f"📅 **Sana:** {booking_date}\n"
                    f"⏰ **Vaqt:** {booking_time}\n"
                    f"⏱ **Davomiyligi:** {total_duration} soat"
                    f"{services_text}\n"
                    f"💰 **Jami summa:** {total_price:,.0f} so'm\n"
                    f"🆔 **Bron ID:** #{new_booking.id}"
                )

                await context.bot.send_message(
                    chat_id=int(barber_admin_id),
                    text=admin_message,
                    parse_mode='Markdown'
                )
                logger.info(f"[{barber_name}] Yangi bron haqida sartaroshga xabar yuborildi: #{new_booking.id}")
            except Exception as e:
                logger.error(f"[{barber_name}] Sartaroshga xabar yuborishda xatolik: {e}")

        # Foydalanuvchiga ham batafsil ma'lumot
        # Xizmatlar ro'yxatini yaratish (foydalanuvchi uchun)
        user_services_text = ""
        if new_booking.services:
            user_services_text = "\n💼 **Xizmatlar:**\n"
            for service in new_booking.services:
                user_services_text += f"   • {service.service_name} - {service.price:,.0f} so'm\n"

        await update.message.reply_text(
            f"✅ **BRON MUVAFFAQIYATLI TASDIQLANDI!** 🎉\n\n"
            f"📋 **Bron ma'lumotlari:**\n"
            f"🆔 Bron raqami: #{new_booking.id}\n"
            f"📅 Sana: {booking_date}\n"
            f"⏰ Vaqt: {booking_time}\n"
            f"⏱ Davomiyligi: {total_duration} soat\n"
            f"👤 Ism: {user.name}"
            f"{user_services_text}\n"
            f"💰 **Jami summa:** {total_price:,.0f} so'm\n\n"
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

@admin_only
async def mijozlar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bugungi mijozlar ro'yxatini ko'rsatish"""
    today = datetime.now().date()
    barber_id = get_barber_id(context)

    db = SessionLocal()
    try:
        # Bugungi bronlarni olish (shu sartarosh uchun)
        bookings = db.query(Booking).filter(
            Booking.barber_id == barber_id,
            Booking.booking_date == today.strftime('%Y-%m-%d'),
            Booking.is_active == True
        ).order_by(Booking.booking_time).all()

        if not bookings:
            await update.message.reply_text(
                f"📅 *{today.strftime('%d.%m.%Y')} - Bugun*\n\n"
                "📝 Hech qanday bron yo'q",
                parse_mode='Markdown'
            )
            return

        message = f"📅 *{today.strftime('%d.%m.%Y')} - Bugun*\n"
        message += f"👥 *Jami: {len(bookings)} ta bron*\n\n"

        for i, booking in enumerate(bookings, 1):
            message += f"*{i}.* 🕐 *{booking.booking_time}* ({booking.total_duration}h)\n"
            message += f"👤 {booking.user_name}\n"
            message += f"📞 {booking.user_phone}\n"
            if booking.services:
                message += f"💼 Xizmatlar: "
                services_names = [s.service_name for s in booking.services]
                message += ", ".join(services_names) + "\n"
            message += f"💰 {booking.total_price:,.0f} so'm\n"
            message += f"🆔 ID: `{booking.id}`\n\n"

        await update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {str(e)}")
    finally:
        db.close()

@admin_only
async def mijozlar_sana_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Belgilangan sanadagi mijozlar ro'yxatini ko'rsatish"""

    if not context.args:
        await update.message.reply_text(
            "📅 *Sanani kiriting:*\n"
            "Masalan: `/mijozlar_sana 2024-01-15`\n"
            "yoki: `/mijozlar_sana 15.01.2024`",
            parse_mode='Markdown'
        )
        return

    date_str = context.args[0]

    try:
        # Turli formatlarni qabul qilish
        if '.' in date_str:
            date_obj = datetime.strptime(date_str, '%d.%m.%Y').date()
        elif '-' in date_str:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            raise ValueError("Noto'g'ri format")

    except ValueError:
        await update.message.reply_text(
            "❌ *Noto'g'ri sana format!*\n"
            "To'g'ri formatlar:\n"
            "• `2024-01-15` (YYYY-MM-DD)\n"
            "• `15.01.2024` (DD.MM.YYYY)",
            parse_mode='Markdown'
        )
        return

    barber_id = get_barber_id(context)
    db = SessionLocal()
    try:
        # Belgilangan sanadagi bronlarni olish (shu sartarosh uchun)
        bookings = db.query(Booking).filter(
            Booking.barber_id == barber_id,
            Booking.booking_date == date_obj.strftime('%Y-%m-%d'),
            Booking.is_active == True
        ).order_by(Booking.booking_time).all()

        if not bookings:
            await update.message.reply_text(
                f"📅 *{date_obj.strftime('%d.%m.%Y')}*\n\n"
                "📝 Bu sanada hech qanday bron yo'q",
                parse_mode='Markdown'
            )
            return

        message = f"📅 *{date_obj.strftime('%d.%m.%Y')}*\n"
        message += f"👥 *Jami: {len(bookings)} ta bron*\n\n"

        for i, booking in enumerate(bookings, 1):
            message += f"*{i}.* 🕐 *{booking.booking_time}*\n"
            message += f"👤 {booking.user_name}\n"
            message += f"📞 {booking.user_phone}\n"
            message += f"🆔 ID: `{booking.id}`\n\n"

        await update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {str(e)}")
    finally:
        db.close()

@admin_only
async def statistika_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Umumiy statistikani ko'rsatish"""
    barber_id = get_barber_id(context)

    db = SessionLocal()
    try:
        # Umumiy statistika (shu sartarosh uchun)
        total_users = db.query(User).filter(User.barber_id == barber_id).count()
        total_bookings = db.query(Booking).filter(Booking.barber_id == barber_id, Booking.is_active == True).count()

        # Bugungi statistika
        today = datetime.now().date()
        today_bookings = db.query(Booking).filter(
            Booking.barber_id == barber_id,
            Booking.booking_date == today.strftime('%Y-%m-%d'),
            Booking.is_active == True
        ).count()

        # Haftalik statistika
        week_ago = today - timedelta(days=7)
        week_bookings = db.query(Booking).filter(
            Booking.barber_id == barber_id,
            Booking.booking_date >= week_ago.strftime('%Y-%m-%d'),
            Booking.is_active == True
        ).count()

        # Oylik statistika
        month_ago = today - timedelta(days=30)
        month_bookings = db.query(Booking).filter(
            Booking.barber_id == barber_id,
            Booking.booking_date >= month_ago.strftime('%Y-%m-%d'),
            Booking.is_active == True
        ).count()

        message = "📊 *STATISTIKA*\n\n"
        message += f"👥 *Jami foydalanuvchilar:* {total_users}\n"
        message += f"📝 *Jami aktiv bronlar:* {total_bookings}\n\n"
        message += f"📅 *Bugun:* {today_bookings} ta bron\n"
        message += f"📅 *So'nggi 7 kun:* {week_bookings} ta bron\n"
        message += f"📅 *So'nggi 30 kun:* {month_bookings} ta bron\n\n"
        if month_bookings > 0:
            message += f"📈 *Kunlik o'rtacha:* {month_bookings/30:.1f} ta bron"

        await update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {str(e)}")
    finally:
        db.close()

@admin_only
async def all_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    barber_id = get_barber_id(context)

    db = SessionLocal()
    try:
        # So'nggi 7 kunlik bronlar (shu sartarosh uchun)
        start_date = datetime.now().date() - timedelta(days=7)
        end_date = datetime.now().date() + timedelta(days=30)

        bookings = db.query(Booking).filter(
            Booking.barber_id == barber_id,
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

@admin_only
async def sheets_url_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Google Sheets linkini olish"""
    user_id = str(update.effective_user.id)

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

@super_admin_only
async def super_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Super Admin paneli"""
    barber_id = get_barber_id(context)
    db = SessionLocal()
    try:
        # Umumiy ma'lumotlar (shu sartarosh uchun)
        total_users = db.query(User).filter(User.barber_id == barber_id).count()
        total_bookings = db.query(Booking).filter(Booking.barber_id == barber_id, Booking.is_active == True).count()

        # Oxirgi 10 ta bron
        recent_bookings = db.query(Booking).filter(Booking.barber_id == barber_id).order_by(Booking.created_at.desc()).limit(10).all()

        message = "👑 **SUPER ADMIN PANEL**\n\n"
        message += f"📊 **Umumiy statistika:**\n"
        message += f"👥 Jami foydalanuvchilar: {total_users}\n"
        message += f"📝 Jami aktiv bronlar: {total_bookings}\n\n"

        if recent_bookings:
            message += "🕐 **So'nggi 10 ta bron:**\n\n"
            for i, booking in enumerate(recent_bookings, 1):
                status = "✅" if booking.is_active else "❌"
                message += f"{i}. {status} {booking.user_name} - {booking.booking_date} {booking.booking_time}\n"
                message += f"   ID: `{booking.id}` | Telegram: `{booking.user_telegram_id}`\n\n"

        message += "\n💡 **Super Admin buyruqlari:**\n"
        message += "/mijozlar - Bugungi mijozlar\n"
        message += "/statistika - To'liq statistika\n"

        await update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Super Admin panel xatoligi: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi.")
    finally:
        db.close()

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and handle conflicts"""
    logger.error("Exception while handling an update:", exc_info=context.error)

    if "Conflict" in str(context.error):
        logger.error("🚨 CONFLICT DETECTED: Another bot instance is running!")
        logger.error("Please stop all other bot instances and try again.")

def create_bot_application(bot_token, barber_id):
    """
    Bot application yaratish (bot_manager.py dan chaqiriladi).
    Har bir sartarosh uchun alohida bot instance yaratadi.
    """
    # Barber ma'lumotlarini olish
    db = SessionLocal()
    try:
        barber = db.query(Barber).filter(Barber.id == barber_id).first()
        barber_name = barber.name if barber else f"Barber-{barber_id}"
    finally:
        db.close()

    application = Application.builder().token(bot_token).build()

    # Bot data ga barber_id va barber_name saqlash
    application.bot_data['barber_id'] = barber_id
    application.bot_data['barber_name'] = barber_name

    # Add error handler
    application.add_error_handler(error_handler)

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("mijozlar", mijozlar_command))
    application.add_handler(CommandHandler("mijozlar_sana", mijozlar_sana_command))
    application.add_handler(CommandHandler("statistika", statistika_command))
    application.add_handler(CommandHandler("super_admin", super_admin_panel))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.CONTACT, handle_message))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))

    logger.info(f"✅ [{barber_name}] Bot application yaratildi (barber_id={barber_id})")
    return application


def main() -> None:
    """Yagona bot ishga tushirish (eski usul, backward compatible)"""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN topilmadi! .env faylini tekshiring.")
        return

    logger.info("🤖 Bot ishga tushmoqda (single mode)...")
    create_tables()

    application = Application.builder().token(BOT_TOKEN).build()

    # Default barber_id = None (eski rejimda)
    application.bot_data['barber_id'] = None
    application.bot_data['barber_name'] = 'Default'

    # Add error handler
    application.add_error_handler(error_handler)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("mijozlar", mijozlar_command))
    application.add_handler(CommandHandler("mijozlar_sana", mijozlar_sana_command))
    application.add_handler(CommandHandler("statistika", statistika_command))
    application.add_handler(CommandHandler("super_admin", super_admin_panel))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.CONTACT, handle_message))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))

    try:
        logger.info("✅ Bot muvaffaqiyatli ishga tushdi!")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            timeout=30,
            poll_interval=1.0
        )
    except Exception as e:
        logger.error(f"❌ Bot ishga tushmadi: {e}")
        if "Conflict" in str(e):
            logger.error("🔄 10 soniyadan keyin qayta urinib ko'ring...")

if __name__ == '__main__':
    main()