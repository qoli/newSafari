# Safari 網頁內容擷取與總結工具 🌐

這是一個強大的 Safari 瀏覽器網頁內容擷取與總結工具，支援兩種操作模式：基本擷取模式和互動式總結模式。

## 功能特點 🌟

### 基本擷取模式 (main.py)
- 📝 自動獲取當前 Safari 頁面的 URL 和標題
- 🧹 智能清理 HTML 內容，提取純文本
- 🤖 使用 LLM (Language Learning Model) 處理頁面內容
- 💾 自動保存為 Markdown 文件
- 📋 支援一鍵複製到剪貼板

### 互動式總結模式 (summarize_safari.py)
- 🔍 自動提取網頁主要內容
- 📊 生成結構化摘要
- 💬 支援互動式問答
- 🔄 支援流式輸出
- 🎯 智能對話記憶上下文

## 系統需求 💻

- macOS 作業系統
- Python 3.10+
- Safari 瀏覽器
- 有效的 LLM API 金鑰

## 安裝步驟 🔧

1. 克隆儲存庫：
```bash
git clone <repository-url>
cd newSafari
```

2. 安裝依賴套件：
```bash
pip install -r requirements.txt
```

## 使用方法 📖

### 基本擷取模式

```bash
python main.py
```

### 互動式總結模式

```bash
python summarize_safari.py --api-key YOUR_API_KEY
```

### Raycast 腳本使用方法

本工具提供兩種 Raycast 腳本：

#### 1. Safari to Markdown（基本擷取模式）

```applescript
#!/usr/bin/osascript

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Safari to Markdown
# @raycast.mode silent

# Optional parameters:
# @raycast.icon 📝

# Documentation:
# @raycast.author qoli
# @raycast.authorURL https://raycast.com/qoli

tell application "Terminal"
    activate
    do script "cd /Volumes/Data/Github/newSafari && python3 ./main.py && exit"
end tell
```

#### 2. Safari Summarizy（互動式總結模式）

```applescript
#!/usr/bin/osascript

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Safari Summarizy
# @raycast.mode silent

# Optional parameters:
# @raycast.icon 🤖

# Documentation:
# @raycast.author qoli
# @raycast.authorURL https://raycast.com/qoli

tell application "Terminal"
    activate
    do script "cd /Volumes/Data/Github/newSafari && python3 ./summarize_safari.py --api-key 'your-api-key-here'"
end tell
```

設定步驟：
1. 在 Raycast 中選擇 `Create Script Command`
2. 選擇 `AppleScript` 作為腳本類型
3. 根據需要複製對應的腳本內容
4. 對於 Safari Summarizy 腳本，請替換 `your-api-key-here` 為您的 API 金鑰
5. 儲存後即可在 Raycast 中使用對應的指令

```

## 專案結構 📁

```
newSafari/
├── main.py                     # 基本擷取模式主程式
├── summarize_safari.py         # 互動式總結模式主程式
├── requirements.txt            # 專案依賴
├── prompts/                    # 提示詞配置
│   └── system.txt             # 系統提示詞
└── scripts/                    # AppleScript 腳本
    ├── get_html_content.applescript
    └── get_url_and_title.applescript
```

## 設定說明 ⚙️

### LLM API 設定

在 `main.py` 中：
```python
LLM_BASE_URL = "http://192.168.6.237:1234/v1"
LLM_API_KEY = ""  # 填入您的 API 金鑰
```

在 `summarize_safari.py` 中：
```python
LLM_BASE_URL = "https://glama.ai/api/gateway/openai/v1"
LLM_MODEL = "gemini-2.0-pro-exp-02-05"
```

## 主要特性說明 🎯

### HTML 內容清理
- 使用 BeautifulSoup 進行智能解析
- 保留重要文本內容
- 移除無關元素
- 智能格式化

### LLM 處理
- 支援串流輸出
- 自適應內容長度控制
- 智能上下文管理
- 錯誤處理與重試機制

### 文件處理
- 智能文件名生成
- 自動創建輸出目錄
- Markdown 格式支援
- 剪貼板整合

## 使用提示 💡

1. 確保 Safari 瀏覽器已打開並訪問目標網頁
2. 運行相應的程式（基本模式或互動式模式）
3. 按照程式提示進行操作
4. 在互動式模式中，可以自由提問關於網頁內容的問題

## 錯誤處理 🚨

程式包含完整的錯誤處理機制：
- 網頁訪問錯誤
- API 調用錯誤
- 文件處理錯誤
- 內容提取錯誤

如遇到問題，請查看控制台輸出的錯誤信息。

## 開發者注意事項 👨‍💻

- 代碼中包含詳細的註釋
- 使用 Rich 庫提供精美的終端輸出
- 模塊化設計便於維護和擴展
- 完整的異常處理機制