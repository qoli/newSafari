# LLM API 設定
LLM_BASE_URL = "http://192.168.6.237:1234/v1"
LLM_API_KEY = ""

# LLM 模型參數
LLM_MODEL = "qwen2.5-32b-instruct-mlx"  # 使用 QWenLM 模型
LLM_TEMPERATURE = 0.1  # 使用低溫度以獲得穩定輸出
LLM_MAX_TOKENS = 64000  # 增加輸出長度限制
LLM_TOP_P = 0.95  # 控制輸出的確定性
LLM_PRESENCE_PENALTY = 0.1  # 鼓勵輸出更多樣化的內容

import subprocess
import sys
import re
import time
from openai import OpenAI
import os
from bs4 import BeautifulSoup, Comment
import base64
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich import print as rprint

# 初始化 Rich console (使用標準錯誤輸出)
console = Console(stderr=True)


def clean_html_content(html):
    """從 HTML 中提取純文本內容"""
    if not html or not isinstance(html, str):
        return ""

    try:
        # 使用 BeautifulSoup 解析 HTML
        soup = BeautifulSoup(html, "html.parser")

        # 簡單地使用 get_text 提取文本
        text_content = soup.get_text(separator="\n\n", strip=True)

        # 基本的文本清理
        if text_content:
            # 移除多餘的空行並標準化間距
            text_content = re.sub(r"\n{3,}", "\n\n", text_content)
            text_content = "\n".join(line.strip() for line in text_content.splitlines())
            text_content = text_content.strip() + "\n"

            # 輸出處理結果
            console.print("\n[bold blue]內容提取結果：[/bold blue]")
            console.print(
                Panel.fit(
                    f"""[green]原始 HTML 大小：[/green]{len(html):,} 字符
[green]提取文本大小：[/green]{len(text_content):,} 字符""",
                    title="處理統計",
                    border_style="blue",
                )
            )

            return text_content

        return ""

    except Exception as e:
        console.print(f"[bold red]提取文本時發生錯誤：[/bold red]{str(e)}")
        return ""


def read_script(filename):
    """讀取腳本文件內容"""
    script_path = os.path.join("scripts", filename)
    try:
        with open(script_path, "r") as f:
            return f.read()
    except Exception as e:
        console.print(
            f"[bold red]錯誤：無法讀取腳本文件 {filename}:[/bold red] {str(e)}"
        )
        return None


def get_safari_content():
    try:
        # 獲取當前頁面的 URL 和標題
        url_script = read_script("get_url_and_title.applescript")
        if url_script is None:
            return None

        # 顯示進度面板
        with console.status(
            "[bold blue]正在獲取頁面內容...[/bold blue]", spinner="dots"
        ):
            # 獲取 URL 和標題
            console.print("[yellow]正在獲取 Safari 頁面信息...[/yellow]")
            url_result = subprocess.run(
                ["osascript", "-e", url_script], capture_output=True, text=True
            )

            if url_result.returncode != 0:
                console.print(
                    Panel(
                        f"[bold red]錯誤：無法獲取 URL 和標題[/bold red]\n{url_result.stderr}",
                        border_style="red",
                    )
                )
                return None

            url, title = url_result.stdout.strip().split(", ", 1)
            console.print(
                Panel.fit(
                    f"[green]URL:[/green] {url}\n[green]標題:[/green] {title}",
                    title="頁面信息",
                    border_style="green",
                )
            )

            # 獲取頁面源代碼
            html_script = read_script("get_html_content.applescript")
            if html_script is None:
                return None

            console.print("[yellow]正在等待頁面完全加載...[/yellow]")
            result = subprocess.run(
                ["osascript", "-e", html_script], capture_output=True, text=True
            )

            if result.returncode != 0:
                console.print(
                    Panel(
                        f"[bold red]錯誤：無法獲取頁面源代碼[/bold red]\n{result.stderr}",
                        border_style="red",
                    )
                )
                return None

            console.print("[green]✓ 成功獲取頁面源代碼[/green]")

            # 清理 HTML 內容
            cleaned_content = clean_html_content(result.stdout)

            console.print("[green]✓ 完成 HTML 內容清理[/green]")

        return {"url": url, "title": title, "content": cleaned_content}
    except Exception as e:
        console.print(f"[bold red]發生錯誤：[/bold red]{str(e)}")
        return None


