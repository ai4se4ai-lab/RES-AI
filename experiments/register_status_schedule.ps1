$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $PSScriptRoot
$taskName = 'RES-AI-Experiment-Status-Hourly'
$python = (& python -c 'import sys; print(sys.executable)').Trim()
$pythonw = Join-Path (Split-Path -Parent $python) 'pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonw)) { throw 'Windowless pythonw.exe was not found.' }
$updater = Join-Path $PSScriptRoot 'update_project_status.py'
$action = New-ScheduledTaskAction -Execute $pythonw -Argument ('"{0}" --reason "hourly scheduled evidence check"' -f $updater) -WorkingDirectory $workspace
$trigger = New-ScheduledTaskTrigger -Once -At ((Get-Date).AddHours(1)) -RepetitionInterval (New-TimeSpan -Hours 1)
$principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'Refresh RES-AI experiment evidence status and append a UTC history record every hour. Local reporting only; no experiment submission.' -Force | Out-Null
$task = Get-ScheduledTask -TaskName $taskName
if ($task.State -eq 'Disabled' -or $task.Triggers[0].Repetition.Interval -ne 'PT1H') { throw 'Hourly task verification failed.' }
$stateDir = Join-Path $workspace 'experiments/results/status-maintenance'
New-Item -ItemType Directory -Force $stateDir | Out-Null
$receipt = [ordered]@{
    task_name = $taskName
    registered_at_utc = [DateTime]::UtcNow.ToString('o')
    interval = $task.Triggers[0].Repetition.Interval
    next_run_utc = (Get-ScheduledTaskInfo -TaskName $taskName).NextRunTime.ToUniversalTime().ToString('o')
    python = $pythonw
    updater = $updater
    logon_type = [string]$task.Principal.LogonType
}
$receipt | ConvertTo-Json | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $stateDir 'scheduler.json')
$receipt | ConvertTo-Json
