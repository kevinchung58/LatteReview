# LatteReview GUI 開發計畫與功能擴展 (TODO List)

## 專案前提與設定

*   **技術棧建議：** 使用 Python 的 Web 框架，如 Streamlit 或 Gradio。對於快速開發和資料科學應用，Streamlit 特別合適，因為它能讓您用純 Python 快速建立互動式介面。以下 TODO 會以 Streamlit 的概念來發想。
*   **LLM 固定模型：** 所有與 LLM 互動的部分，將預設使用 `gemini-2.0-flash`。這會簡化介面，使用者不需要在介面上選擇模型，只需要在設定中輸入自己的 Google AI/Vertex AI API Key 即可。

---

## Part 1: GUI 開發計畫 (TODO List)

目標：打造一個引導式、視覺化的操作流程，讓使用者從匯入文獻到看到審查結果一氣呵成。

[DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] ### 1.0 【基礎架構與主畫面】
*   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] **TODO 1.1: 建立 Streamlit 應用程式骨架**
    *   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] 細節:
*   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] **TODO 1.2: 設計專案管理介面**
    *   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] 細節:
*   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] **TODO 1.3: 全域 API Key 設定**
    *   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] 細節:

[DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] ### 2.0 【資料匯入與預覽介面】
*   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] **TODO 2.1: 實作 RIS 檔案上傳功能**
    *   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] 細節:
*   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] **TODO 2.2: 顯示匯入資料預覽**
    *   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] 細節:

[DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] ### 3.0 【工作流 (Workflow) 設定介面 - 核心部分】
[DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] 這是最複雜但也是最重要的部分。目標是將抽象的 Workflow Schema 轉化為視覺化的設定元件。
*   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] **TODO 3.1: 建立多回合 (Multi-round) 設定介面**
    *   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] 細節:
*   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] **TODO 3.2: 設計 Agent 設定器**
    *   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] 細節:
*   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] **TODO 3.3: 設定回合間的過濾邏輯**
    *   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] 細節:

[DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] ### 4.0 【審查執行與結果呈現介面】
*   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] **TODO 4.1: 執行與進度監控**
    *   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] 細節:
*   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] **TODO 4.2: 結果總覽與篩選**
    *   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] 細節:
*   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] **TODO 4.3: 單篇文章詳細結果視圖**
    *   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] 細節:
*   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] **TODO 4.4: 結果匯出功能**
    *   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] 細節:
        *   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] CSV 格式：包含所有欄位，方便用 Excel 或其他軟體分析。
        *   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] RIS 格式：將審查結果（如 Decision: Included）寫入到每篇文章的 notes 或自訂欄位中，方便匯入回 Zotero 等文獻管理軟體。 [DONE (Full - CSV & RIS export of filtered/selected implemented)]

## Part 2: 新功能擴展計畫 (TODO List)

目標：基於現有架構，讓 LatteReview 更智慧、更貼近研究工作流。

### 5.0 【功能擴展：智慧化與整合】

*   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] **TODO 5.1: "主題概念提取與視覺化" 功能**
    *   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] 背景: AbstractionReviewer 可以提取關鍵概念，但目前只是文字。將其視覺化會更有洞察力。
    *   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] 細節:
        *   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] 在結果頁面新增一個 "主題分析儀表板" Tab。
        *   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] 任務A: 彙整所有被納入 (Included) 文章的 AbstractionReviewer 結果（關鍵概念）。
        *   [DONE (Handles Real Backend DataFrame Structure; LLMs may be simulated)] 任務B: 使用 `wordcloud` 套件生成一個關鍵字雲圖，視覺化核心主題。
        *   [DONE (Pyvis Basic Network Graph Implemented)]                 任務C (進階): 使用 pyvis 或 plotly 繪製概念網路圖，顯示不同概念之間的關聯性（例如，在同一篇文章中出現的就算有關聯）。
