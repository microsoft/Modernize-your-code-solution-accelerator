Get-Content ./.env | ForEach-Object {
    if ($_ -match "^\s*([^=]+?)\s*=\s*(.+?)\s*$") {
        [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}