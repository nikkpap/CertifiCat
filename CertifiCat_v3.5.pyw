# -*- coding: utf-8 -*-
"""
CertifiCat — Self-signed πιστοποιητικά υπογραφής κώδικα & υπογραφή exe/dll/msi/ps1/…
© Νικόλαος Κ. Παρίδης (Nikolaos K. Paridis) · ALU DEV TEAM

Δημόσια έκδοση: ΔΕΝ περιέχει κανένα μυστικό/κλειδί/token. Οι ενημερώσεις (OTA) διαβάζονται από τα
δημόσια GitHub Releases. Ό,τι κωδικό φτιάχνει ο χρήστης μένει ΜΟΝΟ στον υπολογιστή του, σε τοπική βάση,
και μόνο αν το ζητήσει (κρυπτογραφημένο με τον λογαριασμό του στα Windows).

Χρήση από γραμμή εντολών / «Αποστολή προς»:
    CertifiCat_v3.5.pyw  αρχείο1.exe  φάκελος/       → ανοίγει με τα αρχεία στη λίστα
    CertifiCat_v3.5.pyw  --sign  αρχείο1.exe ...     → τα υπογράφει αμέσως (με το τελευταίο πιστοποιητικό)
"""
APP_NAME = "CertifiCat"
APP_VERSION = "3.5.0"
APP_AUTHOR = "ALU DEV TEAM"

# ---- Στοιχεία δημιουργού (εμφανίζονται στο «Σχετικά») ----
AUTHOR_NAME = "Νικόλαος Κ. Παρίδης"
AUTHOR_NAME_EN = "Nikolaos K. Paridis"
AUTHOR_TITLE = "Πολιτικός Μηχανικός · ALU DEV TEAM"
AUTHOR_EMAIL = "nikkpap@gmail.com"
AUTHOR_GITHUB = "https://github.com/nikkpap"

# ---- Ενημερώσεις (OTA) από ΔΗΜΟΣΙΟ αποθετήριο: χωρίς token, χωρίς μυστικά ----
UPDATE_REPO = "nikkpap/CertifiCat"          # github.com/<owner>/<repo> → Releases

import sys, os, subprocess, importlib, importlib.util, json, threading, time, traceback

REQUIRED = [("PyQt6", "PyQt6"), ("cryptography", "cryptography")]
FROZEN = getattr(sys, "frozen", False)
IS_WIN = os.name == "nt"
NOWIN = 0x08000000 if IS_WIN else 0          # CREATE_NO_WINDOW


# ════════════════════════════════════════════════════════════════════
# 0. Αυτόματη εγκατάσταση βιβλιοθηκών
# ════════════════════════════════════════════════════════════════════
def _python_exe(windowed=False):
    exe = sys.executable
    low = exe.lower()
    if not windowed and low.endswith("pythonw.exe"):
        c = exe[:-len("pythonw.exe")] + "python.exe"
        if os.path.exists(c):
            return c
    if windowed and low.endswith("python.exe"):
        c = exe[:-len("python.exe")] + "pythonw.exe"
        if os.path.exists(c):
            return c
    return exe


def _pip(args, timeout=900):
    return subprocess.run([_python_exe(), "-m", "pip", *args, "--disable-pip-version-check"],
                          capture_output=True, text=True, timeout=timeout, creationflags=NOWIN,
                          stdin=subprocess.DEVNULL)


def ensure_dependencies():
    if FROZEN:
        return
    missing = [pkg for mod, pkg in REQUIRED if importlib.util.find_spec(mod) is None]
    if not missing:
        return
    win = None
    status = None
    try:
        import tkinter as tk
        from tkinter import ttk
        win = tk.Tk(); win.title(APP_NAME); win.geometry("480x150"); win.configure(bg="#362044")
        win.resizable(False, False)
        tk.Label(win, text="CertifiCat — Πρώτη εκκίνηση", fg="white", bg="#362044",
                 font=("Segoe UI", 13, "bold")).pack(pady=(18, 6))
        status = tk.StringVar(value="Εγκατάσταση: " + ", ".join(missing) + " …")
        tk.Label(win, textvariable=status, fg="#D9CCE6", bg="#362044").pack()
        bar = ttk.Progressbar(win, mode="indeterminate", length=400); bar.pack(pady=14); bar.start(12)
        win.update()
    except Exception:
        win = None
    res = {}

    def work():
        try:
            r = _pip(["--version"], timeout=60)
            if r.returncode != 0:          # δεν υπάρχει pip → ensurepip
                res["msg"] = "Εγκατάσταση pip…"
                subprocess.run([_python_exe(), "-m", "ensurepip", "--upgrade"], capture_output=True,
                               creationflags=NOWIN, timeout=300, stdin=subprocess.DEVNULL)
            res["msg"] = "Εγκατάσταση: " + ", ".join(missing) + " …"
            r = _pip(["install", "--upgrade", *missing])
            if r.returncode != 0:
                res["msg"] = "Δεύτερη προσπάθεια (μόνο για τον χρήστη)…"
                r = _pip(["install", "--user", "--upgrade", *missing])
            res["ok"], res["err"] = r.returncode == 0, (r.stderr or r.stdout)[-800:]
        except Exception as ex:
            res["ok"], res["err"] = False, str(ex)
    t = threading.Thread(target=work, daemon=True); t.start()
    while t.is_alive():
        if win:
            try:
                if res.get("msg") and status is not None:
                    status.set(res["msg"])
                win.update()
            except Exception:
                pass
        time.sleep(0.05)
    if win:
        try:
            win.destroy()
        except Exception:
            pass
    if not res.get("ok"):
        try:
            import tkinter as tk
            import tkinter.messagebox as mb
            r = tk.Tk(); r.withdraw()
            mb.showerror(APP_NAME, "Δεν εγκαταστάθηκαν οι βιβλιοθήκες:\n" + ", ".join(missing) +
                         "\n\nΕλέγξτε τη σύνδεση στο internet και ξαναδοκιμάστε.\n\n" + res.get("err", ""))
        except Exception:
            print(res)
        sys.exit(1)
    importlib.invalidate_caches()
    import site
    try:
        p = site.getusersitepackages()
        if p not in sys.path:
            sys.path.append(p)
    except Exception:
        pass


ensure_dependencies()

import re, secrets, string, zipfile, base64, hashlib, shutil, tempfile
from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12

from PyQt6.QtCore import Qt, QTimer, QThread, QObject, pyqtSignal, QRectF, QPointF, QUrl
from PyQt6.QtGui import (QIcon, QPixmap, QPainter, QColor, QLinearGradient, QBrush, QPen, QPainterPath,
                         QPolygonF, QDesktopServices, QGuiApplication, QKeySequence, QShortcut, QFont)
from PyQt6.QtWidgets import (QApplication, QWidget, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
                             QGridLayout, QStackedWidget, QLineEdit, QSpinBox, QComboBox, QCheckBox, QFileDialog,
                             QMessageBox, QGroupBox, QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView,
                             QAbstractItemView, QProgressBar, QTextEdit, QPlainTextEdit, QDialog, QMenu)

SIGNABLE = (".exe", ".dll", ".msi", ".sys", ".ocx", ".cab", ".cat", ".ps1", ".psm1", ".psd1",
            ".msix", ".appx", ".msixbundle", ".appxbundle", ".vbs", ".js")
NEEDS_SIGNTOOL = (".msix", ".appx", ".msixbundle", ".appxbundle")
TIMESTAMPS = [("DigiCert (προτείνεται)", "http://timestamp.digicert.com"),
              ("Sectigo", "http://timestamp.sectigo.com"),
              ("GlobalSign", "http://timestamp.globalsign.com/tsa/r6advanced1"),
              ("Χωρίς χρονοσήμανση (offline)", "")]
METHODS = [("Αυτόματα (signtool αν υπάρχει)", "auto"), ("Πάντα signtool", "signtool"),
           ("Πάντα PowerShell των Windows", "powershell")]


# ════════════════════════════════════════════════════════════════════
# 1. Ρυθμίσεις, καταγραφή, αποθήκευση κωδικού (Windows DPAPI)
# ════════════════════════════════════════════════════════════════════
def config_dir():
    base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), ".config")
    d = os.path.join(base, "CertifiCat")
    os.makedirs(d, exist_ok=True)
    return d


_CFG_LOCK = threading.Lock()


def load_cfg():
    with _CFG_LOCK:
        try:
            with open(os.path.join(config_dir(), "config.json"), encoding="utf-8") as f:
                c = json.load(f)
                return c if isinstance(c, dict) else {}
        except Exception:
            return {}


def save_cfg(c):
    with _CFG_LOCK:
        try:
            p = os.path.join(config_dir(), "config.json")
            tmp = p + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(c, f, ensure_ascii=False, indent=1)
            os.replace(tmp, p)                      # ατομική εγγραφή: δεν «σπάει» αν κλείσει απότομα
        except Exception:
            pass


def update_cfg(**kw):
    c = load_cfg(); c.update(kw); save_cfg(c)


class _Log(QObject):
    line = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.buffer = []
        self.path = os.path.join(config_dir(), "certificat.log")
        try:
            if os.path.exists(self.path) and os.path.getsize(self.path) > 1_000_000:
                os.replace(self.path, self.path + ".old")
        except Exception:
            pass

    def __call__(self, msg):
        for part in str(msg).rstrip().splitlines() or [""]:
            s = f"[{datetime.now():%H:%M:%S}] {part}"
            self.buffer.append(s)
            del self.buffer[:-3000]
            try:
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now():%Y-%m-%d} {s}\n")
            except Exception:
                pass
            self.line.emit(s)


log = _Log()


def _pw_key(pfx_path):
    return os.path.normcase(os.path.abspath(pfx_path))


def _dpapi(data: bytes, protect=True):
    """Κρυπτογράφηση με τον λογαριασμό Windows του χρήστη (μόνο αυτός τον ξεκλειδώνει)."""
    if not IS_WIN:
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class BLOB(ctypes.Structure):
            _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]
        buf = ctypes.create_string_buffer(data, len(data))
        inp = BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
        out = BLOB()
        crypt32 = ctypes.windll.crypt32
        if protect:
            ok = crypt32.CryptProtectData(ctypes.byref(inp), ctypes.c_wchar_p("CertifiCat"), None, None, None, 0,
                                          ctypes.byref(out))
        else:
            ok = crypt32.CryptUnprotectData(ctypes.byref(inp), None, None, None, None, 0, ctypes.byref(out))
        if not ok:
            return None
        res = ctypes.string_at(out.pbData, out.cbData)
        ctypes.windll.kernel32.LocalFree(out.pbData)
        return res
    except Exception:
        return None


# ---- Κλειδοθήκη: τοπική βάση SQLite (%APPDATA%\\CertifiCat\\certificat.db) ----
# Κρατά τη λίστα πιστοποιητικών (μόνο δημόσια στοιχεία: όνομα, λήξη, διαδρομές).
# Ο κωδικός του .pfx αποθηκεύεται ΜΟΝΟ αν το ζητήσει ο χρήστης, κρυπτογραφημένος με DPAPI
# (ξεκλειδώνει μόνο ο ίδιος λογαριασμός Windows). Τίποτα δεν φεύγει από τον υπολογιστή.
import sqlite3
from contextlib import closing

DB_LOCK = threading.Lock()


def db_path():
    return os.path.join(config_dir(), "certificat.db")


def _db():
    con = sqlite3.connect(db_path(), timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS certs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pfx_key TEXT UNIQUE NOT NULL, pfx_path TEXT NOT NULL,
        cn TEXT DEFAULT '', org TEXT DEFAULT '', thumbprint TEXT DEFAULT '', not_after TEXT DEFAULT '',
        cer_path TEXT DEFAULT '', zip_path TEXT DEFAULT '',
        created TEXT DEFAULT '', last_used TEXT DEFAULT '', pw_enc TEXT, note TEXT DEFAULT '')""")
    return con


def _db_exec(sql, args=(), fetch=False):
    with DB_LOCK:
        try:
            with closing(_db()) as con, con:
                cur = con.execute(sql, args)
                return [dict(r) for r in cur.fetchall()] if fetch else cur.rowcount
        except Exception as ex:
            try:
                log(f"Βάση: {ex}")
            except Exception:
                pass
            return [] if fetch else 0


def register_cert(pfx_path, info=None, cer_path=None, zip_path=None):
    """Προσθέτει/ενημερώνει ένα πιστοποιητικό στη λίστα της Κλειδοθήκης (χωρίς κωδικό)."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    _db_exec("INSERT OR IGNORE INTO certs(pfx_key, pfx_path, created) VALUES(?,?,?)",
             (_pw_key(pfx_path), os.path.abspath(pfx_path), now))
    sets, args = ["pfx_path=?", "last_used=?"], [os.path.abspath(pfx_path), now]
    if info:
        sets += ["cn=?", "org=?", "thumbprint=?", "not_after=?"]
        args += [info.get("cn", ""), info.get("org", ""), info.get("thumbprint", ""),
                 info["not_after"].strftime("%Y-%m-%d") if info.get("not_after") else ""]
    if cer_path:
        sets.append("cer_path=?"); args.append(os.path.abspath(cer_path))
    if zip_path:
        sets.append("zip_path=?"); args.append(os.path.abspath(zip_path))
    _db_exec(f"UPDATE certs SET {', '.join(sets)} WHERE pfx_key=?", (*args, _pw_key(pfx_path)))


def list_certs():
    return _db_exec("SELECT * FROM certs ORDER BY last_used DESC, id DESC", fetch=True)


def delete_cert(cid):
    return _db_exec("DELETE FROM certs WHERE id=?", (cid,))


def store_password(pfx_path, pw):
    enc = _dpapi(pw.encode("utf-8"), True)
    if enc is None:
        return False
    register_cert(pfx_path)
    _db_exec("UPDATE certs SET pw_enc=? WHERE pfx_key=?", (base64.b64encode(enc).decode(), _pw_key(pfx_path)))
    return True


def recall_password(pfx_path):
    try:
        rows = _db_exec("SELECT pw_enc FROM certs WHERE pfx_key=?", (_pw_key(pfx_path),), fetch=True)
        v = rows[0]["pw_enc"] if rows else None
        if not v:
            return ""
        raw = _dpapi(base64.b64decode(v), False)
        return raw.decode("utf-8") if raw else ""
    except Exception:
        return ""


def has_password(pfx_path):
    rows = _db_exec("SELECT pw_enc FROM certs WHERE pfx_key=?", (_pw_key(pfx_path),), fetch=True)
    return bool(rows and rows[0]["pw_enc"])


def forget_password(pfx_path):
    _db_exec("UPDATE certs SET pw_enc=NULL WHERE pfx_key=?", (_pw_key(pfx_path),))


def migrate_old_versions():
    """Μία φορά: φέρνει ρυθμίσεις & αποθηκευμένους κωδικούς από το παλιό «ALU CertSign»."""
    c = load_cfg()
    if c.get("migrated_from_certsign"):
        return
    base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), ".config")
    old = os.path.join(base, "ALU_" + "CertSign", "config.json")
    n = 0
    try:
        if os.path.isfile(old):
            with open(old, encoding="utf-8") as f:
                oc = json.load(f)
            pws = oc.pop("passwords", {}) or {}
            for k, v in oc.items():
                c.setdefault(k, v)
            for path, enc in pws.items():
                _db_exec("INSERT OR IGNORE INTO certs(pfx_key, pfx_path, created) VALUES(?,?,?)",
                         (_pw_key(path), path, datetime.now().strftime("%Y-%m-%d %H:%M")))
                _db_exec("UPDATE certs SET pw_enc=? WHERE pfx_key=? AND pw_enc IS NULL", (enc, _pw_key(path)))
                n += 1
            log(f"Μεταφορά από ALU CertSign: ρυθμίσεις + {n} αποθηκευμένοι κωδικοί")
    except Exception as ex:
        log(f"Μεταφορά παλιών ρυθμίσεων: {ex}")
    c["migrated_from_certsign"] = True
    save_cfg(c)


def default_publisher():
    user = os.environ.get("USERNAME") or os.environ.get("USER") or "My Company"
    return f"{user} - Code Signing"


def gen_password(n=24):
    a = string.ascii_letters + string.digits
    while True:
        p = "".join(secrets.choice(a) for _ in range(n))
        if any(c.islower() for c in p) and any(c.isupper() for c in p) and any(c.isdigit() for c in p):
            return p


# ════════════════════════════════════════════════════════════════════
# 2. Πιστοποιητικά
# ════════════════════════════════════════════════════════════════════
def make_certificate(cn, org="", country="GR", years=10, password="", key_bits=3072, compatible=True):
    """Self-signed πιστοποιητικό ΜΟΝΟ για υπογραφή κώδικα (CA:FALSE, EKU=Code Signing).
    Επιστρέφει (pfx_bytes, cer_der_bytes, info)."""
    cn = cn.strip()
    country = (country or "").strip().upper()
    if not cn:
        raise ValueError("Λείπει το όνομα εκδότη.")
    if country and not re.fullmatch(r"[A-Z]{2}", country):
        raise ValueError("Η χώρα πρέπει να είναι 2 λατινικά γράμματα (π.χ. GR) ή κενή.")
    key = rsa.generate_private_key(public_exponent=65537, key_size=key_bits)
    attrs = [x509.NameAttribute(NameOID.COMMON_NAME, cn)]
    if org.strip():
        attrs.append(x509.NameAttribute(NameOID.ORGANIZATION_NAME, org.strip()))
    if country:
        attrs.append(x509.NameAttribute(NameOID.COUNTRY_NAME, country))
    name = x509.Name(attrs)
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder()
            .subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=1))
            .not_valid_after(now + timedelta(days=int(365.25 * years)))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.KeyUsage(digital_signature=True, content_commitment=False, key_encipherment=False,
                                         data_encipherment=False, key_agreement=False, key_cert_sign=False,
                                         crl_sign=False, encipher_only=False, decipher_only=False), critical=True)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CODE_SIGNING]), critical=True)
            .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
            .sign(key, hashes.SHA256()))
    if compatible:   # 3DES/SHA1 μέσα στο PFX: ανοίγει σε ΟΛΑ τα Windows (και παλιά)
        enc = (serialization.PrivateFormat.PKCS12.encryption_builder().kdf_rounds(50000)
               .key_cert_algorithm(pkcs12.PBES.PBESv1SHA1And3KeyTripleDESCBC).hmac_hash(hashes.SHA1())
               .build(password.encode("utf-8")))
    else:
        enc = serialization.BestAvailableEncryption(password.encode("utf-8"))
    pfx = pkcs12.serialize_key_and_certificates(cn.encode("utf-8"), key, cert, None, enc)
    der = cert.public_bytes(serialization.Encoding.DER)
    return pfx, der, cert_info(cert)


