# Xem camera từ ba địa điểm qua Tailscale

## Sơ đồ

Mỗi địa điểm có một PC luôn bật, cắm cùng mạng LAN với camera. Cài Tailscale
trên ba PC này; mỗi PC quảng bá dải IP LAN của địa điểm mình như một subnet
router. PC chạy AEMS cũng tham gia cùng tailnet. Backend AEMS kết nối tới địa
chỉ RTSP nội bộ của từng camera qua các tuyến Tailscale; trang **Live Camera**
đã có lưới 1/4/9/16 ô để xem đồng thời.

Không cần cài Tailscale trên từng camera hoặc mở cổng RTSP ra Internet.

## 1. Ghi lại địa chỉ mạng trước khi cấu hình

Ghi địa chỉ IPv4 và subnet của camera ở từng nơi. Ba dải mạng và dải mạng
của PC chạy AEMS phải khác nhau, ví dụ:

- Nơi A: `192.168.10.0/24`, camera `192.168.10.101`.
- Nơi B: `192.168.20.0/24`, camera `192.168.20.101`.
- Nơi C: `192.168.30.0/24`, camera `192.168.30.101`.

Các địa chỉ trên chỉ là ví dụ. Nếu hai nơi đều dùng cùng dải như
`192.168.1.0/24`, hãy đổi một dải LAN trước khi quảng bá tuyến. Đặt IP cố định
hoặc DHCP reservation cho camera và PC subnet router.

## 2. Cấu hình PC tại mỗi nơi

1. Cài Tailscale trên cả ba PC và đăng nhập cùng một tailnet:
   <https://tailscale.com/docs/install/windows> (nếu PC dùng Windows).
2. Đảm bảo PC luôn bật, không tự ngủ. Trên Windows, bật **Run Unattended** trong
   Preferences của Tailscale để tuyến vẫn hoạt động sau khi đăng xuất.
3. Mở PowerShell với quyền Administrator và quảng bá dải LAN tương ứng:

   ```powershell
   # Chạy tại nơi A; thay CIDR bằng mạng thực tế
   tailscale up --advertise-routes=192.168.10.0/24
   ```

   Nơi B dùng `192.168.20.0/24`; nơi C dùng `192.168.30.0/24`.
4. Vào <https://login.tailscale.com/admin/machines>, mở từng PC, chọn
   **Edit route settings** và duyệt tuyến vừa quảng bá. Nếu tailnet có chính
   sách truy cập riêng, cấp quyền cho PC AEMS truy cập các dải camera.

Hướng dẫn chính thức: <https://tailscale.com/docs/use-cases/personal-or-at-home-use/access-devices-without-tailscale?tab=windows>

## 3. Cấu hình PC chạy AEMS

Cài Tailscale và đăng nhập cùng tailnet trên PC chạy backend. Windows nhận
subnet routes đã duyệt theo mặc định. Kiểm tra từ máy chủ:

```powershell
tailscale status
tailscale ping <ten-pc-noi-A>
Test-NetConnection 192.168.10.101 -Port 554
Test-NetConnection 192.168.20.101 -Port 554
Test-NetConnection 192.168.30.101 -Port 554
```

Kiểm tra thêm **bên trong container backend**, vì Docker Desktop dùng mạng
riêng và tuyến hoạt động trên Windows host chưa đủ để xác nhận container đọc
được RTSP:

```powershell
docker exec aems-backend python -c "import socket; socket.create_connection(('192.168.10.101', 554), 5).close(); print('RTSP TCP OK')"
```

Đổi IP ví dụ thành IP từng camera. Nếu Windows kết nối được nhưng container
không kết nối được, cần xử lý mạng Docker Desktop/VPN hoặc chuyển backend sang
máy Linux đã tham gia tailnet trước khi thêm camera vào AEMS.

## 4. Thêm camera và xem đồng thời

Trong **Camera Management**, tạo camera với tên có tiền tố địa điểm, ví dụ
`A - Cửa chính`, `B - Kho`, `C - Quầy`. Điền RTSP URL chứa **IP LAN của camera**
ở địa điểm đó, không dùng IP Tailscale của PC subnet router. Nên dùng substream
độ phân giải thấp để thử nhiều camera qua Internet; ứng dụng ưu tiên
`rtsp_sub` khi trường này được cấu hình.

Mở **Live Camera** và chọn lưới 4, 9 hoặc 16 ô. Trang này tải hình từ backend,
vì vậy trình duyệt chỉ cần truy cập AEMS; backend là thành phần phải tới được
cả ba mạng camera.

Kiểm tra tình trạng từng camera qua `/api/v1/cameras/{id}/health`. Nếu mất
RTSP, chức năng cảnh báo Telegram cho camera enabled sẽ báo sau thời gian chờ
trong `config/camera.yaml`, với điều kiện backend gửi được Telegram.

## Kiểm tra đường truyền

`tailscale ping <ten-pc>` cho biết kết nối trực tiếp hay qua relay. Kết nối
relay vẫn mã hóa nhưng có thể giảm tốc khi xem nhiều luồng. Tổng băng thông
upload cần thiết ở mỗi nơi xấp xỉ tổng bitrate của các camera đang xem từ nơi
đó. Kiểm tra từng camera trước, sau đó mở tất cả ô và theo dõi độ trễ.

Nguồn: <https://tailscale.com/docs/reference/connection-types>,
<https://docs.docker.com/desktop/features/networking/networking-how-tos/>.
