# Giới hạn của ứng dụng
MAX_ROWS = 10
MAX_ACTIVE_USERS = 10

# Cấu hình cookies và API
COOKIES = {
    "ttwid": "",
    "sessionid": "",
    "tt_webid": "",
    "tt_csrf_token": "",
    "sessionid_ss": "",
    "tt-target-idc": ""
}

TIKTOK_CONFIG = {
    "api_endpoints": {
        "base_url": "https://www.tiktok.com",
        "webcast_url": "https://webcast.tiktok.com",
        "live_detail": "/api/live/detail/?aid=1988&roomID={room_id}",
        "room_info": "/webcast/room/info/?aid=1988&room_id={room_id}",
        "check_alive": "/webcast/room/check_alive/?aid=1988&room_ids={room_id}",
        "user_live": "/@{user}/live",
        "user_detail": "/api/user/detail/?uniqueId={user}&aid=1988"
    }
}

# Nội dung README cho cửa sổ "About"
README_CONTENT = """
TikTok Live Recorder - Hướng Dẫn Sử Dụng

1. Mô tả

TikTok Live Recorder giúp bạn ghi hình livestream TikTok, lưu thành file MP4 và chuyển sang MP3 nếu cần.
Chương trình hỗ trợ ghi nhiều user (tối đa 10) cùng lúc và có chế độ tự động kiểm tra, ghi hình khi user livestream.
Sử dụng File -> Exit để thoát khẩn cấp nếu chương trình quá tải (chú ý: sẽ không có dữ liệu nào được lưu lại).

2. Yêu cầu

Windows 10 64-bit (build 19041 trở lên)
CPU: Tối thiểu: Intel Core i7-8700 hoặc AMD Ryzen 5 5600X.
RAM: Tối thiểu: 8 GB DDR4.
Ổ Cứng: SSD với tốc độ ghi tốt (~500 MB/s).
Mạng: Kết nối ổn định, băng thông tải xuống > 40 Mbps.

3. Hướng dẫn sử dụng

Bước 1: Chạy chương trình

Nhấp đúp vào file thực thi của chương trình để mở.

Bước 2: Ghi hình

Ở một hàng trống, nhập username TikTok (ví dụ: @abc) vào ô "Nhập tên người dùng...".
Chọn chế độ:
    - Thủ công: Ghi ngay lập tức nếu user đang livestream.
    - Tự động: Tự động kiểm tra và sẽ bắt đầu ghi hình ngay khi user livestream.
Tùy chọn:
    - Tích "🎵" để tự động chuyển file video sang MP3 sau khi ghi xong.
    - Nhập thời gian ghi (tính bằng giây) vào ô "Thời gian (s)" nếu muốn giới hạn thời gian ghi, hoặc để trống để ghi không giới hạn.
Nhấn "▶" để bắt đầu.
Nhấn "■" để dừng và lưu file.
Nhấn "➖" để hủy ghi hình (không lưu file) và xóa hàng.
Nhấn "➕" để thêm một hàng mới.

Bước 3: Chuyển đổi MP3 thủ công

Nhấn nút "Convert to MP3".
Trong cửa sổ mới, chọn file MP4/FLV cần chuyển, chọn thư mục lưu (nếu để trống sẽ lưu cùng thư mục với file gốc), và nhấn "Chuyển đổi".

4. Lưu ý

File video và audio được lưu trong thư mục Output/<username> (thư mục này được tạo cùng cấp với file chạy chương trình).
Nếu gặp lỗi "Quốc gia bị chặn" hoặc "Tài khoản riêng tư", có thể cần cập nhật cookies.
File recording.txt lưu lại nhật ký hoạt động, hãy gửi file này nếu cần báo lỗi.

5. Hỗ trợ

Gặp vấn đề? Liên hệ người hỗ trợ và gửi file recording.txt.
"""
