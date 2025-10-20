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




