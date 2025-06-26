import os
import sys
import time
import json
import re
import logging
import subprocess
import psutil
import threading
from enum import Enum, IntEnum
from contextlib import contextmanager, nullcontext, suppress
from requests import RequestException, Session
from tenacity import retry, stop_after_attempt, wait_exponential

from logger_setup import logger
from config import TIKTOK_CONFIG

def setup_ffmpeg():
    """Thiết lập FFmpeg và trả về đường dẫn tới ffmpeg.exe."""
    import shutil

    ffmpeg_path = None
    base_path = None

    if not hasattr(sys, '_MEIPASS'):
        base_path = os.path.dirname(os.path.abspath(__file__))
        ffmpeg_dir = os.path.join(base_path, 'ffmpeg')
        ffmpeg_path = os.path.join(ffmpeg_dir, 'ffmpeg.exe')
        if os.path.exists(ffmpeg_path):
            logger.info(f"Đã tìm thấy FFmpeg trong thư mục ffmpeg")
        else:
            logger.warning(f"Không tìm thấy ffmpeg.exe trong {ffmpeg_dir}, thử tìm trong PATH")
            ffmpeg_path = shutil.which("ffmpeg")
            if ffmpeg_path:
                logger.info(f"Đã tìm thấy FFmpeg trong PATH")
            else:
                logger.warning("Không tìm thấy FFmpeg trong PATH")
    else:
        base_path = sys._MEIPASS
        ffmpeg_dir = os.path.join(base_path, 'ffmpeg')
        ffmpeg_path = os.path.join(ffmpeg_dir, 'ffmpeg.exe')
        if os.path.exists(ffmpeg_path):
            logger.info(f"Đã tìm thấy FFmpeg trong thư mục chương trình")
        else:
            logger.warning(f"Không tìm thấy ffmpeg.exe, thử tìm trong PATH")
            ffmpeg_path = shutil.which("ffmpeg")
            if ffmpeg_path:
                logger.info(f"Đã tìm thấy FFmpeg trong PATH")
            else:
                logger.warning("Không tìm thấy FFmpeg trong PATH")

    if not ffmpeg_path:
        error_msg = (
            "Không tìm thấy FFmpeg. Vui lòng tải và đặt 'ffmpeg.exe' vào thư mục 'ffmpeg' "
            "cùng cấp với chương trình, hoặc thêm vào biến môi trường PATH."
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    ffmpeg_path = os.path.normpath(ffmpeg_path)

    if not os.access(ffmpeg_path, os.X_OK):
        error_msg = f"Không có quyền thực thi FFmpeg tại {ffmpeg_path}."
        logger.error(error_msg)
        raise PermissionError(error_msg)

    os.environ["FFMPEG_PATH"] = ffmpeg_path
    return ffmpeg_path

def run_ffmpeg(input_file, output_file, args, recording_id='N/A'):
    ffmpeg_path = os.environ.get("FFMPEG_PATH")
    if not ffmpeg_path:
        raise FileNotFoundError("Đường dẫn FFmpeg chưa được thiết lập.")
        
    cmd = [ffmpeg_path, "-i", input_file] + args + ["-y", output_file]
    
    try:
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW, text=True, encoding='utf-8', errors='ignore'
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            error_msg = stderr if stderr else "Lỗi không xác định"
            logger.error(f"Lỗi FFmpeg: {error_msg.strip()}", extra={'recording_id': recording_id})
            raise Exception(f"Lỗi FFmpeg: {error_msg.strip()}")
        logger.info(f"Chuyển đổi file {os.path.basename(output_file)} thành công", extra={'recording_id': recording_id})
        return process.pid
    except Exception as e:
        logger.error(f"Lỗi chạy FFmpeg: {e}", extra={'recording_id': recording_id})
        raise

def check_audio_stream(file):
    ffmpeg_path = os.environ.get("FFMPEG_PATH")
    try:
        cmd = [ffmpeg_path, "-i", file, "-hide_banner", "-v", "quiet", "-f", "null", "-"]
        process = subprocess.run(cmd, capture_output=True, timeout=10)
        return "Audio:" in process.stderr.decode('utf-8', errors='ignore')
    except Exception:
        return False

def check_video_stream(file):
    ffmpeg_path = os.environ.get("FFMPEG_PATH")
    try:
        cmd = [ffmpeg_path, "-i", file, "-hide_banner", "-v", "quiet", "-f", "null", "-"]
        process = subprocess.run(cmd, capture_output=True, timeout=10)
        return "Video:" in process.stderr.decode('utf-8', errors='ignore')
    except Exception:
        return False

def stop_ffmpeg_processes(pid_list):
    for pid in pid_list[:]:
        try:
            if psutil.pid_exists(pid):
                proc = psutil.Process(pid)
                if 'ffmpeg' in proc.name().lower():
                    proc.kill()
                    logger.info(f"Đã dừng tiến trình FFmpeg (PID: {pid})")
                pid_list.remove(pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            if pid in pid_list:
                pid_list.remove(pid)
        except Exception as e:
            logger.error(f"Lỗi khi dừng FFmpeg (PID: {pid}): {e}")

setup_ffmpeg()


class TimeOut(IntEnum):
    ONE_MINUTE = 60
    AUTOMATIC_MODE = 5
    CONNECTION_CLOSED = 2

class StatusCode(IntEnum):
    OK = 200
    REDIRECT = 302
    MOVED = 301

class Mode(IntEnum):
    MANUAL = 0
    AUTOMATIC = 1

class TikTokError(Enum):
    def __str__(self):
        return str(self.value)
    COUNTRY_BLACKLISTED = "Quốc gia bị chặn, vui lòng dùng VPN hoặc cookies."
    ACCOUNT_PRIVATE = "Tài khoản riêng tư, cần đăng nhập."
    LIVE_RESTRICTION = "Livestream bị giới hạn, cần đăng nhập."
    ROOM_ID_ERROR = "Không lấy được RoomID từ API."
    USER_NOT_CURRENTLY_LIVE = "Người dùng hiện không livestream."
    RETRIEVE_LIVE_URL = "Không lấy được URL livestream."
    API_CHANGED = "Cấu trúc API TikTok đã thay đổi, vui lòng cập nhật ứng dụng."
    USERNAME_NOT_FOUND = "Không tìm thấy người dùng."


class TikTokException(Exception): pass
class UserLiveException(Exception): pass
class LiveNotFound(Exception): pass
class RecordingException(Exception): pass


class VideoManagement:
    @staticmethod
    def convert_flv_to_mp4(file, ffmpeg_lock=None, ffmpeg_pids=None, recording_id='N/A'):
        file = os.path.normpath(file)
        logger.info(f"Bắt đầu chuyển đổi FLV sang MP4: {os.path.basename(file)}", extra={'recording_id': recording_id})
        try:
            output_file = os.path.normpath(file.replace('_flv.mp4', '.mp4'))
            with ffmpeg_lock if ffmpeg_lock else nullcontext():
                pid = run_ffmpeg(file, output_file, ["-c", "copy"], recording_id=recording_id)
                if ffmpeg_pids is not None:
                    with threading.Lock():
                        ffmpeg_pids.append(pid)
            os.remove(file)
        except Exception as e:
            logger.error(f"Lỗi chuyển đổi MP4: {e}", extra={'recording_id': recording_id})
        finally:
            if ffmpeg_pids:
                stop_ffmpeg_processes(ffmpeg_pids)

    @staticmethod
    def convert_mp4_to_mp3(file, output_file=None, ffmpeg_lock=None, ffmpeg_pids=None, recording_id='N/A'):
        file = os.path.normpath(file)
        logger.info(f"Bắt đầu chuyển đổi MP4 sang MP3: {os.path.basename(file)}")
        try:
            if output_file is None:
                output_file = os.path.normpath(file.replace('.mp4', '.mp3'))

            with ffmpeg_lock if ffmpeg_lock else nullcontext():
                pid = run_ffmpeg(file, output_file, ["-vn", "-acodec", "mp3", "-ab", "128k"], recording_id=recording_id)
                if ffmpeg_pids is not None:
                    with threading.Lock():
                        ffmpeg_pids.append(pid)
        except Exception as e:
            logger.error(f"Lỗi chuyển đổi MP3: {e}")
        finally:
            if ffmpeg_pids:
                stop_ffmpeg_processes(ffmpeg_pids)

class HttpClient:
    def __init__(self, cookies=None):
        self.session = Session()
        self.session.trust_env = False
        self.session.verify = True
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
            "Referer": "https://www.tiktok.com/",
        })
        if cookies:
            self.session.cookies.update(cookies)

    def close_session(self):
        if self.session:
            self.session.close()

