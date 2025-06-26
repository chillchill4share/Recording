# Tệp: app_controller.py

import tkinter as tk
from tkinter import filedialog
import threading
import os
import sys
import json
import time
import queue
import re
import uuid
from concurrent.futures import ThreadPoolExecutor

from logger_setup import logger
from config import MAX_ROWS, MAX_ACTIVE_USERS, COOKIES
from rec_logic import (
    TikTokRecorder, TikTokException, UserLiveException,
    LiveNotFound, RecordingException
)
from gui_view import GUIView

class UserRowModel:
    """Lớp chứa toàn bộ dữ liệu và trạng thái của một hàng trong giao diện."""
    def __init__(self, row_id):
        self.id = row_id
        self.status = "Chờ"
        self.recorder = None
        self.future = None
        self.is_stopping = False
        self.widgets = {}
        self.last_known_input = ""

class AppController:
    def __init__(self, root):
        logger.debug("Bắt đầu khởi tạo AppController")
        self.root = root
        
        if hasattr(sys, '_MEIPASS'):
            self.base_path = os.path.dirname(sys.executable)
        else:
            self.base_path = os.path.dirname(os.path.abspath(__file__))
        
        self.is_running = True
        self.user_rows = {}
        self.rows_lock = threading.RLock()
        self.protected_rows = []
        self.custom_output_dir = None
        self.cookies = COOKIES
        self.thread_pool = ThreadPoolExecutor(max_workers=MAX_ACTIVE_USERS + 5)

        self.successful_users = []  
        self.failed_users = []      
        self.active_users = set()     

        self.view = GUIView(root, self)
        self.add_user_row()

        self.update_queue = queue.Queue()
        self.process_queue()

        logger.debug("Khởi động monitor_threads")
        self.monitor_thread = threading.Thread(target=self.monitor_threads, daemon=True)
        self.monitor_thread.start()

        logger.debug("Hoàn tất khởi tạo AppController")

    def handle_url_entry_focus_out(self, row_id, widget):
        model = self.user_rows.get(row_id)
        if not model: return
        current_text = widget.get().strip()
        if current_text == model.last_known_input: return
        username = self.extract_username(current_text)
        widget.delete(0, tk.END)
        if username:
            normalized_text = f"@{username}"
            widget.insert(0, normalized_text)
            widget.config(foreground='black')
            logger.info(f"Đã chuẩn hóa username cho hàng {row_id} thành: {normalized_text}")
            model.last_known_input = normalized_text
        else:
            logger.warning(f"Input '{current_text}' không hợp lệ, đã xóa trắng ô nhập liệu.")
            model.last_known_input = ""

    def update_row_status(self, row_id, text, color):
        model = self.user_rows.get(row_id)
        if model:
            model.status = text
            status_label_widget = model.widgets.get('status_label')
            self.update_queue.put(lambda: self.view.update_status_label(status_label_widget, text, color))

    def process_queue(self):
        try:
            while not self.update_queue.empty():
                callback = self.update_queue.get_nowait()
                if callable(callback): callback()
        except queue.Empty: pass
        finally:
            if self.is_running: self.root.after(100, self.process_queue)

    def update_all_button_states(self):
        with self.rows_lock:
            at_max_rows = len(self.user_rows) >= MAX_ROWS
            for row_id, model in self.user_rows.items():
                self.view.set_widget_state(model.widgets['add_button'], 'disabled' if at_max_rows else 'normal')
                self.view.set_widget_state(model.widgets['remove_button'], 'normal')

    def add_user_row(self):
        with self.rows_lock:
            if len(self.user_rows) >= MAX_ROWS:
                self.view.show_messagebox("warning", "Cảnh báo", f"Đã đạt tối đa {MAX_ROWS} hàng.")
                return None
            row_id = str(uuid.uuid4())
            new_row_widgets = self.view.add_user_row_to_gui(row_id, len(self.user_rows))
            new_model = UserRowModel(row_id)
            new_model.widgets = new_row_widgets
            self.user_rows[row_id] = new_model
            if len(self.user_rows) == 1: self.protected_rows.append(row_id)
            self.view.update_window_size(len(self.user_rows))
            self.update_all_button_states()
            logger.debug(f"Đã thêm hàng mới với row_id: {row_id}")
            return row_id

    def remove_user_row(self, row_id):
        model = self.user_rows.get(row_id)
        if not model: return
        is_recording = model.recorder is not None
        is_protected = row_id in self.protected_rows
        if is_recording:
            msg = "User đang ghi hình/chờ.\nBạn có chắc muốn DỪNG và XÓA hàng này không?"
            response = self.view.show_messagebox("askyesno", "Xác nhận Hủy", msg)
            if response:
                self.stop_recording(row_id, is_removing=True)
        else:
            if is_protected:
                model.widgets['url_entry'].delete(0, tk.END)
                model.last_known_input = ""
                self.update_row_status(row_id, "Chờ", "grey")
            else:
                self.view.remove_user_row_from_gui(row_id)
                with self.rows_lock: del self.user_rows[row_id]
                self.view.update_window_size(len(self.user_rows))
                self.update_all_button_states()
                logger.info(f"Đã xóa hàng với row_id: {row_id}")

    def cleanup_ui_and_data(self, row_id, username, is_protected):
        logger.debug(f"Bắt đầu dọn dẹp giao diện và dữ liệu cho hàng {row_id}")
        
        self.active_users.discard(username)

        with self.rows_lock:
            model = self.user_rows.get(row_id)
            if model:
                model.recorder = None
                model.future = None
                model.is_stopping = False
                if is_protected:
                    self.view.update_ui_for_state(row_id, 'stopped')
                    model.widgets['url_entry'].delete(0, tk.END)
                    model.last_known_input = ""
                    self.update_row_status(row_id, "Chờ", "grey")
                else:
                    self.view.remove_user_row_from_gui(row_id)
                    if row_id in self.user_rows: del self.user_rows[row_id]
                    self.view.update_window_size(len(self.user_rows))
        self.update_all_button_states()
        self.view.update_status_labels(len(self.successful_users), len(self.failed_users))
        self.view.close_active_dialog()
        logger.info(f"Hoàn tất dọn dẹp cho user {username}")
    
    def browse_output_dir(self):
        path = filedialog.askdirectory(title="Chọn thư mục đầu ra")
        if path:
            self.custom_output_dir = os.path.normpath(path)
            self.view.update_output_dir_entry(self.custom_output_dir)
            logger.info(f"Đã chọn thư mục đầu ra tùy chỉnh: {self.custom_output_dir}")

    def start_recording(self, row_id):
        model = self.user_rows.get(row_id)
        if not model or model.recorder: return

        if len(self.active_users) >= MAX_ACTIVE_USERS:
            self.view.show_messagebox("warning", "Quá tải", f"Đã đạt tối đa {MAX_ACTIVE_USERS} user ghi hình cùng lúc.")
            return

        url_input = model.widgets['url_entry'].get()
        username = self.extract_username(url_input)

        if not username:
            self.view.show_messagebox("error", "Lỗi", "Tên người dùng không hợp lệ.")
            return
        
        normalized_text = f"@{username}"
        model.widgets['url_entry'].delete(0, tk.END)
        model.widgets['url_entry'].insert(0, normalized_text)
        model.last_known_input = normalized_text

        for r_id, r_model in self.user_rows.items():
            if r_id != row_id and r_model.recorder and r_model.recorder.user == username:
                self.view.show_messagebox("warning", "Trùng lặp", f"User {username} đã đang được ghi hình ở hàng khác.")
                return

        def record_in_thread():
            try:
                duration_str = model.widgets['duration_entry'].get()
                duration = int(duration_str) if duration_str.isdigit() else None
                
                recorder = TikTokRecorder(
                    user=username, cookies=self.cookies, duration=duration,
                    convert_to_mp3=model.widgets['convert_var'].get(),
                    recording_id=row_id, custom_output_dir=self.custom_output_dir,
                    status_callback=self.update_row_status 
                )
                
                with self.rows_lock: model.recorder = recorder
                
                self.active_users.add(recorder.user)
                self.update_queue.put(lambda: self.view.update_ui_for_state(row_id, 'recording'))
                self.update_queue.put(self.update_all_button_states)
                
                recorder.run()

                if not recorder.cancellation_requested and recorder.final_video_path and os.path.exists(recorder.final_video_path):
                    self.successful_users.append(recorder.user)
                    self.update_row_status(row_id, "Hoàn tất", "green")
                
                elif recorder.cancellation_requested:
                    self.failed_users.append(username)
                    self.update_row_status(row_id, "Đã hủy", "red")
                
                else:
                    self.failed_users.append(username)
                    self.update_row_status(row_id, "Đã dừng/Lỗi", "grey")
                
            except (TikTokException, UserLiveException, LiveNotFound, RecordingException) as e:
                logger.error(f"Lỗi ghi hình cho {username}: {e}")
                self.failed_users.append(username)
                self.update_row_status(row_id, f"Lỗi: {e}", "red")
            except Exception as e:
                logger.critical(f"Lỗi không mong muốn khi ghi hình {username}: {e}", exc_info=True)
                self.failed_users.append(username)
                self.update_row_status(row_id, "Lỗi nghiêm trọng", "red")

        future = self.thread_pool.submit(record_in_thread)
        with self.rows_lock: model.future = future

    def stop_recording(self, row_id, is_removing=False):
        with self.rows_lock:
            model = self.user_rows.get(row_id)
            if not model or not model.recorder: return
        if is_removing:
            logger.info(f"Đã gửi tín hiệu Hủy cho recorder của user {model.recorder.user}.")
            self.update_row_status(row_id, "Đang hủy...", "orange")
            model.recorder.cancel()
        else:
            logger.info(f"Đã gửi tín hiệu Dừng cho recorder của user {model.recorder.user}.")
            self.update_row_status(row_id, "Đang dừng...", "orange")
            model.recorder.stop()

    def extract_username(self, text_input):
        if not text_input or not isinstance(text_input, str): return ""
        text_input = text_input.strip()
        match = re.search(r"@([a-zA-Z0-9_.-]+)", text_input)
        if match: return match.group(1)
        if re.match(r'^[a-zA-Z0-9_.-]+$', text_input): return text_input
        logger.warning(f"Không thể trích xuất username từ đầu vào: '{text_input}'")
        return ""

    def monitor_threads(self):
        while self.is_running:
            time.sleep(1)
            with self.rows_lock:
                for row_id in list(self.user_rows.keys()):
                    model = self.user_rows.get(row_id)
                    if not model or model.is_stopping: continue
                    future = model.future
                    if future and future.done():
                        recorder = model.recorder
                        if not recorder: continue
                        username = recorder.user
                        if future.exception():
                            logger.error(f"Luồng cho user '{username}' đã kết thúc với một exception: {future.exception()}", exc_info=future.exception())
                        else:
                            logger.info(f"Luồng cho user '{username}' đã hoàn thành, chuẩn bị dọn dẹp.")
                        model.is_stopping = True
                        is_protected = row_id in self.protected_rows
                        self.update_queue.put(lambda rid=row_id, u=username, prot=is_protected: self.cleanup_ui_and_data(rid, u, prot))

    def on_closing(self):
        logger.info("Bắt đầu quy trình đóng chương trình")
        self.is_running = False
        for model in self.user_rows.values():
            if model.recorder: model.recorder.stop()
        logger.info("Đang chờ các luồng ghi hình kết thúc...")
        self.thread_pool.shutdown(wait=True)
        logger.info("Đã đóng ThreadPoolExecutor")
        self.root.destroy()
        
    def convert_to_mp3_manual(self, input_file, output_dir):
        if not input_file or not os.path.exists(input_file):
            self.view.show_messagebox("error", "Lỗi", "Vui lòng chọn file đầu vào hợp lệ.")
            return
        if not output_dir or not os.path.isdir(output_dir):
            output_dir = os.path.dirname(input_file)
        base_filename = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(output_dir, f"{base_filename}.mp3")
        logger.info(f"Bắt đầu chuyển đổi thủ công sang MP3: {os.path.basename(input_file)}")
        self.view.set_mp3_button_state('disabled')
        def conversion_thread():
            from rec_logic import VideoManagement
            try:
                VideoManagement.convert_mp4_to_mp3(file=input_file, output_file=output_file)
                self.update_queue.put(lambda: self.view.show_messagebox("info", "Thành công", f"Đã chuyển đổi thành công file:\n{os.path.basename(output_file)}"))
            except Exception as e:
                logger.error(f"Lỗi khi chuyển đổi MP3 thủ công: {e}")
                self.update_queue.put(lambda: self.view.show_messagebox("error", "Lỗi", f"Chuyển đổi thất bại: {e}"))
            finally:
                self.update_queue.put(lambda: self.view.set_mp3_button_state('normal'))
                self.update_queue.put(self.view.close_active_dialog)
        self.thread_pool.submit(conversion_thread)

    def show_status_details(self, status_type):
        if status_type == "success":
            events = self.successful_users
            title = "Lịch sử Thành công"
        else:
            events = self.failed_users
            title = "Lịch sử Thất bại"
        if not events:
            self.view.show_messagebox("info", title, "Không có sự kiện nào trong danh sách này.")
            return
        unique_users = sorted(list(set(events)))
        user_list_str = "\n".join(unique_users)
        self.view.show_details_window(title, user_list_str)
