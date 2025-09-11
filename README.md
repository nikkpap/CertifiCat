# CertifiCat
Create self-signed code-signing certificates on Windows. Generate PFX, export CER, optionally install to Trusted Root (CurrentUser), and sign EXE(s) with timestamp — all from a tiny Tk GUI. Includes signtool auto-discovery, log view, and a built-in Help/About.


🛡️ Security Notes

Protect your PFX password — the PFX contains your private key.

Export and share only the .cer (public certificate).

Timestamping preserves signature validity after the cert expires.

Installing to Trusted Root (CurrentUser) affects only the current user.

🖱️ UI Tips

F1 opens Instructions; Help → About shows app info.

Toggle Show log to expand the log area.

The window auto-fits height based on visible sections.

🧩 How it works (tech notes)

Creates a self-signed code-signing cert via PowerShell:

New-SelfSignedCertificate -Type CodeSigningCert -KeyAlgorithm RSA -KeyLength 3072 -NotAfter (Get-Date).AddYears(3)

Exports to PFX with your password.

Exports .cer from the PFX using Get-PfxData.

Installs CER to Cert:\CurrentUser\Root via Import-Certificate, or falls back to certutil / .NET X509Store API.

Signs EXEs with signtool sign /fd sha256 /td sha256 /tr <timestamp>.

🐞 Troubleshooting

“signtool not found”
Install the Windows SDK or point the signtool.exe Path to a local copy.

Timestamp server errors
Try an alternative URL (see above).

Another PC still shows “Unknown publisher”
They must install your .cer in CurrentUser\Trusted Root (or use a CA-issued cert).

SmartScreen warning
Self-signed certs typically show it. CA-issued certs + reputation reduce it.

🧪 Roadmap

Optional EV/CA-issued cert support (PFX import only)

More timestamp fallbacks + auto-rotate

Separate “Verify signatures” button with detailed report

MSI build script

🤝 Contributing

PRs and issues welcome! Keep UI tidy, avoid external deps, and test on Windows 10/11.

📄 License

GPL-3.0 — see LICENSE
.

❤️ Credits

Icons & app by nikkpap / ALU DEV TEAM.
Thanks to the Windows SDK team for signtool.exe.
