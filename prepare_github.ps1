# PowerShell script để chuẩn bị upload PO System lên GitHub cho Replit

Write-Host "🚀 Chuẩn bị upload PO System lên GitHub..." -ForegroundColor Green

# Kiểm tra git
try {
    git --version | Out-Null
    Write-Host "✅ Git đã được cài đặt" -ForegroundColor Green
} catch {
    Write-Host "❌ Git không được cài đặt. Vui lòng cài đặt Git trước." -ForegroundColor Red
    exit 1
}

# Khởi tạo git repository nếu chưa có
if (!(Test-Path ".git")) {
    Write-Host "📁 Khởi tạo Git repository..." -ForegroundColor Yellow
    git init
    git branch -M main
}

# Thêm tất cả files
Write-Host "📦 Thêm files vào Git..." -ForegroundColor Yellow
git add .

# Commit
Write-Host "💾 Commit changes..." -ForegroundColor Yellow
git commit -m "Initial commit - PO System configured for Replit deployment

- Added Replit configuration files (.replit, replit.nix)
- Updated requirements.txt (removed xlwings, added openpyxl)
- Created main.py as entry point
- Fixed all localhost URLs to 0.0.0.0 for Replit compatibility
- Added openpyxl methods to replace xlwings functionality
- Updated .gitignore for Replit deployment
- Added comprehensive README.md and deployment guide"

Write-Host "✅ Chuẩn bị hoàn tất!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Các bước tiếp theo:" -ForegroundColor Cyan
Write-Host "1. Tạo repository mới trên GitHub" -ForegroundColor White
Write-Host "2. Thêm remote origin:" -ForegroundColor White
Write-Host "   git remote add origin https://github.com/yourusername/po-system-replit.git" -ForegroundColor Gray
Write-Host "3. Push code:" -ForegroundColor White
Write-Host "   git push -u origin main" -ForegroundColor Gray
Write-Host "4. Import vào Replit từ GitHub URL" -ForegroundColor White
Write-Host ""
Write-Host "📁 Các file quan trọng đã được tạo/sửa:" -ForegroundColor Cyan
Write-Host "- main.py (entry point cho Replit)" -ForegroundColor White
Write-Host "- .replit (Replit configuration)" -ForegroundColor White
Write-Host "- replit.nix (Nix packages)" -ForegroundColor White
Write-Host "- requirements.txt (updated dependencies)" -ForegroundColor White
Write-Host "- README.md (documentation)" -ForegroundColor White
Write-Host "- REPLIT_DEPLOYMENT.md (deployment guide)" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  Lưu ý: Đảm bảo folder 'products/' được upload đầy đủ!" -ForegroundColor Red
Write-Host "   Folder này chứa templates Excel và config sản phẩm." -ForegroundColor Red