def load_pfx(path, password):
    with open(path, "rb") as f:
        data = f.read()
    try:
        key, cert, extra = pkcs12.load_key_and_certificates(data, password.encode("utf-8") if password else None)
    except ValueError:
        raise ValueError("Λάθος κωδικός ή κατεστραμμένο αρχείο .pfx.")
    except Exception as ex:
        raise ValueError(f"Το αρχείο δεν διαβάζεται ως .pfx ({type(ex).__name__}).")
    if cert is None or key is None:
        raise ValueError("Το αρχείο δεν περιέχει πιστοποιητικό με ιδιωτικό κλειδί.")
    return key, cert


def cert_info(cert):
    def get(oid):
        v = cert.subject.get_attributes_for_oid(oid)
        return v[0].value if v else ""
    try:
        eku = [o.dotted_string for o in cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value]
    except x509.ExtensionNotFound:
        eku = []
    try:
        is_ca = cert.extensions.get_extension_for_class(x509.BasicConstraints).value.ca
    except x509.ExtensionNotFound:
        is_ca = None
    nb = getattr(cert, "not_valid_before_utc", None) or cert.not_valid_before.replace(tzinfo=timezone.utc)
    na = getattr(cert, "not_valid_after_utc", None) or cert.not_valid_after.replace(tzinfo=timezone.utc)
    der = cert.public_bytes(serialization.Encoding.DER)
    cs = ExtendedKeyUsageOID.CODE_SIGNING.dotted_string
    return {"cn": get(NameOID.COMMON_NAME) or cert.subject.rfc4514_string(), "org": get(NameOID.ORGANIZATION_NAME),
            "country": get(NameOID.COUNTRY_NAME),
            "not_before": nb, "not_after": na, "thumbprint": hashlib.sha1(der).hexdigest().upper(),
            "codesign_only": eku == [cs], "has_codesign": (cs in eku) or not eku,   # χωρίς EKU = κάθε χρήση
            "is_ca": is_ca, "self_signed": cert.subject == cert.issuer,
            "key_bits": getattr(cert.public_key(), "key_size", 0)}


def days_left(info):
    return (info["not_after"] - datetime.now(timezone.utc)).days


def fmt_thumb(t):
    return ":".join(t[i:i + 2] for i in range(0, len(t), 2))


# ---- πακέτο εγκατάστασης για άλλους υπολογιστές ----
INSTALL_BAT = r"""@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Εγκατάσταση πιστοποιητικού - {cn}
echo.
echo  Εγκατάσταση πιστοποιητικού "{cn}"
echo  (μόνο για υπογραφή προγραμμάτων - δεν επηρεάζει ιστοσελίδες/internet)
echo.
if not exist "{cer}" (echo  [!] Λείπει το {cer} - αποσυμπιέστε πρώτα ΟΛΟ το zip. & pause & exit /b 1)
net session >nul 2>&1
if %errorlevel%==0 goto ALL
echo   1 = Μόνο για εμένα
echo   2 = Για ΟΛΟΥΣ τους χρήστες του υπολογιστή (θα ζητηθεί άδεια διαχειριστή)
echo.
choice /c 12 /n /m "  Επιλογή [1 ή 2]: "
if errorlevel 2 goto ELEVATE
goto USER

:ELEVATE
powershell -NoProfile -Command "Start-Process -FilePath \"%~f0\" -Verb RunAs" >nul 2>&1
if errorlevel 1 (echo. & echo  [!] Δεν δόθηκε άδεια διαχειριστή. Δοκιμάστε την επιλογή 1. & pause & exit /b 1)
exit /b 0

:ALL
echo  Εγκατάσταση για ΟΛΟΥΣ τους χρήστες...
certutil -addstore -f TrustedPublisher "{cer}" >nul || goto FAIL
certutil -addstore -f Root "{cer}" >nul || goto FAIL
goto OK

:USER
echo.
echo  Εγκατάσταση για τον τρέχοντα χρήστη.
echo  Τα Windows θα εμφανίσουν «Προειδοποίηση ασφαλείας» - πατήστε ΝΑΙ.
certutil -user -addstore -f TrustedPublisher "{cer}" >nul || goto FAIL
certutil -user -addstore -f Root "{cer}" >nul || goto FAIL
goto OK

:FAIL
echo.
echo  [!] Η εγκατάσταση απέτυχε ή ακυρώθηκε.
echo.
pause
exit /b 1

:OK
echo.
echo  ✓ Έτοιμο! Τα προγράμματα του "{cn}" θα εμφανίζονται με το όνομα του εκδότη.
echo.
pause
exit /b 0
"""
UNINSTALL_BAT = r"""@echo off
chcp 65001 >nul
title Αφαίρεση πιστοποιητικού - {cn}
set TP={tp}
net session >nul 2>&1
if %errorlevel%==0 (
  certutil -delstore Root %TP% >nul 2>&1
  certutil -delstore TrustedPublisher %TP% >nul 2>&1
  echo  ✓ Αφαιρέθηκε για όλους τους χρήστες.
)
certutil -user -delstore Root %TP% >nul 2>&1
certutil -user -delstore TrustedPublisher %TP% >nul 2>&1
echo  ✓ Αφαιρέθηκε για τον τρέχοντα χρήστη.
echo  (Αν είχε εγκατασταθεί «για όλους», τρέξτε το αρχείο με δεξί κλικ → Εκτέλεση ως διαχειριστής.)
echo.
pause
"""
README_TXT = """Πιστοποιητικό εκδότη: {cn}
{line}

Τι κάνει: τα Windows αναγνωρίζουν τα προγράμματα που υπογράφονται με αυτό ως «{cn}»
αντί για «Άγνωστος εκδότης». Γίνεται ΜΙΑ φορά σε κάθε υπολογιστή.

Εγκατάσταση
1. Αποσυμπιέστε ΟΛΟ το zip σε έναν φάκελο (όχι διπλό κλικ μέσα από το zip).
2. Διπλό κλικ στο Install_Certificate.bat
   → 1 = μόνο για εσάς (πατήστε «Ναι» στην προειδοποίηση των Windows)
   → 2 = για όλους τους χρήστες (θα ζητηθεί άδεια διαχειριστή)

Ασφάλεια
- Μόνο για υπογραφή προγραμμάτων (Code Signing, CA:FALSE): δεν μπορεί να εκδώσει άλλα
  πιστοποιητικά ούτε να επηρεάσει ιστοσελίδες/HTTPS.
- Το .cer είναι μόνο το δημόσιο κομμάτι (κανένα μυστικό).
- Αποτύπωμα SHA1: {tpf}
- Λήγει: {exp}

Τμήμα πληροφορικής: Group Policy → Public Key Policies → Trusted Root Certification Authorities
ΚΑΙ Trusted Publishers.
Αφαίρεση: Uninstall_Certificate.bat
"""


def safe_name(s):
    s = re.sub(r"[^\w\-. ]+", "_", s, flags=re.UNICODE).strip().replace(" ", "_").strip("._")
    return s[:60] or "certificate"


def make_install_package(cer_der, info, zip_path):
    cer = "Certificate.cer"      # λατινικά ονόματα: ο Explorer δεν «σπάει» ελληνικά ονόματα αρχείων μέσα σε zip
    files = {
        cer: cer_der,
        "Install_Certificate.bat": INSTALL_BAT.format(cn=info["cn"], cer=cer).replace("\n", "\r\n").encode("utf-8"),
        "Uninstall_Certificate.bat": UNINSTALL_BAT.format(cn=info["cn"], tp=info["thumbprint"].lower())
                                     .replace("\n", "\r\n").encode("utf-8"),
        "README.txt": ("\ufeff" + README_TXT.format(cn=info["cn"], line="=" * (24 + len(info["cn"])),
                                                   tpf=fmt_thumb(info["thumbprint"]),
                                                   exp=info["not_after"].strftime("%d/%m/%Y"))
                       ).replace("\n", "\r\n").encode("utf-8"),
    }
    tmp = zip_path + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for n, d in files.items():
            z.writestr(n, d)
    os.replace(tmp, zip_path)
    return zip_path


# ════════════════════════════════════════════════════════════════════
# 3. Εργαλεία Windows: signtool / PowerShell / certutil
# ════════════════════════════════════════════════════════════════════
_SIGNTOOL_CACHE = {"done": False, "path": None}


def _app_dir():
    return os.path.dirname(sys.executable if FROZEN else os.path.abspath(__file__))


def find_signtool_auto(refresh=False):
    if not IS_WIN:
        return None
    if _SIGNTOOL_CACHE["done"] and not refresh:
        return _SIGNTOOL_CACHE["path"]
    found = None
    for p in (os.path.join(_app_dir(), "signtool.exe"), os.path.join(_app_dir(), "tools", "signtool.exe")):
        if os.path.isfile(p):
            found = p; break
    if not found:
        found = shutil.which("signtool")
    if not found:
        cands = []
        for env, dflt in (("ProgramFiles(x86)", r"C:\Program Files (x86)"), ("ProgramFiles", r"C:\Program Files")):
            root = os.path.join(os.environ.get(env, dflt), "Windows Kits", "10", "bin")
            if not os.path.isdir(root):
                continue
            try:
                for ver in os.listdir(root):
                    for arch, rank in (("x64", 2), ("x86", 1)):
                        p = os.path.join(root, ver, arch, "signtool.exe")
                        if os.path.isfile(p):
                            vkey = tuple(int(x) if x.isdigit() else 0 for x in ver.split("."))
                            cands.append((vkey, rank, p))
            except OSError:
                pass
        legacy = os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
                              "Microsoft SDKs", "ClickOnce", "SignTool", "signtool.exe")
        if os.path.isfile(legacy):
            cands.append(((0,), 0, legacy))
        if cands:
            found = max(cands)[2]          # νεότερη έκδοση SDK, προτίμηση x64
    _SIGNTOOL_CACHE.update(done=True, path=found)
    return found


def get_signtool(cfg=None):
    cfg = cfg if cfg is not None else load_cfg()
    p = (cfg.get("signtool_path") or "").strip()
    if p and os.path.isfile(p):
        return p
    return find_signtool_auto()


def _ps_exe():
    p = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "WindowsPowerShell", "v1.0", "powershell.exe")
    return p if os.path.exists(p) else "powershell.exe"


def _ps_env(extra=None):
    env = dict(os.environ)
    # Αν υπάρχει και PowerShell 7, το PSModulePath του μπερδεύει το Windows PowerShell 5.1
    sysroot = os.environ.get("SystemRoot", r"C:\Windows")
    env["PSModulePath"] = ";".join([
        os.path.join(os.path.expanduser("~"), "Documents", "WindowsPowerShell", "Modules"),
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "WindowsPowerShell", "Modules"),
        os.path.join(sysroot, "system32", "WindowsPowerShell", "v1.0", "Modules")])
    env.update(extra or {})
    return env


def _ps(script, env_extra=None, timeout=180):
    return subprocess.run([_ps_exe(), "-NoLogo", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                           "-Command", script],
                          capture_output=True, text=True, timeout=timeout, env=_ps_env(env_extra),
                          creationflags=NOWIN, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)


def _run(cmd, timeout=180):
    return subprocess.run(cmd, capture_output=True, text=True, creationflags=NOWIN, timeout=timeout,
                          encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)


