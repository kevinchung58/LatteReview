# LatteReview GUI 開發計畫與功能擴展 (TODO List)

## 專案前提與設定

*   **技術棧建議：** 使用 Python 的 Web 框架，如 Streamlit 或 Gradio。對於快速開發和資料科學應用，Streamlit 特別合適，因為它能讓您用純 Python 快速建立互動式介面。以下 TODO 會以 Streamlit 的概念來發想。
*   **LLM 固定模型：** 所有與 LLM 互動的部分，將預設使用 `gemini-1.5-flash`。這會簡化介面，使用者不需要在介面上選擇模型，只需要在設定中輸入自己的 Google AI/Vertex AI API Key 即可。

---

## Part 1: GUI 開發計畫 (TODO List)

目標：打造一個引導式、視覺化的操作流程，讓使用者從匯入文獻到看到審查結果一氣呵成。

### 1.0 【基礎架構與主畫面】

*   **TODO 1.1: 建立 Streamlit 應用程式骨架**
    *   細節:
        *   建立一個主 Python 檔案 (e.g., `app.py`).
        *   使用 `st.set_page_config` 設定頁面標題為 "LatteReview 🤖☕" 和寬版面。
        *   使用 `st.sidebar` 建立一個側邊欄，用於導航和全域設定。
*   **TODO 1.2: 設計專案管理介面**
    *   細節:
        *   在主畫面上顯示 "現有專案列表" 和 "建立新專案" 按鈕。
        *   專案列表可以先用資料夾結構來管理，每個專案一個資料夾，裡面存放 RIS 檔、設定檔和結果。
        *   點擊 "建立新專案" 後，會跳出一個 `st.text_input` 讓使用者輸入專案名稱，並在後端建立對應的資料夾。
*   **TODO 1.3: 全域 API Key 設定**
    *   細節:
        *   在側邊欄 `st.sidebar` 中，新增一個 `st.text_input` 欄位，類型為 `password`，讓使用者輸入他們的 Gemini API Key。
        *   使用 `st.session_state` 來安全地儲存該 Key，避免每次頁面刷新都要重新輸入。
        *   提示使用者模型將固定使用 `gemini-1.5-flash`。

### 2.0 【資料匯入與預覽介面】

*   **TODO 2.1: 實作 RIS 檔案上傳功能**
    *   細節:
        *   在專案頁面中，使用 `st.file_uploader` 允許使用者上傳 `.ris` 檔案。
        *   限制檔案類型為 `['ris']`。
        *   上傳後，後端呼叫現有的 RIS 解析器來處理檔案。
*   **TODO 2.2: 顯示匯入資料預覽**
    *   細節:
        *   解析 RIS 檔後，將結果呈現在一個 `st.dataframe` 中。
        *   至少顯示欄位：ID, Title, Abstract, Year, Authors。
        *   在表格上方顯示統計資訊，例如 "總共匯入 N 篇文章"。

### 3.0 【工作流 (Workflow) 設定介面 - 核心部分】

這是最複雜但也是最重要的部分。目標是將抽象的 Workflow Schema 轉化為視覺化的設定元件。

*   **TODO 3.1: 建立多回合 (Multi-round) 設定介面**
    *   細節:
        *   使用 `st.tabs` 來代表不同的審查回合，例如 "Round 1: 初審", "Round 2: 複審"。
        *   提供 "新增回合" 按鈕，每按一次就動態增加一個 Tab。
*   **TODO 3.2: 設計 Agent 設定器**
    *   細節:
        *   在每個回合的 Tab 內，允許使用者 "新增 Agent"。
        *   每個 Agent 都是一個卡片或 `st.expander`，裡面包含以下設定項：
            *   `st.text_input("Agent 名稱")`: e.g., "初級研究員A", "資深方法學家"。
            *   `st.selectbox("Agent 類型")`: 選項來自 LatteReview 現有的 Agent (TitleAbstractReviewer, ScoringReviewer, AbstractionReviewer)。
            *   `st.text_area("Agent 背景故事 (Backstory/Persona)")`: 提供一個預設模板，引導使用者寫出好的 Persona。
            *   `st.text_area("納入條件 (Inclusion Criteria)")`: 條列式輸入。
            *   `st.text_area("排除條件 (Exclusion Criteria)")`: 條列式輸入。
            *   注意: 這裡不需要選擇 LLM Provider 或模型，因為已預設為 Gemini。
*   **TODO 3.3: 設定回合間的過濾邏輯**
    *   細節:
        *   在除了第一回合的每個 Tab (e.g., "Round 2") 的頂部，需要設定文章來源。
        *   使用 `st.selectbox` 讓使用者選擇這一輪要審查的文章範圍。
        *   選項應包含：
            *   "上一輪中所有通過 (Included) 的文章"
            *   "上一輪中所有被拒絕 (Excluded) 的文章"
            *   "上一輪中 Agent 意見不合的文章" (例如，一個 Agent 說 included，另一個說 excluded)
            *   "上一輪中分數高於 X 的文章" (如果上一輪有 ScoringReviewer，則顯示此選項)

