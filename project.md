# Safari 網頁內容擷取與處理工具

這個項目提供了一個在 macOS 上從 Safari 瀏覽器擷取並處理網頁內容的解決方案。它不僅可以獲取網頁源代碼，還能使用 LLM（大型語言模型）來提取重要內容並轉換為結構化的 Markdown 格式。

## 功能特點

- 直接從 Safari 獲取當前頁面源代碼，無需重新發送請求
- 支持需要登入的頁面內容
- 使用 LLM 智能提取頁面重要內容
- 自動轉換為標準 Markdown 格式
- 無需額外的 WebDriver

## 實現方案

### 1. 源代碼擷取 (AppleScript)

使用 AppleScript 直接與 Safari 瀏覽器互動，獲取當前頁面的 HTML 內容：

```applescript
tell application "Safari"
    tell front document
        return source
    end tell
end tell
```

### 2. Python 整合實現

將 AppleScript 與 Python 結合，並添加 LLM 處理功能：

```python
import subprocess
from openai import OpenAI  # 假設使用 OpenAI API

# AppleScript 代碼
script = '''
tell application "Safari"
    tell front document
        return source
    end tell
end tell
'''

def get_safari_content():
    # 獲取當前頁面的 URL 和標題
    url_script = '''
    tell application "Safari"
        tell front document
            return {URL, name}
        end tell
    end tell
    '''
    
    # 獲取 URL 和標題
    url_result = subprocess.run(['osascript', '-e', url_script],
                              capture_output=True, text=True)
    url, title = url_result.stdout.strip().split(', ', 1)
    
    # 獲取頁面源代碼
    result = subprocess.run(['osascript', '-e', script],
                          capture_output=True, text=True)
    
    return {
        'url': url,
        'title': title,
        'content': result.stdout
    }

def process_with_llm(page_data):
    # 初始化 OpenAI 客戶端（使用兼容 API）
    client = OpenAI(
        base_url="http://192.168.6.176:1234/v1",
        api_key="not-needed"
    )
    
    # 使用 LLM 提取重要內容並轉換為 Markdown
    response = client.chat.completions.create(
        model="mlx-community/deepseek-r1-distill-qwen-32b-mlx",
        messages=[{
            "role": "system",
            "content": """請從以下 HTML 內容中提取重要信息，並按照以下格式轉換為 Markdown：

1. 內容頭部分：
   - URL: [提取當前網頁的 URL]
   - 標題: [提取網頁標題]
   - 摘要: [生成 100 字以內的簡短摘要]

2. 提取規則：
   - 嚴格保持原文內容，不允許修改或重寫
   - 保留原始的層次結構和格式
   - 移除廣告和導航等無關內容
   - 使用標準 Markdown 語法"""
        }, {
            "role": "user",
            "content": f"""頁面信息：
URL: {page_data['url']}
標題: {page_data['title']}

HTML 內容:
{page_data['content']}"""
        }]
    )
    
    return response.choices[0].message.content

def main():
    # 獲取頁面數據
    page_data = get_safari_content()
    
    # 使用 LLM 處理內容
    markdown_content = process_with_llm(page_data)
    
    # 生成文件名（使用標題）
    filename = f"{page_data['title'][:50]}.md"  # 限制長度避免文件名過長
    filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).strip()
    
    # 保存為 Markdown 文件
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

if __name__ == '__main__':
    main()
```

### 3. 處理流程

1. **源代碼擷取**：
   - 使用 AppleScript 直接從 Safari 獲取頁面源代碼
   - 保持所有現有的登入狀態和上下文

2. **內容處理**：
   - 使用 LLM 分析網頁內容
   - 識別並提取重要信息
   - 過濾廣告和無關內容

3. **Markdown 轉換**：
   - 將提取的內容轉換為標準 Markdown 格式
   - 保持內容的層次結構
   - 生成清晰的標題和章節

## 系統要求

- macOS 作業系統
- Python 3.7+
- Safari 瀏覽器
- Python OpenAI 套件（用於訪問 LLM API）

## 使用方式

1. 在 Safari 中打開目標網頁
2. 運行 Python 腳本
3. 自動生成處理後的 Markdown 文件

## 注意事項

- 請確保 Safari 的自動化功能已啟用
- 需要確保本地 LLM API 服務（http://192.168.6.176:1234）可以正常訪問
- 處理大型網頁可能需要更長時間
- 建議遵循網站的使用條款和爬蟲政策