def _last_json(text):
    for line in reversed((text or "").strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except Exception:
                pass
    return None


# Ο κωδικός περνά με μεταβλητή περιβάλλοντος: ΔΕΝ φαίνεται στη γραμμή εντολών της διεργασίας.
PS_SIGN = r"""
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$c = $null
try {
  $c = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($env:CS_PFX, $env:CS_PW)
  $p = @{ LiteralPath = $env:CS_FILE; Certificate = $c; HashAlgorithm = 'SHA256'; ErrorAction = 'Stop' }
  if ($env:CS_TS) { $p.TimestampServer = $env:CS_TS }
  $r = Set-AuthenticodeSignature @p
  $o = [ordered]@{ Status = "$($r.Status)"; Message = "$($r.StatusMessage)"; Signed = [bool]$r.SignerCertificate }
} catch {
  $o = [ordered]@{ Status = 'Error'; Message = "$($_.Exception.Message)"; Signed = $false }
} finally { if ($c) { $c.Reset() } }
$o | ConvertTo-Json -Compress
"""

PS_VERIFY_MANY = r"""
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$files = [IO.File]::ReadAllLines($env:CS_LIST, [Text.Encoding]::UTF8)
$i = 0
foreach ($f in $files) {
  try {
    $r = Get-AuthenticodeSignature -LiteralPath $f -ErrorAction Stop
    $o = [ordered]@{ I = $i; Status = "$($r.Status)"; Message = "$($r.StatusMessage)";
      Signer = if ($r.SignerCertificate) { $r.SignerCertificate.Subject } else { "" };
      Thumb = if ($r.SignerCertificate) { $r.SignerCertificate.Thumbprint } else { "" };
      Timestamp = if ($r.TimeStamperCertificate) { $r.TimeStamperCertificate.Subject } else { "" } }
  } catch {
    $o = [ordered]@{ I = $i; Status = 'Error'; Message = "$($_.Exception.Message)"; Signer = ''; Thumb = ''; Timestamp = '' }
  }
  [Console]::Out.WriteLine(($o | ConvertTo-Json -Compress))
  [Console]::Out.Flush()
  $i++
}
"""

_TS_WORDS = ("timestamp", "time stamp", "χρονοσ", "timestamper", "0x80072ee", "winhttp", "could not connect")


def _is_ts_error(text):
    t = (text or "").lower()
    return any(w in t for w in _TS_WORDS)


def sign_file(path, pfx_path, password, ts_url="", desc="", url="", method="auto", signtool=None):
    """Επιστρέφει (ok, μήνυμα, μέθοδος, timestamp_error)."""
    if not IS_WIN:
        return False, "Η υπογραφή γίνεται μόνο σε Windows.", "-", False
    ext = os.path.splitext(path)[1].lower()
    use_st = method == "signtool" or (method == "auto" and signtool) or ext in NEEDS_SIGNTOOL
    if use_st:
        if not signtool:
            return False, ("Χρειάζεται signtool (Windows SDK) για " + ext if ext in NEEDS_SIGNTOOL
                           else "Δεν βρέθηκε signtool — επιλέξτε «Αυτόματα» ή «PowerShell»"), "signtool", False
        cmd = [signtool, "sign", "/f", pfx_path, "/p", password, "/fd", "SHA256"]
        if ts_url:
            cmd += ["/tr", ts_url, "/td", "SHA256"]
        if desc:
            cmd += ["/d", desc]
        if url:
            cmd += ["/du", url]
        cmd.append(path)
        try:
            r = _run(cmd, timeout=180)
        except subprocess.TimeoutExpired:
            return False, "Λήξη χρόνου (ο διακομιστής χρονοσήμανσης δεν απαντά;)", "signtool", bool(ts_url)
        out = (r.stdout + "\n" + r.stderr).strip()
        if out:
            log("   signtool: " + (out.replace(password, "***") if password else out))
        if r.returncode == 0:
            return True, "Υπογράφηκε", "signtool", False
        if ts_url and _is_ts_error(out):
            return False, "Αποτυχία χρονοσήμανσης (internet;)", "signtool", True
        if "password" in out.lower():
            return False, "Λάθος κωδικός πιστοποιητικού", "signtool", False
        if ext in NEEDS_SIGNTOOL and "publisher" in out.lower():
            return False, "Ο Publisher του πακέτου πρέπει να είναι ίδιος με το Subject του πιστοποιητικού", "signtool", False
        lines = [l for l in out.splitlines() if l.strip()]
        err = next((l for l in lines if "error" in l.lower()), lines[-1] if lines else f"signtool κωδικός {r.returncode}")
        return False, err.strip(), "signtool", False
    try:
        r = _ps(PS_SIGN, {"CS_PFX": pfx_path, "CS_PW": password, "CS_FILE": path, "CS_TS": ts_url})
    except subprocess.TimeoutExpired:
        return False, "Λήξη χρόνου (ο διακομιστής χρονοσήμανσης δεν απαντά;)", "PowerShell", bool(ts_url)
    d = _last_json(r.stdout)
    if not d:
        err = (r.stderr or r.stdout).strip()
        log("   PowerShell: " + err[:600])
        return False, err.splitlines()[0] if err else "Άγνωστο σφάλμα PowerShell", "PowerShell", bool(ts_url) and _is_ts_error(err)
    log(f"   PowerShell: {d.get('Status')} {d.get('Message', '')}".rstrip())
    if d.get("Signed") and d.get("Status") in ("Valid", "UnknownError", "NotTrusted"):
        return True, "Υπογράφηκε", "PowerShell", False
    msg = d.get("Message") or d.get("Status") or "Σφάλμα"
    if ts_url and _is_ts_error(msg):
        return False, "Αποτυχία χρονοσήμανσης (internet;)", "PowerShell", True
    if "password" in msg.lower() or "κωδικ" in msg.lower():
        return False, "Λάθος κωδικός πιστοποιητικού", "PowerShell", False
    return False, f"{d.get('Status')}: {msg}", "PowerShell", False


def verify_many(files, on_result=None, should_stop=lambda: False):
    """Έλεγχος πολλών αρχείων με ΜΙΑ διεργασία PowerShell (γρήγορο). Επιστρέφει λίστα dict."""
    empty = {"Status": "N/A", "Message": "Μόνο σε Windows", "Signer": "", "Thumb": "", "Timestamp": ""}
    if not IS_WIN:
        res = [dict(empty) for _ in files]
        for i, d in enumerate(res):
            on_result and on_result(i, d)
        return res
    results = [None] * len(files)
    fd, lst = tempfile.mkstemp(prefix="certsign_", suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("\n".join(files))
        p = subprocess.Popen([_ps_exe(), "-NoLogo", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                              "-Command", PS_VERIFY_MANY],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, text=True,
                             encoding="utf-8", errors="replace", env=_ps_env({"CS_LIST": lst}), creationflags=NOWIN)
        for line in p.stdout:
            line = line.strip()
            if not line.startswith("{"):
                if line:
                    log("   PowerShell: " + line[:300])
                continue
            try:
                d = json.loads(line)
                i = int(d.pop("I"))
            except Exception:
                continue
            if 0 <= i < len(results):
                results[i] = d
                on_result and on_result(i, d)
            if should_stop():
                p.kill(); break
        try:
            p.wait(timeout=10)
        except Exception:
            p.kill()
    finally:
        try:
            os.remove(lst)
        except OSError:
            pass
    for i, d in enumerate(results):
        if d is None:
            results[i] = {"Status": "Error", "Message": "Δεν ελέγχθηκε", "Signer": "", "Thumb": "", "Timestamp": ""}
    return results


def classify(d, my_thumb=""):
    """→ (εικονίδιο, κείμενο, υπογεγραμμένο_με_το_δικό_μου)"""
    st = d.get("Status")
    m = re.search(r"CN=(\"[^\"]+\"|[^,]+)", d.get("Signer") or "")
    signer = m.group(1).strip('"').strip() if m else (d.get("Signer") or "")
    thumb = (d.get("Thumb") or "").upper()
    mine = bool(my_thumb) and thumb == my_thumb.upper()
    ts = " · με χρονοσήμανση" if d.get("Timestamp") else " · χωρίς χρονοσήμανση"
    tag = " (δικό σας)" if mine else ""
    if st == "Valid":
        return "✅", f"Έγκυρη υπογραφή: {signer}{tag}{ts}", mine
    if st == "NotSigned":
        return "⚪", "Δεν είναι υπογεγραμμένο", False
    if st == "HashMismatch":
        return "❌", "Το αρχείο άλλαξε μετά την υπογραφή!", False
    if thumb and st in ("UnknownError", "NotTrusted"):
        return "🟡", (f"Υπογεγραμμένο από {signer}{tag}{ts} — το πιστοποιητικό δεν είναι εγκατεστημένο "
                     "σε αυτόν τον υπολογιστή (βήμα ③)"), mine
    if st == "NotSupportedFileFormat":
        return "⚪", "Αυτός ο τύπος αρχείου δεν υποστηρίζει υπογραφή", False
    return "❌", f"{st}: {d.get('Message', '')}".strip(), False


# ---- εγκατάσταση στον υπολογιστή ----
def cert_installed(thumb):
    """{'user': bool, 'machine': bool, 'user_tp': bool, 'machine_tp': bool}"""
    out = {"user": False, "machine": False, "user_tp": False, "machine_tp": False}
    if not IS_WIN:
        return out
    for key, args, store in (("user", ["-user"], "Root"), ("machine", [], "Root"),
                             ("user_tp", ["-user"], "TrustedPublisher"), ("machine_tp", [], "TrustedPublisher")):
        try:
            out[key] = _run(["certutil", *args, "-verifystore", store, thumb], timeout=30).returncode == 0
        except Exception:
            pass
    return out


PS_ELEVATED = r"""
try {
  $p = Start-Process -FilePath cmd.exe -ArgumentList $env:CS_ARGS -Verb RunAs -Wait -PassThru -WindowStyle Hidden -ErrorAction Stop
  exit $p.ExitCode
} catch { [Console]::Error.WriteLine("CANCELLED: " + $_.Exception.Message); exit 1223 }
"""


def _elevated_cmd(cmdline, timeout=300):
    """Τρέχει «cmd /c …» με δικαιώματα διαχειριστή (ΕΝΑ παράθυρο UAC). → (ok, μήνυμα)"""
    r = _ps(PS_ELEVATED, {"CS_ARGS": "/c " + cmdline}, timeout=timeout)
    if r.returncode == 0:
        return True, ""
    if r.returncode == 1223 or "CANCELLED" in (r.stderr or ""):
        return False, "Ακυρώθηκε η άδεια διαχειριστή (UAC)."
    return False, f"Κωδικός σφάλματος {r.returncode} {(r.stderr or '').strip()[:200]}"


def install_cert(cer_path, machine=False):
    if not IS_WIN:
        return False, "Μόνο σε Windows"
    if machine:
        q = f'"{cer_path}"'
        return _elevated_cmd(f"certutil -addstore -f TrustedPublisher {q} && certutil -addstore -f Root {q}")
    # TrustedPublisher πρώτα (χωρίς ερώτηση), μετά Root (τα Windows ζητούν επιβεβαίωση)
    for store in ("TrustedPublisher", "Root"):
        r = _run(["certutil", "-user", "-addstore", "-f", store, cer_path], timeout=600)
        txt = (r.stdout + r.stderr).strip()
        log(f"certutil -user -addstore {store}: κωδικός {r.returncode}")
        if r.returncode != 0:
            return False, ("ακυρώθηκε στην προειδοποίηση των Windows" if store == "Root" else
                           (txt.splitlines()[-1] if txt else f"κωδικός {r.returncode}"))
    return True, ""


def uninstall_cert(thumb, machine=False):
    if not IS_WIN:
        return False, "Μόνο σε Windows"
    for store in ("Root", "TrustedPublisher"):
        _run(["certutil", "-user", "-delstore", store, thumb], timeout=600)
    if machine:
        return _elevated_cmd(f"certutil -delstore Root {thumb} & certutil -delstore TrustedPublisher {thumb}")
    return True, ""


# ---- «Αποστολή προς» (δεξί κλικ σε αρχείο) ----
def sendto_path():
    return os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "SendTo", "CertifiCat - Υπογραφή.lnk")


PS_SHORTCUT = r"""
$s = (New-Object -ComObject WScript.Shell).CreateShortcut($env:CS_LNK)
$s.TargetPath = $env:CS_T; $s.Arguments = $env:CS_A; $s.WorkingDirectory = $env:CS_W
if ($env:CS_I) { $s.IconLocation = $env:CS_I }
$s.Description = 'Υπογραφή με CertifiCat'
$s.Save()
"""


def sendto_create(script=None):
    if FROZEN:
        target, args = sys.executable, "--sign"
    else:
        target, args = _python_exe(windowed=True), f'"{script or os.path.abspath(__file__)}" --sign'
    ico = os.path.join(config_dir(), "certificat.ico")
    try:
        if not logo_pixmap(256).save(ico, "ICO"):
            ico = ""
    except Exception:
        ico = ""
    r = _ps(PS_SHORTCUT, {"CS_LNK": sendto_path(), "CS_T": target, "CS_A": args, "CS_W": _app_dir(), "CS_I": ico})
    return r.returncode == 0 and os.path.exists(sendto_path()), (r.stderr or "").strip()[:300]


# ════════════════════════════════════════════════════════════════════
# 4. Λογότυπο
# ════════════════════════════════════════════════════════════════════
LOGO_PNG_B64 = (
    "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"
)
_LOGO_CACHE = {}


def logo_badge(size=64):
    """Το λογότυπο πάνω σε ανοιχτό «σήμα», ώστε να φαίνεται σε σκούρο φόντο."""
    pm = QPixmap(size, size); pm.fill(Qt.GlobalColor.transparent)
    pa = QPainter(pm); pa.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath(); path.addRoundedRect(QRectF(0, 0, size, size), size * .24, size * .24)
    pa.fillPath(path, QBrush(QColor("#F6F2FA")))
    inner = logo_pixmap(int(size * .84))
    pa.drawPixmap((size - inner.width()) // 2, (size - inner.height()) // 2, inner); pa.end()
    return pm


def logo_pixmap(size=256):
    """Το λογότυπο CertifiCat (γατούλα-ροζέτα). Αν υπάρχει logo.png δίπλα στο app, προτιμάται αυτό."""
    if "base" not in _LOGO_CACHE:
        pm = QPixmap()
        f = os.path.join(_app_dir(), "logo.png")
        if not (os.path.isfile(f) and pm.load(f)):
            pm.loadFromData(base64.b64decode(LOGO_PNG_B64), "PNG")
        if pm.isNull():                      # δεν θα συμβεί, αλλά να μη σπάσει ποτέ το app
            pm = QPixmap(256, 256); pm.fill(QColor("#362044"))
        _LOGO_CACHE["base"] = pm
    if size not in _LOGO_CACHE:
        src = _LOGO_CACHE["base"]
        out = QPixmap(size, size); out.fill(Qt.GlobalColor.transparent)
        sc = src.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        pa = QPainter(out); pa.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        pa.drawPixmap((size - sc.width()) // 2, (size - sc.height()) // 2, sc); pa.end()
        _LOGO_CACHE[size] = out
    return _LOGO_CACHE[size]


# ════════════════════════════════════════════════════════════════════
# 5. GUI
# ════════════════════════════════════════════════════════════════════
STYLE = """
* { font-family: 'Segoe UI', 'Noto Sans', sans-serif; font-size: 10.5pt; }
QMainWindow, QWidget#page { background: #F4F6FA; }
QWidget#sidebar { background: #362044; }
QPushButton#step { background: transparent; color: #D9CCE6; text-align: left; padding: 13px 16px; border: none;
    border-left: 4px solid transparent; font-size: 11pt; border-radius: 0; }
QPushButton#step:hover { background: #4A2F5C; color: white; }
QPushButton#step:checked { background: #4A2F5C; color: white; border-left: 4px solid #D6DC68; font-weight: 600; }
QPushButton { background: #2D6CDF; color: white; border: none; border-radius: 7px; padding: 8px 16px; font-weight: 600; }
QPushButton:hover { background: #2259BF; }
QPushButton:disabled { background: #B8C2D3; color: #EEF1F6; }
QPushButton#secondary { background: white; color: #362044; border: 1px solid #CBD3E1; }
QPushButton#secondary:hover { background: #EDF2FB; }
QPushButton#secondary:disabled { background: #F1F3F7; color: #A0AABB; }
QPushButton#orange { background: #F08A00; }
QPushButton#orange:hover { background: #D27800; }
QPushButton#orange:disabled { background: #F2C98F; }
QPushButton#danger { background: #D9443F; }
QPushButton#danger:hover { background: #B9332F; }
QLabel#title { font-size: 18pt; font-weight: 700; color: #362044; }
QLabel#subtitle { color: #5C6B80; }
QLabel#card { background: white; border-radius: 8px; padding: 9px 12px; }
QGroupBox { background: white; border: 1px solid #DDE3EC; border-radius: 10px; margin-top: 14px; padding: 12px;
    font-weight: 600; color: #362044; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }
QLineEdit, QComboBox, QSpinBox { background: white; border: 1px solid #CBD3E1; border-radius: 6px; padding: 5px 8px; min-height: 22px; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border: 2px solid #2D6CDF; }
QTableWidget { background: white; border: 1px solid #DDE3EC; border-radius: 8px; gridline-color: #EEF1F6;
    selection-background-color: #D7E6FB; selection-color: #362044; }
QHeaderView::section { background: #362044; color: white; padding: 6px; border: none; font-weight: 600; }
QProgressBar { border: none; background: #4A2F5C; border-radius: 4px; height: 8px; }
QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #2D6CDF, stop:1 #FCA311); border-radius: 4px; }
QPlainTextEdit#log { background: #10141C; color: #D8E1EE; border-radius: 8px; padding: 6px;
    font-family: Consolas, 'DejaVu Sans Mono', monospace; font-size: 9pt; }
QToolTip { background: #362044; color: white; border: none; padding: 6px; }
QDialog, QMessageBox { background: #F4F6FA; }
QLabel, QCheckBox, QRadioButton { color: #1F2A3D; }
QCheckBox:disabled, QLabel:disabled { color: #9AA5B8; }
QTextEdit, QComboBox QAbstractItemView, QMenu { background: white; color: #1F2A3D; }
QMenu::item:selected { background: #D7E6FB; }
QLineEdit, QComboBox, QSpinBox { color: #1F2A3D; }
"""


def apply_light_theme(app):
    """Η εφαρμογή είναι σχεδιασμένη σε ανοιχτά χρώματα. Αν τα Windows είναι σε σκούρο θέμα (dark mode),
    το Qt δίνει λευκά γράμματα → εξαφανίζονται οι ετικέτες. Κλειδώνουμε ανοιχτό θέμα σε όλες τις εκδόσεις Qt."""
    try:
        app.styleHints().setColorScheme(Qt.ColorScheme.Light)        # Qt 6.8+
    except Exception:
        pass
    from PyQt6.QtGui import QPalette
    pal = QPalette()
    R_ = QPalette.ColorRole
    base = {R_.Window: "#F4F6FA", R_.WindowText: "#1F2A3D", R_.Base: "#FFFFFF", R_.AlternateBase: "#F4F6FA",
            R_.Text: "#1F2A3D", R_.Button: "#FFFFFF", R_.ButtonText: "#1F2A3D", R_.BrightText: "#FFFFFF",
            R_.Highlight: "#2D6CDF", R_.HighlightedText: "#FFFFFF", R_.ToolTipBase: "#362044",
            R_.ToolTipText: "#FFFFFF", R_.PlaceholderText: "#8A94A6", R_.Link: "#2D6CDF", R_.LinkVisited: "#6B3FA0",
            R_.Light: "#FFFFFF", R_.Midlight: "#EEF1F6", R_.Mid: "#CBD3E1", R_.Dark: "#9AA5B8", R_.Shadow: "#5C6B80"}
    for role, col in base.items():
        pal.setColor(role, QColor(col))
    for role in (R_.WindowText, R_.Text, R_.ButtonText):
        pal.setColor(QPalette.ColorGroup.Disabled, role, QColor("#9AA5B8"))
    app.setPalette(pal)


def fit_to_screen(w, want_w=1180, want_h=800):
    """Το παράθυρο χωράει πάντα στην οθόνη (και σε laptop με κλίμακα 125–150%) και ανοίγει στο κέντρο."""
    scr = (w.screen() or QApplication.primaryScreen()).availableGeometry()
    ww, hh = min(want_w, scr.width() - 20), min(want_h, scr.height() - 40)
    w.resize(ww, hh)
    w.move(scr.x() + (scr.width() - ww) // 2, scr.y() + max(0, (scr.height() - hh) // 2 - 10))


def title_block(t, s):
    w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(0, 0, 0, 6)
    a = QLabel(t); a.setObjectName("title"); b = QLabel(s); b.setObjectName("subtitle"); b.setWordWrap(True)
    l.addWidget(a); l.addWidget(b)
    return w


def btn(text, slot=None, kind=None, tip=None, width=None):
    b = QPushButton(text)
    if kind:
        b.setObjectName(kind)
    if slot:
        b.clicked.connect(slot)
    if tip:
        b.setToolTip(tip)
    if width:
        b.setFixedWidth(width)
    return b


def open_in_explorer(path):
    try:
        if IS_WIN and os.path.isfile(path):
            subprocess.Popen(f'explorer /select,"{os.path.normpath(path)}"')
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path if os.path.isdir(path) else os.path.dirname(path)))
    except Exception:
        pass


class Task(QThread):
    """Τρέχει μια συνάρτηση στο παρασκήνιο ώστε το παράθυρο να μην «παγώνει»."""
    result = pyqtSignal(object)

    def __init__(self, fn, *a, **kw):
        super().__init__(); self.fn, self.a, self.kw = fn, a, kw

    def run(self):
        try:
            r = self.fn(*self.a, **self.kw)
        except Exception as ex:
            log("Σφάλμα: " + "".join(traceback.format_exception_only(type(ex), ex)).strip())
            r = ex
        self.result.emit(r)


_TASKS = set()


def run_task(fn, *a, done=None, **kw):
    t = Task(fn, *a, **kw)
    _TASKS.add(t)
    if done:
        t.result.connect(done)
    t.finished.connect(lambda: _TASKS.discard(t))
    t.start()
    return t


class Splash(QWidget):
    done = pyqtSignal(dict)
    _step = pyqtSignal(int, str, str)

    def __init__(self):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint |
                         Qt.WindowType.SplashScreen)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(520, 300)
        l = QVBoxLayout(self); l.setContentsMargins(32, 28, 32, 22)
        top = QHBoxLayout(); lg = QLabel(); lg.setPixmap(logo_badge(88)); top.addWidget(lg)
        tt = QVBoxLayout()
        a = QLabel("CertifiCat"); a.setStyleSheet("color:white;font-size:24pt;font-weight:800;")
        b = QLabel("Πιστοποιητικά & ψηφιακή υπογραφή προγραμμάτων"); b.setWordWrap(True); b.setStyleSheet("color:#D9CCE6;")
        c = QLabel(f"έκδοση {APP_VERSION}"); c.setStyleSheet("color:#B7A3CB;font-size:9pt;")
        tt.addStretch(); tt.addWidget(a); tt.addWidget(b); tt.addWidget(c); tt.addStretch()
        top.addLayout(tt); top.addStretch(); l.addLayout(top); l.addStretch()
        self.st = QLabel("Εκκίνηση…"); self.st.setStyleSheet("color:#F1EAF7;")
        self.dt = QLabel(""); self.dt.setStyleSheet("color:#B7A3CB;font-size:8.5pt;")
        self.bar = QProgressBar(); self.bar.setTextVisible(False); self.bar.setFixedHeight(8)
        l.addWidget(self.st); l.addWidget(self.bar); l.addWidget(self.dt)
        f = QLabel(f"© {datetime.now().year} {AUTHOR_NAME_EN} · {APP_AUTHOR}"); f.setStyleSheet("color:#9C86B3;font-size:8.5pt;")
        f.setAlignment(Qt.AlignmentFlag.AlignRight); l.addWidget(f)
        self.res = {}
        self.steps = [("Έλεγχος Python…", lambda: f"Python {sys.version.split()[0]}"),
                      ("Έλεγχος βιβλιοθηκών…", self.libs),
                      ("Αναζήτηση signtool (Windows SDK)…", self.tool),
                      ("Έλεγχος PowerShell…", self.ps),
                      ("Φόρτωση ρυθμίσεων & Κλειδοθήκης…", self.cfg)]
        self._step.connect(self._show)
        threading.Thread(target=self._work, daemon=True).start()    # οι έλεγχοι στο παρασκήνιο: το splash δεν παγώνει

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        g = QLinearGradient(0, 0, self.width(), self.height()); g.setColorAt(0, QColor("#362044")); g.setColorAt(1, QColor("#4A2F5C"))
        path = QPainterPath(); path.addRoundedRect(QRectF(self.rect()), 18, 18); p.fillPath(path, QBrush(g))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor("#D6DC68")); p.drawRoundedRect(QRectF(0, self.height() - 5, self.width(), 5), 2, 2)

    def _work(self):
        n = len(self.steps)
        for i, (t, fn) in enumerate(self.steps):
            self._step.emit(int(i / n * 100), t, "")
            try:
                d = fn() or ""
            except Exception as ex:
                d = f"⚠ {ex}"
            log(f"{t} {d}")
            self._step.emit(int((i + 1) / n * 100), t, d)
            time.sleep(0.22)
        self._step.emit(100, "Έτοιμο!", "")
        time.sleep(0.3)
        self._step.emit(-1, "", "")

    def _show(self, v, t, d):
        if v < 0:
            self.done.emit(self.res); return
        self.bar.setValue(v)
        if t:
            self.st.setText(t)
        self.dt.setText(d)

    def libs(self):
        from PyQt6.QtCore import PYQT_VERSION_STR
        import cryptography
        return f"PyQt6 {PYQT_VERSION_STR} · cryptography {cryptography.__version__}"

    def tool(self):
        t = get_signtool(); self.res["signtool"] = t
        return f"✓ {t}" if t else ("Δεν βρέθηκε — θα χρησιμοποιηθεί το PowerShell των Windows" if IS_WIN
                                   else "Μη-Windows: μόνο δημιουργία πιστοποιητικών")

    def ps(self):
        if not IS_WIN:
            return "—"
        r = _ps("$PSVersionTable.PSVersion.ToString()", timeout=30)
        return f"PowerShell {r.stdout.strip()}" if r.returncode == 0 else "⚠ PowerShell μη διαθέσιμο"

    def cfg(self):
        migrate_old_versions()
        cleanup_after_update()
        c = load_cfg(); self.res["cfg"] = c
        n = len(list_certs())
        return f"Κλειδοθήκη: {n} πιστοποιητικά · τελευταίο: {os.path.basename(c.get('last_pfx', '')) or '—'}"


