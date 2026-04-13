# EQ 改作業小幫手

在 Mac Mini 上完全本地運行的 AI 改作業系統，專為國小 EQ（情緒教育）練習設計。

學生填寫練習 → AI 自動生成老師評語 → 老師可審閱修改。預設所有資料與模型都在你的 Mac 上，不經過任何雲端。

## 功能

- **學生端**：選擇問卷 → 填寫答案 → 收到老師評語
- **老師端**：瀏覽所有作答 → 查看 AI 評語 → 展開 AI 分析細節（5 維度分數、優缺點）→ 修改評語
- **AI 三階段評分**：理解 → 結構化評估 → 自然語言評語
- **可擴充問卷**：新增 YAML 檔即可，不用改程式碼
- **Google 帳號登入 + 角色審核**：新帳號預設為學生，需由 super user 升級為老師後才能使用老師端
- **Gemini API 評語**：Stage 3 評語可選用 Google Gemini，口語更自然（選配）
- **PostgreSQL 支援**：可切換到 LAN PostgreSQL 資料庫（選配）

### 支援的問卷


| 問卷          | 學生填寫內容              |
| ----------- | ------------------- |
| 情緒ABC練習     | 事件、情緒、想法            |
| EQ練功房：想法心手把 | 事件 + 8格情緒轉盤（含平靜與希望） |


---

## 系統需求


| 項目     | 最低需求                     | 建議                   |
| ------ | ------------------------ | -------------------- |
| 電腦     | Apple Silicon Mac（M1 以上） | Mac Mini M2 Pro / M4 |
| RAM    | 16GB（可跑但較慢）              | 32GB                 |
| macOS  | 13 Ventura 以上            | 最新版本                 |
| 磁碟空間   | 15GB（模型 + 程式）            | 20GB+                |
| Python | 3.11+                    | 3.12                 |


---

## 安裝步驟

### Step 1：安裝 Homebrew（如果還沒有的話）

打開「終端機」（在 Launchpad 搜尋「Terminal」），貼上：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

安裝完成後，按照畫面上的指示把 Homebrew 加入 PATH（通常會提示你執行兩行指令）。

### Step 2：安裝 Python

```bash
brew install python@3.12
```

驗證：

```bash
python3 --version
# 應顯示 Python 3.12.x 或更新
```

### Step 3：安裝 Ollama

方法一：用 Homebrew 安裝

```bash
brew install ollama
```

方法二：直接下載

