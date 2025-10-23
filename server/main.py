from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.routes import login, ballot, cast 

app = FastAPI(
    title="e-Vote Backend",
    description="API cho hệ thống bỏ phiếu điện tử sử dụng mã hóa",
    version="1.0.0",
)

# Cấu hình CORS (cho phép Frontend ở cổng khác giao tiếp)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # Cho phép truy cập từ mọi nguồn (Dev)
    allow_credentials=True, 
    allow_methods=["*"],     
    allow_headers=["*"],     
)

# ----------------------------------------------------------------------
# Thêm các Router (API Endpoints)
# ----------------------------------------------------------------------
# ✅ Router Login
app.include_router(login.router, prefix="/api", tags=["Đăng nhập & Xác thực"])
app.include_router(ballot.router, prefix="/api", tags=["Bầu cử & Thông tin"])
app.include_router(cast.router, prefix="/api", tags=["Bỏ phiếu"])


@app.get("/")
def read_root():
    """Endpoint kiểm tra server có đang hoạt động hay không."""
    return {"message": "e-Vote Backend Server đang hoạt động!"}