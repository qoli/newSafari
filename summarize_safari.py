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
    console = Console()
    
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
            prefix = "\n[bold cyan]📝 網頁摘要：[/]\n"
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
            prefix = "\n[bold green]🤖 回答：[/]\n" if user_input else ""

        with console.status("[bold yellow]🤔 正在思考...[/]", spinner="dots") as status:
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

            # 收集完整回應
            full_response = []
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response.append(chunk.choices[0].delta.content)

        # 組合完整回應
        complete_response = ''.join(full_response)
        
        # 使用 rich 渲染輸出
        console.print(prefix, end="")
        if user_input is None:
            # 摘要模式
            lines = complete_response.split('\n')
            for line in lines:
                if line.startswith('總結：'):
                    console.print(f"[bold cyan]{line}[/]")
                elif '：' in line:
                    console.print(f"[bold yellow]{line}[/]")
                else:
                    console.print(line)
        else:
            # 對話模式
            markdown = Markdown(complete_response)
            console.print(markdown)
        
        console.print()  # 確保有足夠的空行

        # 構造一個類似非流式響應的對象
        class SimpleResponse:
            def __init__(self, content):
                self.choices = [type('Choice', (), {'message': type('Message', (), {'content': content})()})]
        
        return SimpleResponse(''.join(full_response))

    except Exception as e:
        console.print(f"\n[bold red]❌ LLM 請求錯誤: {str(e)}[/]")
        return None


def main():
    """主要執行邏輯"""
    # 解析命令行參數
    args = parse_arguments()

    # 創建 rich console
    console = Console()
    
    # 顯示程序標題
    console.rule("[bold cyan]🚀 Safari 網頁助手[/]", characters="═")
    
    with console.status("[bold yellow]初始化中...[/]") as status:
        # 創建 OpenAI 客戶端
        client = OpenAI(base_url=LLM_BASE_URL, api_key=args.api_key)
        
        # 更新狀態
        status.update("[bold yellow]正在獲取頁面內容...[/]")
        page_data = get_safari_content()
        if page_data is None:
            console.print("\n[bold red]❌ 無法獲取頁面數據，程序終止[/]")
            return

        # 顯示頁面信息
        console.print("\n[bold green]✅ 成功獲取頁面[/]")
        console.print(f"📑 標題：[bold]{page_data['title']}[/]")
        console.print(f"🔗 網址：[blue underline]{page_data['url']}[/]")

        # 更新狀態
        status.update("[bold yellow]正在提取文本內容...[/]")
        title, extracted_text = extract_text(page_data["html"])
        if extracted_text is None:
            console.print("\n[bold red]❌ 無法從頁面提取文本，程序終止[/]")
            return

        console.print("\n[bold green]✅ 文本提取完成[/]")

        # 更新狀態
        status.update("[bold yellow]正在生成摘要...[/]")
        summary_response = summarize_text(client, extracted_text, title)

        if not summary_response:
            console.print("\n[bold red]❌ 無法生成摘要[/]")
            return

    # 進入對話模式
    console.rule("[bold cyan]💬 對話模式[/]", characters="─")
    console.print("[dim]您可以詢問任何關於該網頁內容的問題。輸入 'exit' 退出。[/]")
    
    while True:
        try:
            # 使用 console.print 來正確顯示樣式化的輸入提示
            console.print("\n您的問題", style="bold purple", end=" > ")
            user_input = input()
            if user_input.lower() == "exit":
                console.rule("[bold cyan]👋 感謝使用[/]", characters="─")
                break

            # 使用相同的 summarize_text 函數進行對話
            chat_response = summarize_text(client,
                                         summary_response.choices[0].message.content,
                                         title,
                                         user_input)
            
            if not chat_response:
                console.print("\n[bold red]❌ 無法生成回應[/]")
        except KeyboardInterrupt:
            console.print("\n\n[bold cyan]👋 感謝使用[/]")
            break

if __name__ == "__main__":
    main()