class SignWorker(QThread):
    progress = pyqtSignal(int, str, str, str)     # row, icon, text, method
    finished_all = pyqtSignal(int, int, int)      # ok, bad, skipped

    def __init__(self, rows, pfx, pw, ts_list, auto_ts, desc, url, thumb, method, signtool, skip_signed):
        super().__init__()
        self.rows, self.pfx, self.pw = rows, pfx, pw
        self.ts_list, self.auto_ts, self.desc, self.url = ts_list, auto_ts, desc, url
        self.thumb, self.method, self.signtool, self.skip_signed = thumb, method, signtool, skip_signed
        self.ts_idx = 0
        self.ts_dead = False
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        ok = bad = skipped = 0
        try:
            already = {}
            if self.skip_signed:
                res = verify_many([f for _, f in self.rows], should_stop=lambda: self._stop)
                for (row, f), d in zip(self.rows, res):
                    if classify(d, self.thumb)[2]:
                        already[row] = True
            for row, f in self.rows:
                if self._stop:
                    self.progress.emit(row, "•", "Διακόπηκε", "")
                    continue
                if already.get(row):
                    self.progress.emit(row, "⏭", "Ήδη υπογεγραμμένο με αυτό το πιστοποιητικό — παραλείφθηκε", "-")
                    skipped += 1
                    continue
                self.progress.emit(row, "⏳", "Υπογραφή…", "")
                log(f"Υπογραφή: {f}")
                try:
                    ic, txt, how, good = self._sign_one(f)
                except Exception as ex:
                    ic, txt, how, good = "❌", str(ex), "-", False
                log(f"   → {ic} {txt}")
                self.progress.emit(row, ic, txt, how)
                ok += 1 if good else 0
                bad += 0 if good else 1
        finally:
            self.finished_all.emit(ok, bad, skipped)

    def _sign_one(self, f):
        if not os.path.isfile(f):
            return "❌", "Το αρχείο δεν υπάρχει πια", "-", False
        try:
            with open(f, "r+b"):
                pass
        except PermissionError:
            return "❌", "Το αρχείο είναι κλειδωμένο ή μόνο-για-ανάγνωση (μήπως τρέχει το πρόγραμμα;)", "-", False
        except OSError as ex:
            return "❌", f"Δεν ανοίγει: {ex}", "-", False
        if self.ts_list:
            if self.ts_dead:
                return "❌", ("Κανένας διακομιστής χρονοσήμανσης δεν απαντά. Επιλέξτε «Χωρίς χρονοσήμανση» "
                             "για υπογραφή χωρίς internet."), "-", False
            servers = self.ts_list[self.ts_idx:] if self.auto_ts else self.ts_list[:1]
        else:
            servers = [""]
        how = "-"
        for k, ts in enumerate(servers):
            ok, msg, how, ts_err = sign_file(f, self.pfx, self.pw, ts, self.desc, self.url, self.method, self.signtool)
            if ok:
                if k:
                    self.ts_idx += k
                    log(f"   Χρονοσήμανση: χρησιμοποιείται πλέον ο {ts}")
                break
            if ts_err and self.auto_ts and k < len(servers) - 1:
                log(f"   ⚠ Ο διακομιστής {ts} δεν απάντησε — δοκιμή επόμενου…")
                continue
            if ts_err:
                self.ts_dead = True
            return "❌", msg, how, False
        d = verify_many([f])[0]
        ic, txt, mine = classify(d, self.thumb)
        if mine:
            return ic, txt, how, True
        return "❌", "Η υπογραφή δεν επιβεβαιώθηκε: " + txt, how, False


class VerifyWorker(QThread):
    progress = pyqtSignal(int, str, str)
    finished_all = pyqtSignal()

    def __init__(self, rows, thumb):
        super().__init__(); self.rows, self.thumb = rows, thumb; self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            def cb(i, d):
                ic, txt, _ = classify(d, self.thumb)
                self.progress.emit(self.rows[i][0], ic, txt)
            verify_many([f for _, f in self.rows], cb, lambda: self._stop)
        finally:
            self.finished_all.emit()


# ──────────────────────────── ① Πιστοποιητικό ────────────────────────────
class CertPage(QWidget):
    def __init__(self, main):
        super().__init__(); self.setObjectName("page"); self.m = main
        cfg = load_cfg()
        lay = QVBoxLayout(self); lay.setContentsMargins(26, 22, 26, 22)
        lay.addWidget(title_block("① Πιστοποιητικό",
                                  "Φτιάξτε ένα νέο πιστοποιητικό υπογραφής (μία φορά) ή ανοίξτε ένα που ήδη έχετε (.pfx)."))
        row = QHBoxLayout(); row.setSpacing(14)
        # ---- νέο ----
        g = QGroupBox("✨ Νέο πιστοποιητικό"); f = QFormLayout(g)
        self.cn = QLineEdit(cfg.get("cn", default_publisher()))
        self.org = QLineEdit(cfg.get("org", ""))
        self.cn.setPlaceholderText("π.χ. Το Όνομά Σας - Code Signing")
        self.org.setPlaceholderText("προαιρετικό")
        self.country = QLineEdit(cfg.get("country", "GR")); self.country.setMaxLength(2)
        self.country.setToolTip("2 λατινικά γράμματα (π.χ. GR) ή κενό")
        self.years = QSpinBox(); self.years.setRange(1, 30); self.years.setValue(int(cfg.get("years", 10)))
        self.years.setSuffix(" χρόνια")
        self.pw = QLineEdit(gen_password()); self.pw.setEchoMode(QLineEdit.EchoMode.Password)
        pr = QHBoxLayout(); pr.addWidget(self.pw)
        pr.addWidget(btn("👁", self.toggle_pw, "secondary", "Εμφάνιση/απόκρυψη", 46))
        pr.addWidget(btn("↻", lambda: self.pw.setText(gen_password()), "secondary", "Νέος τυχαίος κωδικός", 46))
        pr.addWidget(btn("📋", self.copy_pw, "secondary", "Αντιγραφή κωδικού", 46))
        self.compat = QCheckBox("Συμβατό με όλα τα Windows"); self.compat.setChecked(True)
        self.compat.setToolTip("Κρυπτογράφηση .pfx που ανοίγει και σε παλιά Windows / signtool.")
        f.addRow("Όνομα εκδότη:", self.cn); f.addRow("Οργανισμός:", self.org); f.addRow("Χώρα (2 γράμματα):", self.country)
        f.addRow("Ισχύς:", self.years); f.addRow("Κωδικός .pfx:", pr); f.addRow("", self.compat)
        self.mk = btn("✨ Δημιουργία πιστοποιητικού…", self.create, "orange")
        f.addRow("", self.mk)
        note = QLabel("🔒 Μόνο για υπογραφή κώδικα")
        note.setToolTip("Δεν μπορεί να εκδώσει άλλα πιστοποιητικά ούτε να επηρεάσει ιστοσελίδες/HTTPS.")
        note.setObjectName("subtitle"); f.addRow("", note)
        row.addWidget(g, 1)
        # ---- υπάρχον ----
        g2 = QGroupBox("📂 Υπάρχον πιστοποιητικό"); f2 = QFormLayout(g2)
        self.path = QLineEdit(cfg.get("last_pfx", "")); self.path.setPlaceholderText("…\\πιστοποιητικό.pfx")
        br = QHBoxLayout(); br.addWidget(self.path); br.addWidget(btn("…", self.browse, "secondary", "Αναζήτηση .pfx", 46))
        self.pw2 = QLineEdit(); self.pw2.setEchoMode(QLineEdit.EchoMode.Password); self.pw2.setPlaceholderText("κωδικός του .pfx")
        self.pw2.returnPressed.connect(self.open_existing)
        self.remember = QCheckBox("Αποθήκευση κωδικού στην Κλειδοθήκη")
        self.remember.setEnabled(IS_WIN)
        self.remember.setToolTip("Μόνο σε αυτόν τον υπολογιστή, κρυπτογραφημένα με τον λογαριασμό σας στα Windows (DPAPI).")
        op = btn("🔓 Άνοιγμα", self.open_existing)
        f2.addRow("Αρχείο .pfx:", br); f2.addRow("Κωδικός:", self.pw2); f2.addRow("", self.remember); f2.addRow("", op)
        self.info = QLabel("Κανένα πιστοποιητικό ανοιχτό."); self.info.setWordWrap(True)
        self.info.setTextFormat(Qt.TextFormat.RichText)
        self.info.setStyleSheet("background:#F4F6FA;border-radius:8px;padding:10px;")
        self.info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        f2.addRow(self.info)
        fr = QHBoxLayout()
        self.b_folder = btn("📂 Φάκελος", self.open_folder, "secondary", "Άνοιγμα του φακέλου του .pfx")
        self.b_close = btn("✖ Κλείσιμο", self.close_cert, "secondary", "Κλείσιμο πιστοποιητικού (και διαγραφή αποθηκευμένου κωδικού)")
        fr.addWidget(self.b_folder); fr.addWidget(self.b_close); fr.addStretch()
        f2.addRow(fr)
        self.b_folder.setEnabled(False); self.b_close.setEnabled(False)
        row.addWidget(g2, 1)
        lay.addLayout(row)
        nxt = btn("Επόμενο: Υπογραφή αρχείων  →", lambda: main.go(1), "orange")
        h = QHBoxLayout(); h.addStretch(); h.addWidget(nxt)
        lay.addStretch(); lay.addLayout(h)

    def autoload(self):
        p = self.path.text().strip()
        if p and os.path.exists(p):
            saved = recall_password(p)
            if saved:
                self.pw2.setText(saved); self.remember.setChecked(True)
                self.open_existing(silent=True)

    def toggle_pw(self):
        self.pw.setEchoMode(QLineEdit.EchoMode.Normal if self.pw.echoMode() == QLineEdit.EchoMode.Password
                            else QLineEdit.EchoMode.Password)

    def copy_pw(self):
        QGuiApplication.clipboard().setText(self.pw.text()); self.m.toast("Ο κωδικός αντιγράφηκε")

    def browse(self):
        f, _ = QFileDialog.getOpenFileName(self, "Πιστοποιητικό",
                                           os.path.dirname(self.path.text()) or os.path.expanduser("~"),
                                           "Πιστοποιητικό με ιδιωτικό κλειδί (*.pfx *.p12);;Όλα (*.*)")
        if f:
            if f.lower().endswith((".cer", ".crt")):
                QMessageBox.warning(self, APP_NAME, "Το .cer είναι μόνο το δημόσιο κομμάτι και ΔΕΝ υπογράφει.\n"
                                                    "Διαλέξτε το αντίστοιχο .pfx."); return
            self.path.setText(f)
            s = recall_password(f)
            self.pw2.setText(s); self.remember.setChecked(bool(s))
            if s:
                self.open_existing()
            else:
                self.pw2.setFocus()

    def create(self):
        cn = self.cn.text().strip()
        country = self.country.text().strip().upper()
        if not cn:
            QMessageBox.warning(self, APP_NAME, "Γράψτε όνομα εκδότη."); self.cn.setFocus(); return
        if country and not re.fullmatch(r"[A-Z]{2}", country):
            QMessageBox.warning(self, APP_NAME, "Η χώρα πρέπει να είναι 2 λατινικά γράμματα (π.χ. GR) ή κενή.")
            self.country.setFocus(); return
        if len(self.pw.text()) < 8:
            QMessageBox.warning(self, APP_NAME, "Ο κωδικός πρέπει να έχει τουλάχιστον 8 χαρακτήρες."); return
        d = QFileDialog.getExistingDirectory(self, "Φάκελος για τα αρχεία του πιστοποιητικού",
                                             load_cfg().get("out_dir", os.path.expanduser("~")))
        if not d:
            return
        if not os.access(d, os.W_OK):
            QMessageBox.critical(self, APP_NAME, f"Δεν επιτρέπεται εγγραφή στον φάκελο:\n{d}"); return
        pwd = self.pw.text()
        self.mk.setEnabled(False); self.mk.setText("⏳ Δημιουργία…")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        log(f"Δημιουργία πιστοποιητικού: CN={cn}, {self.years.value()} χρόνια, RSA 3072")
        run_task(self._create_files, cn, self.org.text(), country, self.years.value(), pwd, self.compat.isChecked(), d,
                 done=lambda r: self._created(r, cn, d, pwd))

    @staticmethod
    def _create_files(cn, org, country, years, pwd, compat, d):
        pfx, der, info = make_certificate(cn, org, country, years, pwd, compatible=compat)
        base = safe_name(cn)
        pfx_path = os.path.join(d, base + ".pfx")
        if any(os.path.exists(os.path.join(d, base + e)) for e in (".pfx", ".cer", "_Certificate.zip")):
            base = f"{base}_{datetime.now():%Y%m%d_%H%M%S}"       # ποτέ δεν σβήνει παλιό πιστοποιητικό
            pfx_path = os.path.join(d, base + ".pfx")
        with open(pfx_path, "wb") as f:
            f.write(pfx)
        cer_path = os.path.join(d, base + ".cer")
        with open(cer_path, "wb") as f:
            f.write(der)
        zp = make_install_package(der, info, os.path.join(d, base + "_Certificate.zip"))
        return pfx_path, cer_path, zp, info

    def _created(self, r, cn, d, pwd):
        QApplication.restoreOverrideCursor()
        self.mk.setEnabled(True); self.mk.setText("✨ Δημιουργία πιστοποιητικού…")
        if isinstance(r, Exception):
            QMessageBox.critical(self, APP_NAME, f"Η δημιουργία απέτυχε:\n\n{r}"); return
        pfx_path, cer_path, zp, info = r
        log(f"✓ Δημιουργήθηκαν: {pfx_path}, {cer_path}, {zp}")
        register_cert(pfx_path, info, cer_path, zp)
        update_cfg(cn=cn, org=self.org.text(), country=self.country.text().strip().upper(), years=self.years.value(),
                   out_dir=d, last_pfx=pfx_path)
        self.path.setText(pfx_path); self.pw2.setText(pwd)
        dlg = QMessageBox(self); dlg.setWindowTitle("Έτοιμο")
        dlg.setIcon(QMessageBox.Icon.Information)
        dlg.setTextFormat(Qt.TextFormat.RichText)
        dlg.setText(f"✓ Δημιουργήθηκε: <b>{info['cn']}</b><br><br>"
                    f"<b>Κωδικός:</b> <code>{pwd}</code><br>"
                    "<span style='color:#B34700'>Φυλάξτε τον κωδικό! Χωρίς αυτόν το .pfx δεν μπορεί να υπογράψει.</span><br><br>"
                    f"📁 {d}<br>• {os.path.basename(pfx_path)} — <b>ιδιωτικό</b>, μην το μοιράζεστε<br>"
                    f"• {os.path.basename(cer_path)} — δημόσιο<br>• {os.path.basename(zp)} — για εγκατάσταση σε άλλους υπολογιστές")
        cp = dlg.addButton("📋 Αντιγραφή κωδικού", QMessageBox.ButtonRole.ActionRole)
        fo = dlg.addButton("📂 Φάκελος", QMessageBox.ButtonRole.ActionRole)
        dlg.addButton("OK", QMessageBox.ButtonRole.AcceptRole)
        for _ in range(20):                 # το «Αντιγραφή» ξανανοίγει το παράθυρο· όριο για ασφάλεια
            dlg.exec()
            if dlg.clickedButton() == cp:
                QGuiApplication.clipboard().setText(pwd); self.m.toast("Ο κωδικός αντιγράφηκε"); continue
            if dlg.clickedButton() == fo:
                open_in_explorer(pfx_path)
            break
        self.pw.setText(gen_password())
        rem = IS_WIN and QMessageBox.question(
            self, APP_NAME, "Να αποθηκευτεί ο κωδικός στην Κλειδοθήκη (④);\n\n"
                            "• Μένει ΜΟΝΟ σε αυτόν τον υπολογιστή, σε τοπική βάση.\n"
                            "• Κρυπτογραφείται με τον λογαριασμό σας στα Windows.\n"
                            "• Δεν στέλνεται πουθενά.\n\n"
                            "Αν πατήσετε «Όχι», κρατήστε τον κάπου αλλού με ασφάλεια!") == QMessageBox.StandardButton.Yes
        self.remember.setChecked(bool(rem))
        self.open_existing(silent=True)
        if self.m.info and IS_WIN and QMessageBox.question(
                self, APP_NAME, "Να εγκατασταθεί το πιστοποιητικό και σε ΑΥΤΟΝ τον υπολογιστή τώρα;\n"
                                "(ώστε τα Windows να δείχνουν το όνομά σας αντί για «Άγνωστος εκδότης»)"
        ) == QMessageBox.StandardButton.Yes:
            self.m.go(2); self.m.p3.install(False)

    def open_existing(self, silent=False):
        p = self.path.text().strip().strip('"')
        if not p or not os.path.isfile(p):
            if not silent:
                QMessageBox.warning(self, APP_NAME, "Διαλέξτε αρχείο .pfx.")
            return False
        try:
            key, cert = load_pfx(p, self.pw2.text())
        except Exception as ex:
            log(f"Άνοιγμα {p}: {ex}")
            if not silent:
                QMessageBox.critical(self, APP_NAME, str(ex)[:300]); self.pw2.selectAll(); self.pw2.setFocus()
            return False
        info = cert_info(cert)
        self.m.set_cert(p, self.pw2.text(), cert, info)
        register_cert(p, info)
        if self.remember.isChecked():
            store_password(p, self.pw2.text())
        else:
            forget_password(p)
        update_cfg(last_pfx=p)
        self.show_info(info)
        self.b_folder.setEnabled(True); self.b_close.setEnabled(True)
        log(f"Άνοιξε το πιστοποιητικό: {info['cn']} ({fmt_thumb(info['thumbprint'])})")
        if not silent:
            self.m.toast("✓ Το πιστοποιητικό άνοιξε")
        dl = days_left(info)
        if dl < 60:
            self.m.toast("❌ Το πιστοποιητικό έχει λήξει!" if dl < 0 else f"⚠ Το πιστοποιητικό λήγει σε {dl} ημέρες")
        return True

    def close_cert(self):
        p = self.path.text().strip()
        if p and has_password(p) and QMessageBox.question(
                self, APP_NAME, "Να διαγραφεί και ο αποθηκευμένος κωδικός;") == QMessageBox.StandardButton.Yes:
            forget_password(p)
        self.m.set_cert("", "", None, None)
        self.pw2.clear(); self.remember.setChecked(False)
        self.info.setText("Κανένα πιστοποιητικό ανοιχτό.")
        self.b_folder.setEnabled(False); self.b_close.setEnabled(False)

    def open_folder(self):
        if self.m.pfx:
            open_in_explorer(self.m.pfx)

    def show_info(self, i):
        dl = days_left(i)
        warn = []
        if not i["has_codesign"]:
            warn.append("❌ ΔΕΝ είναι για υπογραφή κώδικα — δεν μπορεί να υπογράψει")
        if i["is_ca"]:
            warn.append("⚠ Είναι αρχή πιστοποίησης (CA) — επικίνδυνο για εγκατάσταση στο Root")
        if dl < 0:
            warn.append("❌ Έχει λήξει — φτιάξτε νέο πιστοποιητικό")
        elif dl < 60:
            warn.append(f"⚠ Λήγει σε {dl} ημέρες")
        ok = "✓ Μόνο υπογραφή κώδικα · ✓ Όχι CA" if (i["codesign_only"] and i["is_ca"] is False) else ""
        self.info.setText(f"<b>{i['cn']}</b><br>{i['org']} {i['country']}<br>"
                          f"Ισχύει έως: <b>{i['not_after']:%d/%m/%Y}</b> ({max(dl, 0)} ημέρες) · RSA {i['key_bits']}<br>"
                          f"<span style='color:#5C6B80;font-size:8.5pt'>SHA1 {' '.join(i['thumbprint'][k:k + 8] for k in range(0, 40, 8))}</span><br>"
                          f"<span style='color:#1E8449'>{ok}</span>"
                          + ("<br><span style='color:#B34700'>" + "<br>".join(warn) + "</span>" if warn else ""))


