# 改作業 AI — 系統架構規劃書

## 一、系統概覽

```
┌─────────────────────────────────────────────────────┐
│                    Mac Mini (M2/M4, 32GB)            │
│                                                       │
│  ┌──────────┐   ┌──────────────┐   ┌──────────────┐ │
│  │ Web UI   │──▶│ FastAPI      │──▶│ Ollama/MLX   │ │
│  │ (Next.js)│◀──│ Backend      │◀──│ LLM Engine   │ │
│  └──────────┘   └──────┬───────┘   └──────────────┘ │
│                        │                              │
│              ┌─────────┴──────────┐                   │
│              │                    │                    │
│        ┌─────▼─────┐      ┌──────▼──────┐            │
│        │ SQLite    │      │ ChromaDB    │            │
│        │ (資料庫)  │      │ (RAG向量庫) │            │
│        └───────────┘      └─────────────┘            │
└─────────────────────────────────────────────────────┘
```

## 二、Data Flow（資料流）

```
學生填寫答案 → 前端表單
        ↓
後端接收 → 存入 SQLite (raw answer)
        ↓
┌─── Stage 1: 理解與結構化 ───┐
│  RAG 注入: 問卷 schema + 評分規準    │
│  LLM 解析學生答案, 生成結構化理解      │
└──────────────┬───────────────┘
               ↓
┌─── Stage 2: 評估與評分 ───┐
│  RAG 注入: 範例答案 + 評分標準         │
│  LLM 生成:                            │
│    - student_self_reflection (內部)    │
│    - teacher_feedback.scores (內部)    │
│    - teacher_feedback.overall (內部)   │
└──────────────┬───────────────┘
               ↓
┌─── Stage 3: 生成老師評語 ───┐
│  基於 Stage 2 的結構化評估             │
│  LLM 生成溫暖、具體、鼓勵性的老師評語   │
│  → 這是學生唯一看到的 AI 輸出          │
└──────────────┬───────────────┘
               ↓
老師審閱/修改 (optional) → 學生看到最終評語
```

## 三、模型選擇（關鍵決策）

| 層級 | 推薦模型 | 備選 | 理由 |
|---|---|---|---|
| **主 LLM** | **Qwen2.5-14B-Instruct** (Q4_K_M) | Qwen3-14B | 中文能力最強的開源模型之一，JSON 結構化輸出穩定，14B Q4 約需 ~10GB RAM，Mac Mini 32GB 綽綽有餘 |
| **台灣在地化** | **Gemma-3-TAIDE-12b-Chat** | Llama3.1-TAIDE-LX-8B | 國科會 TAIDE 計畫，專為台灣繁體中文訓練，更懂台灣教育語境 |
| **Embedding** | **BAAI/bge-m3** | GTE-multilingual | 多語言嵌入模型，中文效果極佳，支援 local 部署 |
| **推論引擎** | **Ollama** (開發/簡單) | MLX (效能最佳) | Ollama 一鍵部署最方便；MLX 吞吐量最高但需更多設定 |

### 模型策略建議：雙模型方案

- **Qwen2.5-14B**: 負責 Stage 1 & 2（理解 + 結構化評分），JSON output 穩定
- **TAIDE-12B**: 負責 Stage 3（生成老師評語），台灣口吻更自然

如果不想管兩個模型，單用 **Qwen2.5-14B** 即可 cover 全部。

### Mac Mini 32GB 效能估算

| 模型 | 量化 | RAM 佔用 | 推估速度 (tok/s) |
|---|---|---|---|
| Qwen2.5-14B | Q4_K_M | ~10 GB | ~15-20 tok/s |
| TAIDE-12B | Q4_K_M | ~8 GB | ~18-25 tok/s |
| bge-m3 | FP16 | ~2 GB | batch 即時 |
| **合計** | | **~20 GB** | 留 12GB 給系統 |

## 四、RAG 計畫

### 4.1 需要 RAG 的內容

