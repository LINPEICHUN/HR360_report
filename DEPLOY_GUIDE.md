# 360 度回饋分析系統 - 企業內網部署指南 (IT 專用)

本文件專為 IT / 系統管理人員設計，用以將「360 度回饋分析系統」部署於公司內部伺服器，供 HRBP 同仁使用。

本系統基於 **Python 3.12 + FastAPI** 架構開發，前端採用 HTML/CSS/JS (Jinja2 模板)，後端與 AI 大模型介接（達哥 GAISF / Gemini / OpenAI）。

---

## 一、 伺服器需求與環境準備

### 1. 系統需求
* **作業系統**：Windows Server (2016 或更新版本) 或 Linux (Ubuntu 20.04+)。本指南以 Windows Server 為主要說明。
* **網路權限**：
  * **出站限制 (Outbound)**：伺服器必須能夠連線至網際網路，以呼叫大模型 API（例如達哥平台 API 或是 Google Gemini API 終端節點）。
  * **入站限制 (Inbound)**：需對內網（Intranet）開放連線 Port（預設為 `8000`），允許同仁透過瀏覽器連線。
* **基本軟體**：
  * **Git** (用於程式碼版本同步)
  * **Python 3.12+** (請確保安裝時有勾選 `Add Python to PATH`)

---

## 二、 部署步驟

### 步驟 1：取得專案原始碼
以管理員權限開啟命令提示字元 (CMD) 或 PowerShell，切換至部署目錄，並拉取專案程式碼：
```powershell
git clone https://github.com/LINPEICHUN/HR360_report.git
cd HR360_report
```

### 步驟 2：初始化 Python 虛擬環境
本專案採用 `uv` 作為套件與虛擬環境管理工具，以確保依賴套件版本的嚴格一致。
1. 安裝 `uv`：
   ```powershell
   pip install uv
   ```
2. 還原專案依賴（這會自動建立 `.venv` 虛擬環境並安裝所有套件）：
   ```powershell
   uv sync
   ```

### 步驟 3：設定管理員預設 API 金鑰
為了讓 HRBP 同仁免除手動設定 API 金鑰的繁瑣步驟，請直接在伺服器端配置預設的 API 資訊。
編輯專案目錄下的 `app/admin_config.json` 檔案：
```json
{
  "api_provider": "davinci",
  "api_key": "YOUR_COMPANY_DAVINCI_JWT_KEY",
  "model": "gpt-4o-mini"
}
```
* **api_provider**：填入 `"davinci"` (達哥平台) 或 `"gemini"` (Google Gemini)。
* **api_key**：填入達哥平台的 JWT 金鑰，或者對應平台的 API 憑證。
* **model**：預設使用的模型名稱。

### 步驟 4：進行本機啟動測試
在專案根目錄下，使用虛擬環境中的 `uvicorn` 啟動服務：
```powershell
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```
啟動後，請在伺服器本機打開瀏覽器，測試連線 `http://localhost:8000`，並確保能看到 360 分析系統的登入與設定首頁。

---

## 三、 將系統註冊為 Windows 背景服務 (防中斷)

為了避免手動開啟的黑框視窗被不小心關閉，或伺服器重啟後服務失效，推薦使用 [NSSM (Non-Sucking Service Manager)](https://nssm.cc/) 將 FastAPI 註冊為 Windows 系統服務。

1. **下載 NSSM**：至官網下載並解壓縮，將對應架構的 `nssm.exe` 放於方便執行的目錄下。
2. **註冊服務**：以管理員身分開啟 PowerShell，執行：
   ```powershell
   nssm install HR360ReportService
   ```
3. **在 NSSM 視窗中設定**：
   * **Path**：指向專案資料夾內虛擬環境的 python 執行檔，例如：
     `C:\DeployPath\HR_360_Report\.venv\Scripts\python.exe`
   * **Arguments**：`-m uvicorn app.main:app --host 0.0.0.0 --port 8000`
   * **Startup directory**：填入專案的根目錄路徑，例如：
     `C:\DeployPath\HR_360_Report`
4. **安裝與啟動**：
   * 點擊 **Install service** 完成註冊。
   * 開啟 Windows 的「服務 (services.msc)」，找到 `HR360ReportService`。
   * 將其啟動類型設為「自動」，並點選「啟動」服務。

---

## 四、 防火牆設定

為了讓同仁能夠順利連線，請在 Windows 防火牆（或雲端安全組）新增一條規則：
1. **通訊協定**：TCP
2. **連接埠 (Port)**：`8000` (或您在啟動參數中指定的 Port)
3. **動作**：允許連線
4. **範圍**：建議限制在公司內部網段 (例如 `10.0.0.0/8` 或 `192.168.0.0/16`)，保障安全。

---

## 五、 後續維護與更新

當系統有功能更新時，只需要在伺服器端執行以下指令：
1. 以管理員身分開啟 PowerShell，進入專案目錄：
   ```powershell
   cd C:\DeployPath\HR_360_Report
   ```
2. 拉取最新代碼：
   ```powershell
   git pull origin main
   ```
3. 更新依賴套件（若有異動）：
   ```powershell
   uv sync
   ```
4. 重啟 Windows 服務即可生效：
   ```powershell
   Restart-Service -Name "HR360ReportService"
   ```
