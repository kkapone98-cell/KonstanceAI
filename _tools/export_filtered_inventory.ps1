param(
  [string]$OutPath = ".\\_file_inventory_filtered.csv"
)

$pattern = '\\(\.venv|node_modules|__pycache__|\.git)\\'

Get-ChildItem -Recurse -File |
  Where-Object { $_.FullName -notmatch $pattern } |
  Select-Object FullName, Length |
  Sort-Object FullName |
  Export-Csv -NoTypeInformation -Encoding UTF8 $OutPath