| 文件類型 | 用途 | 更新頻率 |
|---|---|---|
| **問卷 Schema** | 每種問卷的結構定義（欄位、型別、驗證規則） | 新增問卷時 |
| **評分規準 (Rubric)** | 各維度的 1-5 分標準描述 | 老師可調整 |
| **範例答案 + 評估** | 優秀/良好/待加強的標註範例 | 持續累積 |
| **老師評語風格範本** | 溫暖鼓勵的評語寫法參考 | 老師可自訂 |
| **情緒詞彙表** | 適合國小生的情緒詞彙 & 顏色對應 | 半固定 |

### 4.2 RAG 架構

```
┌──── 文件處理 ────┐
│ Markdown/JSON    │
│ 問卷定義檔       │──→ Text Splitter ──→ bge-m3 Embedding
│ 評分規準         │                          ↓
│ 範例答案集       │                    ChromaDB (持久化)
└──────────────────┘                          ↓
                                        Query 時
                                          ↓
                           ┌─── Retriever ───┐
                           │ 1. 根據問卷類型篩選    │
                           │ 2. 根據學生答案相似度   │
                           │ 3. Top-K 取回相關規準   │
                           └─────────┬───────┘
                                     ↓
                              注入 LLM Prompt
```

### 4.3 RAG vs 純 Prompt 的判斷

對於這個場景，**兩種問卷的 schema 相對固定**，所以：

- **Stage 1 & 2**：RAG 注入評分規準 + 相似範例答案（真正有價值）
- **Stage 3**：RAG 注入老師評語風格範本
- **問卷 Schema**：因為只有 2 種，直接寫在 System Prompt 中更穩定（不需要 RAG）

**簡言之：小規模先用 Structured Prompt Template，規準和範例多了再上 RAG。**

## 五、技術棧

```
Frontend:  Next.js 14+ (App Router) 或 純 HTML + HTMX（更輕量）
Backend:   Python FastAPI
Database:  SQLite (透過 SQLModel/SQLAlchemy)
Vector DB: ChromaDB (local persistent mode)
LLM:       Ollama (REST API on localhost:11434)
Embedding: bge-m3 via Ollama 或 sentence-transformers
```

## 六、資料模型

```python
# 問卷模板 (可擴充新問卷)
class QuestionnaireTemplate:
    id: str                    # e.g. "emotion_abc", "eq_thought_handle"
    name: str                  # "情緒ABC練習"
    description: str
    schema: dict               # JSON Schema 定義學生需填的欄位
    rubric: dict               # 評分規準 (各維度的 1-5 分標準)
    system_prompt: str         # 該問卷專用的 LLM system prompt
    example_answers: list      # 標註過的範例答案

# 學生作答
class StudentSubmission:
    id: str
    questionnaire_id: str      # FK → QuestionnaireTemplate
    student_id: str
    student_name: str
    raw_answer: dict           # 學生填的原始 JSON
    created_at: datetime

# AI 評估結果
class AIEvaluation:
    id: str
    submission_id: str         # FK → StudentSubmission
    student_self_reflection: dict  # AI 模擬的學生自評 (內部)
    teacher_scores: dict           # 結構化評分 (內部)
    teacher_comment: str           # 老師評語 (學生可見!)
    raw_llm_output: dict           # 完整 LLM 回傳 (debug 用)
    reviewed_by_teacher: bool      # 老師是否已審閱
    teacher_override: str | None   # 老師修改後的評語
    created_at: datetime

# 最終呈現給學生的
class StudentView:
    # → student_raw_answer       # 你寫的答案
    # → final_comment            # teacher_override or teacher_comment
    pass
```

## 七、Prompt Engineering 策略

### 三階段 Pipeline（推薦）

