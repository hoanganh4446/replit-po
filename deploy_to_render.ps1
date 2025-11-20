# PowerShell script để chuẩn bị và hướng dẫn deploy lên Render.com

Write-Host "🚀 Chuẩn bị deploy PO System lên Render.com..." -ForegroundColor Green

# 1. Kiểm tra Git
try {
    git --version | Out-Null
    Write-Host "✅ Git đã được cài đặt" -ForegroundColor Green
} catch {
    Write-Host "❌ Git chưa được cài đặt. Vui lòng cài đặt Git trước." -ForegroundColor Red
    exit 1
}

# 2. Thêm tất cả files vào Git
Write-Host "📦 Đang thêm files vào Git..." -ForegroundColor Yellow
git add .

# 3. Commit changes
Write-Host "💾 Đang commit changes..." -ForegroundColor Yellow
$commitMessage = "Ready for Render deployment: Added configuration files and persistent storage support"
git commit -m "$commitMessage"

# 4. Hướng dẫn Push
Write-Host ""
Write-Host "✅ Đã commit thành công!" -ForegroundColor Green
Write-Host ""
Write-Host "👉 BƯỚC TIẾP THEO: Push code lên GitHub" -ForegroundColor Cyan
Write-Host "   Chạy lệnh sau (nếu chưa push lần nào):" -ForegroundColor White
Write-Host "   git push -u origin main" -ForegroundColor Gray
Write-Host ""
Write-Host "👉 SAU ĐÓ: Deploy trên Render" -ForegroundColor Cyan
Write-Host "1. Truy cập: https://dashboard.render.com/" -ForegroundColor White
Write-Host "2. Chọn 'New +' -> 'Blueprint'" -ForegroundColor White
Write-Host "3. Kết nối với repository GitHub của bạn" -ForegroundColor White
Write-Host "4. Render sẽ tự động nhận diện file render.yaml" -ForegroundColor White
Write-Host "5. Nhấn 'Apply' để bắt đầu deploy" -ForegroundColor White
Write-Host ""
Write-Host "📄 Xem chi tiết hướng dẫn tại file RENDER_DEPLOYMENT.md" -ForegroundColor Yellow
