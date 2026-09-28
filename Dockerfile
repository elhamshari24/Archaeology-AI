# =============================================================================
# منصة الذكاء الاصطناعي في علم الآثار — هيئة الشارقة للآثار
# صورة Docker جاهزة لتشغيل المنصة على أي خادم (VPS / Azure / AWS / محلي)
#
#   بناء:   docker build -t archaeology-ai .
#   تشغيل:  docker run -d -p 8501:8501 -e GEMINI_API_KEY=xxxx --name archaeology-ai archaeology-ai
#   ثم افتح: http://<عنوان-الخادم>:8501
# =============================================================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# مكتبات النظام اللازمة لـ OpenCV وRasterio وPyMuPDF
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libexpat1 \
        libgomp1 \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# تثبيت الاعتماديات أولاً للاستفادة من طبقات البناء المخزّنة
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# نسخ ملفات المشروع (الصور، العروض، الدفاتر، الكود)
COPY . .

EXPOSE 8501

# فحص صحة الحاوية
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS http://localhost:8501/_stcore/health || exit 1

# تشغيل Streamlit على جميع الواجهات ليصبح متاحًا من خارج الحاوية
CMD ["streamlit", "run", "app.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
