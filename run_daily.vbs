' Run run_daily.bat silently (no console window). Keep this file ASCII-only:
' wscript reads it as ANSI, so non-ASCII comments can swallow line breaks.
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
CreateObject("WScript.Shell").Run """" & dir & "\run_daily.bat""", 0, True
