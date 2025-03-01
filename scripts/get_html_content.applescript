tell application "Safari"
	tell front document
		-- 等待頁面加載完成
		repeat until (do JavaScript "document.readyState") is "complete"
			delay 0.1
		end repeat
		
		-- 等待一段時間讓 JavaScript 執行
		delay 2
		
		-- 獲取完整的 DOM
		return do JavaScript "document.documentElement.outerHTML"
	end tell
end tell