### 4.0 【審查執行與結果呈現介面】

*   **TODO 4.1: 執行與進度監控**
    *   細節:
        *   在 Workflow 設定頁面底部，放置一個醒目的 "開始審查" 按鈕。
        *   點擊後，按鈕變為禁用狀態，並顯示一個 `st.progress` 進度條和一個 `st.status` 區塊。
        *   在 `st.status` 區塊中，即時更新日誌，例如 "Round 1: Agent A 正在審查 'Article Title X'..."。
        *   利用 LatteReview 的成本追蹤功能，即時顯示 "預估/已花費成本: $X.XX"。
*   **TODO 4.2: 結果總覽與篩選**
    *   細節:
        *   審查完成後，用一個 `st.dataframe` 顯示最終結果。
        *   表格欄位應包含：Title, Final Decision, Avg Score, Reasoning Summary。
        *   在表格上方提供篩選器：`st.multiselect` 篩選最終決定 (Included, Excluded)，`st.slider` 篩選分數。
*   **TODO 4.3: 單篇文章詳細結果視圖**
    *   細節:
        *   讓結果表格的每一行都可以點擊 (或在旁邊加一個 "詳情" 按鈕)。
        *   點擊後，在下方或彈出視窗 `st.dialog` 中顯示該篇文章的完整審查歷史。
        *   內容包括：文章原文 (摘要)、每一輪、每一個 Agent 的詳細評分、決策和完整理由 (Reasoning)。這對於透明度至關重要。
*   **TODO 4.4: 結果匯出功能**
    *   細節:
        *   提供 "匯出結果" 按鈕。
        *   使用 `st.download_button` 提供至少兩種格式：
            *   CSV 格式：包含所有欄位，方便用 Excel 或其他軟體分析。
            *   RIS 格式：將審查結果（如 Decision: Included）寫入到每篇文章的 notes 或自訂欄位中，方便匯入回 Zotero 等文獻管理軟體。

## Part 2: 新功能擴展計畫 (TODO List)

目標：基於現有架構，讓 LatteReview 更智慧、更貼近研究工作流。

### 5.0 【功能擴展：智慧化與整合】

*   **TODO 5.1: "主題概念提取與視覺化" 功能**
    *   背景: AbstractionReviewer 可以提取關鍵概念，但目前只是文字。將其視覺化會更有洞察力。
    *   細節:
        *   在結果頁面新增一個 "主題分析儀表板" Tab。
        *   任務A: 彙整所有被納入 (Included) 文章的 AbstractionReviewer 結果（關鍵概念）。
        *   任務B: 使用 `wordcloud` 套件生成一個關鍵字雲圖，視覺化核心主題。
        *   任務C (進階): 使用 `pyvis` 或 `plotly` 繪製概念網路圖，顯示不同概念之間的關聯性（例如，在同一篇文章中出現的就算有關聯）。
*   **TODO 5.2: "審查員辯論 (Reviewer Debate)" 工作流**
    *   背景: 當 Agent 意見不合時，不只交給資深 Agent 決定，而是讓他們進行一輪 "辯論"。
    *   細節:
        *   任務A: 設計一個新的 Workflow 流程。如果 Round 1 的 Agent 意見不合，自動觸發一個 "辯論回合 (Debate Round)"。
        *   任務B: 在辯論回合中，修改 Agent 的 Prompt。新的 Prompt 應包含："你的同事 Reviewer B 認為應該納入，理由是 '...'。請你根據他的理由，重新評估你的決定，並提出你的最終看法與反駁。"
        *   任務C: 將這個 "辯論過程" 的對話記錄完整地顯示在文章的詳細結果視圖中，讓使用者能看到 AI "思辨" 的過程。
*   **TODO 5.3: "RAG 強化審查 (RAG-Enhanced Review)" 功能**
    *   背景: 現有架構已支援 RAG 概念，現在將其實作成具體功能。
    *   細節:
        *   任務A: 在 Workflow 設定介面，增加一個 "上傳背景資料" 的區域 (`st.file_uploader`)，允許使用者上傳 1-3 篇他們自己的核心論文或研究計畫 (PDF/TXT)。
        *   任務B: 後端使用 `langchain` 或類似工具，將這些背景資料建立成一個小型的向量資料庫 (Vector Store)。
        *   任務C: 修改 Agent 的執行流程。在審查每篇文章前，先從向量資料庫中檢索與該文章摘要最相關的 1-2 段背景資料。
        *   任務D: 將檢索到的背景資料片段，注入到 Agent 的 Prompt 中，例如："根據你 '專案背景知識：{retrieved_context}'，請評估以下文章..."。這能讓審查標準極度貼近使用者自身的研究方向。
