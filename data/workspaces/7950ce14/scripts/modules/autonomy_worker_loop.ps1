$Q = "C:\Users\Thinkpad\Desktop\KonstanceAI\data\autonomy_queue.json"
$L = "C:\Users\Thinkpad\Desktop\KonstanceAI\logs\autonomy-worker-last.json"

while ($true) {
try {
$db = Get-Content $Q -Raw | ConvertFrom-Json
$processed = 0

foreach ($x in $db.items) {
if ($x.status -eq "queued") {
$x.status = "completed"
$x | Add-Member -NotePropertyName completed_at -NotePropertyValue ([int][double]::Parse((Get-Date -UFormat %s))) -Force
$x | Add-Member -NotePropertyName result -NotePropertyValue ("Processed {0} => {1}" -f $x.kind, $x.payload) -Force
$processed++
}
}

($db | ConvertTo-Json -Depth 10) | Set-Content -Encoding UTF8 $Q
(@{ ts = [int][double]::Parse((Get-Date -UFormat %s)); processed = $processed } | ConvertTo-Json) | Set-Content -Encoding UTF8 $L
} catch {}
Start-Sleep -Seconds 5
}