# ──────────────────────────── ② Υπογραφή ────────────────────────────
class SignPage(QWidget):
    COLS = ["", "Αρχείο", "Αποτέλεσμα", "Μέθοδος", "Φάκελος"]
    COLORS = {"✅": "#E3F4E9", "🟡": "#FFF6DD", "❌": "#FDECEA", "⏭": "#EAF0FA", "⏳": "#F4F6FA"}

    def __init__(self, main):
        super().__init__(); self.setObjectName("page"); self.m = main; self.files = []
        self.w = None; self.vw = None
        cfg = load_cfg()
        self.setAcceptDrops(True)
        lay = QVBoxLayout(self); lay.setContentsMargins(26, 18, 26, 18); lay.setSpacing(8)
        lay.addWidget(title_block("② Υπογραφή αρχείων",
                                  "Σύρετε εδώ exe / dll / msi / ps1 (ή πατήστε «Προσθήκη») και μετά «Υπογραφή όλων»."))
        self.cur = QLabel(); self.cur.setTextFormat(Qt.TextFormat.RichText); self.cur.setObjectName("card")
        lay.addWidget(self.cur)
        r = QHBoxLayout()
        self.b_add = btn("➕ Αρχεία…", self.add_files, "secondary", "Προσθήκη αρχείων")
        self.b_dir = btn("📁 Φάκελος…", self.add_folder, "secondary", "Προσθήκη όλων των αρχείων ενός φακέλου (και υποφακέλων)")
        self.b_rem = btn("✖ Αφαίρεση", self.remove_selected, "secondary", "Αφαίρεση επιλεγμένων από τη λίστα (πλήκτρο Delete)")
        self.b_clr = btn("🧹 Καθαρισμός", self.clear, "secondary", "Άδειασμα λίστας")
        for b in (self.b_add, self.b_dir, self.b_rem, self.b_clr):
            r.addWidget(b)
        r.addStretch()
        self.count = QLabel(""); self.count.setObjectName("subtitle"); r.addWidget(self.count)
        lay.addLayout(r)
        self.tbl = QTableWidget(0, len(self.COLS)); self.tbl.setHorizontalHeaderLabels(self.COLS)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tbl.setWordWrap(False)
        hh = self.tbl.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive); self.tbl.setColumnWidth(4, 180)
        self.tbl.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tbl.customContextMenuRequested.connect(self.menu)
        self.tbl.cellDoubleClicked.connect(lambda rr, _c: open_in_explorer(self.files[rr]) if rr < len(self.files) else None)
        QShortcut(QKeySequence(Qt.Key.Key_Delete), self.tbl, activated=self.remove_selected)
        lay.addWidget(self.tbl, 1)
        self.drop = QLabel("⬇  Σύρετε αρχεία ή φακέλους εδώ  ·  διπλό κλικ σε γραμμή = άνοιγμα φακέλου  ·  δεξί κλικ = περισσότερα")
        self.drop.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop.setStyleSheet("border:2px dashed #A9B7CE;border-radius:10px;padding:9px;color:#5C6B80;background:white;")
        lay.addWidget(self.drop)

        g = QGroupBox("Επιλογές"); gl = QGridLayout(g); gl.setHorizontalSpacing(12); gl.setVerticalSpacing(6)
        self.ts = QComboBox()
        for t, u in TIMESTAMPS:
            self.ts.addItem(t, u)
        self.ts.setCurrentIndex(max(0, self.ts.findData(cfg.get("ts", TIMESTAMPS[0][1]))))
        self.auto_ts = QCheckBox("Αν δεν απαντά, δοκίμασε αυτόματα τους άλλους")
        self.auto_ts.setChecked(cfg.get("auto_ts", True))
        self.desc = QLineEdit(cfg.get("desc", "")); self.desc.setPlaceholderText("π.χ. MyApp (προαιρετικό)")
        self.url = QLineEdit(cfg.get("url", "")); self.url.setPlaceholderText("https://… (προαιρετικό)")
        for wdg in (self.desc, self.url):
            wdg.setToolTip("Εμφανίζεται στο παράθυρο UAC. Χρησιμοποιείται μόνο με το signtool.")
        self.method = QComboBox()
        for t, v in METHODS:
            self.method.addItem(t, v)
        self.method.setCurrentIndex(max(0, self.method.findData(cfg.get("method", "auto"))))
        self.st_path = QLineEdit(cfg.get("signtool_path", ""))
        self.st_path.setPlaceholderText("αυτόματη αναζήτηση (Windows SDK)")
        self.st_ok = QLabel(); self.st_ok.setFixedWidth(22)
        stl = QHBoxLayout(); stl.setContentsMargins(0, 0, 0, 0); stl.addWidget(self.st_path)
        stl.addWidget(btn("…", self.browse_signtool, "secondary", "Επιλογή signtool.exe", 46)); stl.addWidget(self.st_ok)
        self.skip = QCheckBox("Παράλειψη αρχείων που είναι ήδη υπογεγραμμένα με αυτό το πιστοποιητικό")
        self.skip.setChecked(cfg.get("skip_signed", False))
        self.b_sendto = btn("", self.toggle_sendto, "secondary",
                            "Προσθέτει «CertifiCat - Υπογραφή» στο δεξί κλικ → Αποστολή προς (Send to)")
        self.b_sendto.setEnabled(IS_WIN)
        gl.addWidget(QLabel("Χρονοσήμανση:"), 0, 0); gl.addWidget(self.ts, 0, 1); gl.addWidget(self.auto_ts, 0, 2, 1, 2)
        gl.addWidget(QLabel("Περιγραφή:"), 1, 0); gl.addWidget(self.desc, 1, 1)
        gl.addWidget(QLabel("Ιστοσελίδα:"), 1, 2); gl.addWidget(self.url, 1, 3)
        gl.addWidget(QLabel("Εργαλείο:"), 2, 0); gl.addWidget(self.method, 2, 1)
        gl.addWidget(QLabel("signtool.exe:"), 2, 2); gl.addLayout(stl, 2, 3)
        gl.addWidget(self.skip, 3, 0, 1, 4)
        gl.setColumnStretch(1, 1); gl.setColumnStretch(3, 1)
        lay.addWidget(g)
        self.st_path.textChanged.connect(self._signtool_status)
        self.method.currentIndexChanged.connect(self._signtool_status)

        b = QHBoxLayout()
        self.bv = btn("🔍 Έλεγχος υπογραφών", self.verify, "secondary")
        self.bstop = btn("■ Διακοπή", self.stop, "danger"); self.bstop.hide()
        self.bs = btn("✍  Υπογραφή όλων", self.sign, "orange"); self.bs.setMinimumHeight(44)
        self.prog = QProgressBar(); self.prog.setTextVisible(False); self.prog.setFixedHeight(8)
        self.prog.setStyleSheet("QProgressBar{background:#DDE3EC;}"); self.prog.hide()
        self.bv.setMinimumHeight(44); self.b_sendto.setMinimumHeight(44)
        b.addWidget(self.bv); b.addWidget(self.b_sendto); b.addWidget(self.prog, 1); b.addWidget(self.bstop)
        b.addWidget(self.bs, 1)
        lay.addLayout(b)
        self._signtool_status()
        self._sendto_label()

    # ---- κατάσταση ----
    def busy(self):
        return bool((self.w and self.w.isRunning()) or (self.vw and self.vw.isRunning()))

    def _set_busy(self, on):
        for wdg in (self.b_add, self.b_dir, self.b_rem, self.b_clr, self.bv, self.bs, self.ts, self.method,
                    self.st_path, self.skip, self.auto_ts, self.desc, self.url):
            wdg.setEnabled(not on)
        self.b_sendto.setEnabled(IS_WIN and not on)
        self.bstop.setVisible(on); self.prog.setVisible(on)
        self.setAcceptDrops(not on)
        self.m.set_nav_enabled(not on)
        if not on:
            self.refresh()

    def _signtool_status(self):
        p = self.st_path.text().strip()
        if p and not os.path.isfile(p):
            self.st_ok.setText("✘"); self.st_ok.setStyleSheet("color:#D9443F;font-weight:700;")
            self.st_ok.setToolTip("Το αρχείο δεν υπάρχει")
        else:
            t = get_signtool({"signtool_path": p})
            self.st_ok.setText("✔" if t else "—")
            self.st_ok.setStyleSheet("color:#1E8449;font-weight:700;" if t else "color:#5C6B80;")
            self.st_ok.setToolTip(t or "Δεν βρέθηκε — θα χρησιμοποιηθεί το PowerShell")
        self.refresh()

    def _cfg_now(self):
        return {"signtool_path": self.st_path.text().strip(), "method": self.method.currentData()}

    def effective_method(self):
        m = self.method.currentData()
        st = get_signtool(self._cfg_now())
        if m == "powershell" or (m == "auto" and not st):
            return "PowerShell"
        return "signtool" if st else "signtool (δεν βρέθηκε!)"

    def refresh(self):
        i = self.m.info
        if i:
            dl = days_left(i)
            extra = ""
            if not i["has_codesign"]:
                extra = " · <span style='color:#C0392B'>❌ δεν είναι πιστοποιητικό υπογραφής κώδικα</span>"
            elif dl < 0:
                extra = " · <span style='color:#C0392B'>❌ έχει λήξει</span>"
            elif dl < 60:
                extra = f" · <span style='color:#B34700'>⚠ λήγει σε {dl} ημέρες</span>"
            self.cur.setText(f"🔏 Υπογραφή ως: <b>{i['cn']}</b> · έως {i['not_after']:%d/%m/%Y} · "
                             f"μέθοδος: <b>{self.effective_method()}</b>{extra}")
        else:
            self.cur.setText("<span style='color:#B34700'>⚠ Ανοίξτε πρώτα πιστοποιητικό (βήμα ①)</span>")
        n = len(self.files)
        self.count.setText(f"{n} αρχεία" if n != 1 else "1 αρχείο")
        if not self.busy():
            self.bs.setEnabled(bool(i) and bool(self.files) and IS_WIN)
            self.bv.setEnabled(bool(self.files) and IS_WIN)
            self.b_rem.setEnabled(bool(self.files)); self.b_clr.setEnabled(bool(self.files))
        self.drop.setVisible(n < 3)

    # ---- λίστα αρχείων ----
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls() and not self.busy():
            e.acceptProposedAction()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls() and not self.busy():
            e.acceptProposedAction()

    def dropEvent(self, e):
        self.add_paths([u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()])

    @staticmethod
    def _scan(d):
        out = []
        for dp, dn, fn in os.walk(d):
            dn[:] = [x for x in dn if not x.startswith(".") and x.lower() not in ("__pycache__", "node_modules")]
            out += [os.path.join(dp, f) for f in sorted(fn) if f.lower().endswith(SIGNABLE)]
        return out

    def add_paths(self, paths):
        out, ignored = [], 0
        for p in paths:
            if os.path.isdir(p):
                out += self._scan(p)
            elif os.path.isfile(p) and p.lower().endswith(SIGNABLE):
                out.append(p)
            else:
                ignored += 1
        added = self.add(out)
        if ignored:
            self.m.toast(f"Προστέθηκαν {added} · αγνοήθηκαν {ignored} (δεν υπογράφονται)")
        return added

    def add_files(self):
        fs, _ = QFileDialog.getOpenFileNames(self, "Αρχεία για υπογραφή", load_cfg().get("sign_dir", os.path.expanduser("~")),
                                             "Προγράμματα (" + " ".join("*" + x for x in SIGNABLE) + ");;Όλα (*.*)")
        if fs:
            update_cfg(sign_dir=os.path.dirname(fs[0]))
            self.add_paths(fs)

    def add_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Φάκελος", load_cfg().get("sign_dir", os.path.expanduser("~")))
        if d:
            update_cfg(sign_dir=d)
            found = self._scan(d)
            if not found:
                self.m.toast("Δεν βρέθηκαν αρχεία για υπογραφή σε αυτόν τον φάκελο"); return
            if len(found) > 200 and QMessageBox.question(
                    self, APP_NAME, f"Βρέθηκαν {len(found)} αρχεία (και σε υποφακέλους). Να προστεθούν όλα;") \
                    != QMessageBox.StandardButton.Yes:
                return
            self.add(found)

    def add(self, files):
        known = {os.path.normcase(x) for x in self.files}
        n = 0
        for f in files:
            f = os.path.abspath(f)
            if os.path.normcase(f) in known:
                continue
            known.add(os.path.normcase(f))
            self.files.append(f)
            r = self.tbl.rowCount(); self.tbl.insertRow(r)
            for c, v in enumerate(["•", os.path.basename(f), "Σε αναμονή", "", os.path.dirname(f)]):
                it = QTableWidgetItem(v)
                if c == 0:
                    it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if c in (1, 4):
                    it.setToolTip(f)
                self.tbl.setItem(r, c, it)
            n += 1
        self.refresh()
        return n

    def selected_rows(self):
        return sorted({i.row() for i in self.tbl.selectedIndexes()})

    def remove_selected(self):
        if self.busy():
            return
        for r in reversed(self.selected_rows()):
            self.tbl.removeRow(r); del self.files[r]
        self.refresh()

    def clear(self):
        if self.busy():
            return
        self.files = []; self.tbl.setRowCount(0); self.refresh()

    def menu(self, pos):
        rows = self.selected_rows()
        if not rows:
            return
        mn = QMenu(self)
        a1 = mn.addAction("📂 Άνοιγμα φακέλου")
        a2 = mn.addAction("🔍 Έλεγχος επιλεγμένων")
        a3 = mn.addAction("✍ Υπογραφή επιλεγμένων")
        mn.addSeparator()
        a4 = mn.addAction("➖ Αφαίρεση από τη λίστα")
        busy = self.busy()
        a2.setEnabled(not busy and IS_WIN); a3.setEnabled(not busy and IS_WIN and bool(self.m.info)); a4.setEnabled(not busy)
        act = mn.exec(self.tbl.viewport().mapToGlobal(pos))
        if act == a1:
            open_in_explorer(self.files[rows[0]])
        elif act == a2:
            self.verify(rows)
        elif act == a3:
            self.sign(rows)
        elif act == a4:
            self.remove_selected()

    def set_row(self, i, icon, text, how=None):
        if i >= self.tbl.rowCount():
            return
        self.tbl.item(i, 0).setText(icon); self.tbl.item(i, 2).setText(text); self.tbl.item(i, 2).setToolTip(text)
        if how is not None:
            self.tbl.item(i, 3).setText(how)
        col = QColor(self.COLORS.get(icon, "#FFFFFF"))
        for c in range(self.tbl.columnCount()):
            self.tbl.item(i, c).setBackground(col)
        if icon != "⏳":
            self.prog.setValue(self.prog.value() + 1)
            self.tbl.scrollToItem(self.tbl.item(i, 0))

    # ---- ρυθμίσεις ----
    def browse_signtool(self):
        f, _ = QFileDialog.getOpenFileName(self, "signtool.exe", os.path.dirname(self.st_path.text()) or "",
                                           "SignTool (signtool*.exe);;Προγράμματα (*.exe)")
        if f:
            self.st_path.setText(f)

    def save_options(self):
        update_cfg(desc=self.desc.text(), url=self.url.text(), ts=self.ts.currentData(), auto_ts=self.auto_ts.isChecked(),
                   method=self.method.currentData(), signtool_path=self.st_path.text().strip(),
                   skip_signed=self.skip.isChecked())

    def _sendto_label(self):
        self.b_sendto.setText("📌 Αφαίρεση από «Αποστολή προς»" if IS_WIN and os.path.exists(sendto_path())
                              else "📌 Δεξί κλικ → «Αποστολή προς»")

    def toggle_sendto(self):
        if os.path.exists(sendto_path()):
            try:
                os.remove(sendto_path()); self.m.toast("Αφαιρέθηκε από το «Αποστολή προς»")
            except OSError as ex:
                QMessageBox.warning(self, APP_NAME, str(ex))
        else:
            ok, err = sendto_create()
            if ok:
                QMessageBox.information(self, APP_NAME, "Έτοιμο! Τώρα μπορείτε να κάνετε δεξί κλικ σε exe/dll/msi "
                                        "(ή σε φάκελο) → «Αποστολή προς» → «CertifiCat - Υπογραφή».\n\n"
                                        "Υπογράφονται αμέσως με το τελευταίο πιστοποιητικό (αν έχει αποθηκευτεί ο κωδικός).")
            else:
                QMessageBox.warning(self, APP_NAME, "Δεν δημιουργήθηκε η συντόμευση.\n\n" + err)
        self._sendto_label()

    # ---- υπογραφή / έλεγχος ----
    def sign(self, rows=None):
        if self.busy() or not self.files:
            return
        i = self.m.info
        if not i:
            QMessageBox.warning(self, APP_NAME, "Ανοίξτε πρώτα πιστοποιητικό (βήμα ①)."); self.m.go(0); return
        if not i["has_codesign"]:
            QMessageBox.critical(self, APP_NAME, "Αυτό το πιστοποιητικό δεν επιτρέπεται για υπογραφή κώδικα."); return
        if days_left(i) < 0:
            QMessageBox.critical(self, APP_NAME, "Το πιστοποιητικό έχει λήξει. Φτιάξτε νέο στο βήμα ①."); return
        if not os.path.isfile(self.m.pfx):
            QMessageBox.critical(self, APP_NAME, f"Δεν βρίσκεται πια το αρχείο:\n{self.m.pfx}"); return
        method = self.method.currentData()
        st = get_signtool(self._cfg_now())
        if method == "signtool" and not st:
            QMessageBox.warning(self, APP_NAME, "Επιλέξατε «Πάντα signtool» αλλά δεν βρέθηκε το signtool.exe.\n"
                                "Διαλέξτε «Αυτόματα» ή δείξτε τη θέση του."); return
        rows = rows if rows else list(range(len(self.files)))
        pkgs = [self.files[r] for r in rows if self.files[r].lower().endswith(NEEDS_SIGNTOOL)]
        if pkgs and not st:
            QMessageBox.warning(self, APP_NAME, "Τα αρχεία MSIX/APPX υπογράφονται μόνο με signtool (Windows SDK). "
                                                "Θα παραλειφθούν/αποτύχουν:\n" + "\n".join(os.path.basename(x) for x in pkgs[:5]))
        self.save_options()
        url = self.ts.currentData()
        ts_list = [url] + [u for _, u in TIMESTAMPS if u and u != url] if url else []
        log("═" * 60)
        log(f"Υπογραφή {len(rows)} αρχείων ως «{i['cn']}» · μέθοδος {self.effective_method()} · "
            f"χρονοσήμανση {url or 'καμία'}")
        for r in rows:
            self.set_row(r, "•", "Σε αναμονή", "")
        self.prog.setMaximum(len(rows)); self.prog.setValue(0)
        self._set_busy(True)
        self.w = SignWorker([(r, self.files[r]) for r in rows], self.m.pfx, self.m.pw, ts_list, self.auto_ts.isChecked(),
                            self.desc.text().strip(), self.url.text().strip(), i["thumbprint"], method, st,
                            self.skip.isChecked())
        self.w.progress.connect(self.set_row)
        self.w.finished_all.connect(self.signed)
        self.w.start()

    def signed(self, ok, bad, skipped):
        self._set_busy(False)
        msg = f"✓ Υπογράφηκαν {ok} αρχεία" + (f" · ⏭ {skipped} παραλείφθηκαν" if skipped else "") + \
              (f" · ❌ {bad} απέτυχαν" if bad else "")
        log(msg)
        self.m.toast(msg)
        if bad and not ok:
            QMessageBox.warning(self, APP_NAME, msg + "\n\nΔείτε τη στήλη «Αποτέλεσμα» ή την Καταγραφή για λεπτομέρειες.")
            return
        if ok and IS_WIN and self.m.info:
            run_task(cert_installed, self.m.info["thumbprint"], done=lambda s: self._after_sign(s, msg))

    def _after_sign(self, s, msg):
        if isinstance(s, dict) and not (s.get("user") or s.get("machine")):
            if QMessageBox.question(self, APP_NAME, msg + "\n\nΤο πιστοποιητικό δεν είναι ακόμα εγκατεστημένο σε αυτόν τον "
                                    "υπολογιστή, γι' αυτό τα Windows θα δείχνουν «άγνωστο εκδότη».\n"
                                    "Να πάμε στο βήμα ③ (Εγκατάσταση);") == QMessageBox.StandardButton.Yes:
                self.m.go(2)

    def verify(self, rows=None):
        if self.busy() or not self.files:
            return
        rows = rows if rows else list(range(len(self.files)))
        self.prog.setMaximum(len(rows)); self.prog.setValue(0)
        for r in rows:
            self.set_row(r, "⏳", "Έλεγχος…")
        self._set_busy(True)
        self.vw = VerifyWorker([(r, self.files[r]) for r in rows], self.m.info["thumbprint"] if self.m.info else "")
        self.vw.progress.connect(lambda i, ic, t: self.set_row(i, ic, t))
        self.vw.finished_all.connect(lambda: self._set_busy(False))
        self.vw.start()

    def stop(self):
        for w in (self.w, self.vw):
            if w and w.isRunning():
                w.stop()
        self.bstop.setEnabled(False); self.m.toast("Διακοπή μετά το τρέχον αρχείο…")
        QTimer.singleShot(1500, lambda: self.bstop.setEnabled(True))