class TikTokAPI:
    def __init__(self, cookies):
        self.config = TIKTOK_CONFIG
        self.http_client = HttpClient(cookies)

    def get_room_id_from_user(self, user: str) -> str:
        try:
            url = f"{self.config['api_endpoints']['base_url']}/@{user}/live"
            response = self.http_client.session.get(url, timeout=10)
            response.raise_for_status()

            content = response.text
            match = re.search(r'<script id="SIGI_STATE" type="application/json">(.*?)</script>', content)
            if not match:
                raise UserLiveException(TikTokError.API_CHANGED)

            data = json.loads(match.group(1))
            
            room_id = None
            if 'LiveRoom' in data and 'liveRoomUserInfo' in data['LiveRoom']:
                room_id = data['LiveRoom']['liveRoomUserInfo'].get('user', {}).get('roomId')
            
            if not room_id and 'RoomFeed' in data and 'liveRoom' in data['RoomFeed']['detail']:
                 room_id = data['RoomFeed']['detail']['liveRoom'].get('roomId')
            
            if not room_id:
                 logger.warning(f"Không tìm thấy RoomID cho {user} trong SIGI_STATE.")
                 raise UserLiveException(TikTokError.ROOM_ID_ERROR)
            
            return str(room_id)
        
        except RequestException as e:
            if e.response and e.response.status_code == 404:
                raise UserLiveException(TikTokError.USERNAME_NOT_FOUND)
            logger.error(f"Lỗi mạng khi lấy RoomID từ {user}: {e}")
            raise TikTokException(f"Lỗi mạng: {e}")
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Lỗi phân tích cú pháp JSON hoặc Key cho {user}: {e}")
            raise UserLiveException(TikTokError.API_CHANGED)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    def is_room_alive(self, room_id: str):
        if not room_id: return False
        try:
            url = f"{self.config['api_endpoints']['webcast_url']}{self.config['api_endpoints']['room_info'].format(room_id=room_id)}"
            response = self.http_client.session.get(url, timeout=5)
            if response.status_code != 200: return False
            data = response.json()
            return data.get('data', {}).get('status', 0) == 2
        except Exception:
            return False

    def get_live_url(self, room_id: str):
        try:
            url = f"{self.config['api_endpoints']['webcast_url']}{self.config['api_endpoints']['room_info'].format(room_id=room_id)}"
            response = self.http_client.session.get(url, timeout=10)
            data = response.json().get('data', {})

            if data.get('status', 0) != 2:
                raise LiveNotFound(TikTokError.USER_NOT_CURRENTLY_LIVE)

            stream_data = data.get('stream_url', {}).get('flv_pull_url', {})
            live_url = stream_data.get('FULL_HD1') or stream_data.get('HD1') or stream_data.get('SD1') or stream_data.get('SD2')
            
            if not live_url:
                raise LiveNotFound(TikTokError.RETRIEVE_LIVE_URL)
            return live_url
        except (RequestException, json.JSONDecodeError):
            raise LiveNotFound(TikTokError.RETRIEVE_LIVE_URL)