def load_system_prompt():
    """讀取系統提示詞"""
    try:
        with open("prompts/system.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        console.print(f"[bold red]錯誤：無法讀取系統提示詞：[/bold red]{str(e)}")
        return None


def process_with_llm(page_data):
    try:
        # 讀取系統提示詞
        system_prompt = load_system_prompt()
        if system_prompt is None:
            return None

        # 初始化 OpenAI 客戶端
        client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)

        # 限制輸入內容長度，避免超過模型上下文限制
        MAX_CONTENT_LENGTH = 1600000  # 增加內容長度限制
        content = page_data["content"]
        if len(content) > MAX_CONTENT_LENGTH:
            print(f"內容過長，將截斷至 {MAX_CONTENT_LENGTH} 字符")
            content = content[:MAX_CONTENT_LENGTH] + "\n\n... (內容已截斷)"

        try:
            # 創建 stream
            stream = client.chat.completions.create(
                model=LLM_MODEL,
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS,
                top_p=LLM_TOP_P,
                presence_penalty=LLM_PRESENCE_PENALTY,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": f"""頁面信息：
URL: {page_data['url']}
標題: {page_data['title']}

HTML 內容:
{content}""",
                    },
                ],
                stream=True,
            )

            print("\nLLM 處理輸出：\n")

            # 直接輸出流式內容
            full_content = []
            for chunk in stream:
                try:
                    if hasattr(chunk.choices[0], "delta") and hasattr(
                        chunk.choices[0].delta, "content"
                    ):
                        content = chunk.choices[0].delta.content
                        if content is not None:  # 確保內容不是 None
                            print(content, end="", flush=True)  # 直接使用 print 輸出
                            full_content.append(str(content))  # 確保轉換為字符串
                except Exception as e:
                    print(f"\n處理串流輸出時發生錯誤：{str(e)}")
                    continue

            # 驗證和合併內容
            if not full_content:
                print("\n警告：處理後的內容為空")
                return None

            # 過濾掉任何 None 值並合併內容
            cleaned_content = "".join(c for c in full_content if c is not None)
            if not cleaned_content.strip():
                print("\n警告：合併後的內容為空")
                return None

            # 移除 <think> 標籤之間的內容
            cleaned_content = re.sub(
                r"<think>.*?</think>", "", cleaned_content, flags=re.DOTALL
            )

            # 再次檢查處理後的內容是否為空
            if not cleaned_content.strip():
                print("\n警告：過濾後的內容為空")
                return None

            return cleaned_content.strip()

        except Exception as e:
            print(f"\nAPI 調用過程中發生錯誤：{str(e)}")
            return None

    except Exception as e:
        print(f"\nLLM 處理過程中發生錯誤：{str(e)}")
        return None


def main():
    console.print("\n[bold blue]🚀 開始執行網頁內容擷取...[/bold blue]")

    # 獲取頁面數據
    page_data = get_safari_content()
    if page_data is None:
        console.print("[bold red]❌ 無法獲取頁面數據，程序終止[/bold red]")
        return

    # 使用 LLM 處理內容
    markdown_content = process_with_llm(page_data)
    if markdown_content is None:
        console.print("[bold red]❌ 無法處理頁面內容，程序終止[/bold red]")
        return

    # 生成文件名（使用標題）
    filename = f"{page_data['title'][:50]}.md".replace(
        " ", "-"
    )  # 限制長度避免文件名過長
    filename = "".join(
        c for c in filename if c.isalnum() or c in ("-", "_", ".")
    ).strip()

    # 保存為 Markdown 文件
    try:
        with console.status("[bold blue]正在保存文件...[/bold blue]", spinner="dots"):
            # 保存文件
            console.print(f"[yellow]保存到文件：[/yellow]{filename}")
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True) # 確保目錄存在
            output_path = os.path.join(output_dir, filename)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            console.print("[green]✓ 文件保存成功！[/green]")

            # 顯示文件信息
            console.print(
                Panel.fit(
                    f"""[blue]檔案名稱：[/blue]{filename}
[blue]內容大小：[/blue]{len(markdown_content):,} 字符""",
                    title="保存結果",
                    border_style="green",
                )
            )

            # 複製到剪貼板
            console.print("\n[yellow]按下 Enter 複製內容到剪貼板...[/yellow]")
            input()
            subprocess.run(
                ["pbcopy"], input=markdown_content.encode("utf-8"), check=True
            )
            console.print("[green]✓ 內容已複製到剪貼板！[/green]")

    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]複製到剪貼板時發生錯誤：[/bold red]{str(e)}")
    except Exception as e:
        console.print(f"[bold red]保存文件時發生錯誤：[/bold red]{str(e)}")


if __name__ == "__main__":
    main()