# ──────────────────────────── ③ Εγκατάσταση ────────────────────────────
class InstallPage(QWidget):
    def __init__(self, main):
        super().__init__(); self.setObjectName("page"); self.m = main
        lay = QVBoxLayout(self); lay.setContentsMargins(26, 22, 26, 22)
        lay.addWidget(title_block("③ Εγκατάσταση & διανομή",
                                  "Για να δείχνουν τα Windows τον εκδότη σας αντί για «Άγνωστος εκδότης», το πιστοποιητικό "
                                  "πρέπει να εγκατασταθεί μία φορά σε κάθε υπολογιστή."))
        self.state = QLabel(); self.state.setTextFormat(Qt.TextFormat.RichText)
        self.state.setStyleSheet("background:white;border-radius:8px;padding:12px;font-size:11pt;")
        lay.addWidget(self.state)
        g = QGroupBox("💻 Αυτός ο υπολογιστής"); gl = QHBoxLayout(g)
        self.b1 = btn("👤 Εγκατάσταση για εμένα", lambda: self.install(False))
        self.b2 = btn("🛡 Εγκατάσταση για όλους (διαχειριστής)", lambda: self.install(True), "secondary")
        self.b3 = btn("🗑 Αφαίρεση", self.remove, "secondary")
        self.b4 = btn("↻", self.refresh, "secondary", "Επανέλεγχος", 46)
        for b in (self.b1, self.b2, self.b3, self.b4):
            gl.addWidget(b)
        gl.addStretch(); lay.addWidget(g)
        g2 = QGroupBox("📦 Άλλοι υπολογιστές (δουλειά, συνεργάτες)"); g2l = QVBoxLayout(g2)
        t = QLabel("Φτιάχνει ένα zip με το δημόσιο πιστοποιητικό και ένα «Install_Certificate.bat». "
                   "Το μεταφέρετε με USB / email / κοινόχρηστο φάκελο, το αποσυμπιέζουν και κάνουν διπλό κλικ. "
                   "Δεν περιέχει κανένα μυστικό.")
        t.setWordWrap(True); t.setObjectName("subtitle"); g2l.addWidget(t)
        r = QHBoxLayout()
        self.z = btn("📦 Δημιουργία πακέτου εγκατάστασης…", self.package, "orange")
        self.ce = btn("📄 Εξαγωγή μόνο .cer…", self.export_cer, "secondary")
        r.addWidget(self.z); r.addWidget(self.ce); r.addStretch(); g2l.addLayout(r)
        lay.addWidget(g2)
        warn = QLabel("ℹ Όταν ένα exe κατεβαίνει από τον browser, το SmartScreen μπορεί να ρωτήσει ακόμα την πρώτη φορά "
                      "(κρίνει και με βάση τη δημοφιλία του αρχείου). Από USB/κοινόχρηστο φάκελο συνήθως δεν ρωτά. "
                      "Σε υπολογιστές ΧΩΡΙΣ το πιστοποιητικό, θα εμφανίζεται «Άγνωστος εκδότης».")
        warn.setWordWrap(True); warn.setObjectName("subtitle"); lay.addWidget(warn)
        lay.addStretch()
        self._status = {}
        self._busy = False

    def _buttons(self):
        has = bool(self.m.info)
        for b in (self.b1, self.b2, self.b3, self.b4):
            b.setEnabled(has and IS_WIN and not self._busy)
        self.z.setEnabled(has); self.ce.setEnabled(has)

    def refresh(self):
        i = self.m.info
        self._buttons()
        if not i:
            self.state.setText("<span style='color:#B34700'>⚠ Ανοίξτε πρώτα πιστοποιητικό (βήμα ①)</span>"); return
        if not IS_WIN:
            self.state.setText(f"<b>{i['cn']}</b><br>— (η εγκατάσταση γίνεται μόνο σε Windows)"); return
        self.state.setText(f"<b>{i['cn']}</b><br>⏳ Έλεγχος…")
        thumb = i["thumbprint"]
        run_task(cert_installed, thumb, done=lambda s: self._show(s, thumb))

    def _show(self, s, thumb):
        i = self.m.info
        if not i or i["thumbprint"] != thumb or not isinstance(s, dict):
            return
        self._status = s
        if s.get("machine"):
            lab = "✅ Εγκατεστημένο για όλους τους χρήστες"
            if not s.get("machine_tp"):
                lab += " <span style='color:#B34700'>(λείπει από Trusted Publishers — ξαναπατήστε εγκατάσταση)</span>"
        elif s.get("user"):
            lab = "✅ Εγκατεστημένο για τον λογαριασμό σας"
            if not s.get("user_tp"):
                lab += " <span style='color:#B34700'>(λείπει από Trusted Publishers — ξαναπατήστε εγκατάσταση)</span>"
        else:
            lab = "⚪ Δεν είναι εγκατεστημένο σε αυτόν τον υπολογιστή"
        self.state.setText(f"<b>{i['cn']}</b><br>{lab}")

    def _cer_file(self):
        der = self.m.cert.public_bytes(serialization.Encoding.DER)
        p = os.path.join(config_dir(), "install_" + self.m.info["thumbprint"][:12] + ".cer")
        with open(p, "wb") as f:
            f.write(der)
        return p

    def install(self, machine):
        if not self.m.info or self._busy:
            return
        if self.m.info.get("is_ca"):
            if QMessageBox.warning(self, APP_NAME, "Αυτό το πιστοποιητικό είναι αρχή πιστοποίησης (CA). Η εγκατάστασή του "
                                   "στο Root είναι επικίνδυνη. Συνέχεια;",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) \
                    != QMessageBox.StandardButton.Yes:
                return
        if not machine:
            QMessageBox.information(self, APP_NAME, "Τα Windows θα εμφανίσουν «Προειδοποίηση ασφαλείας» για την "
                                    "εγκατάσταση του πιστοποιητικού.\n\nΠατήστε «Ναι».\n"
                                    "(Αν δεν τη βλέπετε, κοιτάξτε στη γραμμή εργασιών — μπορεί να είναι πίσω από αυτό το παράθυρο.)")
        else:
            self.m.toast("Θα ζητηθεί άδεια διαχειριστή (UAC)…")
        self._busy = True; self._buttons()
        self.state.setText(f"<b>{self.m.info['cn']}</b><br>⏳ Εγκατάσταση… (απαντήστε στο παράθυρο των Windows)")
        log(f"Εγκατάσταση πιστοποιητικού ({'όλοι οι χρήστες' if machine else 'τρέχων χρήστης'})")
        run_task(install_cert, self._cer_file(), machine, done=self._installed)

    def _installed(self, r):
        self._busy = False
        ok, msg = r if isinstance(r, tuple) else (False, str(r))
        log("✓ Εγκαταστάθηκε" if ok else f"✗ Η εγκατάσταση δεν ολοκληρώθηκε: {msg}")
        self.m.toast("✓ Εγκαταστάθηκε" if ok else f"Η εγκατάσταση δεν ολοκληρώθηκε: {msg}")
        self.refresh()

    def remove(self):
        if not self.m.info or self._busy:
            return
        if QMessageBox.question(self, APP_NAME, "Να αφαιρεθεί το πιστοποιητικό από αυτόν τον υπολογιστή;\n"
                                "(Τα ήδη υπογεγραμμένα αρχεία ΔΕΝ επηρεάζονται.)") != QMessageBox.StandardButton.Yes:
            return
        self._busy = True; self._buttons()
        thumb = self.m.info["thumbprint"]
        log("Αφαίρεση πιστοποιητικού από τον υπολογιστή")

        def work():
            s = cert_installed(thumb)
            return uninstall_cert(thumb, machine=s.get("machine") or s.get("machine_tp"))
        run_task(work, done=self._removed)

    def _removed(self, r):
        self._busy = False
        ok, msg = r if isinstance(r, tuple) else (False, str(r))
        self.m.toast("Αφαιρέθηκε" if ok else f"Η αφαίρεση δεν ολοκληρώθηκε: {msg}")
        log("✓ Αφαιρέθηκε" if ok else f"✗ {msg}")
        self.refresh()

    def package(self):
        if not self.m.info:
            return
        f, _ = QFileDialog.getSaveFileName(self, "Πακέτο εγκατάστασης",
                                           os.path.join(load_cfg().get("out_dir", os.path.expanduser("~")),
                                                        safe_name(self.m.info["cn"]) + "_Certificate.zip"), "Zip (*.zip)")
        if not f:
            return
        f = f if f.lower().endswith(".zip") else f + ".zip"
        try:
            make_install_package(self.m.cert.public_bytes(serialization.Encoding.DER), self.m.info, f)
        except Exception as ex:
            QMessageBox.critical(self, APP_NAME, f"Δεν δημιουργήθηκε:\n{ex}"); return
        log(f"Πακέτο εγκατάστασης: {f}")
        self.m.toast("✓ Το πακέτο δημιουργήθηκε")
        open_in_explorer(f)

    def export_cer(self):
        if not self.m.info:
            return
        f, _ = QFileDialog.getSaveFileName(self, "Δημόσιο πιστοποιητικό",
                                           os.path.join(load_cfg().get("out_dir", os.path.expanduser("~")),
                                                        safe_name(self.m.info["cn"]) + ".cer"), "Πιστοποιητικό (*.cer)")
        if not f:
            return
        f = f if f.lower().endswith((".cer", ".crt")) else f + ".cer"
        try:
            with open(f, "wb") as fh:
                fh.write(self.m.cert.public_bytes(serialization.Encoding.DER))
        except OSError as ex:
            QMessageBox.critical(self, APP_NAME, str(ex)); return
        self.m.toast("✓ Αποθηκεύτηκε")


class LogDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Καταγραφή — " + APP_NAME); self.resize(820, 480)
        l = QVBoxLayout(self)
        self.t = QPlainTextEdit(); self.t.setObjectName("log"); self.t.setReadOnly(True)
        self.t.setMaximumBlockCount(5000)
        self.t.setPlainText("\n".join(log.buffer))
        l.addWidget(self.t)
        r = QHBoxLayout()
        r.addWidget(btn("📋 Αντιγραφή", lambda: QGuiApplication.clipboard().setText(self.t.toPlainText()), "secondary"))
        r.addWidget(btn("🧹 Καθαρισμός", self.clear, "secondary"))
        r.addWidget(btn("📄 Αρχείο καταγραφής", lambda: open_in_explorer(log.path), "secondary"))
        r.addStretch(); r.addWidget(btn("Κλείσιμο", self.close))
        l.addLayout(r)
        log.line.connect(self.append)
        self.t.moveCursor(self.t.textCursor().MoveOperation.End)

    def append(self, s):
        self.t.appendPlainText(s)

    def clear(self):
        log.buffer.clear(); self.t.clear()


# ════════════════════════════════════════════════════════════════════
# 6. Ενημερώσεις (OTA) — δημόσια GitHub Releases, ΧΩΡΙΣ token
# ════════════════════════════════════════════════════════════════════
import urllib.request
import urllib.error

RELEASES_API = f"https://api.github.com/repos/{UPDATE_REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{UPDATE_REPO}/releases"


def _ver(s):
    return tuple(int(x) for x in re.findall(r"\d+", s or "")[:4]) or (0,)


def _http(url, timeout=20, accept="application/vnd.github+json"):
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": f"{APP_NAME}-updater/{APP_VERSION}"})
    return urllib.request.urlopen(req, timeout=timeout)


def update_target():
    """Το αρχείο που θα αντικατασταθεί: το .exe (αν είναι compiled) ή το .pyw."""
    return sys.executable if FROZEN else os.path.abspath(__file__)


def download_path():
    t = update_target()
    return os.path.splitext(t)[0] + ".update.exe" if FROZEN else t + ".download"


def check_update():
    """→ dict(newer, tag, notes, page, asset_name, asset_url, size, sha_url, msg)"""
    try:
        with _http(RELEASES_API) as r:
            d = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as ex:
        if ex.code == 404:
            return {"newer": False, "msg": "Δεν έχει δημοσιευτεί ακόμα καμία έκδοση.", "page": RELEASES_PAGE}
        return {"newer": False, "msg": f"GitHub: σφάλμα {ex.code}", "page": RELEASES_PAGE, "error": True}
    except Exception as ex:
        return {"newer": False, "msg": f"Χωρίς σύνδεση με το GitHub ({type(ex).__name__}).", "page": RELEASES_PAGE,
                "error": True}
    tag = d.get("tag_name") or ""
    want = ".exe" if FROZEN else ".pyw"
    assets = d.get("assets") or []
    asset = next((a for a in assets if a.get("name", "").lower().endswith(want)), None)
    sha = None
    if asset:
        nm = asset["name"].lower()
        sha = next((a for a in assets if a.get("name", "").lower() in (nm + ".sha256", "sha256sums.txt", "sha256sums")), None)
    info = {"newer": _ver(tag) > _ver(APP_VERSION), "tag": tag, "notes": d.get("body") or "",
            "page": d.get("html_url") or RELEASES_PAGE, "published": (d.get("published_at") or "")[:10],
            "asset_name": asset["name"] if asset else "", "asset_url": asset["browser_download_url"] if asset else "",
            "size": asset.get("size", 0) if asset else 0, "sha_url": sha["browser_download_url"] if sha else ""}
    if info["newer"] and not asset:
        info["msg"] = f"Η έκδοση {tag} δεν έχει αρχείο {want} — κατεβάστε την από τη σελίδα."
    elif info["newer"]:
        info["msg"] = f"Υπάρχει νέα έκδοση: {tag} (έχετε {APP_VERSION})"
    else:
        info["msg"] = f"Έχετε την τελευταία έκδοση ({APP_VERSION})."
    return info


class DownloadWorker(QThread):
    progress = pyqtSignal(int, int)
    done = pyqtSignal(object)          # (ok, path_or_msg)

    def __init__(self, info):
        super().__init__(); self.info = info; self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            self.done.emit((True, self._download()))
        except Exception as ex:
            self.done.emit((False, str(ex)))

    def _download(self):
        target = update_target()
        tdir = os.path.dirname(target)
        if not os.access(tdir, os.W_OK):
            raise RuntimeError(f"Δεν επιτρέπεται εγγραφή στον φάκελο:\n{tdir}\n\n"
                               "Κατεβάστε τη νέα έκδοση χειροκίνητα από τη σελίδα.")
        tmp = download_path()
        h = hashlib.sha256()
        with _http(self.info["asset_url"], timeout=60, accept="application/octet-stream") as r, open(tmp, "wb") as f:
            total = int(r.headers.get("Content-Length") or self.info.get("size") or 0)
            got = 0
            while True:
                if self._stop:
                    raise RuntimeError("Ακυρώθηκε.")
                chunk = r.read(65536)
                if not chunk:
                    break
                f.write(chunk); h.update(chunk); got += len(chunk)
                self.progress.emit(got, total)
        if got == 0 or (total and got != total):
            raise RuntimeError("Η λήψη δεν ολοκληρώθηκε.")
        digest = h.hexdigest().lower()
        if self.info.get("sha_url"):                      # προαιρετικό SHA-256 στο release
            with _http(self.info["sha_url"], accept="text/plain") as r:
                txt = r.read().decode("utf-8", "replace")
            hashes_ = {}
            for line in txt.splitlines():
                parts = line.replace("*", " ").split()
                if parts and re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]):
                    hashes_[parts[1] if len(parts) > 1 else self.info["asset_name"]] = parts[0].lower()
            exp = hashes_.get(self.info["asset_name"]) or (next(iter(hashes_.values())) if len(hashes_) == 1 else None)
            if exp and exp != digest:
                os.remove(tmp)
                raise RuntimeError("Το SHA-256 της λήψης δεν ταιριάζει — η ενημέρωση ακυρώθηκε.")
            log(f"Ενημέρωση: SHA-256 {'OK' if exp else 'δεν βρέθηκε στο αρχείο ελέγχου'}")
        if not FROZEN:                                     # .pyw: πρέπει να είναι έγκυρος Python & CertifiCat
            src = open(tmp, encoding="utf-8").read()
            compile(src, "update.pyw", "exec")
            if 'APP_NAME = "CertifiCat"' not in src:
                os.remove(tmp)
                raise RuntimeError("Το αρχείο δεν είναι CertifiCat — η ενημέρωση ακυρώθηκε.")
        elif IS_WIN:                                       # .exe: ίδια ψηφιακή υπογραφή με το τρέχον
            cur, new = verify_many([target, tmp])
            if cur.get("Thumb") and (cur.get("Thumb") or "").upper() != (new.get("Thumb") or "").upper():
                os.remove(tmp)
                raise RuntimeError("Η ψηφιακή υπογραφή της νέας έκδοσης δεν ταιριάζει με την τρέχουσα — ακυρώθηκε.")
        return tmp


def apply_update(tmp, asset_name=""):
    """Αντικαθιστά το τρέχον αρχείο και ξεκινά τη νέα έκδοση. → (ok, msg)"""
    target = update_target()
    try:
        if FROZEN:
            old = target + ".old"
            if os.path.exists(old):
                os.remove(old)
            os.replace(target, old)              # τα Windows επιτρέπουν μετονομασία του exe που τρέχει
            os.replace(tmp, target)
            subprocess.Popen([target], close_fds=True)
        else:
            # το νέο .pyw παίρνει το όνομα του release (π.χ. CertifiCat_v3.6.pyw)· το παλιό μένει ως .bak
            name = os.path.basename(asset_name or "") or os.path.basename(target)
            new = os.path.join(os.path.dirname(target), name)
            shutil.copy2(target, target + ".bak")
            os.replace(tmp, new)
            if os.path.normcase(new) != os.path.normcase(target):
                os.remove(target)
                if IS_WIN and os.path.exists(sendto_path()):
                    sendto_create(new)           # το «Αποστολή προς» δείχνει στη νέα έκδοση
            target = new
            subprocess.Popen([_python_exe(windowed=True), target], close_fds=True, creationflags=NOWIN)
        log(f"Ενημέρωση εγκαταστάθηκε: {target}")
        return True, ""
    except Exception as ex:
        return False, str(ex)


def cleanup_after_update():
    for p in (update_target() + ".old", download_path()):
        try:
            if os.path.exists(p):
                os.remove(p)
        except OSError:
            pass


class UpdateDialog(QDialog):
    def __init__(self, main, info=None):
        super().__init__(main)
        self.m = main; self.info = info; self.dw = None
        self.setWindowTitle("Ενημερώσεις — " + APP_NAME); self.resize(600, 460)
        l = QVBoxLayout(self)
        top = QHBoxLayout()
        lg = QLabel(); lg.setPixmap(logo_pixmap(64)); top.addWidget(lg)
        self.head = QLabel(f"<b>{APP_NAME}</b> — έκδοση {APP_VERSION}<br>"
                           f"<span style='color:#5C6B80'>Πηγή: github.com/{UPDATE_REPO} (δημόσιες εκδόσεις)</span>")
        self.head.setTextFormat(Qt.TextFormat.RichText); top.addWidget(self.head, 1); l.addLayout(top)
        self.status = QLabel("…"); self.status.setObjectName("card"); self.status.setWordWrap(True); l.addWidget(self.status)
        self.notes = QTextEdit(); self.notes.setReadOnly(True); self.notes.setPlaceholderText("Σημειώσεις έκδοσης")
        l.addWidget(self.notes, 1)
        self.bar = QProgressBar(); self.bar.setTextVisible(False); self.bar.setFixedHeight(8)
        self.bar.setStyleSheet("QProgressBar{background:#DDE3EC;}"); self.bar.hide(); l.addWidget(self.bar)
        self.auto = QCheckBox("Έλεγχος για ενημερώσεις αυτόματα σε κάθε εκκίνηση")
        self.auto.setChecked(load_cfg().get("auto_update", True))
        self.auto.toggled.connect(lambda v: update_cfg(auto_update=v))
        l.addWidget(self.auto)
        r = QHBoxLayout()
        self.b_check = btn("⟳ Έλεγχος τώρα", self.check, "secondary")
        self.b_page = btn("🌐 Σελίδα εκδόσεων", lambda: QDesktopServices.openUrl(QUrl(
            (self.info or {}).get("page") or RELEASES_PAGE)), "secondary")
        self.b_get = btn("⬇ Λήψη && εγκατάσταση", self.download, "orange"); self.b_get.setEnabled(False)
        r.addWidget(self.b_check); r.addWidget(self.b_page); r.addStretch(); r.addWidget(self.b_get)
        r.addWidget(btn("Κλείσιμο", self.close, "secondary"))
        l.addLayout(r)
        if info:
            self.show_info(info)
        else:
            self.check()

    def check(self):
        self.status.setText("⏳ Έλεγχος στο GitHub…"); self.b_check.setEnabled(False); self.b_get.setEnabled(False)
        run_task(check_update, done=self.show_info)

    def show_info(self, info):
        self.b_check.setEnabled(True)
        if not isinstance(info, dict):
            info = {"newer": False, "msg": str(info)}
        self.info = info
        icon = "🆕" if info.get("newer") else ("⚠" if info.get("error") else "✅")
        extra = f" · δημοσιεύτηκε {info['published']}" if info.get("published") else ""
        self.status.setText(f"{icon} {info.get('msg', '')}{extra}")
        if info.get("notes"):
            self.notes.setMarkdown(info["notes"])
        self.b_get.setEnabled(bool(info.get("newer") and info.get("asset_url")))
        log(f"Έλεγχος ενημερώσεων: {info.get('msg')}")

    def download(self):
        if not self.info or not self.info.get("asset_url"):
            return
        if self.m.p2.busy():
            QMessageBox.warning(self, APP_NAME, "Περιμένετε να τελειώσει η υπογραφή."); return
        self.b_get.setEnabled(False); self.b_check.setEnabled(False); self.bar.show(); self.bar.setValue(0)
        self.status.setText(f"⬇ Λήψη {self.info['asset_name']}…")
        self.dw = DownloadWorker(self.info)
        self.dw.progress.connect(self._prog)
        self.dw.done.connect(self._downloaded)
        self.dw.start()

    def _prog(self, got, total):
        if total:
            self.bar.setMaximum(total); self.bar.setValue(got)
        else:
            self.bar.setMaximum(0)

    def _downloaded(self, r):
        ok, val = r
        self.bar.hide(); self.b_check.setEnabled(True)
        if not ok:
            self.status.setText("❌ " + val); self.b_get.setEnabled(True); log("Ενημέρωση: " + val); return
        if QMessageBox.question(self, APP_NAME, f"Η έκδοση {self.info['tag']} κατέβηκε και ελέγχθηκε.\n\n"
                                "Να γίνει επανεκκίνηση τώρα με τη νέα έκδοση;\n"
                                "(Οι ρυθμίσεις και η Κλειδοθήκη σας διατηρούνται.)") != QMessageBox.StandardButton.Yes:
            self.status.setText("Η λήψη έγινε — θα εγκατασταθεί όταν πατήσετε ξανά «Λήψη & εγκατάσταση».")
            try:
                os.remove(val)
            except OSError:
                pass
            self.b_get.setEnabled(True); return
        ok, msg = apply_update(val, self.info.get("asset_name", ""))
        if ok:
            self.m.restarting = True
            QApplication.instance().quit()
        else:
            self.status.setText("❌ Η εγκατάσταση απέτυχε: " + msg)

    def closeEvent(self, e):
        if self.dw and self.dw.isRunning():
            self.dw.stop(); self.dw.wait(5000)
        e.accept()