class TikTokRecorder:
    def __init__(self, user, cookies=None, duration=None, convert_to_mp3=False, recording_id='N/A', custom_output_dir=None, status_callback=None):
        from config import COOKIES
        self.user = user
        self.cookies = cookies or COOKIES
        self.duration = duration
        self.convert_to_mp3 = convert_to_mp3
        self.recording_id = recording_id
        self.custom_output_dir = custom_output_dir
        self.status_callback = status_callback
        
        self.tiktok = TikTokAPI(self.cookies)
        self.room_id = None
        self.stop_event = threading.Event()
        self.cancellation_requested = False
        self.output_filepath = None
        self.final_video_path = None # <-- THÊM THUỘC TÍNH MỚI

        logger.info(f"Khởi tạo recorder cho user: {self.user}")

    def _update_status(self, message, color):
        if self.status_callback:
            self.status_callback(self.recording_id, message, color)

    def run(self):
        try:
            self._update_status("Lấy RoomID...", "blue")
            self.room_id = self.tiktok.get_room_id_from_user(self.user)
        except (UserLiveException, TikTokException) as e:
            logger.error(f"Lỗi khi lấy RoomID cho {self.user}: {e}")
            self._update_status(f"Lỗi: {e}", "red")
            return
            
        wait_intervals = [120, 300, 600, 900]
        interval_index = 0
        
        while not self.stop_event.is_set():
            try:
                self._update_status("Kiểm tra live...", "blue")
                is_live = self.tiktok.is_room_alive(self.room_id)
                if is_live:
                    logger.info(f"User {self.user} đang livestream. Bắt đầu ghi hình.")
                    self._update_status("Đang ghi hình...", "green")
                    self.start_recording()
                    break 
                else:
                    wait_time = wait_intervals[min(interval_index, len(wait_intervals) - 1)]
                    wait_time_minutes = wait_time / 60
                    logger.info(f"User {self.user} không live, chờ {wait_time_minutes:.1f} phút.")
                    self._update_status(f"Chờ live ({wait_time_minutes:.1f}p)...", "orange")
                    interval_index += 1
                    self.stop_event.wait(wait_time)
            except Exception as e:
                logger.error(f"Lỗi trong vòng lặp chờ của {self.user}: {e}")
                self._update_status("Lỗi, đang thử lại...", "red")
                self.stop_event.wait(300)

    def start_recording(self):
        try:
            live_url = self.tiktok.get_live_url(self.room_id)
            self.output_filepath = os.path.join(
                self.get_user_dir(),
                f"TK_{self.user}_{time.strftime('%Y%m%d_%H%M%S')}_flv.mp4"
            )
            logger.info(f"Bắt đầu ghi hình @{self.user}. Lưu vào: {os.path.basename(self.output_filepath)}")
            self.fetch_stream(live_url, self.output_filepath)
        except LiveNotFound as e:
            logger.warning(f"Không thể bắt đầu ghi hình cho {self.user}: {e}")
        finally:
            if self.cancellation_requested:
                logger.warning(f"Hủy bỏ được yêu cầu, xóa file tạm cho {self.user}.")
                if self.output_filepath and os.path.exists(self.output_filepath):
                    with suppress(OSError):
                        os.remove(self.output_filepath)
                        logger.info(f"Đã xóa thành công file tạm.")
            else:
                self.process_recorded_file(self.output_filepath)

    def fetch_stream(self, live_url, output_file):
        start_time = time.time()
        try:
            with self.tiktok.http_client.session.get(live_url, stream=True, timeout=10) as response:
                response.raise_for_status()
                with open(output_file, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if self.stop_event.is_set():
                            break
                        if self.duration and (time.time() - start_time) > self.duration:
                            logger.info(f"Đã đạt thời gian ghi hình {self.duration}s. Dừng lại.")
                            break
                        f.write(chunk)
        except RequestException as e:
            raise RecordingException(f"Lỗi kết nối khi tải stream: {e}")

    def process_recorded_file(self, file_path):
        if file_path and os.path.exists(file_path):
            if os.path.getsize(file_path) > 1024:
                mp4_file = file_path.replace('_flv.mp4', '.mp4')
                VideoManagement.convert_flv_to_mp4(file_path, recording_id=self.recording_id)
                self.final_video_path = mp4_file # <-- LƯU LẠI ĐƯỜNG DẪN MP4
                if self.convert_to_mp3 and os.path.exists(mp4_file):
                    VideoManagement.convert_mp4_to_mp3(mp4_file, recording_id=self.recording_id)
            else:
                os.remove(file_path)
                logger.warning(f"File ghi hình của @{self.user} rỗng hoặc quá nhỏ, đã xóa.")
        
    def stop(self):
        logger.info(f"Đã gửi tín hiệu Dừng & Lưu cho recorder của {self.user}")
        self.stop_event.set()

    def cancel(self):
        logger.warning(f"Đã gửi tín hiệu Hủy & Xóa cho recorder của {self.user}")
        self.cancellation_requested = True
        self.stop_event.set()

    def get_user_dir(self):
        if hasattr(sys, '_MEIPASS'):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        output_dir_base = self.custom_output_dir or os.path.join(base_path, 'Output')
        user_dir = os.path.normpath(os.path.join(output_dir_base, self.user))
        os.makedirs(user_dir, exist_ok=True)
        return user_dir
