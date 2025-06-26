# TikTok Live Recorder - Hướng dẫn Sử dụng

Đây là công cụ giúp bạn tự động ghi lại các phiên livestream trên TikTok và lưu về máy tính dưới dạng file video MP4.

## Tính năng Nổi bật

- **Tự động chờ:** Nếu người dùng chưa live, chương trình sẽ tự động chờ và bắt đầu ghi ngay khi họ livestream.
- **Ghi nhiều luồng:** Hỗ trợ theo dõi và ghi nhiều người dùng cùng một lúc.
- **Lưu và Chuyển đổi:** Tự động lưu file dưới dạng MP4 và tùy chọn chuyển sang audio MP3.
- **Giao diện đơn giản:** Tất cả các chức năng chính đều nằm trên một cửa sổ duy nhất.

## Yêu cầu Hệ thống

1.  **Hệ điều hành:** Windows 10 hoặc Windows 11 (phiên bản 64-bit).
2.  **FFmpeg:** **(Bắt buộc)** Chương trình yêu cầu `ffmpeg.exe` để xử lý video. Vui lòng tải FFmpeg và đặt thư mục `ffmpeg` (chứa file `ffmpeg.exe`) nằm cùng cấp với file chạy chương trình của bạn.

## Hướng dẫn Sử dụng

### 1. Thiết lập Thư mục Lưu trữ
- Khi khởi động, chương trình sẽ mặc định lưu video vào thư mục `Output` tại nơi bạn chạy chương trình.
- Để thay đổi, nhấn nút **`Output:`** ở trên cùng và chọn thư mục bạn muốn lưu.

### 2. Ghi một Livestream
- **Bước 1:** Trong một hàng trống, nhập **tên người dùng** (ví dụ: `funachair`) hoặc dán **link live/link trang cá nhân** vào ô nhập liệu. Sau khi bạn bấm ra ngoài, chương trình sẽ tự động chuẩn hóa về dạng `@username`.
- **Bước 2:** Nhấn nút **▶ (Bắt đầu)**.
    - Nếu người dùng đang live, chương trình sẽ bắt đầu ghi ngay lập tức.
    - Nếu chưa live, trạng thái sẽ chuyển thành "Chờ live..." và chương trình sẽ tự động kiểm tra lại sau các khoảng thời gian tăng dần (2, 5, 10, rồi 15 phút).
- **Bước 3 (Tùy chọn):**
    - **Dừng & Lưu:** Nhấn nút **■ (Dừng)** để kết thúc việc ghi hình và lưu lại file video. Tác vụ này sẽ được đếm là một lần **Thành công**.
    - **Hủy & Xóa:** Nhấn nút **➖ (Hủy)** để hủy tác vụ đang chạy (sẽ không lưu file) và xóa hàng đó đi. Tác vụ này sẽ được đếm là một lần **Thất bại**.
- **Bước 4:** Nhấn nút **➕ (Thêm)** để có thêm hàng mới và theo dõi nhiều người dùng khác.

### 3. Các Tùy chọn trên mỗi hàng
- **Ô nhập thời gian:** Nhập số giây (ví dụ: `3600`) nếu bạn muốn giới hạn thời gian ghi hình. Để trống nếu muốn ghi cho đến khi live kết thúc.
- **Hộp kiểm (Checkbox):** Tích vào ô này nếu bạn muốn chương trình tự động chuyển video sang file audio **MP3** sau khi ghi xong.

### 4. Các Chức năng khác
- **Xem Lịch sử:** Nhấn nút **`Xem`** bên cạnh bộ đếm `Thành công` hoặc `Thất bại` để xem danh sách các user tương ứng trong phiên làm việc đó.
- **Chuyển đổi Thủ công:** Nhấn nút **`Convert to MP3`** ở dưới cùng để mở cửa sổ chuyển đổi một file video bất kỳ sang MP3.

## Lưu ý Quan trọng
- Tất cả các file được lưu trong thư mục con mang tên của user. Ví dụ: `Output\funachair\video.mp4`.
- File `recording.txt` được tạo ra để ghi lại nhật ký hoạt động. Nếu bạn gặp lỗi và cần hỗ trợ, vui lòng gửi kèm file này.
- Nếu gặp lỗi liên quan đến "Quốc gia bị chặn" hoặc "Tài khoản riêng tư", bạn có thể sẽ cần cung cấp cookies tài khoản TikTok của mình vào file `config.py` (nếu chạy từ mã nguồn) hoặc chờ các phiên bản cập nhật trong tương lai.
