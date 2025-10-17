import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from datetime import datetime
from database import SessionLocal, Booking
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    def __init__(self):
        self.gc = None
        self.sheet = None
        self.setup_sheets()
    
    def setup_sheets(self):
        """Google Sheets API ni sozlash"""
        try:
            # Google Sheets API credential faylini tekshirish
            credentials_path = os.path.join(os.path.dirname(__file__), 'credentials.json')
            
            if not os.path.exists(credentials_path):
                logger.warning("Google Sheets credentials.json fayli topilmadi")
                return False
            
            # Google Sheets API ga ulanish
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
            self.gc = gspread.authorize(creds)
            
            # Sheet ID .env faylidan olish
            sheet_id = os.getenv('GOOGLE_SHEET_ID')
            if sheet_id:
                self.sheet = self.gc.open_by_key(sheet_id).sheet1
                logger.info("Google Sheets muvaffaqiyatli ulandi")
                return True
            else:
                logger.warning("GOOGLE_SHEET_ID .env faylida topilmadi")
                return False
                
        except Exception as e:
            logger.error(f"Google Sheets ulanishida xatolik: {e}")
            return False
    
    def create_headers_if_needed(self):
        """Agar jadval bo'sh bo'lsa, sarlavhalarni yaratish"""
        try:
            if not self.sheet:
                return False
                
            # Birinchi qatorni tekshirish
            first_row = self.sheet.row_values(1)
            
            if not first_row or len(first_row) == 0:
                # Sarlavhalarni qo'shish
                headers = [
                    'ID', 'Mijoz Ismi', 'Telefon', 'Sana', 'Vaqt', 
                    'Yaratilgan Vaqt', 'Status', 'Telegram ID'
                ]
                self.sheet.insert_row(headers, 1)
                logger.info("Google Sheets sarlavhalari yaratildi")
            
            return True
            
        except Exception as e:
            logger.error(f"Sarlavhalar yaratishda xatolik: {e}")
            return False
    
    def export_booking(self, booking):
        """Bitta bronni Google Sheets'ga export qilish"""
        try:
            if not self.sheet:
                return False
            
            self.create_headers_if_needed()
            
            # Bron ma'lumotlarini tayyorlash
            row_data = [
                booking.id,
                booking.user_name,
                booking.user_phone,
                booking.booking_date,
                booking.booking_time,
                booking.created_at.strftime('%Y-%m-%d %H:%M:%S') if booking.created_at else '',
                'Aktiv' if booking.is_active else 'Bekor qilingan',
                booking.user_telegram_id
            ]
            
            # Qatorni qo'shish
            self.sheet.append_row(row_data)
            logger.info(f"Bron #{booking.id} Google Sheets'ga export qilindi")
            return True
            
        except Exception as e:
            logger.error(f"Bronni export qilishda xatolik: {e}")
            return False
    
    def export_all_bookings(self):
        """Barcha bronlarni Google Sheets'ga export qilish"""
        try:
            if not self.sheet:
                return False
            
            db = SessionLocal()
            
            try:
                # Barcha bronlarni olish
                bookings = db.query(Booking).order_by(Booking.created_at.desc()).all()
                
                if not bookings:
                    logger.info("Export qilish uchun bronlar topilmadi")
                    return True
                
                # Jadvalni tozalash (sarlavhalardan boshqa)
                self.sheet.clear()
                self.create_headers_if_needed()
                
                # Barcha bronlarni qo'shish
                for booking in bookings:
                    row_data = [
                        booking.id,
                        booking.user_name,
                        booking.user_phone,
                        booking.booking_date,
                        booking.booking_time,
                        booking.created_at.strftime('%Y-%m-%d %H:%M:%S') if booking.created_at else '',
                        'Aktiv' if booking.is_active else 'Bekor qilingan',
                        booking.user_telegram_id
                    ]
                    self.sheet.append_row(row_data)
                
                logger.info(f"{len(bookings)} ta bron Google Sheets'ga export qilindi")
                return True
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Barcha bronlarni export qilishda xatolik: {e}")
            return False
    
    def get_sheet_url(self):
        """Google Sheets linkini olish"""
        try:
            if self.sheet:
                return f"https://docs.google.com/spreadsheets/d/{self.sheet.spreadsheet.id}"
            return None
        except:
            return None

# Global manager instance
sheets_manager = GoogleSheetsManager()

def export_booking_to_sheets(booking):
    """Bronni Google Sheets'ga export qilish (tashqi funksiya)"""
    return sheets_manager.export_booking(booking)

def export_all_bookings_to_sheets():
    """Barcha bronlarni export qilish (tashqi funksiya)"""
    return sheets_manager.export_all_bookings()

def get_sheets_url():
    """Google Sheets linkini olish (tashqi funksiya)"""
    return sheets_manager.get_sheet_url()