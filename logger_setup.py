import logging
from logging.handlers import RotatingFileHandler
import sys
import os
import re

class SensitiveInfoFilter(logging.Filter):
    def __init__(self):
        super().__init__()

    def filter(self, record):
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = re.sub(r'Output/[^/]+/', '', record.msg)
            record.msg = re.sub(r'sessionid giống mặc định|số lượng mục: \d+', '', record.msg)
            record.msg = re.sub(r'\(PID: \d+\)', '', record.msg)
            record.msg = re.sub(r'mã trạng thái: \d+', '', record.msg)
            record.msg = re.sub(r'Khởi tạo [^\s]+|Đã đọc file [^\s]+|API TikTok|Cấu trúc API|icon\.ico|biểu tượng', '', record.msg)
        return True

class MaxLevelFilter(logging.Filter):
    def __init__(self, max_level):
        super().__init__()
        self.max_level = max_level
    def filter(self, record):
        return record.levelno <= self.max_level

class PathShortenerFilter(logging.Filter):
    def __init__(self, base_path):
        super().__init__()
        self.base_path = os.path.normpath(base_path)

    def filter(self, record):
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            normalized_msg = os.path.normpath(record.msg)
            if self.base_path in normalized_msg:
                record.msg = normalized_msg.replace(self.base_path, '').lstrip(os.sep).lstrip('/').replace('\\', '/')
            else:
                record.msg = normalized_msg.lstrip('/').lstrip(os.sep).replace('\\', '/')
        return True

class ProductionFilter(logging.Filter):
    def __init__(self, logged_messages):
        super().__init__()
        self.logged_messages = logged_messages
        self.allowed_keywords = [
            'FFmpeg', 'ghi hình', 'dừng', 'Hoàn tất', 'chuyển đổi', 'thành công',
            'Lỗi', 'lỗi', 'thất bại', 'Không thể', 'không tìm thấy', 'Cảnh báo',
            'bị chặn', 'hết thời gian', 'quá tải', 'rỗng', 'xóa', 'đóng'
        ]

    def filter(self, record):
        if record.levelno < logging.INFO:
            return False
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            if not any(keyword in record.msg for keyword in self.allowed_keywords):
                return False
            message_key = (record.msg, record.levelno)
            if message_key in self.logged_messages:
                return False
            self.logged_messages.add(message_key)
        return True

class LoggerManager:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
            cls._instance.logger = None
            cls._instance.is_production = hasattr(sys, '_MEIPASS')
            cls._instance.logged_messages = set()
            cls._instance.setup_logger()
        return cls._instance

    def setup_logger(self):
        if self.logger is None:
            self.logger = logging.getLogger('TikTokRecorder')
            self.logger.setLevel(logging.DEBUG)

            if self.is_production:
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            self.base_path = base_path
            log_path = os.path.normpath(os.path.join(base_path, 'recording.txt'))

            if os.path.exists(log_path):
                try:
                    os.remove(log_path)
                except Exception as e:
                    if not self.is_production:
                        print(f"[ERROR] Không thể xóa file log cũ: {e}")

            try:
                file_handler = RotatingFileHandler(
                    log_path, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
                )
                if self.is_production:
                    file_handler.setLevel(logging.INFO)
                    file_handler.addFilter(ProductionFilter(self.logged_messages))
                else:
                    file_handler.setLevel(logging.DEBUG)
                file_format = '%(asctime)s [%(levelname)s] %(message)s'
                file_datefmt = '%H:%M:%S'
                file_formatter = logging.Formatter(file_format, file_datefmt)
                file_handler.setFormatter(file_formatter)
                file_handler.addFilter(PathShortenerFilter(self.base_path))
                file_handler.addFilter(SensitiveInfoFilter())
                self.logger.addHandler(file_handler)
            except Exception as e:
                if not self.is_production:
                    print(f"[ERROR] Không thể tạo file log: {str(e)}")

            if not self.is_production:
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.DEBUG)
                console_format = '\033[1;34m%(asctime)s \033[1;32m[%(levelname)s]\033[0m [%(funcName)s] %(message)s'
                console_datefmt = '%H:%M:%S'
                console_formatter = logging.Formatter(console_format, console_datefmt)
                console_handler.setFormatter(console_formatter)
                self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger

logger = LoggerManager().get_logger()