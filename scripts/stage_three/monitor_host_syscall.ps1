param(
    [string]$FeatureDir = "C:\Users\Public\PythonProjects\storage\parquet\features\host_syscall\host\TRAIN\schema=v1",
    [int]$TotalArtifacts = 63573,
    [int]$IntervalSec = 30
)

$proc = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
    Where-Object {
        $_.CommandLine -like "*stage-three extract-features*" -and
        $_.CommandLine -like "*--branch host*" -and
        $_.CommandLine -like "*--feature-group host_syscall*" -and
        $_.CommandLine -like "*--experiment-id exp001-host*"
    } |
    Sort-Object CreationDate -Descending |
    Select-Object -First 1

if (-not $proc) {
    Write-Host "Process not found: no matching stage-three extract-features run for exp001-host."
    exit 1
}

$pid = [int]$proc.ProcessId
$start = (Get-Process -Id $pid).StartTime
$processStartUtc = $start.ToUniversalTime()
$monitorStartedAt = Get-Date

$processedTotal = 0
$prevProcessed = 0
$processedBytes = 0L
$firstObservedWrite = $null
$lastObservedWrite = $null
$uniqueArtifacts = @{}
$prevTime = $monitorStartedAt

if (-not (Test-Path -LiteralPath $FeatureDir)) {
    Write-Host "Feature path not found: $FeatureDir"
    exit 1
}

# Keep last known file state to avoid double-counting unchanged files on every tick.
$fileState = @{}
Get-ChildItem -LiteralPath $FeatureDir -File -ErrorAction SilentlyContinue | ForEach-Object {
    $fileState[$_.FullName] = @{
        Ticks = $_.LastWriteTimeUtc.Ticks
        Length = $_.Length
    }
}

Write-Host ("Monitoring PID={0} from {1}" -f $pid, $start)

while ($true) {
    $p = Get-Process -Id $pid -ErrorAction SilentlyContinue
    if (-not $p) {
        Write-Host "Process finished. Monitoring stopped."
        break
    }

    if (-not (Test-Path -LiteralPath $FeatureDir)) {
        Write-Host ("Feature path missing: {0}" -f $FeatureDir)
        Start-Sleep -Seconds $IntervalSec
        continue
    }

    $files = Get-ChildItem -LiteralPath $FeatureDir -File -ErrorAction SilentlyContinue
    $newFiles = @()

    foreach ($file in $files) {
        if ($file.LastWriteTimeUtc -lt $processStartUtc) {
            continue
        }
        $state = $fileState[$file.FullName]
        if ($null -eq $state) {
            $newFiles += $file
            $fileState[$file.FullName] = @{ Ticks = $file.LastWriteTimeUtc.Ticks; Length = $file.Length }
            continue
        }
        if ($file.LastWriteTimeUtc.Ticks -gt $state.Ticks -or $file.Length -ne $state.Length) {
            $newFiles += $file
            $fileState[$file.FullName].Ticks = $file.LastWriteTimeUtc.Ticks
            $fileState[$file.FullName].Length = $file.Length
        }
    }

    if ($newFiles.Count -gt 0) {
        foreach ($file in $newFiles) {
            if ($file.Name -match 'artifact-(\d+)') {
                $uniqueArtifacts[$matches[1]] = $true
            }
            if ($null -eq $firstObservedWrite -or $file.LastWriteTimeUtc -lt $firstObservedWrite) {
                $firstObservedWrite = $file.LastWriteTimeUtc
            }
            if ($null -eq $lastObservedWrite -or $file.LastWriteTimeUtc -gt $lastObservedWrite) {
                $lastObservedWrite = $file.LastWriteTimeUtc
            }
            $processedBytes += $file.Length
        }
    }

    $processedDelta = $newFiles.Count
    $processedTotal += $processedDelta
    $uniqueCount = $uniqueArtifacts.Count

    $now = Get-Date
    $elapsed = $now - $start
    $elapsedMinutes = [math]::Max(1e-9, $elapsed.TotalMinutes)
    $avgArtifactsPerMinute = $processedTotal / $elapsedMinutes
    $windowMinutes = [math]::Max(1e-9, ($now - $prevTime).TotalMinutes)
    $instArtifactsPerMinute = if ($processedTotal -ge $prevProcessed) { ($processedTotal - $prevProcessed) / $windowMinutes } else { 0 }
    $prevProcessed = $processedTotal
    $prevTime = $now

    $remaining = [math]::Max(0, $TotalArtifacts - $processedTotal)
    $etaMinutes = if ($avgArtifactsPerMinute -gt 0) { $remaining / $avgArtifactsPerMinute } else { [double]::PositiveInfinity }
    $etaText = if ([double]::IsPositiveInfinity($etaMinutes)) { "n/a" } else { [timespan]::FromMinutes($etaMinutes).ToString("dd\:hh\:mm\:ss") }

    $sizeGb = [math]::Round([double]$processedBytes / 1GB, 3)

    $line = [PSCustomObject]@{
        Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        Pid = $pid
        ProcessedFiles = $processedTotal
        UniqueArtifacts = $uniqueCount
        Elapsed = $elapsed.ToString("hh\:mm\:ss")
        AvgSpeedPerMin = [math]::Round($avgArtifactsPerMinute, 2)
        InstSpeedPerMin = [math]::Round($instArtifactsPerMinute, 2)
        Remaining = $remaining
        ETA = $etaText
        OutputSizeGb = $sizeGb
        FirstWriteUtc = $firstObservedWrite
        LastWriteUtc = $lastObservedWrite
        WorkingSetGb = [math]::Round($p.WorkingSet64 / 1GB, 3)
        HandleCount = $p.HandleCount
        ThreadCount = $p.Threads.Count
    }

    Write-Output ($line | ConvertTo-Json -Depth 3)

    Start-Sleep -Seconds $IntervalSec
}
