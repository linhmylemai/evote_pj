--Cách kết hợp AES + RSA trong hệ thống eVote

Client sinh khóa AES ngẫu nhiên → dùng để mã hóa lá phiếu (vì AES rất nhanh).

Client dùng RSA (khóa công khai của admin) để mã hóa khóa AES đó.

Gửi lên server:
    Dữ liệu mã hóa bằng AES: cipher_vote
    Khóa AES đã được mã hóa bằng RSA: enc_key
    Thêm iv, timestamp, receipt_id...

Admin dùng RSA (khóa riêng) để giải mã enc_key → lấy lại khóa AES.

Dùng AES để giải mã lá phiếu → đếm phiếu.


--------------------------------------------------------
AES nhanh nhưng không an toàn nếu chia sẻ khóa trực tiếp.

RSA an toàn để chia sẻ khóa, nhưng chậm nếu dùng cho dữ liệu lớn.

Kết hợp cả hai giúp:
    Bảo mật dữ liệu (AES)
    Bảo mật khóa (RSA)
    Tối ưu hiệu năng


1. Tạo cặp khóa Admin
Sinh ra cặp khóa RSA (private + public) để:
Private key: Admin dùng để giải mã khóa AES (chỉ có admin giữ).
Public key: Client dùng để mã hóa khóa AES trước khi gửi phiếu. 
(
    admin_private_key.pem → chỉ admin giữ.
    admin_public_key.pem → server phát cho client để mã hóa khóa AES.
)

2. Đọc data_input


3. tạo routes
login.py	Xác thực người dùng (login) và sinh mã thông hành (ballot token).
ballot.py	ballot.py	Trả về thông tin ứng viên và khóa công khai.
cast.py	cast.py	Nhận và lưu phiếu bầu đã mã hóa.




------------------------Client--------------------

/api/login	POST	Đăng nhập	name_login, password	ballot_token, voter_name
/api/ballot/{id}	GET	Lấy thông tin bầu cử	(Không)	candidates_info, admin_public_key (chuỗi PEM)
/api/cast	POST	Bỏ phiếu	ballot_token, enc_key, cipher_vote, iv	receipt_id