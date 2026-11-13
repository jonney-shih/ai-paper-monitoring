param([int]$ExitCode = 0, [int]$TimeoutSec = 0)
# 读取日志最后一行「完成:...」,弹出对话框通知(TimeoutSec=0 表示停留到按确定)
$log = Join-Path $PSScriptRoot "data\run.log"
$lines = Get-Content $log -Tail 20 -Encoding UTF8
$done = $lines | Where-Object { $_ -like "完成:*" } | Select-Object -Last 1
$warn = @($lines | Where-Object { $_ -like "*[warn]*" }).Count

if ($ExitCode -ne 0 -or -not $done) {
    $title = "AI 论文监控:执行失败"
    $body  = "请查看 data\run.log"
    $icon  = 16   # 错误图标
} else {
    $title = "AI 论文监控:今日简报已完成"
    $body  = ($done -replace '^完成:.*?\s{2}', '')
    if ($warn -gt 0) { $body += "  ($warn 个来源失败)" }
    $report = Join-Path $PSScriptRoot "reports\index.html"
    $body += "`n`n按「确定」打开报告目录页,按「取消」关闭。"
    $icon  = 64   # 信息图标
}

# 0x1000 = 置于最上层;成功时用「确定/取消」(类型 1),失败时只有「确定」
$btn = if ($report) { 1 } else { 0 }
$sh = New-Object -ComObject WScript.Shell
$ans = $sh.Popup($body, $TimeoutSec, $title, $btn + $icon + 0x1000)
Add-Content $log "[notify] 对话框结果=$ans (1=确定 2=取消 -1=逾时)" -Encoding UTF8
if ($report -and $ans -eq 1 -and (Test-Path $report)) {
    # 优先用 Chrome 打开;找不到 Chrome 才退回系统默认浏览器
    $chrome = @("$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
                "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
                "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($chrome) { Start-Process $chrome -ArgumentList "--new-window", "`"$report`"" } else { Start-Process $report }
    # 把刚开的报告窗口拉到最前面(否则可能被其他窗口盖在后面)
    for ($k = 0; $k -lt 12; $k++) {
        Start-Sleep -Milliseconds 700
        if ($sh.AppActivate("每日简报 · 目录")) { break }
    }
}
