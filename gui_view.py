# Tệp: gui_view.py

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk, scrolledtext, filedialog
import sys
import os
from ui_utils import ToolTip, center_dialog
from config import README_CONTENT
from logger_setup import logger

class GUIView:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.active_dialog = None
        self.dialog_result = None
        self.initial_height = 150
        self.row_height = 40
        self.WINDOW_WIDTH = 850

        self.root.title("Recording TikTok Live v1.3.0")
        self.root.resizable(False, False)
        self.root.geometry(f"{self.WINDOW_WIDTH}x{self.initial_height}")
        self.root.minsize(self.WINDOW_WIDTH, self.initial_height)

        self.setup_icon()
        self.setup_menu()
        self.setup_ui()

    def setup_icon(self, window=None):
        if window is None: window = self.root
        try:
            base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(base_path, 'icon.ico')
            if os.path.exists(icon_path): window.winfo_toplevel().iconbitmap(default=icon_path)
        except Exception as e: logger.warning(f"Không thể thiết lập icon: {e}")

    def setup_menu(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.controller.on_closing)
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def setup_ui(self):
        header_frame = tk.Frame(self.root, borderwidth=2, relief="groove", padx=10, pady=5)
        header_frame.pack(padx=10, pady=(10, 0), fill="x")

        output_button = tk.Button(
            header_frame,
            text="Output:",
            command=self.controller.browse_output_dir,
            relief=tk.RAISED,
            cursor="hand2",
        )
        output_button.pack(side=tk.LEFT, padx=(0, 5))
        ToolTip(output_button, "Nhấp để chọn thư mục đầu ra")

        self.output_dir_entry = tk.Entry(header_frame)
        # Sử dụng self.controller.base_path đã được định nghĩa
        default_output_path = os.path.join(self.controller.base_path, 'Output')
        self.output_dir_entry.insert(0, default_output_path)
        self.output_dir_entry.pack(side=tk.LEFT, fill="x", expand=True)

        self.main_frame = tk.Frame(self.root, borderwidth=2, relief="groove", padx=10, pady=5)
        self.main_frame.pack(padx=10, pady=(10, 0), fill="both", expand=True)
        self.main_frame.grid_columnconfigure(1, weight=1)

        status_frame_container = tk.Frame(self.root, borderwidth=2, relief="groove")
        status_frame_container.pack(padx=10, pady=(5, 10), fill="x", side="bottom")
        status_content_frame = tk.Frame(status_frame_container)
        status_content_frame.pack(fill='x', padx=5, pady=2)
        success_frame = tk.Frame(status_content_frame)
        success_frame.pack(side=tk.LEFT, expand=True, fill='x')
        self.success_label = tk.Label(success_frame, text="Thành công: 0", fg="green")
        self.success_label.pack(side=tk.LEFT)
        tk.Button(success_frame, text="Xem", command=lambda: self.controller.show_status_details("success")).pack(side=tk.LEFT, padx=5)
        ttk.Separator(status_content_frame, orient='vertical').pack(side=tk.LEFT, fill='y', padx=10)
        failure_frame = tk.Frame(status_content_frame)
        failure_frame.pack(side=tk.LEFT, expand=True, fill='x')
        self.failure_label = tk.Label(failure_frame, text="Thất bại: 0", fg="red")
        self.failure_label.pack(side=tk.LEFT)
        tk.Button(failure_frame, text="Xem", command=lambda: self.controller.show_status_details("failure")).pack(side=tk.LEFT, padx=5)
        ttk.Separator(status_content_frame, orient='vertical').pack(side=tk.LEFT, fill='y', padx=10)
        self.mp3_button = tk.Button(status_content_frame, text="Convert to MP3", command=self.show_mp3_dialog)
        self.mp3_button.pack(side=tk.LEFT, padx=(5, 0))
        ToolTip(self.mp3_button, "Mở cửa sổ chuyển đổi file sang MP3")

    def add_user_row_to_gui(self, row_id, current_row_count):
        row_index = current_row_count
        
        action_button_frame = tk.Frame(self.main_frame)
        action_button_frame.grid(row=row_index, column=0, padx=(0, 5), pady=2, sticky="w")
        add_button = tk.Button(action_button_frame, text="➕", command=self.controller.add_user_row, width=2)
        add_button.pack(side=tk.LEFT)
        ToolTip(add_button, "Thêm user mới")
        remove_button = tk.Button(action_button_frame, text="➖", command=lambda: self.controller.remove_user_row(row_id), width=2)
        remove_button.pack(side=tk.LEFT, padx=2)
        ToolTip(remove_button, "Xóa hàng / Hủy ghi hình (không lưu file)")
        
        url_entry = tk.Entry(self.main_frame, width=30)
        url_entry.grid(row=row_index, column=1, padx=(0, 5), pady=2, sticky="ew")
        ToolTip(url_entry, "Nhập username hoặc link rồi nhấn nút ▶")
        
        controls_frame = tk.Frame(self.main_frame)
        controls_frame.grid(row=row_index, column=2, padx=(0, 5), pady=2, sticky="w")
        start_button = tk.Button(controls_frame, text="▶", command=lambda: self.controller.start_recording(row_id), width=2)
        start_button.pack(side=tk.LEFT)
        ToolTip(start_button, "Bắt đầu ghi hình")
        stop_button = tk.Button(controls_frame, text="■", command=lambda: self.controller.stop_recording(row_id), width=2, state="disabled")
        stop_button.pack(side=tk.LEFT, padx=2)
        ToolTip(stop_button, "Dừng ghi hình & lưu file")

        options_frame = tk.Frame(self.main_frame)
        options_frame.grid(row=row_index, column=3, padx=(0, 5), pady=2, sticky="w")

        duration_entry = tk.Entry(options_frame, width=10)
        duration_entry.pack(side=tk.LEFT, padx=2)
        ToolTip(duration_entry, "Thời gian ghi (giây), để trống nếu không giới hạn")
        
        convert_var = tk.BooleanVar(value=True)
        convert_check = tk.Checkbutton(options_frame, variable=convert_var)
        convert_check.pack(side=tk.LEFT)
        ToolTip(convert_check, "Chuyển file video sang MP3 sau khi ghi hình")
        
        status_label = tk.Label(self.main_frame, text="Chờ", width=20, anchor="w", fg="grey")
        status_label.grid(row=row_index, column=4, padx=(5, 0), pady=2, sticky="w")

        url_entry.bind("<FocusOut>", lambda e, rid=row_id: self.controller.handle_url_entry_focus_out(rid, e.widget))
        
        return {
            'row_id': row_id, 'add_button': add_button, 'remove_button': remove_button,
            'url_entry': url_entry, 'start_button': start_button, 'stop_button': stop_button,
            'convert_var': convert_var, 'convert_check': convert_check,
            'duration_entry': duration_entry,
            'status_label': status_label,
            'widgets': [action_button_frame, url_entry, controls_frame, options_frame, status_label]
        }
        
    def remove_user_row_from_gui(self, row_id):
        user_row_model = self.controller.user_rows.get(row_id)
        if user_row_model:
            for widget in user_row_model.widgets['widgets']:
                if widget and widget.winfo_exists():
                    widget.destroy()

    def update_status_label(self, status_label, text, color):
        if status_label and status_label.winfo_exists():
            status_label.config(text=text, fg=color)
    
    def update_window_size(self, num_rows):
        status_frame_height = 50
        header_height = 80
        new_height = header_height + num_rows * self.row_height + status_frame_height
        self.root.geometry(f"{self.WINDOW_WIDTH}x{max(self.initial_height, new_height)}")

    def update_status_labels(self, success_count, failure_count):
        self.success_label.config(text=f"Thành công: {success_count}")
        self.failure_label.config(text=f"Thất bại: {failure_count}")

    def update_output_dir_entry(self, text, color='black'):
        self.output_dir_entry.delete(0, tk.END)
        self.output_dir_entry.insert(0, text)
        self.output_dir_entry.config(foreground=color)

    def set_widget_state(self, widget, state):
        if widget and widget.winfo_exists():
            widget.config(state=state)

    def update_ui_for_state(self, row_id, state):
        model = self.controller.user_rows.get(row_id)
        if not model: return

        widgets = model.widgets
        is_recording = state == 'recording'

        self.set_widget_state(widgets.get('url_entry'), 'disabled' if is_recording else 'normal')
        self.set_widget_state(widgets.get('start_button'), 'disabled' if is_recording else 'normal')
        self.set_widget_state(widgets.get('stop_button'), 'normal' if is_recording else 'disabled')

        self.set_widget_state(widgets.get('duration_entry'), 'disabled' if is_recording else 'normal')
        self.set_widget_state(widgets.get('convert_check'), 'disabled' if is_recording else 'normal')

    def show_messagebox(self, msg_type, title, message):
        if self.active_dialog and self.active_dialog.winfo_exists(): return None
        self.dialog_result = None
        self.active_dialog = dialog = tk.Toplevel(self.root)
        dialog.title(title); dialog.resizable(False, False); self.setup_icon(dialog)
        main_frame = tk.Frame(dialog, padx=15, pady=10); main_frame.pack(expand=True, fill="both")
        msg_frame = tk.Frame(main_frame); msg_frame.pack(fill="x")
        tk.Label(msg_frame, text=message, justify=tk.LEFT, wraplength=400).pack(side="left", anchor="nw", padx=(10,0))
        btn_frame = tk.Frame(main_frame); btn_frame.pack(pady=(15, 5))
        def on_yes(): self.dialog_result = True; self.close_active_dialog()
        def on_no(): self.dialog_result = False; self.close_active_dialog()
        def on_ok(): self.dialog_result = None; self.close_active_dialog()
        if msg_type == 'askyesno':
            tk.Button(btn_frame, text="Yes", width=10, command=on_yes).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text="No", width=10, command=on_no).pack(side=tk.LEFT, padx=5)
        else:
            tk.Button(btn_frame, text="OK", width=10, command=on_ok).pack()
        dialog.transient(self.root); dialog.update_idletasks(); center_dialog(dialog); dialog.grab_set()
        self.root.wait_window(dialog)
        return self.dialog_result

    def show_about(self):
        if self.active_dialog: return
        about_window = tk.Toplevel(self.root)
        self.active_dialog = about_window
        about_window.title("About TikTok Live Recorder")
        about_window.resizable(False, False); self.setup_icon(about_window)
        text_area = scrolledtext.ScrolledText(about_window, wrap=tk.WORD, width=70, height=20, font=("Arial", 10))
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        text_area.insert(tk.END, README_CONTENT); text_area.config(state="disabled")
        tk.Button(about_window, text="Close", command=self.close_active_dialog).pack(pady=5)
        about_window.transient(self.root); about_window.grab_set(); center_dialog(about_window)
        about_window.protocol("WM_DELETE_WINDOW", self.close_active_dialog)
        
    def show_mp3_dialog(self):
        if self.active_dialog: return
        dialog = tk.Toplevel(self.root)
        self.active_dialog = dialog
        dialog.title("Chuyển đổi sang MP3")
        dialog.resizable(False, False); self.setup_icon(dialog)
        frame = tk.Frame(dialog, padx=10, pady=10); frame.pack()
        tk.Label(frame, text="File MP4:").grid(row=0, column=0, sticky="w", pady=2)
        input_entry = tk.Entry(frame, width=50); input_entry.grid(row=1, column=0, columnspan=2, sticky="ew")
        def browse_input():
            path = filedialog.askopenfilename(title="Chọn file MP4/FLV", filetypes=[("Video files", "*.mp4 *.flv")])
            if path: input_entry.delete(0, tk.END); input_entry.insert(0, path)
        tk.Button(frame, text="Duyệt...", command=browse_input).grid(row=1, column=2, padx=5)
        tk.Label(frame, text="Thư mục lưu (để trống nếu muốn lưu cùng chỗ):").grid(row=2, column=0, sticky="w", pady=2)
        output_entry = tk.Entry(frame, width=50); output_entry.grid(row=3, column=0, columnspan=2, sticky="ew")
        def browse_output():
            path = filedialog.askdirectory(title="Chọn thư mục lưu file MP3")
            if path: output_entry.delete(0, tk.END); output_entry.insert(0, path)
        tk.Button(frame, text="Duyệt...", command=browse_output).grid(row=3, column=2, padx=5)
        button_frame = tk.Frame(frame); button_frame.grid(row=4, column=0, columnspan=3, pady=10)
        self.convert_mp3_btn = tk.Button(button_frame, text="Chuyển đổi", command=lambda: self.controller.convert_to_mp3_manual(input_entry.get(), output_entry.get()))
        self.convert_mp3_btn.pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Đóng", command=self.close_active_dialog).pack(side=tk.LEFT, padx=10)
        dialog.transient(self.root); dialog.grab_set(); center_dialog(dialog)
        dialog.protocol("WM_DELETE_WINDOW", self.close_active_dialog)

    def set_mp3_button_state(self, state):
        if hasattr(self, 'convert_mp3_btn') and self.convert_mp3_btn.winfo_exists():
            self.convert_mp3_btn.config(state=state)

    def show_progress_dialog(self, message="Đang xử lý..."):
        if self.active_dialog: self.close_active_dialog()
        dialog = tk.Toplevel(self.root); self.active_dialog = dialog
        dialog.title("Vui lòng chờ"); dialog.resizable(False, False)
        tk.Label(dialog, text=message, pady=10, padx=20).pack()
        progress = ttk.Progressbar(dialog, length=300, mode='indeterminate')
        progress.pack(pady=10, padx=20); progress.start(10)
        dialog.transient(self.root); dialog.grab_set(); center_dialog(dialog)
        dialog.protocol("WM_DELETE_WINDOW", lambda: None)

    def show_details_window(self, title, content):
        if self.active_dialog: return
        dialog = tk.Toplevel(self.root); self.active_dialog = dialog
        dialog.title(title); dialog.geometry("300x400"); self.setup_icon(dialog)
        text_area = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, width=40, height=20)
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        text_area.insert(tk.END, content); text_area.config(state="disabled")
        tk.Button(dialog, text="Đóng", command=self.close_active_dialog).pack(pady=5)
        dialog.transient(self.root); dialog.grab_set(); center_dialog(dialog)
        dialog.protocol("WM_DELETE_WINDOW", self.close_active_dialog)

    def close_active_dialog(self):
        if self.active_dialog and self.active_dialog.winfo_exists():
            self.active_dialog.destroy()
        self.active_dialog = None
