#!/Users/ronnie/.pyenv/versions/3.10.4/bin/python

import sys
sys.path.insert(0, "/Users/ronnie/.pyenv/versions/3.10.4/lib/python3.10/site-packages")

import subprocess
import re
import argparse
from openai import OpenAI
from readability import Document
import os
from rich.console import Console
from rich.markdown import Markdown

# LLM API 設定
LLM_BASE_URL = "https://glama.ai/api/gateway/openai/v1"
LLM_MODEL = "gemini-2.0-pro-exp-02-05"

def parse_arguments():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(description='Safari 網頁內容擷取與對話助手')
    parser.add_argument('--api-key',
                      required=True,
                      help='Glama API Key')
    return parser.parse_args()

def get_safari_content():
    """獲取 Safari 當前頁面的 HTML 源代碼"""
    try:
        # 獲取當前頁面的 URL 和標題 (直接使用 main.py 的 script)
        url_script = """
            tell application "Safari"
                set currentURL to URL of document 1
                set pageTitle to name of document 1
                return currentURL & ", " & pageTitle
            end tell
        """
        url_result = subprocess.run(
            ["osascript", "-e", url_script], capture_output=True, text=True
        )

        if url_result.returncode != 0:
            print(f"錯誤：無法獲取 URL 和標題\n{url_result.stderr}")
            return None

        url, title = url_result.stdout.strip().split(", ", 1)

        # 獲取頁面源代碼 (直接使用 main.py 的 script)
        html_script = """
            tell application "Safari"
                tell document 1
                    set theSource to source
                end tell
            end tell
            return theSource
        """
        
        html_result = subprocess.run(
            ["osascript", "-e", html_script], capture_output=True, text=True
        )
        if html_result.returncode != 0:
            print(f"錯誤：無法獲取頁面源代碼\n{html_result.stderr}")
            return None

        html = html_result.stdout
        return {"url": url, "title": title, "html": html}

    except Exception as e:
        print(f"發生錯誤：{str(e)}")
        return None

def extract_text(html):
    """使用 python-readability 從 HTML 中提取主要文本和標題"""
    try:
        doc = Document(html)
        title = doc.title()
        summary = doc.summary()
        return title, summary
    except Exception as e:
        print(f"提取文本時發生錯誤: {e}")
        return None, None

def summarize_text(client, text, title, user_input=None):
    """調用 LLM API 來總結文本或進行對話，支持流式輸出"""
    try:
        if user_input is None:
            # 初始總結模式
            messages = [
                {
                    "role": "system",
                    "content": "為最後提供的文字內容進行按要求的總結。如果是其他語言，請翻譯到繁體中文。\n\n請嚴格按照下面的格式進行輸出，在格式以外的地方，不需要多餘的文本內容。這裡是格式指導：總結：簡短的一句話概括內容，此單獨佔用一行，記得輸出換行符號；要點：對文字內容提出多個要點內容，並每一個要點都附加一個裝飾用的 emoji，每一個要點佔用一行，注意記得輸出換行符號；下面為需要總結的文字內容：",
                },
                {
                    "role": "user",
                    "content": f"Title: {title}\n\nContent:\n{text}"
                }
            ]
            temperature = 0.1
            prefix = "\n📝 網頁摘要：\n"
        else:
            # 對話模式
            messages = [
                {
                    "role": "system",
                    "content": "你是一個熱心的助手。基於先前提供的網頁內容進行對話。回答時請使用繁體中文。",
                },
                {
                    "role": "assistant",
                    "content": text,  # 這裡的 text 參數用於傳遞先前的總結
                },
                {
                    "role": "user",
                    "content": user_input,
                }
            ]
            temperature = 0.7
            prefix = "\n🤖：" if user_input else ""

        print("🤔 正在思考回答...")
        
        # 使用流式輸出
        stream = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=8192,
            top_p=0.95,
            presence_penalty=0.1,
            stream=True
        )

        # 先進行流式輸出
        print(prefix, end="", flush=True)
        full_response = []
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response.append(content)
        print()  # 換行

        # 組合完整回應
        complete_response = ''.join(full_response)

        # 使用 ANSI 轉義序列清除先前輸出（包括思考提示和前綴）
        lines_to_clear = complete_response.count('\n') + 3  # 包括思考提示和前綴
        print("\033[F" * lines_to_clear + "\033[J")  # 清除從游標到屏幕底部的內容
        
        # 使用 rich 渲染 Markdown
        console = Console()
        if user_input is None:
            # 摘要模式，保持原有格式
            markdown_text = complete_response
        else:
            # 對話模式，添加適當的標記
            markdown_text = complete_response
            
        # 渲染 Markdown
        markdown = Markdown(markdown_text)
        console.print(markdown)
        print()  # 確保有足夠的空行

        # 構造一個類似非流式響應的對象
        class SimpleResponse:
            def __init__(self, content):
                self.choices = [type('Choice', (), {'message': type('Message', (), {'content': content})()})]
        
        return SimpleResponse(''.join(full_response))

    except Exception as e:
        print(f"\n❌ LLM 請求錯誤: {e}")
        return None


def main():
    """主要執行邏輯"""
    # 解析命令行參數
    args = parse_arguments()

    # 創建 rich console
    console = Console()
    
    console.print("🚀 Safari 網頁助手", style="bold")
    console.print("\n處理進度：", style="bold")

    # 創建 OpenAI 客戶端
    client = OpenAI(base_url=LLM_BASE_URL, api_key=args.api_key)

    page_data = get_safari_content()
    if page_data is None:
        console.print("\n❌ 無法獲取頁面數據，程序終止", style="red")
        return

    console.print(f"\n✅ 成功獲取頁面：{page_data['title']}")
    console.print(f"🔗 {page_data['url']}", style="blue underline")

    title, extracted_text = extract_text(page_data["html"])
    if extracted_text is None:
        console.print("\n❌ 無法從頁面提取文本，程序終止", style="red")
        return

    console.print("✅ 成功提取文本內容")

    summary_response = summarize_text(client, extracted_text, title)  # 獲取 response

    if not summary_response:
        console.print("\n❌ 無法生成摘要", style="red")
        return
    
    # 進入對話模式
    console.print("\n💬 對話模式", style="bold")
    console.print("您可以詢問任何關於該網頁內容的問題。")
    while True:
        user_input = input("\n請輸入您的問題（或輸入 'exit' 退出）：")
        if user_input.lower() == "exit":
            break

        # 使用相同的 summarize_text 函數進行對話
        chat_response = summarize_text(client,
                                     summary_response.choices[0].message.content,
                                     title,
                                     user_input)
        
        if not chat_response:
            print("\n❌ 無法生成回應")

if __name__ == "__main__":
    main()