# SignTool_QuickStart.ps1
param(
    [string]$ExePath = ".\dist\The_Channelizer_v3.5.exe",
    [string]$CommonName = "TheChannelizer Dev",
    [string]$PfxOut = "$env:USERPROFILE\Desktop\self-cert.pfx",
    [string]$Password = "ChangeThisPassword!",
    [string]$TimestampUrl = "http://timestamp.sectigo.com"
)

Write-Host "Creating self-signed certificate..."
$cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=$CommonName" -CertStoreLocation Cert:\CurrentUser\My
Export-PfxCertificate -Cert $cert -FilePath $PfxOut -Password (ConvertTo-SecureString -String $Password -Force -AsPlainText)

Write-Host "Signing $ExePath ..."
signtool sign /f "$PfxOut" /p $Password /tr $TimestampUrl /td sha256 /fd sha256 "$ExePath"

Write-Host "Done."