```
Stage 1: 理解 (Understanding)
─────────────────────────────
System: 你是國小EQ教育專家。分析以下學生答案。
Context: {問卷schema} + {學生答案}
Task: 結構化描述學生答了什麼、理解程度如何
Output: JSON (structured understanding)

Stage 2: 評估 (Evaluation)
─────────────────────────────
System: 根據以下評分規準，評估學生的答案。
Context: {評分規準} + {相似範例} + {Stage 1 output}
Task: 生成 scores + self_reflection + strengths/weaknesses
Output: JSON (structured evaluation)

Stage 3: 評語生成 (Feedback Generation)
─────────────────────────────
System: 你是一位溫暖鼓勵的國小老師，正在寫評語給學生。
Context: {Stage 2 evaluation} + {評語風格範本}
Task: 用口語、親切的方式寫一段評語
Rules:
  - 先肯定做得好的地方
  - 具體指出可以進步的方向
  - 用「你可以試試看...」而非「你做錯了...」
  - 長度 80-150 字
Output: 純文字評語
```

### 為什麼三階段而非單次？

1. 結構化評分和自然語言評語是不同任務，分開做品質更好
2. 中間結果可以 debug / audit
3. 老師可以看到評分依據，不只是最終評語
4. 如果評語不好，只需重跑 Stage 3

## 八、可擴充性設計

新增問卷類型 **不需改程式碼**：

```yaml
# questionnaires/emotion_abc.yaml
id: emotion_abc
name: 情緒ABC練習
schema:
  fields:
    - name: event
      type: text
      label: 發生了什麼事？（事件）
      required: true
    - name: emotion
      type: text
      label: 你當時的感覺是什麼？（情緒）
      required: true
    - name: thought
      type: text
      label: 你心裡在想什麼？（想法）
      required: true

rubric:
  completeness: "5分=所有欄位完整填寫且有實質內容..."
  depth: "5分=能深入反思情緒與想法的連結..."
  # ...

system_prompt: |
  你是資深國小EQ教育專家...

example_answers:
  - file: examples/emotion_abc_excellent.json
  - file: examples/emotion_abc_needs_improvement.json
```

**新增問卷 = 新增一個 YAML 檔 + 幾個範例答案。**

## 九、需要準備的東西

| 類別 | 項目 | 說明 |
|---|---|---|
| **硬體** | Mac Mini M2 Pro/M4 32GB | 最低 16GB 可跑但會慢 |
| **軟體** | Ollama | `brew install ollama` |
| | Python 3.11+ | Backend runtime |
| | Node.js 20+ | Frontend (如果用 Next.js) |
| | ChromaDB | `pip install chromadb` |
| **模型** | Qwen2.5-14B | `ollama pull qwen2.5:14b` |
| | TAIDE-12B (optional) | 從 HuggingFace 下載 GGUF |
| | bge-m3 | `ollama pull bge-m3` 或 pip |
| **教育內容** | 評分規準文件 | 每個維度的 1-5 分標準 (需老師定義) |
| | 範例答案集 | 每個問卷 5-10 個標註過的範例 |
| | 評語風格指南 | 老師期望的評語口吻/風格 |

## 十、建議的開發順序

```
Phase 1 (MVP - 1-2 週)
├── Ollama + Qwen2.5-14B 部署測試
├── 單一問卷 (情緒ABC) 的 Prompt Pipeline
├── FastAPI 後端 + SQLite
└── 極簡前端 (學生填答 + 看評語)

Phase 2 (完整功能 - 2-3 週)
├── 第二種問卷 (想法心手把) 支援
├── YAML-based 問卷擴充系統
├── ChromaDB RAG (評分規準 + 範例)
├── 老師審閱/修改介面
└── 品質調校 (prompt tuning)

Phase 3 (進階 - 選做)
├── 批次改作業功能
├── 學生歷史紀錄 & 進步追蹤
├── TAIDE 雙模型方案
└── 匯出報表 (PDF/Excel)
```

## 十一、風險與對策

| 風險 | 對策 |
|---|---|
| LLM 評分不一致 | Few-shot examples in prompt + RAG 注入標註範例 |
| 評語語氣不當 | Stage 3 prompt 明確限制 + 老師審閱機制 |
| 14B 模型速度不夠 | 降級到 7B (Qwen2.5-7B) 或 TAIDE-8B |
| JSON 輸出格式錯誤 | Ollama `format: json` 參數 + 後端 retry 機制 |
| 繁體中文品質 | TAIDE 模型兜底 / prompt 中強調「使用台灣繁體中文」 |
