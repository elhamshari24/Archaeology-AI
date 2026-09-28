# منصة الذكاء الاصطناعي في علم الآثار — هيئة الشارقة للآثار

تحويل دفاتر Colab الأربعة (ومشروع «التنبؤ بالماضي») إلى **تطبيق ويب بواجهة أمامية كاملة**
يعمل على جهازك المحلي أو على أي خادم.

التطبيق مبني بـ **Streamlit** (`app.py`) ويقدّم ستة تبويبات:

| التبويب | الدفتر المصدر |
| --- | --- |
| 🪙 المحور 1: فك النقوش والمسكوكات | `colab/1.ipynb` |
| 🏺 المحور 2: مقاطع الفخار والتوثيق الطبقي | `colab/2.ipynb` |
| 🛰️ المحور 3: الاستشعار الفضائي (Sentinel-2 مليحة) | `colab/3.ipynb` |
| 🧱 المحور 4: الرصد الإنشائي للشروخ (EAMENA) | `colab/4.ipynb` |
| 🔮 التنبؤ بالماضي (Ithaca & Aeneas) | `colab/Predicting the Past.ipynb` |
| 📽️ العرض التقديمي الكامل (PDF) | — |

---

## 1) التشغيل المحلي (Local)

### المتطلبات
- **Python 3.10+** (مُختبر على 3.13)
- **مفتاح Google Gemini API** — احصل عليه مجانًا من <https://aistudio.google.com/>

### الخطوات (Windows / PowerShell)

```powershell
cd "e:\DATA\AI\Workshops\Archaeology AI"

# 1. إنشاء بيئة افتراضية (مرة واحدة)
python -m venv .venv

# 2. تثبيت الاعتماديات (مرة واحدة — قد تستغرق عدة دقائق)
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. إعداد مفتاح الـ API
Copy-Item .env.example .env
notepad .env          # ضع المفتاح مكان your_gemini_api_key_here

# 4. تشغيل المنصة
.venv\Scripts\streamlit.exe run app.py
```

### الخطوات (macOS / Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && nano .env      # ضع المفتاح
streamlit run app.py
```

ثم افتح المتصفح على: **<http://localhost:8501>**

> 💡 بديل سريع: يمكنك تخطّي ملف `.env` ولصق المفتاح مباشرة في الشريط الجانبي داخل الواجهة.

---

## 2) النشر على خادم (Server)

### الخيار (أ) — Streamlit Community Cloud (مجاني، الأسرع)

1. ارفع المشروع إلى مستودع GitHub (عام أو خاص).
2. ادخل إلى <https://share.streamlit.io> → **Create app**.
3. اختر المستودع والفرع، وحدّد **Main file path = `app.py`**.
4. من **Advanced settings → Secrets** أضف:
   ```toml
   GEMINI_API_KEY = "ضع_مفتاحك_هنا"
   ```
5. اضغط **Deploy** — ستنشئ المنصة رابطًا عامًا تلقائيًا.

> ملف `packages.txt` في المشروع يخبر المنصة بمكتبات النظام المطلوبة (`libgl1`, `libgdal-dev` …).

### الخيار (ب) — Docker (لأي خادم VPS: DigitalOcean / Azure / AWS …)

```bash
# بناء الصورة
docker build -t archaeology-ai .

# تشغيل الحاوية مع تمرير مفتاح الـ API
docker run -d --name archaeology-ai \
  -p 8501:8501 \
  -e GEMINI_API_KEY="ضع_مفتاحك_هنا" \
  --restart unless-stopped \
  archaeology-ai
```

ثم افتح: `http://<عنوان-الخادم>:8501`

### الخيار (ج) — تشغيل يدوي على VPS مع إبقائه دائمًا

```bash
# على الخادم (Ubuntu مثالًا)
sudo apt update && sudo apt install -y python3-venv python3-pip libgl1 libglib2.0-0
cd /opt/archaeology-ai
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# ملف خدمة systemd  (/etc/systemd/system/archaeology.service)
# [Unit]
# Description=Archaeology AI Platform
# After=network.target
#
# [Service]
# WorkingDirectory=/opt/archaeology-ai
# Environment="GEMINI_API_KEY=ضع_مفتاحك_هنا"
# ExecStart=/opt/archaeology-ai/.venv/bin/streamlit run app.py --server.address=0.0.0.0 --server.port=8501 --server.headless=true
# Restart=always
#
# [Install]
# WantedBy=multi-user.target

sudo systemctl daemon-reload
sudo systemctl enable --now archaeology
```

> للنشر العام مع اسم نطاق وشهادة SSL، ضع **Nginx** كوسيط عكسي أمام المنفذ 8501.

---

## 3) بنية المشروع

```
├── app.py                     ← التطبيق الكامل (واجهة الويب)
├── requirements.txt           ← اعتماديات Python
├── packages.txt               ← مكتبات نظام Linux (لـ Streamlit Cloud)
├── Dockerfile / .dockerignore ← حزمة النشر بالحاويات
├── .streamlit/config.toml     ← الثيم والاتجاه (RTL) وإعدادات الخادم
├── .env.example               ← نموذج مفتاح الـ API
├── images/                    ← الصور والعينات التجريبية
├── colab/                     ← دفاتر Colab الأصلية (متاحة للتنزيل من الواجهة)
└── ورشة الذكاء الاصطناعي…pdf  ← العرض التقديمي الكامل
```

---

## 4) ملاحظات مهمة

- **لا ترفع ملف `.env` أو `.streamlit/secrets.toml`** إلى GitHub — فهي مُستثناة في `.gitignore`.
- الوحدات الجغرافية (المحور 3) تعمل **بدون أي مفتاح** لأنها تعتمد على Microsoft Planetary Computer المفتوح.
- بقية الوحدات (تحليل الصور والنقوش) تحتاج مفتاح Gemini.
- عند فتح المنصة أول مرة انتظر ثوانٍ حتى تكتمل تهيئة الاعتماديات الثقيلة (rasterio / OpenCV).