# ──────────────────────────── ④ Κλειδοθήκη ────────────────────────────
class VaultPage(QWidget):
    COLS = ["Πιστοποιητικό", "Λήγει", "Κωδικός", "Αρχείο .pfx"]

    def __init__(self, main):
        super().__init__(); self.setObjectName("page"); self.m = main; self.rows = []
        self._clip_timer = QTimer(self); self._clip_timer.setSingleShot(True); self._clip_timer.timeout.connect(self._clear_clip)
        self._clip_text = ""
        lay = QVBoxLayout(self); lay.setContentsMargins(26, 22, 26, 22)
        lay.addWidget(title_block("④ Κλειδοθήκη",
                                  "Τα πιστοποιητικά που φτιάξατε ή ανοίξατε σε αυτόν τον υπολογιστή. Οι κωδικοί φυλάσσονται "
                                  "ΜΟΝΟ αν το επιλέξετε — κρυπτογραφημένοι με τον λογαριασμό σας στα Windows, σε τοπική "
                                  "βάση. Τίποτα δεν στέλνεται πουθενά."))
        self.tbl = QTableWidget(0, len(self.COLS)); self.tbl.setHorizontalHeaderLabels(self.COLS)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        hh = self.tbl.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tbl.cellDoubleClicked.connect(lambda *_: self.use())
        self.tbl.itemSelectionChanged.connect(self._buttons)
        lay.addWidget(self.tbl, 1)
        r = QHBoxLayout()
        self.b_use = btn("🔓 Χρήση", self.use, None, "Άνοιγμα αυτού του πιστοποιητικού στο βήμα ①")
        self.b_copy = btn("📋 Αντιγραφή", self.copy_pw, "secondary",
                          "Αντιγραφή κωδικού — σβήνεται από το πρόχειρο αυτόματα μετά από 60 δευτερόλεπτα")
        self.b_show = btn("👁 Εμφάνιση", self.show_pw, "secondary", "Εμφάνιση του αποθηκευμένου κωδικού")
        self.b_dir = btn("📂 Φάκελος", self.folder, "secondary")
        self.b_forget = btn("🔑 Ξέχνα κωδικό", self.forget, "secondary", "Σβήνει μόνο τον αποθηκευμένο κωδικό")
        self.b_del = btn("🗑 Αφαίρεση", self.remove, "secondary", "Αφαίρεση από τη λίστα — τα αρχεία .pfx/.cer ΔΕΝ διαγράφονται")
        for b in (self.b_use, self.b_copy, self.b_show, self.b_dir, self.b_forget, self.b_del):
            r.addWidget(b)
        r.addStretch(); lay.addLayout(r)
        g = QGroupBox("💾 Αντίγραφο ασφαλείας"); gl = QHBoxLayout(g)
        t = QLabel("Κρατήστε αντίγραφο των αρχείων .pfx (και του κωδικού τους) σε ασφαλές μέρος — π.χ. USB. "
                   "Οι κωδικοί της βάσης ανοίγουν μόνο από τον δικό σας λογαριασμό σε αυτόν τον υπολογιστή.")
        t.setWordWrap(True); t.setObjectName("subtitle"); gl.addWidget(t, 1)
        gl.addWidget(btn("📦 Αντιγραφή σε φάκελο…", self.backup, "secondary", "Αντιγράφει όλα τα .pfx/.cer/.zip σε φάκελο (π.χ. USB)"))
        lay.addWidget(g)

    def refresh(self):
        self.rows = list_certs()
        self.tbl.setRowCount(0)
        today = datetime.now().strftime("%Y-%m-%d")
        for r in self.rows:
            i = self.tbl.rowCount(); self.tbl.insertRow(i)
            exists = os.path.isfile(r["pfx_path"])
            exp = r.get("not_after") or ""
            exp_txt = (datetime.strptime(exp, "%Y-%m-%d").strftime("%d/%m/%Y") if exp else "—")
            if exp and exp < today:
                exp_txt += "  ❌ έληξε"
            vals = [r.get("cn") or os.path.splitext(os.path.basename(r["pfx_path"]))[0], exp_txt,
                    "🔒 αποθηκευμένος" if r.get("pw_enc") else "—",
                    r["pfx_path"] + ("" if exists else "   ⚠ δεν βρίσκεται")]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                if r.get("thumbprint"):
                    it.setToolTip(f"SHA1 {fmt_thumb(r['thumbprint'])}\nΔημιουργία/πρώτη χρήση: {r.get('created', '')}")
                if not exists:
                    it.setForeground(QColor("#B34700"))
                if self.m.pfx and _pw_key(self.m.pfx) == r["pfx_key"]:
                    f = it.font(); f.setBold(True); it.setFont(f)
                self.tbl.setItem(i, c, it)
        if self.rows:
            self.tbl.selectRow(0)
        self._buttons()

    def cur(self):
        rr = self.tbl.currentRow()
        return self.rows[rr] if 0 <= rr < len(self.rows) and self.tbl.selectedItems() else None

    def _buttons(self):
        r = self.cur()
        has = bool(r); pw = bool(r and r.get("pw_enc"))
        for b in (self.b_use, self.b_dir, self.b_del):
            b.setEnabled(has)
        for b in (self.b_copy, self.b_show, self.b_forget):
            b.setEnabled(pw)

    def use(self):
        r = self.cur()
        if not r:
            return
        if not os.path.isfile(r["pfx_path"]):
            QMessageBox.warning(self, APP_NAME, f"Δεν βρίσκεται το αρχείο:\n{r['pfx_path']}"); return
        self.m.p1.path.setText(r["pfx_path"])
        pw = recall_password(r["pfx_path"])
        self.m.p1.pw2.setText(pw); self.m.p1.remember.setChecked(bool(pw))
        self.m.go(0)
        if pw:
            self.m.p1.open_existing()
        else:
            self.m.p1.pw2.setFocus(); self.m.toast("Γράψτε τον κωδικό και πατήστε «Άνοιγμα»")

    def _pw(self):
        r = self.cur()
        pw = recall_password(r["pfx_path"]) if r else ""
        if r and not pw:
            QMessageBox.warning(self, APP_NAME, "Ο κωδικός δεν ξεκλειδώνει σε αυτόν τον λογαριασμό/υπολογιστή.")
        return pw

    def copy_pw(self):
        pw = self._pw()
        if pw:
            QGuiApplication.clipboard().setText(pw); self._clip_text = pw; self._clip_timer.start(60000)
            self.m.toast("Ο κωδικός αντιγράφηκε (σβήνεται από το πρόχειρο σε 60″)")

    def _clear_clip(self):
        cb = QGuiApplication.clipboard()
        if self._clip_text and cb.text() == self._clip_text:
            cb.clear()
        self._clip_text = ""

    def show_pw(self):
        pw = self._pw()
        if pw:
            d = QMessageBox(self); d.setWindowTitle(APP_NAME); d.setTextFormat(Qt.TextFormat.RichText)
            d.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            d.setText(f"Κωδικός για <b>{self.cur().get('cn', '')}</b>:<br><br>"
                      f"<code style='font-size:13pt'>{pw}</code>"); d.exec()

    def folder(self):
        r = self.cur()
        if r:
            open_in_explorer(r["pfx_path"])

    def forget(self):
        r = self.cur()
        if r and QMessageBox.question(self, APP_NAME, "Να διαγραφεί ο αποθηκευμένος κωδικός;\n"
                                      "Θα χρειάζεται να τον γράφετε κάθε φορά.") == QMessageBox.StandardButton.Yes:
            forget_password(r["pfx_path"])
            if self.m.pfx and _pw_key(self.m.pfx) == r["pfx_key"]:
                self.m.p1.remember.setChecked(False)
            self.refresh()

    def remove(self):
        r = self.cur()
        if r and QMessageBox.question(self, APP_NAME, "Να αφαιρεθεί από τη λίστα (μαζί με τον αποθηκευμένο κωδικό);\n"
                                      "Τα αρχεία .pfx/.cer στον δίσκο ΔΕΝ διαγράφονται.") == QMessageBox.StandardButton.Yes:
            delete_cert(r["id"]); self.refresh()

    def backup(self):
        rows = [r for r in self.rows if os.path.isfile(r["pfx_path"])]
        if not rows:
            self.m.toast("Δεν υπάρχουν αρχεία για αντιγραφή"); return
        d = QFileDialog.getExistingDirectory(self, "Φάκελος αντιγράφου (π.χ. USB)")
        if not d:
            return
        n = 0
        for r in rows:
            for src in (r["pfx_path"], r.get("cer_path") or "", r.get("zip_path") or ""):
                if src and os.path.isfile(src):
                    dst = os.path.join(d, os.path.basename(src))
                    if os.path.abspath(dst) != os.path.abspath(src):
                        shutil.copy2(src, dst); n += 1
        log(f"Αντίγραφο ασφαλείας: {n} αρχεία → {d}")
        QMessageBox.information(self, APP_NAME, f"Αντιγράφηκαν {n} αρχεία στο:\n{d}\n\n"
                                                "Θυμηθείτε: χωρίς τον κωδικό, το .pfx δεν χρησιμοποιείται.")
        open_in_explorer(d)



HELP = """<h2>Πώς δουλεύει</h2>
<ol>
<li><b>Πιστοποιητικό:</b> «Δημιουργία» μία φορά. Βγαίνουν 3 αρχεία: <b>.pfx</b> (ιδιωτικό — ΜΗΝ το δίνετε),
<b>.cer</b> (δημόσιο) και <b>_Certificate.zip</b> (για τους άλλους υπολογιστές). Φυλάξτε τον κωδικό.</li>
<li><b>Υπογραφή:</b> σύρετε τα exe/dll/msi και πατήστε «Υπογραφή όλων». Υπογράψτε ΞΑΝΑ μετά από κάθε νέο build.</li>
<li><b>Εγκατάσταση:</b> σε αυτόν τον υπολογιστή με ένα κουμπί· στους άλλους με το zip (διπλό κλικ στο bat).</li>
</ol>
<h3>Γρήγορα</h3>
<ul>
<li><b>Δεξί κλικ → Αποστολή προς:</b> στο βήμα ② πατήστε «📌 Δεξί κλικ → «Αποστολή προς»». Μετά υπογράφετε απευθείας από τον Explorer.</li>
<li><b>Από build script:</b> <code>pythonw CertifiCat_v3.5.pyw --sign dist\\MyApp.exe</code></li>
<li><b>Χρονοσήμανση:</b> αν ένας διακομιστής δεν απαντά, δοκιμάζονται αυτόματα οι άλλοι. Χωρίς internet διαλέξτε «Χωρίς χρονοσήμανση».</li>
<li><b>Καταγραφή:</b> όλα τα μηνύματα των signtool/PowerShell, για όταν κάτι αποτύχει.</li>
<li><b>Κλειδοθήκη (④):</b> λίστα με όλα τα πιστοποιητικά σας. Ο κωδικός φυλάσσεται μόνο αν το επιλέξετε,
κρυπτογραφημένος, σε τοπική βάση (<code>%APPDATA%\\CertifiCat\\certificat.db</code>).</li>
<li><b>Ενημερώσεις:</b> ελέγχονται από τις δημόσιες εκδόσεις στο GitHub. Η εφαρμογή δεν στέλνει κανένα προσωπικό στοιχείο.</li>
</ul>
<p><b>Ασφάλεια:</b> τα πιστοποιητικά της εφαρμογής επιτρέπονται ΜΟΝΟ για υπογραφή προγραμμάτων και δεν μπορούν να
εκδώσουν άλλα πιστοποιητικά, άρα δεν επηρεάζουν ιστοσελίδες/HTTPS ακόμα κι αν εγκατασταθούν στο Root.
Ο αποθηκευμένος κωδικός κρυπτογραφείται με τον λογαριασμό σας στα Windows (DPAPI).</p>
<p><b>Μέθοδος:</b> αν υπάρχει το signtool (Windows SDK) χρησιμοποιείται αυτό· αλλιώς το PowerShell των Windows
(Set-AuthenticodeSignature) — δεν χρειάζεται να εγκαταστήσετε τίποτα. Μόνο τα MSIX/APPX θέλουν signtool.</p>"""


class MainWindow(QMainWindow):
    def __init__(self, res, start_files=None, autosign=False):
        super().__init__()
        self.pfx = self.pw = ""; self.cert = None; self.info = None
        self.log_dlg = None
        self.restarting = False
        self.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}")
        self.setWindowIcon(QIcon(logo_pixmap(256))); self.resize(1180, 800); self.setMinimumSize(900, 600)
        root = QWidget(); self.setCentralWidget(root)
        h = QHBoxLayout(root); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(0)
        side = QWidget(); side.setObjectName("sidebar"); side.setFixedWidth(265)
        sl = QVBoxLayout(side); sl.setContentsMargins(0, 18, 0, 14); sl.setSpacing(2)
        top = QHBoxLayout(); top.setContentsMargins(16, 0, 16, 12)
        lg = QLabel(); lg.setPixmap(logo_badge(46)); top.addWidget(lg)
        nm = QLabel(f"CertifiCat<br><span style='font-size:8.5pt;color:#B7A3CB;font-weight:400'>v{APP_VERSION}</span>")
        nm.setStyleSheet("color:white;font-size:14pt;font-weight:800;"); top.addWidget(nm); top.addStretch()
        sl.addLayout(top)
        self.btns = []
        for i, t in enumerate(["①  Πιστοποιητικό", "②  Υπογραφή αρχείων", "③  Εγκατάσταση && διανομή", "④  Κλειδοθήκη"]):
            b = QPushButton(t); b.setObjectName("step"); b.setCheckable(True); b.clicked.connect(lambda _, k=i: self.go(k))
            sl.addWidget(b); self.btns.append(b)
        sl.addStretch()
        for t, fn in (("📜  Καταγραφή", self.show_log), ("⟳  Ενημερώσεις", self.show_update), ("❓  Οδηγός", self.help),
                      ("ℹ️  Σχετικά", self.about)):
            b = QPushButton(t); b.setObjectName("step"); b.clicked.connect(fn); sl.addWidget(b)
            if t.startswith("⟳"):
                self.b_update = b
        cr = QLabel(f"  {AUTHOR_NAME_EN} · {APP_AUTHOR}"); cr.setStyleSheet("color:#9C86B3;font-size:8.5pt;padding:8px 16px;"); sl.addWidget(cr)
        h.addWidget(side)
        self.stack = QStackedWidget()
        self.p1 = CertPage(self); self.p2 = SignPage(self); self.p3 = InstallPage(self); self.p4 = VaultPage(self)
        for p in (self.p1, self.p2, self.p3, self.p4):
            self.stack.addWidget(p)
        h.addWidget(self.stack, 1)
        self.statusBar().setStyleSheet("background:white;color:#5C6B80;")
        self.go(0)
        self.p1.autoload()
        if not IS_WIN:
            self.toast("Μη-Windows: διαθέσιμη μόνο η δημιουργία πιστοποιητικών/πακέτων")
        if start_files:
            n = self.p2.add_paths(start_files)
            self.go(1)
            if autosign and n:
                if self.info:
                    QTimer.singleShot(400, self.p2.sign)
                else:
                    self.toast("Ανοίξτε πρώτα το πιστοποιητικό (βήμα ①) και πατήστε «Υπογραφή όλων»")
        if load_cfg().get("auto_update", True) and not autosign:
            QTimer.singleShot(3000, lambda: run_task(check_update, done=self._auto_update))

    def _auto_update(self, info):
        if not isinstance(info, dict) or not info.get("newer"):
            return
        self.b_update.setText(f"🆕  Νέα έκδοση {info['tag']}")
        if load_cfg().get("skip_version") == info["tag"]:
            return
        box = QMessageBox(self); box.setWindowTitle(APP_NAME); box.setIcon(QMessageBox.Icon.Information)
        box.setText(f"Υπάρχει νέα έκδοση {APP_NAME} <b>{info['tag']}</b> (έχετε {APP_VERSION}).")
        see = box.addButton("Δείτε τι νέο υπάρχει", QMessageBox.ButtonRole.AcceptRole)
        skip = box.addButton("Παράλειψη αυτής της έκδοσης", QMessageBox.ButtonRole.DestructiveRole)
        box.addButton("Αργότερα", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() == see:
            self.show_update(info)
        elif box.clickedButton() == skip:
            update_cfg(skip_version=info["tag"])

    def set_cert(self, pfx, pw, cert, info):
        self.pfx, self.pw, self.cert, self.info = pfx, pw, cert, info
        self.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}" + (f"  ·  {info['cn']}" if info else ""))
        self.p2.refresh()

    def set_nav_enabled(self, on):
        for k, b in enumerate(self.btns):
            if k != 1:
                b.setEnabled(on)

    def go(self, i):
        if self.p2.busy() and i != 1:
            return
        for k, b in enumerate(self.btns):
            b.setChecked(k == i)
        self.stack.setCurrentIndex(i)
        if i == 1:
            self.p2.refresh()
        elif i == 2:
            self.p3.refresh()
        elif i == 3:
            self.p4.refresh()

    def toast(self, m):
        self.statusBar().showMessage(m, 7000)

    def show_log(self):
        if not self.log_dlg:
            self.log_dlg = LogDialog(self)
        self.log_dlg.show(); self.log_dlg.raise_(); self.log_dlg.activateWindow()

    def show_update(self, info=None):
        UpdateDialog(self, info if isinstance(info, dict) else None).exec()

    def help(self):
        d = QDialog(self); d.setWindowTitle("Οδηγός"); d.resize(640, 520)
        l = QVBoxLayout(d); t = QTextEdit(); t.setReadOnly(True); t.setHtml(HELP); l.addWidget(t)
        b = QPushButton("Κατάλαβα!"); b.clicked.connect(d.accept); l.addWidget(b); d.exec()

    def about(self):
        d = QDialog(self); d.setWindowTitle("Σχετικά"); d.setFixedWidth(460)
        l = QVBoxLayout(d); l.setSpacing(4)
        lg = QLabel(); lg.setPixmap(logo_pixmap(120)); lg.setAlignment(Qt.AlignmentFlag.AlignCenter); l.addWidget(lg)
        rows = [
            (APP_NAME, "font-size:22pt;font-weight:800;color:#362044;"),
            ("Πιστοποιητικά & ψηφιακή υπογραφή προγραμμάτων", "color:#5C6B80;"),
            (f"Έκδοση {APP_VERSION}", "color:#2D6CDF;font-weight:600;margin-bottom:10px;"),
            (AUTHOR_NAME, "font-size:14pt;font-weight:700;color:#362044;"),
            (AUTHOR_NAME_EN, "color:#5C6B80;"),
            (AUTHOR_TITLE, "color:#362044;font-weight:600;margin-bottom:6px;"),
            (f"✉ <a href='mailto:{AUTHOR_EMAIL}'>{AUTHOR_EMAIL}</a>", ""),
            (f"<a href='{AUTHOR_GITHUB}'>{AUTHOR_GITHUB.replace('https://', '')}</a> · "
             f"<a href='https://github.com/{UPDATE_REPO}'>κώδικας & εκδόσεις</a>", ""),
            (f"© {datetime.now().year} {AUTHOR_NAME_EN} · Άδεια GPL-3.0 · Δωρεάν λογισμικό",
             "color:#9AA5B8;font-size:8.5pt;margin-top:10px;"),
        ]
        for txt, css in rows:
            q = QLabel(txt); q.setStyleSheet(css); q.setAlignment(Qt.AlignmentFlag.AlignCenter)
            q.setTextFormat(Qt.TextFormat.RichText); q.setOpenExternalLinks(True); q.setWordWrap(True); l.addWidget(q)
        r = QHBoxLayout()
        r.addWidget(btn("⟳ Έλεγχος ενημερώσεων", lambda: (d.accept(), self.show_update()), "secondary"))
        r.addStretch(); r.addWidget(btn("OK", d.accept)); l.addSpacing(8); l.addLayout(r)
        d.exec()

    def closeEvent(self, e):
        if self.p2.busy():
            if QMessageBox.question(self, APP_NAME, "Η υπογραφή/έλεγχος βρίσκεται σε εξέλιξη. Διακοπή και έξοδος;") \
                    != QMessageBox.StandardButton.Yes:
                e.ignore(); return
            self.p2.stop()
            for w in (self.p2.w, self.p2.vw):
                if w:
                    w.wait(15000)
        self.p2.save_options()
        for t in list(_TASKS):
            t.wait(3000)
        e.accept()


def _excepthook(tp, val, tb):
    txt = "".join(traceback.format_exception(tp, val, tb))
    log("ΣΦΑΛΜΑ:\n" + txt)
    try:
        if QApplication.instance():
            QMessageBox.critical(None, APP_NAME, f"Απρόσμενο σφάλμα:\n\n{val}\n\n(Λεπτομέρειες στην Καταγραφή)")
    except Exception:
        pass


def parse_args(argv):
    autosign = False
    files = []
    for a in argv:
        if a.lower() in ("--sign", "/sign", "-s"):
            autosign = True
        elif os.path.exists(a):
            files.append(os.path.abspath(a))
    return files, autosign


def main():
    sys.excepthook = _excepthook          # το PyQt6 κλείνει την εφαρμογή σε ανεπεξέργαστο σφάλμα — εδώ εμφανίζεται μήνυμα
    if IS_WIN:
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ALU.CertifiCat")
        except Exception:
            pass
    files, autosign = parse_args(sys.argv[1:])
    log(f"{APP_NAME} {APP_VERSION} — εκκίνηση" + (f" με {len(files)} αρχεία" if files else ""))
    app = QApplication(sys.argv); app.setStyle("Fusion"); apply_light_theme(app); app.setStyleSheet(STYLE)
    app.setWindowIcon(QIcon(logo_pixmap(256)))
    sp = Splash()
    scr = app.primaryScreen().availableGeometry()
    sp.move(scr.center().x() - sp.width() // 2, scr.center().y() - sp.height() // 2); sp.show()
    hold = {}

    def start(res):
        if "w" in hold:
            return
        hold["w"] = MainWindow(res, files, autosign); fit_to_screen(hold["w"]); hold["w"].show(); sp.close()
    sp.done.connect(start)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
