"""
Script khởi động nhanh cho hệ thống PO Web
Cung cấp các shortcut để chạy ứng dụng web
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_requirements():
    """Kiểm tra requirements"""
    print("🔍 Kiểm tra requirements...")
    
    try:
        import flask
        import xlwings
        print("✅ Flask và xlwings đã được cài đặt")
        
        # Kiểm tra pandas (không bắt buộc)
        try:
            import pandas
            print("✅ Pandas đã được cài đặt (tùy chọn)")
        except ImportError:
            print("ℹ️  Pandas không được cài đặt (không cần thiết)")
        
        return True
    except ImportError as e:
        print(f"❌ Thiếu package: {e}")
        print("💡 Chạy: pip install -r requirements_web.txt")
        return False

def check_templates():
    """Kiểm tra template files"""
    print("🔍 Kiểm tra template files...")
    
    base_dir = Path(__file__).parent
    template_dirs = [
        "LA800", "SV2000", "LA555", "UV730", "HX100", 
        "HD400", "LA700", "VX100", "LA480", "HP152"
    ]
    
    missing_templates = []
    for template_dir in template_dirs:
        template_path = base_dir / template_dir
        if not template_path.exists():
            missing_templates.append(template_dir)
    
    if missing_templates:
        print(f"⚠️ Thiếu thư mục template: {', '.join(missing_templates)}")
        print("💡 Đảm bảo các thư mục sản phẩm tồn tại")
    else:
        print("✅ Tất cả template directories tồn tại")
    
    return len(missing_templates) == 0

def create_directories():
    """Tạo các thư mục cần thiết"""
    print("📁 Tạo thư mục cần thiết...")
    
    directories = ["output", "templates", "static"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Thư mục {directory} đã sẵn sàng")

def start_web_app():
    """Khởi động ứng dụng web"""
    print("🚀 Khởi động ứng dụng web...")
    
    try:
        # Import và chạy app
        from app import app
        
        print("🌐 Ứng dụng web đang khởi động...")
        print("📱 Truy cập: http://0.0.0.0:5000")
        print("🔄 Nhấn Ctrl+C để dừng")
        print("-" * 50)
        
        # Mở trình duyệt sau 2 giây
        def open_browser():
            time.sleep(2)
            webbrowser.open('http://0.0.0.0:5000')
        
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Chạy app
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except Exception as e:
        print(f"❌ Lỗi khởi động: {e}")
        return False
    
    return True

def show_help():
    """Hiển thị trợ giúp"""
    print("🌐 HỆ THỐNG PO WEB - QUICK START")
    print("=" * 50)
    print("📋 CÁCH SỬ DỤNG:")
    print("  python web_start.py              # Chạy ứng dụng web")
    print("  python web_start.py --check      # Kiểm tra hệ thống")
    print("  python web_start.py --help       # Hiển thị trợ giúp")
    print()
    print("🔧 YÊU CẦU HỆ THỐNG:")
    print("  • Python 3.7+")
    print("  • Flask 2.3+")
    print("  • xlwings 0.30+")
    print("  • Microsoft Excel")
    print()
    print("📁 CẤU TRÚC:")
    print("  app.py                    - Ứng dụng Flask chính")
    print("  templates/               - HTML templates")
    print("  static/                  - CSS, JS, images")
    print("  output/                  - File Excel được tạo")
    print("  requirements_web.txt     - Python dependencies")
    print("=" * 50)

def check_system():
    """Kiểm tra hệ thống"""
    print("🔍 KIỂM TRA HỆ THỐNG")
    print("=" * 30)
    
    # Check Python version
    python_version = sys.version_info
    print(f"🐍 Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 7):
        print("❌ Cần Python 3.7+")
        return False
    else:
        print("✅ Python version OK")
    
    # Check requirements
    if not check_requirements():
        return False
    
    # Check templates
    if not check_templates():
        print("⚠️ Một số template có thể thiếu")
    
    # Check Excel
    try:
        import xlwings as xw
        app = xw.App(visible=False)
        app.quit()
        print("✅ Microsoft Excel OK")
    except Exception as e:
        print(f"❌ Microsoft Excel không khả dụng: {e}")
        return False
    
    print("✅ Hệ thống sẵn sàng!")
    return True

def main():
    """Hàm main"""
    args = sys.argv[1:]
    
    if '--help' in args or '-h' in args:
        show_help()
        return
    
    if '--check' in args:
        if check_system():
            print("\n🎉 Hệ thống đã sẵn sàng!")
        else:
            print("\n❌ Hệ thống chưa sẵn sàng!")
        return
    
    # Default: start web app
    print("🌐 HỆ THỐNG PO WEB - QUICK START")
    print("=" * 40)
    
    # Check system first
    if not check_system():
        print("\n❌ Hệ thống chưa sẵn sàng!")
        print("💡 Chạy 'python web_start.py --check' để kiểm tra chi tiết")
        return
    
    # Create directories
    create_directories()
    
    # Start web app
    print("\n🚀 Khởi động ứng dụng web...")
    start_web_app()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Tạm biệt!")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        input("⏸️ Nhấn Enter để thoát...")
