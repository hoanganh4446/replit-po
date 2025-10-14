#!/bin/bash

# Script để chuẩn bị upload PO System lên GitHub cho Replit

echo "🚀 Chuẩn bị upload PO System lên GitHub..."

# Kiểm tra git
if ! command -v git &> /dev/null; then
    echo "❌ Git không được cài đặt. Vui lòng cài đặt Git trước."
    exit 1
fi

# Khởi tạo git repository nếu chưa có
if [ ! -d ".git" ]; then
    echo "📁 Khởi tạo Git repository..."
    git init
    git branch -M main
fi

# Thêm tất cả files
echo "📦 Thêm files vào Git..."
git add .

# Commit
echo "💾 Commit changes..."
git commit -m "Initial commit - PO System configured for Replit deployment

- Added Replit configuration files (.replit, replit.nix)
- Updated requirements.txt (removed xlwings, added openpyxl)
- Created main.py as entry point
- Fixed all localhost URLs to 0.0.0.0 for Replit compatibility
- Added openpyxl methods to replace xlwings functionality
- Updated .gitignore for Replit deployment
- Added comprehensive README.md and deployment guide"

echo "✅ Chuẩn bị hoàn tất!"
echo ""
echo "📋 Các bước tiếp theo:"
echo "1. Tạo repository mới trên GitHub"
echo "2. Thêm remote origin:"
echo "   git remote add origin https://github.com/yourusername/po-system-replit.git"
echo "3. Push code:"
echo "   git push -u origin main"
echo "4. Import vào Replit từ GitHub URL"
echo ""
echo "📁 Các file quan trọng đã được tạo/sửa:"
echo "- main.py (entry point cho Replit)"
echo "- .replit (Replit configuration)"
echo "- replit.nix (Nix packages)"
echo "- requirements.txt (updated dependencies)"
echo "- README.md (documentation)"
echo "- REPLIT_DEPLOYMENT.md (deployment guide)"
echo ""
echo "⚠️  Lưu ý: Đảm bảo folder 'products/' được upload đầy đủ!"
echo "   Folder này chứa templates Excel và config sản phẩm."