*   [DONE (Simulated - Detailed Log Integration)] **TODO 5.2: "審查員辯論 (Reviewer Debate)" 工作流**
    *   - Simulation implemented in GUI logs; real backend debate requires `lattereview` package changes.
    *   [DONE (Simulated - Detailed Log Integration)] 背景: 當 Agent 意見不合時，不只交給資深 Agent 決定，而是讓他們進行一輪 "辯論"。
    *   [DONE (Simulated - Detailed Log Integration)] 細節:
        *   [DONE (Simulated - Detailed Log Integration)] 任務A: 設計一個新的 Workflow 流程。如果 Round 1 的 Agent 意見不合，自動觸發一個 "辯論回合 (Debate Round)"。
        *   [DONE (Simulated - Detailed Log Integration)] 任務B: 在辯論回合中，修改 Agent 的 Prompt。新的 Prompt 應包含："你的同事 Reviewer B 認為應該納入，理由是 '...'。請你根據他的理由，重新評估你的決定，並提出你的最終看法與反駁。"
        *   [DONE (Simulated - Detailed Log Integration)] 任務C: 將這個 "辯論過程" 的對話記錄完整地顯示在文章的詳細結果視圖中，讓使用者能看到 AI "思辨" 的過程。
*   [DONE (Handles Real Backend DataFrame Structure with Enhanced RAG Simulation; LLMs may be simulated)] **TODO 5.3: "RAG 強化審查 (RAG-Enhanced Review)" 功能**
    *   [DONE (Handles Real Backend DataFrame Structure with Enhanced RAG Simulation; LLMs may be simulated)] 背景: 現有架構已支援 RAG 概念，現在將其實作成具體功能。
    *   [DONE (Handles Real Backend DataFrame Structure with Enhanced RAG Simulation; LLMs may be simulated)] 細節:
        *   [DONE (Handles Real Backend DataFrame Structure with Enhanced RAG Simulation; LLMs may be simulated)] 任務A: 在 Workflow 設定介面，增加一個 "上傳背景資料" 的區域 (`st.file_uploader`)，允許使用者上傳 1-3 篇他們自己的核心論文或研究計畫 (PDF/TXT)。
        *   [DONE (Handles Real Backend DataFrame Structure with Enhanced RAG Simulation; LLMs may be simulated)] 任務B: 後端使用 `langchain` 或類似工具，將這些背景資料建立成一個小型的向量資料庫 (Vector Store)。
        *   [DONE (Handles Real Backend DataFrame Structure with Enhanced RAG Simulation; LLMs may be simulated)] 任務C: 修改 Agent 的執行流程。在審查每篇文章前，先從向量資料庫中檢索與該文章摘要最相關的 1-2 段背景資料。
        *   [DONE (Handles Real Backend DataFrame Structure with Enhanced RAG Simulation; LLMs may be simulated)] 任務D: 將檢索到的背景資料片段，注入到 Agent 的 Prompt 中，例如："根據你 '專案背景知識：{retrieved_context}'，請評估以下文章..."。這能讓審查標準極度貼近使用者自身的研究方向。

## General Tasks / Documentation

*   **TODO G1: Internationalize UI and documentation to English.**
    *   [DONE] Translate `PROJECT_OVERVIEW.md` to English.
    *   [DONE] Translate `LatteReview_Project_Vision.md` to English.
    *   [DONE] Review and translate comments in `app.py` to English.
    *   [DONE] Review and translate UI text (button labels, messages, placeholders) in `app.py` to English.
*   **[DONE] G2: Implement Save/Load/Delete Workflow Functionality.**
    *   [DONE] Design UI for Save/Load/Delete workflow.
    *   [DONE] Implement `save_workflow_to_file` utility and UI call.
    *   [DONE] Implement `list_saved_workflows` utility and UI call.
    *   [DONE] Implement `load_workflow_from_file` utility and UI call.
    *   [DONE] Implement `delete_workflow_file` utility and UI call (with confirmation).
