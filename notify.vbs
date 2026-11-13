' Launch notify.ps1 with no console window at all. Usage: wscript notify.vbs <exitcode> [timeoutSec]
' Keep this file ASCII-only (wscript reads it as ANSI).
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
code = "0"
If WScript.Arguments.Count > 0 Then code = WScript.Arguments(0)
extra = ""
If WScript.Arguments.Count > 1 Then extra = " -TimeoutSec " & WScript.Arguments(1)
cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File """ & dir & "\notify.ps1"" -ExitCode " & code & extra
CreateObject("WScript.Shell").Run cmd, 0, False
