"""
Multi-Bot Manager
Har bir sartarosh uchun alohida Telegram bot ishga tushiradi.
"""

import os
import logging
import asyncio
import signal
from sqlalchemy.orm import sessionmaker
from database import engine, Barber, create_tables
from bot import create_bot_application

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Running bot applications
running_bots = {}


async def start_bot(barber_id, bot_token, barber_name):
    """Bitta botni ishga tushirish"""
    try:
        logger.info(f"🤖 [{barber_name}] Bot ishga tushmoqda... (ID: {barber_id})")

        application = create_bot_application(bot_token, barber_id)
        running_bots[barber_id] = application

        # Initialize and start
        await application.initialize()
        await application.start()
        await application.updater.start_polling(
            allowed_updates=["message", "callback_query"],
            timeout=30,
            poll_interval=1.0
        )

        logger.info(f"✅ [{barber_name}] Bot muvaffaqiyatli ishga tushdi!")
        return True

    except Exception as e:
        logger.error(f"❌ [{barber_name}] Bot ishga tushmadi: {e}")
        if barber_id in running_bots:
            del running_bots[barber_id]
        return False


async def stop_bot(barber_id, barber_name="Unknown"):
    """Bitta botni to'xtatish"""
    if barber_id in running_bots:
        try:
            application = running_bots[barber_id]
            await application.updater.stop()
            await application.stop()
            await application.shutdown()
            del running_bots[barber_id]
            logger.info(f"🛑 [{barber_name}] Bot to'xtatildi")
            return True
        except Exception as e:
            logger.error(f"❌ [{barber_name}] Bot to'xtatishda xatolik: {e}")
            if barber_id in running_bots:
                del running_bots[barber_id]
            return False
    return False


async def start_all_bots():
    """Barcha faol sartaroshlar uchun botlarni ishga tushirish"""
    create_tables()

    db = SessionLocal()
    try:
        barbers = db.query(Barber).filter(Barber.is_active == True).all()

        if not barbers:
            logger.warning("⚠️ Faol sartaroshlar topilmadi. Bot ishga tushmadi.")
            logger.info("Admin paneldan sartarosh qo'shing: /admin/")
            return

        logger.info(f"📋 {len(barbers)} ta faol sartarosh topildi")

        for barber in barbers:
            await start_bot(barber.id, barber.bot_token, barber.name)
            # Botlar orasida biroz kutish (conflict oldini olish)
            await asyncio.sleep(1)

        logger.info(f"✅ Jami {len(running_bots)} ta bot ishga tushdi")

    finally:
        db.close()


async def stop_all_bots():
    """Barcha botlarni to'xtatish"""
    logger.info("🛑 Barcha botlar to'xtatilmoqda...")
    barber_ids = list(running_bots.keys())
    for barber_id in barber_ids:
        await stop_bot(barber_id)
    logger.info("✅ Barcha botlar to'xtatildi")


async def main():
    """Asosiy funksiya"""
    # Register bot manager with FastAPI for dynamic bot control
    try:
        import main as main_module
        import sys
        current_module = sys.modules[__name__]
        main_module.set_bot_manager(current_module)
        logger.info("✅ Bot manager FastAPI ga ulandi")
    except Exception as e:
        logger.warning(f"⚠️ Bot manager FastAPI ga ulanmadi: {e}")

    await start_all_bots()

    if not running_bots:
        logger.info("Hech qanday bot ishga tushmadi. Kutish rejimida...")
        # Botlar yo'q bo'lsa ham manager ishlayveradi (API orqali qo'shish uchun)

    # Keep running until interrupted
    stop_event = asyncio.Event()

    def signal_handler():
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    logger.info("🟢 Bot manager ishlayapti. Ctrl+C bilan to'xtatish mumkin.")
    await stop_event.wait()

    # Cleanup
    await stop_all_bots()


if __name__ == "__main__":
    asyncio.run(main())
