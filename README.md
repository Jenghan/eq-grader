# EQ 改作業小幫手

在 Mac Mini 上完全本地運行的 AI 改作業系統，專為國小 EQ（情緒教育）練習設計。

學生填寫練習 → AI 自動生成老師評語 → 老師可審閱修改。所有資料與模型都在你的 Mac 上，不經過任何雲端。

## 功能

- **學生端**：選擇問卷 → 填寫答案 → 收到老師評語
- **老師端**：瀏覽所有作答 → 查看 AI 評分細節（5 維度分數、優缺點分析）→ 修改評語
- **AI 三階段評分**：理解 → 結構化評估 → 自然語言評語
- **可擴充問卷**：新增 YAML 檔即可，不用改程式碼

### 支援的問卷

| 問卷 | 學生填寫內容 |
|---|---|
| 情緒ABC練習 | 事件、情緒、想法 |
| EQ練功房：想法心手把 | 事件 + 8格情緒轉盤（含平靜與希望） |

---

## 系統需求

| 項目 | 最低需求 | 建議 |
|---|---|---|
| 電腦 | Apple Silicon Mac（M1 以上） | Mac Mini M2 Pro / M4 |
| RAM | 16GB（可跑但較慢） | 32GB |
| macOS | 13 Ventura 以上 | 最新版本 |
| 磁碟空間 | 15GB（模型 + 程式） | 20GB+ |
| Python | 3.11+ | 3.12 |

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

1. 前往 https://ollama.com/download
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
> ```bash
> ollama pull qwen2.5:7b
> ```
> 然後在 Step 7 啟動前，修改 `app/config.py` 裡的 `ollama_model` 為 `"qwen2.5:7b"`。

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

### Step 7：啟動應用

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

### Step 8：開始使用

打開瀏覽器：

| 頁面 | 網址 |
|---|---|
| 學生填答 | http://localhost:8000 |
| 老師審閱 | http://localhost:8000/teacher |
| 系統狀態 | http://localhost:8000/health |

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
Stage 1: 理解 ─── LLM 解析答案，產出結構化理解
  ↓
Stage 2: 評估 ─── 根據評分規準打分（完整性/正確性/深度/表達/適切性，各 1-5 分）
  ↓
Stage 3: 評語 ─── 生成溫暖鼓勵的老師評語（80-150 字）
  ↓
老師審閱（可修改）→ 學生看到最終評語
```

學生只會看到自己的答案和老師評語。AI 的結構化評分與分析僅供老師參考。

---

## 設定

### 環境變數

在 `app/config.py` 中修改：

| 設定 | 預設值 | 說明 |
|---|---|---|
| `ollama_base_url` | `http://localhost:11434` | Ollama 服務位址 |
| `ollama_model` | `qwen2.5:14b` | 使用的 LLM 模型 |
| `database_url` | `sqlite:///./eq_grader.db` | 資料庫位置 |

### 模型替換

| 情境 | 建議模型 | RAM 需求 | 安裝指令 |
|---|---|---|---|
| 32GB Mac（預設） | `qwen2.5:14b` | ~10GB | `ollama pull qwen2.5:14b` |
| 16GB Mac | `qwen2.5:7b` | ~5GB | `ollama pull qwen2.5:7b` |
| 台灣在地化口吻 | `taide:8b` | ~5GB | `ollama pull taide:8b` |

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
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 設定 + 載入問卷
│   ├── database.py          # SQLite 資料庫
│   ├── models.py            # 資料模型
│   ├── llm/
│   │   ├── client.py        # Ollama HTTP client
│   │   ├── prompts.py       # 三階段 prompt 模板
│   │   └── pipeline.py      # 評分管線
│   ├── routers/
│   │   ├── student.py       # 學生路由
│   │   └── teacher.py       # 老師路由
│   ├── templates/           # Jinja2 HTML 模板
│   └── static/              # CSS
├── questionnaires/          # 問卷定義（YAML）
│   ├── emotion_abc.yaml     # 情緒ABC練習
│   └── eq_thought_handle.yaml  # 想法心手把
├── requirements.txt
├── setup.sh                 # 一鍵安裝腳本
└── README.md
```

## 技術棧

- **Backend**: Python FastAPI + SQLModel + SQLite
- **Frontend**: Jinja2 模板 + 原生 CSS
- **LLM**: Ollama（本地推論）
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
