param([string]$SettingsPath = (Join-Path $PSScriptRoot '../.runtime/wechat-test.json'))
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()
$settingsFile = [System.IO.Path]::GetFullPath($SettingsPath)
if (-not (Test-Path -LiteralPath $settingsFile)) { throw 'Run wechat-test configure first.' }
$settings = Get-Content -LiteralPath $settingsFile -Raw -Encoding UTF8 | ConvertFrom-Json
$form = New-Object System.Windows.Forms.Form
$form.Text = '物业系统 - 微信测试号配置'
$form.Size = New-Object System.Drawing.Size(640, 300)
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$form.MinimizeBox = $false
$form.TopMost = $true
$description = New-Object System.Windows.Forms.Label
$description.Text = '从微信官方测试号页面复制下面两项。密钥仅保存到本机，不上传 GitHub。'
$description.Location = New-Object System.Drawing.Point(20, 20)
$description.Size = New-Object System.Drawing.Size(590, 38)
$form.Controls.Add($description)
$appLabel = New-Object System.Windows.Forms.Label
$appLabel.Text = '测试号 appID'
$appLabel.Location = New-Object System.Drawing.Point(20, 76)
$appLabel.Size = New-Object System.Drawing.Size(120, 25)
$form.Controls.Add($appLabel)
$appBox = New-Object System.Windows.Forms.TextBox
$appBox.Location = New-Object System.Drawing.Point(150, 72)
$appBox.Size = New-Object System.Drawing.Size(450, 28)
$appBox.Text = [string]$settings.appId
$form.Controls.Add($appBox)
$secretLabel = New-Object System.Windows.Forms.Label
$secretLabel.Text = '测试号 appsecret'
$secretLabel.Location = New-Object System.Drawing.Point(20, 120)
$secretLabel.Size = New-Object System.Drawing.Size(125, 25)
$form.Controls.Add($secretLabel)
$secretBox = New-Object System.Windows.Forms.TextBox
$secretBox.Location = New-Object System.Drawing.Point(150, 116)
$secretBox.Size = New-Object System.Drawing.Size(450, 28)
$secretBox.UseSystemPasswordChar = $true
$secretBox.Text = [string]$settings.appSecret
$form.Controls.Add($secretBox)
$resultLabel = New-Object System.Windows.Forms.Label
$resultLabel.Text = ''
$resultLabel.Location = New-Object System.Drawing.Point(20, 162)
$resultLabel.Size = New-Object System.Drawing.Size(580, 28)
$resultLabel.ForeColor = [System.Drawing.Color]::DarkRed
$form.Controls.Add($resultLabel)
$saveButton = New-Object System.Windows.Forms.Button
$saveButton.Text = '保存配置'
$saveButton.Location = New-Object System.Drawing.Point(460, 202)
$saveButton.Size = New-Object System.Drawing.Size(140, 34)
$saveButton.Add_Click({
    $appValue = $appBox.Text.Trim()
    $secretValue = $secretBox.Text.Trim()
    if ($appValue -notmatch '^wx[a-zA-Z0-9]{16}$' -or $secretValue -notmatch '^[a-fA-F0-9]{32}$') {
        $resultLabel.Text = '请检查：appID 通常以 wx 开头，appsecret 为 32 位字符。'
        return
    }
    $settings.appId = $appValue
    $settings.appSecret = $secretValue
    [System.IO.File]::WriteAllText($settingsFile, ($settings | ConvertTo-Json -Depth 8), (New-Object System.Text.UTF8Encoding($false)))
    $form.DialogResult = [System.Windows.Forms.DialogResult]::OK
    $form.Close()
})
$form.Controls.Add($saveButton)
$form.AcceptButton = $saveButton
[void]$form.ShowDialog()
$form.Dispose()
