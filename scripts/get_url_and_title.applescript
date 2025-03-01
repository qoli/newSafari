tell application "Safari"
    tell front document
        return {URL, name}
    end tell
end tell