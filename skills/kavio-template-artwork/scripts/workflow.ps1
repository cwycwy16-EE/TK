param(
    [ValidateSet('verify','prepare')][string]$Mode = 'verify',
    [string]$TemplateRoot = 'D:\跨境美工成品\_固定母版\KAVIO_35630_v1',
    [string]$Product,
    [string]$SourceDir,
    [string]$OutputDir
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $TemplateRoot).Path
$rules = Join-Path $root '母版使用规则.md'
if (-not (Test-Path -LiteralPath $rules -PathType Leaf)) { throw '母版规则缺失' }
$manifest = @(Get-Content -LiteralPath (Join-Path $root 'reference-manifest.json') -Raw -Encoding utf8 | ConvertFrom-Json)
if ($manifest.Count -ne 14) { throw '母版应包含14张参考图' }
$seen = @{}
foreach ($row in $manifest) {
    if ($seen.ContainsKey($row.relative_path)) { throw '参考路径重复' }
    $seen[$row.relative_path] = $true
    $path = [IO.Path]::GetFullPath((Join-Path (Join-Path $root '参考原图') $row.relative_path))
    if (-not $path.StartsWith(($root.TrimEnd('\') + '\'), [StringComparison]::OrdinalIgnoreCase)) { throw '参考路径越界' }
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $row.sha256) { throw "母版校验失败: $path" }
}
if ($Mode -eq 'verify') {
    [pscustomobject]@{status='verified'; references=$manifest.Count; template_root=$root} | ConvertTo-Json
    return
}
if ([string]::IsNullOrWhiteSpace($Product) -or [string]::IsNullOrWhiteSpace($SourceDir) -or [string]::IsNullOrWhiteSpace($OutputDir)) { throw 'prepare需要Product、SourceDir、OutputDir' }
if (-not (Test-Path -LiteralPath $SourceDir -PathType Container)) { throw '新品素材目录不存在' }
if (Test-Path -LiteralPath $OutputDir) { throw '目标目录已存在；请读取并继续原任务，不覆盖' }
$source = (Resolve-Path -LiteralPath $SourceDir).Path
$destination = [IO.Path]::GetFullPath($OutputDir)
if ($destination.StartsWith(($root.TrimEnd('\') + '\'), [StringComparison]::OrdinalIgnoreCase) -or $destination -eq $root) { throw '不能写入母版目录' }
$assets = @(Get-ChildItem -LiteralPath $source -Recurse -File | Where-Object { $_.Extension -in '.png','.jpg','.jpeg','.webp','.pdf','.txt','.json','.md','.xlsx','.mp4' } | ForEach-Object {
    [ordered]@{path=$_.FullName; sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}
})
if ($assets.Count -eq 0) { throw '新品目录中未发现可用素材或资料' }
$pages = @($manifest | ForEach-Object {
    [ordered]@{
        reference=$_.relative_path
        reference_path=(Join-Path (Join-Path $root '参考原图') $_.relative_path)
        reference_sha256=$_.sha256
        width=$_.width; height=$_.height
        status='needs_evidence'; replacements=@{}; evidence=@(); output_file=$null
        review=[ordered]@{layout='pending'; appearance='pending'; copy='pending'; facts='pending'; reviewer=$null; reviewed_at=$null; issues=@()}
    }
})
$task = [ordered]@{
    schema_version=1; template='KAVIO_35630_v1'; template_root=$root
    rules_sha256=(Get-FileHash -LiteralPath $rules -Algorithm SHA256).Hash
    product=$Product; market=$null; language=$null; sku=$null; scope=$null
    source_dir=$source; source_assets=$assets; created_at=[DateTimeOffset]::Now.ToString('o')
    status='prepared_not_generated'; pages=$pages
}
New-Item -ItemType Directory -Path $destination | Out-Null
$task | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $destination 'workflow.json') -Encoding utf8
[pscustomobject]@{status='prepared_not_generated'; pages=$pages.Count; assets=$assets.Count; workflow=(Join-Path $destination 'workflow.json')} | ConvertTo-Json