1. 前往 [https://ollama.com/download](https://ollama.com/download)
2. 下載 Mac 版本
3. 打開 .dmg 檔，將 Ollama 拖進「應用程式」
4. 首次打開 Ollama 應用程式（它會在選單列出現一個小圖示）

驗證：

```bash
ollama --version
# 應顯示版本號
```

### Step 4：啟動 Ollama 服務

```bash
ollama serve
```

> 如果你是用方法二（下載 .dmg）安裝的，打開 Ollama 應用程式後服務就會自動啟動，不需要手動執行這個指令。
>
> 服務啟動後，這個終端機視窗會持續運行。**請另開一個新的終端機視窗**繼續以下步驟。

### Step 5：下載 AI 模型

```bash
# 主模型（約 8GB，首次下載需 10-30 分鐘）
ollama pull qwen2.5:14b
```

下載完成後驗證：

```bash
ollama list
# 應該會看到 qwen2.5:14b
```

> **RAM 只有 16GB？** 改用較小的模型：
>
> ```bash
> ollama pull qwen2.5:7b
> ```
>
> 然後在 `.env` 中將 `OLLAMA_MODEL` 改為 `qwen2.5:7b`。

### Step 6：安裝專案

```bash
# 進入專案目錄
cd ~/Desktop/ActiveKM/eq-grader

# 建立 Python 虛擬環境
python3 -m venv venv

# 啟動虛擬環境
source venv/bin/activate

# 安裝 Python 套件
pip install -r requirements.txt
```

或者直接用一鍵安裝腳本（會自動完成 Step 4-6）：

```bash
cd ~/Desktop/ActiveKM/eq-grader
bash setup.sh
```

### Step 7：設定環境變數

複製範例設定檔：

```bash
cp .env.example .env
```

預設值即可直接使用。如需自訂，用文字編輯器打開 `.env`：

```bash
open -e .env
```

可調整的設定：


| 設定                     | 預設值                            | 說明                         |
| ---------------------- | ------------------------------ | -------------------------- |
| `OLLAMA_BASE_URL`      | `http://localhost:11434`       | Ollama 服務位址                |
| `OLLAMA_MODEL`         | `qwen2.5:14b`                  | 使用的 LLM 模型                 |
| `DATABASE_URL`         | `sqlite:///./eq_grader.db`     | 資料庫連線（支援 PostgreSQL）       |
| `GEMINI_API_KEY`       | （空，停用）                         | 填入後 Stage 3 評語改走 Gemini    |
| `GEMINI_MODEL`         | `gemini-2.0-flash`             | Gemini 模型                  |
| `GOOGLE_CLIENT_ID`     | （空，停用）                         | Google OAuth Client ID     |
| `GOOGLE_CLIENT_SECRET` | （空，停用）                         | Google OAuth Client Secret |
| `SUPER_USER_EMAIL`     | `jenghan.hsieh@gmail.com`            | super user 帳號（可管理使用者角色） |
| `APP_BASE_URL`         | `http://localhost:8000`        | 部署用的 Base URL              |
| `SESSION_SECRET`       | `change-me-to-a-random-string` | Session 加密密鑰（正式環境請更換）      |


### Step 8：啟動應用

```bash
# 確保在虛擬環境中（前面有 (venv) 字樣）
source venv/bin/activate

# 啟動伺服器
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

看到類似以下訊息就代表成功：

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Started reloader process
```

### Step 9：開始使用

打開瀏覽器：


| 頁面   | 網址                                                             |
| ---- | -------------------------------------------------------------- |
| 學生填答 | [http://localhost:8000](http://localhost:8000)                 |
| 老師審閱 | [http://localhost:8000/teacher](http://localhost:8000/teacher) |
| 系統狀態 | [http://localhost:8000/health](http://localhost:8000/health)   |


---

## 日常使用

每次要用的時候，只需要：

```bash
# 1. 確保 Ollama 在運行（如果用 app 版，打開應用即可）
ollama serve

# 2. 另開終端機，啟動專案
cd ~/Desktop/ActiveKM/eq-grader
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. 開瀏覽器 → http://localhost:8000
```

要停止服務：在終端機按 `Ctrl + C`。

---

## AI 評分流程

```
學生答案
  ↓
Stage 1: 理解 ─── LLM 解析答案，產出結構化理解          [Ollama]
  ↓
Stage 2: 評估 ─── 根據評分規準打分（5 維度，各 1-5 分）  [Ollama]
  ↓
Stage 3: 評語 ─── 生成溫暖鼓勵的老師評語（80-150 字）   [Ollama 或 Gemini]
  ↓
老師審閱（可修改）→ 學生看到最終評語
```

學生只會看到自己的答案和老師評語。AI 的結構化評分與分析僅供老師參考（預設收合，點擊展開）。

### Gemini 評語（選配）

如果覺得 Ollama 本地模型的評語不夠自然，可以讓 Stage 3 改走 Google Gemini：

1. 取得 [Gemini API Key](https://aistudio.google.com/apikey)
2. 在 `.env` 填入：
  ```
   GEMINI_API_KEY=your-api-key-here
  ```
3. 重啟服務即生效。Stage 1+2 仍走本地 Ollama（JSON 結構化輸出穩定），Stage 3 走 Gemini（口語更自然）

---

## Google 登入（選配）

啟用後，老師端（`/teacher`）需要使用 Google 帳號登入才能進入。學生端不受影響。

帳號角色規則如下：

1. 新使用者第一次 Google 登入後，預設為「學生」角色（只能使用學生功能）
2. `SUPER_USER_EMAIL`（預設 `jenghan.hsieh@gmail.com`）登入後自動成為 `super user`
3. `super user` 可在「使用者清單」（`/teacher/users`）將指定帳號升級為「老師」
4. 只有「老師」與 `super user` 可以使用老師端功能

每次登入都會記錄到 `login_record` 資料表（email、IP、時間）。

### 快速設定

1. 到 Google Cloud Console 建立 OAuth 憑證
2. 在 `.env` 填入 Client ID 和 Secret：
  ```
   GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=xxxxx
  ```
3. 重啟服務，Nav 會出現「Google 登入」按鈕

> 完整圖文步驟請參考 `[docs/google-oauth-setup.md](docs/google-oauth-setup.md)`

---

## PostgreSQL 資料庫（選配）

預設使用 SQLite（零設定）。如需切換到 LAN 上的 PostgreSQL：

在 `.env` 中修改：

```
DATABASE_URL=postgresql://user:password@192.168.x.x:5432/eq_grader
```

重啟服務即可。所有資料模型完全相容，不需改任何程式碼。

---

## 模型替換


| 情境           | 建議模型          | RAM 需求 | 安裝指令                      |
| ------------ | ------------- | ------ | ------------------------- |
| 32GB Mac（預設） | `qwen2.5:14b` | ~10GB  | `ollama pull qwen2.5:14b` |
| 16GB Mac     | `qwen2.5:7b`  | ~5GB   | `ollama pull qwen2.5:7b`  |
| 台灣在地化口吻      | `taide:8b`    | ~5GB   | `ollama pull taide:8b`    |


切換模型：修改 `.env` 中的 `OLLAMA_MODEL`，重啟服務。

---

## 新增問卷

在 `questionnaires/` 建立 YAML 檔，重啟服務即自動載入：

```yaml
id: my_new_quiz
name: 我的新問卷
description: 問卷說明
instructions: |
  給學生的作答指示

schema:
  fields:
    - name: field_name
      type: text          # text 或 emotion_wheel
      label: 顯示標籤
      placeholder: 提示文字
      required: true

rubric:
  completeness:
    "5": 滿分描述
    "1": 最低分描述
  # ... 其他維度

feedback_style:
  tone: 溫暖、鼓勵
  guidelines:
    - 先肯定優點
    - 用鼓勵語氣建議改進
  examples:
    - |
      範例評語...
```

---

## 專案結構

```
eq-grader/
├── app/
│   ├── main.py              # FastAPI 入口 + middleware
│   ├── config.py            # 環境變數設定（讀 .env）
│   ├── database.py          # 資料庫引擎（SQLite / PostgreSQL）
│   ├── models.py            # 資料模型（含 User、LoginRecord）
│   ├── llm/
│   │   ├── client.py        # Ollama HTTP client
│   │   ├── gemini_client.py # Gemini API client
│   │   ├── prompts.py       # 三階段 prompt 模板
│   │   └── pipeline.py      # 評分管線（自動選引擎）
│   ├── routers/
│   │   ├── student.py       # 學生路由
│   │   ├── teacher.py       # 老師路由（含登入保護）
│   │   └── auth.py          # Google OAuth 登入/登出
│   ├── templates/           # Jinja2 HTML 模板
│   └── static/              # CSS
├── questionnaires/          # 問卷定義（YAML）
│   ├── emotion_abc.yaml     # 情緒ABC練習
│   └── eq_thought_handle.yaml  # 想法心手把
├── docs/
│   └── google-oauth-setup.md  # Google OAuth 設定指南
├── .env.example             # 環境變數範本
├── .gitignore
├── requirements.txt
├── setup.sh                 # 一鍵安裝腳本
└── README.md
```

## 技術棧

- **Backend**: Python FastAPI + SQLModel + SQLite（可切 PostgreSQL）
- **Frontend**: Jinja2 模板 + 原生 CSS
- **LLM**: Ollama（本地推論）/ Gemini API（選配）
- **認證**: Google OAuth2 + Starlette Session（選配）
- **預設模型**: Qwen2.5-14B（Q4 量化）

---

## 常見問題

**Q: 啟動時報錯 "Connection refused"**
A: Ollama 服務沒在運行。執行 `ollama serve` 或打開 Ollama 應用程式。

**Q: AI 回覆很慢**
A: 14B 模型在 32GB Mac 上大約 15-20 tok/s，一次評分需 30-60 秒。如果太慢可改用 7B 模型。

**Q: 想重置所有資料**
A: 刪除 `eq_grader.db` 檔案，重啟服務會自動建立空的資料庫。

**Q: 區域網路內其他電腦可以連嗎？**
A: 可以。啟動時已設定 `--host 0.0.0.0`，其他電腦用 `http://你的Mac的IP:8000` 即可連入。用 `ifconfig | grep inet` 查看 IP。

**Q: Google 登入按鈕沒有出現**
A: 確認 `.env` 中 `GOOGLE_CLIENT_ID` 和 `GOOGLE_CLIENT_SECRET` 都有填入，且前面沒有 `#` 註解符號。修改後須重啟服務。

**Q: 登入時出現 "redirect_uri_mismatch"**
A: Google Cloud Console 中設定的「已授權的重新導向 URI」與實際存取的網址不符。確認有加入 `http://localhost:8000/auth/callback`（以及 LAN IP 版本）。

**Q: 如何切換到 PostgreSQL？**
A: 在 `.env` 中將 `DATABASE_URL` 改為 `postgresql://user:pass@host:5432/dbname`，重啟服務即可。首次連線會自動建立所有資料表。