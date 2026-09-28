# =============================================================================
# تشغيل منصة الذكاء الاصطناعي في علم الآثار — هيئة الشارقة للآثار
# سكربت جاهز: يُنشئ البيئة، يثبّت الاعتماديات، ويشغّل الواجهة — بأمر واحد.
#
#   الاستخدام:  .\run_app.ps1
# =============================================================================

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "🏛️  منصة الذكاء الاصطناعي في علم الآثار — تشغيل محلي" -ForegroundColor Cyan

# 1) التأكد من وجود Python
$python = "python"
try { & $python --version | Out-Null } catch {
    Write-Host "❌ لم يتم العثور على Python. ثبّته من python.org ثم أعد المحاولة." -ForegroundColor Red
    exit 1
}

# 2) إنشاء البيئة الافتراضية عند الحاجة
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "📦 إنشاء البيئة الافتراضية (.venv)..." -ForegroundColor Yellow
    & $python -m venv .venv
}

# 3) تثبيت الاعتماديات عند الحاجة
& .venv\Scripts\python.exe -c "import streamlit" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⬇️  تثبيت الاعتماديات (قد تستغرق دقائق)... " -ForegroundColor Yellow
    & .venv\Scripts\python.exe -m pip install --upgrade pip --quiet
    & .venv\Scripts\python.exe -m pip install -r requirements.txt
}

# 4) تجهيز ملف المفتاح
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "🔑 تم إنشاء ملف .env — افتحه وضع مفتاح Gemini API بداخله." -ForegroundColor Yellow
    Write-Host "   (أو ضعه مباشرة من الشريط الجانبي داخل الواجهة)" -ForegroundColor DarkGray
}

# (اختياري) فتح ملف .env للمستخدم إن كان لا يزال يحتوي القيمة الافتراضية
if ((Get-Content ".env" -Raw) -match "your_gemini_api_key_here") {
    $answer = Read-Host "هل تريد فتح ملف .env الآن لإضافة المفتاح؟ (y/n)"
    if ($answer -eq "y") { Start-Process notepad ".env" }
}

# 5) تشغيل المنصة
Write-Host ""
Write-Host "🚀 تشغيل المنصة على:  http://localhost:8501" -ForegroundColor Green
Write-Host "   (للإيقاف اضغط Ctrl+C)" -ForegroundColor DarkGray
Write-Host ""

& .venv\Scripts\streamlit.exe run app.py --server.port 8501
