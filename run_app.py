"""
360 度回饋分析系統 - EXE 啟動入口
"""
import sys
import os
import time
import webbrowser
import threading
from pathlib import Path
import uvicorn

# 處理 PyInstaller 的 sys.path 以防 import 問題
if hasattr(sys, '_MEIPASS'):
    sys.path.insert(0, sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent
    sys.path.insert(0, str(BASE_DIR))

# 在 sys.path 修改後再 import 我們的 FastAPI app
from app.main import app

def open_browser():
    """啟動後延遲自動開啟瀏覽器"""
    time.sleep(1.5)
    url = "http://127.0.0.1:8000"
    print(f"[*] 正在自動開啟瀏覽器至: {url}")
    webbrowser.open(url)

def main():
    # 啟動自動開啟瀏覽器的背景執行緒
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    print("[*] 正在啟動 360 度回饋分析系統服務...")
    print("[*] 服務啟動後，請不要關閉此視窗。")
    print("[*] 若要停止服務，請直接關閉此視窗或在視窗中按下 Ctrl+C。")
    
    # 直接傳遞 app 物件，避免 uvicorn 因為 sys.path 問題找不到 "app.main:app"
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
    except Exception as e:
        print("\n" + "="*60)
        print("[ERROR] 服務啟動失敗！")
        if "10048" in str(e) or (hasattr(e, 'errno') and e.errno == 10048):
            print("\n-> 錯誤原因: 8000 端口已被佔用！")
            print("   這表示系統可能已經在後台運行中，或是其他程式佔用了這個通訊埠。")
            print("   請先關閉所有已開啟的 360 度回饋分析系統，或者在 Windows 工作管理員結束該進程。")
        else:
            print(f"\n-> 錯誤原因: {e}")
        print("="*60)
        input("\n請按 [Enter] 鍵結束此視窗...")


if __name__ == "__main__":
    main()
