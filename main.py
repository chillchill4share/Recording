import tkinter as tk
from app_controller import AppController
from logger_setup import logger
import tkinter.messagebox

def main():
    """
    Điểm khởi đầu của ứng dụng TikTok Recorder.
    Khởi tạo cửa sổ chính Tkinter và lớp điều khiển ứng dụng.
    """
    try:
        logger.info("Khởi tạo ứng dụng TikTok Recorder")
        root = tk.Tk()
        app = AppController(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()
        logger.info("Ứng dụng đã đóng thành công")
    except Exception as e:
        logger.critical(f"Lỗi nghiêm trọng không mong muốn khi khởi chạy hoặc trong vòng lặp chính: {e}", exc_info=True)
        tkinter.messagebox.showerror(
            "Lỗi nghiêm trọng",
            f"Ứng dụng đã gặp lỗi không thể phục hồi và sẽ thoát.\n\nLỗi: {e}\n\nVui lòng kiểm tra file 'recording.txt' để biết chi tiết."
        )

if __name__ == "__main__":
    main()
