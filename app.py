import os
import io
import json
import base64
import shutil
import time
import datetime
import numpy as np
import cv2
from PIL import Image
import matplotlib.pyplot as plt
import streamlit as st
from dotenv import load_dotenv

# Optional geographic & satellite libraries
try:
    import folium
    from streamlit_folium import st_folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False

try:
    import pystac_client
    import planetary_computer as pc
    import rasterio
    from rasterio.windows import from_bounds
    from rasterio.transform import xy
    from rasterio.warp import transform_bounds
    HAS_GEO = True
except ImportError:
    HAS_GEO = False

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    from pptx.enum.shapes import MSO_SHAPE
    HAS_PPTX = True
except ImportError:
    HAS_PPTX = False

try:
    import fitz  # PyMuPDF — renders PDF slides as images for the interactive viewer
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

# Load local environment variables if available
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="الذكاء الاصطناعي في توثيق المواقع والقطع الأثرية",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# Comprehensive RTL and Theme Styling (Sharjah Archaeology Heritage Palette)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap');
    
    /* 1. Universal RTL reset and Typography */
    *, html, body, [class*="css"], .stApp, [data-testid="stAppViewContainer"] {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    .stApp {
        background: radial-gradient(circle at 85% 15%, #1e293b 0%, #0f172a 100%) !important;
        color: #f8fafc !important;
    }

    /* 2. Headers and Titles */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Cairo', sans-serif !important;
        font-weight: 800 !important;
        color: #d4a373 !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    p, span, div, li, ul, ol, caption {
        direction: rtl !important;
        text-align: right !important;
    }

    /* 3. Sidebar RTL Styling */
    section[data-testid="stSidebar"], 
    [data-testid="stSidebarContent"], 
    [data-testid="stSidebarUserContent"] {
        direction: rtl !important;
        text-align: right !important;
        background-color: #0b1120 !important;
        border-left: 1px solid rgba(212, 163, 115, 0.25) !important;
    }

    /* 4. Labels and Inputs alignment */
    label, [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p, .stWidgetLabel {
        direction: rtl !important;
        text-align: right !important;
        justify-content: flex-start !important;
        font-weight: 600 !important;
        color: #e2e8f0 !important;
    }

    input, textarea, [data-baseweb="input"], [data-baseweb="textarea"] {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }

    /* 5. Dropdowns and Selectboxes */
    div[data-baseweb="select"], div[data-baseweb="select"] * {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }

    /* 6. Radio & Checkbox Buttons */
    div[data-testid="stRadio"] > div {
        direction: rtl !important;
        text-align: right !important;
        gap: 15px !important;
    }
    div[data-testid="stRadio"] label, div[data-testid="stCheckbox"] label {
        direction: rtl !important;
        text-align: right !important;
    }

    /* 7. Horizontal Columns */
    div[data-testid="stHorizontalBlock"] {
        direction: rtl !important;
    }

    /* 8. Sliders & Date Inputs */
    div[data-testid="stSlider"], div[data-testid="stDateInput"] {
        direction: rtl !important;
        text-align: right !important;
    }

    /* 9. Metrics Cards */
    .metric-card {
        background: #1e293b;
        border: 1px solid rgba(212, 163, 115, 0.3);
        border-radius: 12px;
        padding: 16px;
        text-align: center !important;
        margin-bottom: 15px;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 900;
        color: #d4a373;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #94a3b8;
    }

    /* 10. Header Container */
    .main-header {
        background: linear-gradient(135deg, rgba(212, 163, 115, 0.15) 0%, rgba(30, 41, 59, 0.95) 100%);
        border: 1px solid rgba(212, 163, 115, 0.35);
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        direction: rtl !important;
        text-align: right !important;
    }

    .stat-badge {
        display: inline-block;
        background: rgba(212, 163, 115, 0.15);
        border: 1px solid #d4a373;
        color: #d4a373;
        padding: 4px 14px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 700;
        margin-bottom: 8px;
    }

    /* 11. Reports Display Box */
    .report-box {
        background-color: #0b1120;
        border: 1px solid rgba(212, 163, 115, 0.3);
        border-radius: 10px;
        padding: 20px;
        direction: rtl !important;
        text-align: right !important;
        line-height: 1.8;
    }

    /* 12. Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        direction: rtl !important;
        gap: 8px;
        border-bottom: 2px solid rgba(212, 163, 115, 0.25);
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Cairo', sans-serif !important;
        font-weight: 700 !important;
        padding: 12px 18px;
        border-radius: 8px 8px 0 0;
        color: #94a3b8;
        direction: rtl !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(212, 163, 115, 0.18) !important;
        color: #d4a373 !important;
        border-bottom: 3px solid #d4a373 !important;
    }

    /* 13. Buttons & Download Buttons */
    .stButton > button, .stDownloadButton > button {
        font-family: 'Cairo', sans-serif !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, #d4a373 0%, #b23a22 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 9px 24px !important;
        transition: all 0.3s ease;
        direction: rtl !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(212, 163, 115, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# API Key and Model Helpers
# -----------------------------------------------------------------------------
def safe_secret(name):
    """Read a Streamlit secret without raising when no secrets.toml exists."""
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return None

def get_api_key():
    """Retrieve Gemini API key from user input, Streamlit Secrets, or environment."""
    key = st.session_state.get("gemini_key", "").strip()
    if not key:
        key = (safe_secret("GEMINI_API_KEY") or "").strip()
    if not key:
        key = os.getenv("GEMINI_API_KEY", "").strip()
    return key

def get_genai_client(api_key):
    """Instantiate Google GenAI Client."""
    if not HAS_GENAI:
        st.error("مكتبة `google-genai` غير مثبتة. يرجى تثبيتها عبر requirements.txt")
        return None
    if not api_key:
        st.warning("⚠️ يرجى إدخال مفتاح Google Gemini API في القائمة الجانبية لتفعيل التحليل بالذكاء الاصطناعي.")
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"خطأ في تهيئة عميل الذكاء الاصطناعي: {e}")
        return None

# -----------------------------------------------------------------------------
# Resilient text generation (retry on 503 + automatic model fallback)
# -----------------------------------------------------------------------------
# Fallback order used when the selected model is unavailable or overloaded.
FALLBACK_MODEL_CHAIN = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-1.5-flash",
]

# Substrings marking a *transient* server-side failure worth retrying.
TRANSIENT_ERROR_MARKERS = (
    "503", "429", "500", "502", "504",
    "UNAVAILABLE", "RESOURCE_EXHAUSTED", "INTERNAL",
    "OVERLOADED", "HIGH DEMAND", "TRY AGAIN LATER",
)


def is_transient_error(exc):
    """True when the failure is temporary (safe to retry or fail over from)."""
    message = str(exc).upper()
    return any(marker in message for marker in TRANSIENT_ERROR_MARKERS)


def show_ai_error(exc):
    """Render a clear, actionable Arabic error message."""
    if is_transient_error(exc):
        st.error(
            "⚠️ خوادم الذكاء الاصطناعي مزدحمة حالياً (خطأ مؤقت 503). "
            "أُعيدت المحاولة وتِم التبديل بين النماذج تلقائياً دون جدوى — "
            "يرجى إعادة المحاولة بعد لحظات، أو اختيار نموذج آخر من القائمة الجانبية."
        )
    else:
        st.error(f"حدث خطأ أثناء معالجة الطلب: {exc}")


def generate_ai_content(client, contents, model=None, max_attempts=3):
    """Call Gemini with retry-on-transient-error and automatic model fallback.

    1. Retries the selected model up to ``max_attempts`` times (backoff).
    2. Then falls back through FALLBACK_MODEL_CHAIN, one attempt per model.

    Returns ``(response, model_used)``; re-raises the last error if all fail.
    Non-transient errors (e.g. invalid API key) are raised immediately.
    """
    primary = (model or "").strip() or FALLBACK_MODEL_CHAIN[0]
    chain = [primary] + [m for m in FALLBACK_MODEL_CHAIN if m != primary]

    last_error = None
    for position, model_name in enumerate(chain):
        attempts = max_attempts if position == 0 else 1
        for attempt in range(attempts):
            try:
                response = client.models.generate_content(model=model_name, contents=contents)
                if position > 0:
                    st.info(f"⚡ النموذج `{primary}` غير متاح حالياً — تم تحويل الطلب تلقائياً إلى `{model_name}`.")
                return response, model_name
            except Exception as exc:
                last_error = exc
                if not is_transient_error(exc):
                    raise
                if attempt < attempts - 1:
                    time.sleep(1.5 * (attempt + 1))  # 1.5s, then 3s
    raise last_error


def ensure_presentation_static_copy(pdf_path):
    """Copy the presentation PDF into ./static so Streamlit serves it for full-screen viewing."""
    try:
        os.makedirs("static", exist_ok=True)
        target_path = os.path.join("static", "presentation_workshop.pdf")
        if pdf_path and os.path.exists(pdf_path):
            if (not os.path.exists(target_path)) or (os.path.getsize(target_path) != os.path.getsize(pdf_path)):
                shutil.copyfile(pdf_path, target_path)
            return target_path
    except Exception:
        return None
    return None


@st.cache_data(show_spinner=False, max_entries=24)
def render_pdf_slide_png(pdf_file_path, pdf_mtime, page_index, zoom):
    """Render a single PDF slide into PNG bytes using PyMuPDF (cached per slide and zoom level)."""
    if not HAS_FITZ:
        raise RuntimeError("PyMuPDF (fitz) is not available.")
    with fitz.open(pdf_file_path) as pdf_doc:
        page = pdf_doc.load_page(page_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        return pix.tobytes("png")


def find_presentation_pdf():
    """Locate the presentation PDF file in the repository root."""
    exact_name = "ورشة الذكاء الاصطناعي في توثيق المواقع والقطع الأثرية.pdf"
    if os.path.exists(exact_name):
        return exact_name
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, exact_name)
    if os.path.exists(script_path):
        return script_path
    for f in os.listdir("."):
        if f.endswith(".pdf") and "ورشة" in f:
            return f
    for f in os.listdir("."):
        if f.endswith(".pdf"):
            return f
    return None

# -----------------------------------------------------------------------------
# Sidebar Configuration
# -----------------------------------------------------------------------------
with st.sidebar:
    if os.path.exists("images/Gemini.png"):
        st.image("images/Gemini.png", width=180)
    else:
        try:
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Sharjah_Archaeology_Authority_Logo.png/320px-Sharjah_Archaeology_Authority_Logo.png", width=180)
        except Exception:
            pass
    
    st.markdown("### ⚙️ إعدادات المنصة")
    
    # Pre-fill from secrets or env if present
    default_key = safe_secret("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or ""

    user_api_key = st.text_input(
        "🔑 مفتاح Google Gemini API:",
        type="password",
        value=default_key,
        help="يمكنك الحصول على المفتاح مجاناً من Google AI Studio (aistudio.google.com)",
        key="gemini_key"
    )

    # Model list: reliable IDs first, then the newest flash variants.
    # An unavailable or overloaded model falls back automatically (see generate_ai_content).
    model_options = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-3.5-flash",
        "gemini-3.7-flash",
        "gemini-3.8-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "نموذج مخصص (Custom Model)...",
    ]
    chosen_model = st.selectbox("🤖 النموذج المعتمد:", model_options, index=0)
    if chosen_model == "نموذج مخصص (Custom Model)...":
        selected_model = st.text_input("أدخل اسم النموذج المطلوب:", value="gemini-2.5-flash")
    else:
        selected_model = chosen_model

    st.caption(f"النموذج النشط حالياً: `{selected_model}`")
    st.caption("🔄 عند ازدحام النموذج (503) يُعاد المحاولة تلقائياً ثم يُحوَّل الطلب إلى نموذج بديل.")
    
    st.markdown("---")
    st.markdown("""
    **محاور الورشة والتطبيقات المستقلة:**
    - 🪙 **المحور 1:** الفهرسة اللحظية وفك النقوش والمسكوكات (`1.ipynb`).
    - 🏺 **المحور 2:** استخراج مقاطع الفخار والتوثيق الطبقي (`2.ipynb`).
    - 🛰️ **المحور 3:** الاستشعار الفضائي لقطاع مليحة (`3.ipynb`).
    - 🧱 **المحور 4:** الرصد الإنشائي للشروخ وتقارير الصيانة (`4.ipynb`).
    - 🔮 **التنبؤ بالماضي (Predicting the Past):** النمذجة التنبؤية بالذكاء الجغرافي ومولد العروض (`Predicting the Past.ipynb`).
    - 📽️ **العرض التقديمي الكامل:** استعراض وتنزيل شرائح الورشة (PDF).
    """)
    st.markdown("---")
    st.caption("هيئة الشارقة للآثار — ورشة الذكاء الاصطناعي في توثيق المواقع والقطع الأثرية")

# -----------------------------------------------------------------------------
# Main Header
# -----------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <span class="stat-badge">ورشة عمل متقدمة — هيئة الشارقة للآثار</span>
    <h1 style="margin: 0; font-size: 2.2rem;">🏛️ منصة الذكاء الاصطناعي في علم الآثار</h1>
    <p style="margin-top: 8px; color: #94a3b8; font-size: 1.05rem;">
        بيئة رقمية موحدة للتوثيق الذكي، والرؤية الحاسوبية، والاستشعار الفضائي عن بعد، والنماذج متعددة الوسائط (Multimodal AI).
    </p>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Navigation Tabs (Separate Tab for Each Module & Predicting the Past)
# -----------------------------------------------------------------------------
tab_coin, tab_pottery, tab_satellite, tab_structural, tab_predicting, tab_presentation = st.tabs([
    "🪙 المحور 1: فك النقوش والمسكوكات",
    "🏺 المحور 2: مقاطع الفخار والتوثيق الطبقي",
    "🛰️ المحور 3: الاستشعار الفضائي (Sentinel-2 مليحة)",
    "🧱 المحور 4: الرصد الإنشائي للشروخ (EAMENA)",
    "🔮 التنبؤ بالماضي (Predicting the Past)",
    "📽️ العرض التقديمي الكامل (PDF) ودليل الورشة"
])

current_api_key = get_api_key()

# =============================================================================
# TAB 1: المسكوكات والنقوش (1.ipynb)
# =============================================================================
with tab_coin:
    st.header("🪙 الفهرسة اللحظية وفك النقوش والمسكوكات الأثرية")
    st.write("تحليل القطع والمسكوكات الأثرية عبر النماذج البصرية واستخراج بيانات Dublin Core القياسية وقراءة الخطوط والرموز وتوصيات الحفظ.")

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("📤 اختيار أو رفع صورة اللقية الأثرية")
        
        coin_sample_options = {
            "رفع صورة مخصصة من جهازي": None,
            "شاهد قبر": "images/masnad.png",
            "درهم سلطان": "images/Picture1.jpg",
            "درهم اسلامي": "images/hfgd8.jpg",
            "كسرة طبق": "images/dfdff.png",
            "حصن الذيد": "images/al-dhaid-fort-2.webp",
            "حصن دبا": "images/7195313.jpeg",
            "عملة الاسكندر": "images/47-91.png",
            "خاتم ذهبي": "images/11.png",
            "كسرة فخارية": "images/8.png"
        }
        chosen_coin_sample = st.selectbox("اختر عينة تجريبية أو ارفع ملفك:", list(coin_sample_options.keys()), key="coin_sample_sel")
        
        coin_image_to_process = None
        if coin_sample_options[chosen_coin_sample] and os.path.exists(coin_sample_options[chosen_coin_sample]):
            coin_image_to_process = Image.open(coin_sample_options[chosen_coin_sample]).convert("RGB")
            st.image(coin_image_to_process, caption=f"عينة: {chosen_coin_sample}", use_container_width=True)
        else:
            uploaded_coin = st.file_uploader(
                "اختر صورة المسكوكة أو اللقية (JPG, PNG):",
                type=["jpg", "jpeg", "png"],
                key="coin_file"
            )
            if uploaded_coin is not None:
                coin_image_to_process = Image.open(uploaded_coin).convert("RGB")
                st.image(coin_image_to_process, caption="الصورة المرفوعة", use_container_width=True)

        custom_coin_prompt = st.text_area(
            "تخصيص برومبت التحليل الأثري:",
            value="""بصفتك خبيراً في علم المسكوكات والآثار بهيئة الشارقة للآثار:
حلل صورة القطعة الأثرية المرفقة تحليلاً أكاديمياً متخصصاً وأعد تقريراً بصيغة Markdown يشمل:
1. جدول البيانات الوصفية القياسي (Dublin Core Metadata):
   - العنوان والتعريف، المادة الخام، العصر التاريخي التقديري، دار السك أو مكان الإنتاج المحتمل.
2. التحليل الباليوغرافي والرموز:
   - نوع الخط أو الزخرفة (مثل: كوفي مبكر، مسند، أو نقوش نباتية/هندسية).
   - قراءة العبارات الظاهرة في الطوق والمركز إن وجدت.
3. التقييم المورفولوجي وحالة الحفظ:
   - مظاهر التآكل، آثار الصدمات، ومطابقة قوالب السك وتوصيات الحفظ.""",
            height=180
        )

        analyze_coin_btn = st.button("🚀 بدء التحليل وفك النقوش", key="btn_run_coin")

    with col2:
        st.subheader("📋 التقرير الأثري الآلي المعتمد")
        if analyze_coin_btn:
            if coin_image_to_process is None:
                st.warning("يرجى رفع صورة مسكوكة أولاً أو تفعيل العينة النموذجية.")
            else:
                client = get_genai_client(current_api_key)
                if client:
                    with st.spinner("جاري استقراء النقوش وتحليل الخصائص المورفولوجية..."):
                        try:
                            response, _model_used = generate_ai_content(
                                client,
                                [coin_image_to_process, custom_coin_prompt],
                                selected_model,
                            )
                            st.session_state["coin_report_output"] = response.text
                        except Exception as e:
                            show_ai_error(e)

        if "coin_report_output" in st.session_state:
            st.markdown(f'<div class="report-box">{st.session_state["coin_report_output"]}</div>', unsafe_allow_html=True)
            st.download_button(
                label="📥 تحميل التقرير (Markdown)",
                data=st.session_state["coin_report_output"],
                file_name="Archaeological_Coin_Report.md",
                mime="text/markdown",
                key="btn_dl_coin_report"
            )
        else:
            st.info("قم برفع صورة واضغط على 'بدء التحليل' لظهور التقرير الأثري هنا.")

# =============================================================================
# TAB 2: مقاطع الفخار والتوثيق الطبقي (2.ipynb)
# =============================================================================
with tab_pottery:
    st.header("🏺 استخراج مقاطع الفخار وأتمتة استمارات الحفر الطبقي")
    st.write("دمج خوارزميات الرؤية الحاسوبية (Computer Vision) لاستخراج الحافة (Rim Profile) وتقدير القطر الهندسي، ثم توليد استمارة سياق طبقي رقمية (JSON) متوافقة مع مصفوفة هاريس.")

    col_p1, col_p2 = st.columns([1, 1], gap="large")

    with col_p1:
        st.subheader("📤 اختيار أو رفع صورة الكسرة الفخارية")
        
        pottery_sample_options = {
            "رفع صورة مخصصة من جهازي": None,
            "شاهد قبر": "images/masnad.png",
            "درهم سلطان": "images/Picture1.jpg",
            "درهم اسلامي": "images/hfgd8.jpg",
            "كسرة طبق": "images/dfdff.png",
            "حصن الذيد": "images/al-dhaid-fort-2.webp",
            "حصن دبا": "images/7195313.jpeg",
            "عملة الاسكندر": "images/47-91.png",
            "خاتم ذهبي": "images/11.png",
            "كسرة فخارية": "images/8.png"
        }
        chosen_pottery_sample = st.selectbox("اختر عينة تجريبية أو ارفع ملفك:", list(pottery_sample_options.keys()), key="pot_sample_sel")
        
        pottery_img = None
        if pottery_sample_options[chosen_pottery_sample] and os.path.exists(pottery_sample_options[chosen_pottery_sample]):
            pottery_img = Image.open(pottery_sample_options[chosen_pottery_sample]).convert("RGB")
            st.image(pottery_img, caption=f"عينة: {chosen_pottery_sample}", use_container_width=True)
        else:
            up_pottery = st.file_uploader("ارفع صورة الكسرة الفخارية (Rim / Sherd):", type=["jpg", "jpeg", "png"], key="pot_file")
            if up_pottery:
                pottery_img = Image.open(up_pottery).convert("RGB")
                st.image(pottery_img, caption="الصورة المرفوعة", use_container_width=True)
        
        canny_low = st.slider("عتبة Canny السفلى (Edge Low):", 10, 100, 40)
        canny_high = st.slider("عتبة Canny العليا (Edge High):", 80, 250, 130)

        estimated_diameter_cm = "غير محدد"
        rim_vis_img = None

        if pottery_img is not None:
            img_np = np.array(pottery_img)
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, canny_low, canny_high)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                (cx, cy), radius = cv2.minEnclosingCircle(largest_contour)
                estimated_diameter_cm = round((radius * 2) * 0.04, 1)

                rim_vis = img_np.copy()
                cv2.drawContours(rim_vis, [largest_contour], -1, (0, 255, 0), 3)
                cv2.circle(rim_vis, (int(cx), int(cy)), int(radius), (255, 0, 0), 2)
                rim_vis_img = rim_vis

                col_sub1, col_sub2 = st.columns(2)
                with col_sub1:
                    st.image(img_np, caption="الكسرة الأصلية", use_container_width=True)
                with col_sub2:
                    st.image(rim_vis, caption=f"الحافة المستخرجة (القطر التقديري: {estimated_diameter_cm} سم)", use_container_width=True)
            else:
                st.image(img_np, caption="الكسرة الأصلية (لم يتم رصد حواف كافية)", use_container_width=True)

        gen_json_btn = st.button("📝 توليد استمارة الحفر الميدانية (Context Sheet JSON)", key="btn_pot_json")

    with col_p2:
        st.subheader("📋 استمارة السياق الطبقي الرقمية (Harris Matrix Record)")
        if gen_json_btn:
            if pottery_img is None:
                st.warning("يرجى تزويد صورة للكسرة الفخارية أولاً.")
            else:
                client = get_genai_client(current_api_key)
                if client:
                    with st.spinner("جاري توصيف الطينة وتحليل الحقبة الطبقية وتوليد الـ JSON..."):
                        prompt_pot = f"""
بناءً على صورة كسرة الفخار المرفقة المكتشفة في حفريات إمارة الشارقة:
- القطر التقديري المقاس بالرؤية الحاسوبية: {estimated_diameter_cm} سم.
قم بإنشاء استمارة حفر أثري طبقي رسمية (Archaeological Stratigraphic Context Unit Record) متوافقة مع مصفوفة هاريس، وأخرج الإجابة كـ JSON صالح ومفصل فقط دون نصوص إضافية:
{{
  "Site_Code": "SHJ-ARC-2026",
  "Context_Number": "Locus-104",
  "Fabric_Description": "وصف طينة الفخار ولونها وفق مقياس مانسل",
  "Inclusions": "نوع الشوائب (رمل، كلس، صدف)",
  "Estimated_Form": "شكل الإناء المقدر (جرة، صحن، قنينة)",
  "Typological_Dating": "الحقبة الزمنية التقديرية في الشارقة",
  "Stratigraphic_Relations": "العلاقة مع الطبقات الأعلى والأدنى",
  "Field_Curator_Recommendation": "توصيات الترميم والمعالجة الحقلية"
}}
"""
                        try:
                            res_ai, _model_used = generate_ai_content(
                                client,
                                [pottery_img, prompt_pot],
                                selected_model,
                            )
                            raw_text = res_ai.text.strip()
                            if raw_text.startswith("```json"):
                                raw_text = raw_text[7:]
                            if raw_text.endswith("```"):
                                raw_text = raw_text[:-3]
                            st.session_state["pottery_json_output"] = raw_text.strip()
                        except Exception as e:
                            show_ai_error(e)

        if "pottery_json_output" in st.session_state:
            try:
                parsed_json = json.loads(st.session_state["pottery_json_output"])
                st.json(parsed_json)
                st.download_button(
                    label="📥 تحميل الاستمارة (JSON)",
                    data=json.dumps(parsed_json, ensure_ascii=False, indent=2),
                    file_name="Stratigraphic_Context_Unit_Record.json",
                    mime="application/json",
                    key="btn_dl_pottery_json"
                )
            except Exception:
                st.code(st.session_state["pottery_json_output"], language="json")
                st.download_button(
                    label="📥 تحميل الاستمارة (JSON)",
                    data=st.session_state["pottery_json_output"],
                    file_name="Stratigraphic_Context_Unit_Record.json",
                    mime="application/json",
                    key="btn_dl_pottery_raw"
                )
        else:
            st.info("قم برفع صورة كسرة فخار واضغط على زر التوليد لإنتاج الاستمارة الميدانية.")

# =============================================================================
# TAB 3: الاستشعار الفضائي لقطاع مليحة (3.ipynb)
# =============================================================================
with tab_satellite:
    st.header("🛰️ المحور الثالث: الاستشعار الفضائي عن بعد لقطاع مليحة الأثري (Sentinel-2 L2A)")
    st.write("استدعاء وتحليل المشاهد الفضائية الحقيقية لقمر Sentinel-2 عبر بوابة Microsoft Planetary Computer STAC لموقع مليحة الأثري بالشارقة، ومعالجة مؤشر التباين الهيكلي للرطوبة والأساسات (ANDI)، واستخراج إحداثيات الشذوذ الجغرافية مع إسقاطها على خريطة تفاعلية فضائية وتوليد التقرير الاستكشافي بالذكاء الاصطناعي.")

    if not HAS_GEO:
        st.error("مكتبات الاستشعار عن بعد (rasterio, pystac_client, planetary_computer) غير مثبتة بالكامل في البيئة الحالية.")
    else:
        col_sat_in1, col_sat_in2 = st.columns([1, 1], gap="large")

        with col_sat_in1:
            st.markdown("**إحداثيات النطاق الجغرافي (Bounding Box):**")
            col_bb1, col_bb2 = st.columns(2)
            with col_bb1:
                s_west = st.number_input("غرب (West Lon):", value=55.870, format="%.4f")
                s_south = st.number_input("جنوب (South Lat):", value=25.105, format="%.4f")
            with col_bb2:
                s_east = st.number_input("شرق (East Lon):", value=55.910, format="%.4f")
                s_north = st.number_input("شمال (North Lat):", value=25.145, format="%.4f")

            # Added Date Range Selection for Axis 3
            st.markdown("📅 **النطاق الزمني للبحث الفضائي (Date Range):**")
            col_dt1, col_dt2 = st.columns(2)
            with col_dt1:
                sat_start_date = st.date_input("من تاريخ (Start):", value=datetime.date(2023, 1, 1), key="sat_start_dt")
            with col_dt2:
                sat_end_date = st.date_input("إلى تاريخ (End):", value=datetime.date(2026, 6, 1), key="sat_end_dt")

            if sat_start_date > sat_end_date:
                st.error("⚠️ تاريخ البداية يجب أن يكون قبل أو يساوي تاريخ النهاية.")
            
            max_cloud = st.slider("الحد الأقصى لنسبة الغيوم (%):", 0, 20, 5)
            
            run_real_satellite_btn = st.button("📡 جلب المشهد الفضائي وتحليله", key="btn_run_sat_real")

        with col_sat_in2:
            if run_real_satellite_btn and sat_start_date <= sat_end_date:
                    date_query_str = f"{sat_start_date.strftime('%Y-%m-%d')}/{sat_end_date.strftime('%Y-%m-%d')}"
                    with st.spinner(f"الاتصال بـ Planetary Computer والبحث في الفترة ({date_query_str})..."):
                        try:
                            bbox_coords = [s_west, s_south, s_east, s_north]
                            catalog = pystac_client.Client.open(
                                "https://planetarycomputer.microsoft.com/api/stac/v1",
                                modifier=pc.sign_inplace
                            )
                            search = catalog.search(
                                collections=["sentinel-2-l2a"],
                                bbox=bbox_coords,
                                datetime=date_query_str,
                                query={"eo:cloud_cover": {"lt": max_cloud}},
                                sortby=[{"field": "properties.eo:cloud_cover", "direction": "asc"}],
                                max_items=1
                            )
                            items = list(search.items())
                            if not items:
                                st.warning("لم يتم العثور على مشاهد تطابق نسبة الغيوم المحددة.")
                            else:
                                scene = items[0]
                                st.success(f"تم جلب المشهد: `{scene.id}` | السحب: {scene.properties['eo:cloud_cover']:.2f}%")
                                
                                b04_url = scene.assets["B04"].href
                                b08_url = scene.assets["B08"].href
                                b03_url = scene.assets["B03"].href
                                b02_url = scene.assets["B02"].href

                                with rasterio.open(b04_url) as src_r:
                                    proj_bbox = transform_bounds("EPSG:4326", src_r.crs, *bbox_coords)
                                    window = from_bounds(proj_bbox[0], proj_bbox[1], proj_bbox[2], proj_bbox[3], src_r.transform)
                                    red_d = src_r.read(1, window=window).astype(float)
                                    affine_trans = src_r.window_transform(window)
                                    native_crs = src_r.crs

                                with rasterio.open(b08_url) as src_nir:
                                    nir_d = src_nir.read(1, window=window).astype(float)

                                denom = nir_d + red_d
                                denom[denom == 0] = 1e-5
                                andi_idx = (nir_d - red_d) / denom
                                andi_sc = np.nan_to_num(andi_idx, nan=0.0)
                                andi_norm_real = cv2.normalize(andi_sc, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

                                blurred_r = cv2.GaussianBlur(andi_norm_real, (5, 5), 0)
                                threshold_val_r = np.percentile(blurred_r, 97)
                                _, thresh_r = cv2.threshold(blurred_r, threshold_val_r, 255, cv2.THRESH_BINARY)
                                contours_r, _ = cv2.findContours(thresh_r, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                                real_anomalies_list = []
                                pixel_res = 100 # 10x10m

                                for cnt in contours_r:
                                    area_px = cv2.contourArea(cnt)
                                    if 3 < area_px < 300:
                                        M = cv2.moments(cnt)
                                        if M["m00"] != 0:
                                            cx = int(M["m10"] / M["m00"])
                                            cy = int(M["m01"] / M["m00"])
                                            px, py = xy(affine_trans, cy, cx)
                                            with rasterio.open(b04_url) as src_r:
                                                lon_lat = rasterio.warp.transform(src_r.crs, "EPSG:4326", [px], [py])
                                                r_lon, r_lat = lon_lat[0][0], lon_lat[1][0]
                                            
                                            real_anomalies_list.append({
                                                "id": len(real_anomalies_list) + 1,
                                                "lat": r_lat,
                                                "lon": r_lon,
                                                "area_m2": int(area_px * pixel_res),
                                                "intensity": float(andi_idx[cy, cx])
                                            })

                                st.session_state["real_anomalies_data"] = real_anomalies_list
                                st.session_state["sat_scene_date"] = scene.datetime.strftime("%Y-%m-%d")
                                st.write(f"🔍 تم اكتشاف **{len(real_anomalies_list)}** نقطة شذوذ أثري حقيقية.")
                        except Exception as e:
                            st.error(f"خطأ أثناء استعلام STAC: {e}")

        if "real_anomalies_data" in st.session_state and HAS_FOLIUM:
            st.subheader("🗺️ خريطة الاستكشاف الفضائي التفاعلية لموقع مليحة")
            anoms = st.session_state["real_anomalies_data"]
            center_lat = (s_south + s_north) / 2
            center_lon = (s_west + s_east) / 2

            m_map = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=14,
                tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attr="Esri Satellite"
            )

            folium.Rectangle(
                bounds=[[s_south, s_west], [s_north, s_east]],
                color="#d4a373",
                weight=2,
                fill=False,
                popup="نطاق المسح الأثري المعتمد"
            ).add_to(m_map)

            for a in anoms:
                popup_html = f"""
                <div style="font-family: Cairo; direction: rtl; text-align: right; width: 160px;">
                    <b>شذوذ أثري #{a['id']}</b><br>
                    خط العرض: {a['lat']:.5f}<br>
                    خط الطول: {a['lon']:.5f}<br>
                    المساحة: {a['area_m2']} م²<br>
                    قوة الإشارة: {a['intensity']:.2f}
                </div>
                """
                folium.CircleMarker(
                    location=[a['lat'], a['lon']],
                    radius=6,
                    color="#00FF00",
                    fill=True,
                    fill_color="#00FF00",
                    fill_opacity=0.8,
                    popup=folium.Popup(popup_html, max_width=200)
                ).add_to(m_map)

            st_folium(m_map, width=950, height=450)

            # AI Exploration Report
            if st.button("🧠 إعداد تقرير الاستكشاف التنبؤي بواسطة الذكاء الاصطناعي", key="btn_sat_ai_rep"):
                client = get_genai_client(current_api_key)
                if client:
                    with st.spinner(f"جاري صياغة التقرير الجيوفيزيائي والأثري عبر {selected_model}..."):
                        summary_anom = "\n".join([
                            f"- موقع #{a['id']}: إحداثيات ({a['lat']:.5f} N, {a['lon']:.5f} E) | المساحة التقديرية: {a['area_m2']} م² | قوة الشذوذ: {a['intensity']:.3f}"
                            for a in anoms[:5]
                        ])
                        prompt_sat_ai = f"""
بصفتك مستشار الاستشعار عن بعد والآثار الفضائية بهيئة الشارقة للآثار:
إليك مخرجات التحليل الطيفي الفضائي الحقيقي لبيانات قمر Sentinel-2 فوق موقع مليحة الأثري:
قائمة بأبرز نقاط الشذوذ الطيفي الحقيقية:
{summary_anom}

المطلوب: إعداد "تقرير استكشاف أثري تنبؤي" بصيغة Markdown يتضمن:
1. التفسير الجيوفيزيائي والأثري للشذوذ الطيفي المرصود في بيئة مليحة الصحراوية.
2. تقييم الإحداثيات المرصودة وترتيب أولويات التحقق الميداني لفرق التنقيب بالهيئة.
3. التوصيات الإجرائية المباشرة (مثل استخدام الرادار الأرضي GPR أو طائرات الدرون الحرارية عند هذه الإحداثيات قبل بدء الحفر).
"""
                        try:
                            res_sat, _model_used = generate_ai_content(
                                client, prompt_sat_ai, selected_model
                            )
                            st.session_state["sat_report_output"] = res_sat.text
                        except Exception as e:
                            show_ai_error(e)

            if "sat_report_output" in st.session_state:
                st.markdown(f'<div class="report-box">{st.session_state["sat_report_output"]}</div>', unsafe_allow_html=True)

# =============================================================================
# TAB 4: الرصد الإنشائي للشروخ (4.ipynb)
# =============================================================================
with tab_structural:
    st.header("🧱 الرصد الإنشائي للشروخ وتقارير الصيانة الوقائية (EAMENA)")
    st.write("استخلاص التصدعات والشقوق الإنشائية في الجدران والمباني التاريخية عبر مرشحات Blackhat المورفولوجية، وحساب نسبة الضرر السطحي وإعداد تقرير إدارة المخاطر الدولية.")

    col_w1, col_w2 = st.columns([1, 1], gap="large")

    with col_w1:
        st.subheader("📤 صورة الجدار أو المنشأة التاريخية")
        
        struct_sample_options = {
            "رفع صورة مخصصة من جهازي": None,
            "شاهد قبر": "images/masnad.png",
            "درهم سلطان": "images/Picture1.jpg",
            "درهم اسلامي": "images/hfgd8.jpg",
            "كسرة طبق": "images/dfdff.png",
            "حصن الذيد": "images/al-dhaid-fort-2.webp",
            "حصن دبا": "images/7195313.jpeg",
            "عملة الاسكندر": "images/47-91.png",
            "خاتم ذهبي": "images/11.png",
            "كسرة فخارية": "images/8.png"
        }
        chosen_struct_sample = st.selectbox("اختر عينة تجريبية أو ارفع ملفك:", list(struct_sample_options.keys()), key="struct_sample_sel")

        wall_img_process = None
        if struct_sample_options[chosen_struct_sample] and os.path.exists(struct_sample_options[chosen_struct_sample]):
            wall_img_process = Image.open(struct_sample_options[chosen_struct_sample]).convert("RGB")
        else:
            up_wall = st.file_uploader("ارفع صورة الجدار الأثري المصاب بالشروخ:", type=["jpg", "jpeg", "png"], key="wall_file")
            if up_wall:
                wall_img_process = Image.open(up_wall).convert("RGB")

        # Morphology kernel slider
        kernel_sz = st.slider("حجم مرشح استخلاص الشقوق (Kernel Size):", min_value=7, max_value=31, value=17, step=2)
        thresh_crack_val = st.slider("عتبة حساسية الشق (Crack Threshold):", min_value=10, max_value=80, value=30, step=5)

        damage_pct = 0.0
        crack_overlay_img = None

        if wall_img_process is not None:
            w_np = np.array(wall_img_process)
            gray_w = cv2.cvtColor(w_np, cv2.COLOR_RGB2GRAY)
            kernel_w = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_sz, kernel_sz))
            blackhat_w = cv2.morphologyEx(gray_w, cv2.MORPH_BLACKHAT, kernel_w)
            _, crack_m = cv2.threshold(blackhat_w, thresh_crack_val, 255, cv2.THRESH_BINARY)

            total_px = crack_m.size
            damaged_px = cv2.countNonZero(crack_m)
            damage_pct = round((damaged_px / total_px) * 100, 2)

            crack_ov = w_np.copy()
            crack_ov[crack_m == 255] = [255, 0, 0]
            crack_overlay_img = crack_ov

            col_img1, col_img2 = st.columns(2)
            with col_img1:
                st.image(w_np, caption="الصورة الأصلية", use_container_width=True)
            with col_img2:
                st.image(crack_ov, caption=f"خريطة الشروخ (نسبة التضرر: {damage_pct}%)", use_container_width=True)

            # Metric card
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{damage_pct}%</div>
                <div class="metric-label">نسبة التضرر السطحي المقاسة بالرؤية الحاسوبية</div>
            </div>
            """, unsafe_allow_html=True)

        analyze_wall_btn = st.button("🚨 توليد تقرير الصيانة الوقائية (EAMENA)", key="btn_run_wall")

    with col_w2:
        st.subheader("📄 تقرير تقييم الحالة والمخاطر الإنشائية")
        if analyze_wall_btn:
            if wall_img_process is None:
                st.warning("يرجى رفع صورة جدار أو منشأة أثرية أولاً.")
            else:
                client = get_genai_client(current_api_key)
                if client:
                    with st.spinner("جاري صياغة تقرير الحالة الإنشائية وتصنيف المخاطر..."):
                        prompt_wall = f"""
بصفتك مهندس ترميم وصيانة المواقع الأثرية بهيئة الشارقة للآثار:
حلل صورة الجدار المرفقة وخريطة الشروخ المستخرجة آلياً بنسبة تضرر سطحي {damage_pct}%:
أعد تقرير تقييم حالة ومخاطر إنشائية (Structural Condition Assessment) بصيغة Markdown يتضمن:
1. التشخيص المورفولوجي:
   - تحديد نوع الشروخ (شروخ إجهاد إنشائي، شروخ حرارية، أو تفتت ناجم عن الرطوبة والأملاح).
2. تصنيف درجة الخطورة والاستجابة:
   - [أخضر: مستقر] أو [أصفر: مراقبة فنية مستمرة] أو [أحمر: تدخل هندسي عاجل].
3. خطة التدخل الوقائي الموصى بها لفريق الترميم بالهيئة لحماية المنشأة من تفاقم الأضرار.
"""
                        try:
                            overlay_pil = Image.fromarray(crack_overlay_img)
                            res_wall, _model_used = generate_ai_content(
                                client,
                                [overlay_pil, prompt_wall],
                                selected_model,
                            )
                            st.session_state["wall_report_output"] = res_wall.text
                        except Exception as e:
                            show_ai_error(e)

        if "wall_report_output" in st.session_state:
            st.markdown(f'<div class="report-box">{st.session_state["wall_report_output"]}</div>', unsafe_allow_html=True)
            st.download_button(
                label="📥 تحميل تقرير الصيانة (Markdown)",
                data=st.session_state["wall_report_output"],
                file_name="EAMENA_Structural_Condition_Report.md",
                mime="text/markdown",
                key="btn_dl_wall_report"
            )
        else:
            st.info("قم برفع صورة الجدار واضغط على 'توليد تقرير الصيانة' لعرض التقييم المعتمد هنا.")

# =============================================================================
# TAB 5: التنبؤ بالماضي (Predicting the Past — Ithaca & Aeneas)
# =============================================================================
with tab_predicting:
    st.header("🔮 التنبؤ بالماضي (Predicting the Past — Ithaca & Aeneas)")
    st.write("المنصة المعتمدة على الذكاء الاصطناعي التوليدي من DeepMind وجامعة أكسفورد (predictingthepast.com) لمعالجة، وترميم، ونسب وتأريخ النصوص والنقوش التاريخية القديمة (Contextualising, Restoring, and Attributing Ancient Inscriptions).")

    # Banner with official link
    st.markdown("""
    <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #d4a373; border-radius: 12px; padding: 18px; margin-bottom: 22px;">
        <h4 style="margin: 0 0 8px 0; color: #d4a373;">🏛️ عن مبادرة Predicting the Past (نماذج Ithaca و Aeneas)</h4>
        <p style="margin: 0; color: #cbd5e1; font-size: 0.95rem; line-height: 1.8;">
            مبادرة علمية عالمية طُورت بالتعاون بين <b>Google DeepMind</b> و<b>جامعة أكسفورد</b> وجامعة كا فوسكاري بالبندقية ونُشرت في مجلة <i>Nature</i>. تهدف النماذج التوليدية المتخصصة (<b>Ithaca</b> للنقوش اليونانية و<b>Aeneas</b> للنقوش اللاتينية) إلى مساعدة الباحثين والمؤرخين عبر ثلاثة مسارات رئيسية:
            <br>1️⃣ <b>ترميم واستكمال النصوص المتآكلة (Text Restoration)</b> للأحرف والكلمات المفقودة [---] بدقة تفوق 71%.
            <br>2️⃣ <b>تحديد الموطن الجغرافي ونسب النقش (Geographical Attribution)</b> وتوزيع احتمالات مكان الكتابة أو دار السك بدقة 84%.
            <br>3️⃣ <b>التأريخ الزمني الدقيق (Chronological Dating)</b> وتحديد العقود والحقب الزمنية المرجحة في نطاق 30 عاماً.
        </p>
        <div style="margin-top: 12px;">
            <a href="https://predictingthepast.com/" target="_blank" style="color: #38bdf8; text-decoration: underline; font-weight: bold; font-size: 1rem;">
                🌐 زيارة المنصة الرسمية لـ DeepMind وأكسفورد: https://predictingthepast.com/
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_it1, col_it2 = st.columns([1, 1], gap="large")

    with col_it1:
        st.subheader("📝 إدخال النقيشة أو المأثورة المتآكلة")
        
        input_mode = st.radio(
            "طريقة فحص النقيشة:",
            ["نص نقشي مع فجوات تآكل [---] (Epigraphic Text Input)", "فحص بصري من صورة نقش / مسكوكة (Vision Analysis)"],
            horizontal=True
        )

        preset_text = ""
        target_script = "كوفي مبكر (مسكوكات إسلامية - الشارقة)"
        user_damaged_text = ""
        ithaca_image = None

        if input_mode.startswith("نص"):
            inscription_presets = {
                "درهم موقع المدام بالشارقة (تآكل اسم دار السك)": {
                    "text": "بسم الله ضرب هذا الدرهم بـ [---] سنة سبعين ومائة",
                    "script": "كوفي مبكر (مسكوكات إسلامية - الشارقة)",
                    "target": "استكمال دار السك المفقودة وتأريخها ونسبها الجغرافي"
                },
                "نقيشة شاهد قبر مسند صخرية من مليحة": {
                    "text": "نفس وقبر [---] بن كاهل بن عمـ[---] ذو تيم بن أوس عـ[---]",
                    "script": "خط المسند الجنوبي القديم (مكتشفات مليحة)",
                    "target": "استكمال أسماء النسب والقبيلة وتأريخ النقيشة"
                },
                "مسكوكة الملكة أبيئيل من مليحة (نقش آرامي/حسياني)": {
                    "text": "أبيئيل ملـ[---] عمان و[---]",
                    "script": "الآرامي والحسياني القديم (حضارة مليحة وعمان القديمة)",
                    "target": "استكمال لقب الحاكم 'ملك/ملكة عمان' وحقبة السك"
                },
                "مرسوم أثيني كلاسيكي (معيار نموذج Ithaca اليوناني)": {
                    "text": "ἔδοξεν τῇ βουλῇ καὶ τῷ δήμῳ [---] ἐπεστάτει",
                    "script": "اليوناني القديم (Ancient Greek - معيار Ithaca)",
                    "target": "استكمال اسم الخطيب/الحاكم ونسب المرسوم إلى أتيكا"
                },
                "نقيشة إمبراطورية رومانية (معيار نموذج Aeneas اللاتيني)": {
                    "text": "IMP CAESAR DIVI [---] AUGUSTUS PONTIFEX MAXIMUS [---]",
                    "script": "اللاتيني الإمبراطوري (Latin - معيار Aeneas)",
                    "target": "استكمال ألقاب الإمبراطور وتأريخ الحقبة الرومانية"
                },
                "نص نقشي مخصص...": {
                    "text": "",
                    "script": "كوفي مبكر (مسكوكات إسلامية - الشارقة)",
                    "target": "تحديد يدوي"
                }
            }

            chosen_preset_name = st.selectbox(
                "اختر عينة نقشية تاريخية أو أدخل نصك:",
                list(inscription_presets.keys())
            )
            
            preset_obj = inscription_presets[chosen_preset_name]
            default_txt = preset_obj["text"]
            
            user_damaged_text = st.text_area(
                "النص النقشي مع تمثيل مواضع التآكل والفقد بـ [---]:",
                value=default_txt,
                height=130,
                help="استخدم [---] لتمثيل الكلمات أو الحروف المتآكلة أو المفقودة."
            )
            
            target_script = st.selectbox(
                "نوع الخط والحضارة المرجعية للنقيشة:",
                [
                    "كوفي مبكر (مسكوكات إسلامية - الشارقة)",
                    "خط المسند الجنوبي القديم (مكتشفات مليحة)",
                    "الآرامي والحسياني القديم (حضارة مليحة وعمان القديمة)",
                    "اليوناني القديم (Ancient Greek - معيار Ithaca)",
                    "اللاتيني الإمبراطوري (Latin - معيار Aeneas)"
                ],
                index=0 if "المدام" in chosen_preset_name else (1 if "مسند" in chosen_preset_name else (2 if "أبيئيل" in chosen_preset_name else (3 if "Ithaca" in chosen_preset_name else 0)))
            )
        else:
            st.markdown("**رفع أو اختيار صورة النقيشة أو المسكوكة:**")
            ithaca_sample_options = {
                "رفع صورة مخصصة من جهازي": None,
                "شاهد قبر": "images/masnad.png",
                "درهم سلطان": "images/Picture1.jpg",
                "درهم اسلامي": "images/hfgd8.jpg",
                "كسرة طبق": "images/dfdff.png",
                "حصن الذيد": "images/al-dhaid-fort-2.webp",
                "حصن دبا": "images/7195313.jpeg",
                "عملة الاسكندر": "images/47-91.png",
                "خاتم ذهبي": "images/11.png",
                "كسرة فخارية": "images/8.png"
            }
            chosen_ithaca_sample = st.selectbox("اختر عينة تجريبية أو ارفع ملفك:", list(ithaca_sample_options.keys()), key="ithaca_sample_sel")
            
            if ithaca_sample_options[chosen_ithaca_sample] and os.path.exists(ithaca_sample_options[chosen_ithaca_sample]):
                ithaca_image = Image.open(ithaca_sample_options[chosen_ithaca_sample]).convert("RGB")
                st.image(ithaca_image, caption=f"عينة: {chosen_ithaca_sample}", use_container_width=True)
            else:
                up_ithaca = st.file_uploader("ارفع صورة النقيشة المتآكلة (JPG, PNG):", type=["jpg", "jpeg", "png"], key="ithaca_img_up")
                if up_ithaca:
                    ithaca_image = Image.open(up_ithaca).convert("RGB")
                    st.image(ithaca_image, caption="الصورة المرفوعة", use_container_width=True)

            user_damaged_text = st.text_input("ملاحظات أو قراءة أولية للنقش (اختياري):", value="قراءة جزئية لمأثورات الطوق والمركز مع مناطق متآكلة غير مقروءة")

        ithaca_run_btn = st.button("🔮 بدء المعالجة بنموذج Predicting the Past (Ithaca / Aeneas AI)", key="btn_run_ithaca_eval")

        if os.path.exists("colab/Predicting the Past.ipynb"):
            with open("colab/Predicting the Past.ipynb", "rb") as f_nb:
                nb_bytes_pred = f_nb.read()
            st.download_button(
                label="📓 تنزيل دفتر (Predicting the Past.ipynb)",
                data=nb_bytes_pred,
                file_name="Predicting_the_Past.ipynb",
                mime="application/x-ipynb+json",
                key="btn_dl_pred_nb_tab5"
            )

    with col_it2:
        st.subheader("📊 مخرجات الاستعادة والنسب والتأريخ (Epigraphic Intelligence)")

        if ithaca_run_btn:
            client = get_genai_client(current_api_key)
            if not client:
                st.warning("يرجى إدخال مفتاح Google Gemini API في القائمة الجانبية لتشغيل النموذج التوليدي.")
            else:
                with st.spinner(f"جاري تطبيق خوارزمية Ithaca & Aeneas ونمذجة الفجوات عبر {selected_model}..."):
                    ithaca_prompt = f"""
بصفتك الذكاء الاصطناعي التوليدي المتخصص في فقه النقوش والمسكوكات التاريخية (Collaborative Epigraphic AI) وفق منهجية نماذج Ithaca و Aeneas ومبادرة Predicting the Past (predictingthepast.com المطورة مع DeepMind وجامعة أكسفورد):

المعطيات:
- نوع الخط / السياق الحضاري: {target_script}
- النص المتآكل / المقروء مع الفجوات [---]: {user_damaged_text}

المطلوب: إجراء تحليل تاريخي وفقهي متكامل وإخراج تقرير رسمي بصيغة Markdown يتضمن بدقة:
1. ✍️ **استكمال وترميم الفجوات المتآكلة (Text Restoration):**
   - تقديم أفضل 3 مقترحات ترجيحية لملء كل فجوة [---].
   - نسبة الثقة الاحتمالية (Restoration Probability %) لكل مقترح.
   - النص الكامل المستعاد لكل مقترح مع تمييز الكلمات المستعادة بخط بارز.
2. 🗺️ **النسب الجغرافي وتحديد الموطن / دار السك (Geographical Attribution):**
   - توزيع الاحتمالات لأبرز المناطق الجغرافية أو دور السك المتوقعة (مثل: الكوفة، البصرة، واسط، دمشق، مليحة، المدام، أثينا، روما...).
   - نسبة الاحتمال لكل موطن (Geographical Probability Distribution).
3. ⏳ **التأريخ الزمني الدقيق (Chronological Dating):**
   - العقد أو السنة التقديرية بدقة (Dating Estimate).
   - النطاق الزمني الاحتمالي (Date Interval) مع ذكر الخليفة أو الحاكم أو الحقبة المتطابقة.
4. 📜 **التعليل اللغوي والتاريخي (Epigraphic Rationale):**
   - المقاربات مع نقوش ومسكوكات مكتشفات هيئة الشارقة للآثار أو المجموعات العالمية المشابهة.
   - تفسير سبب ترجيح المقترح الأول لغوياً ومورفولوجياً.
"""
                    try:
                        content_payload = [ithaca_prompt]
                        if input_mode.startswith("فحص بصري") and ithaca_image is not None:
                            content_payload = [ithaca_image, ithaca_prompt]

                        ithaca_res, _model_used = generate_ai_content(
                            client, content_payload, selected_model
                        )
                        st.session_state["ithaca_report_output"] = ithaca_res.text
                    except Exception as e:
                        show_ai_error(e)

        if "ithaca_report_output" in st.session_state:
            st.markdown(f'<div class="report-box">{st.session_state["ithaca_report_output"]}</div>', unsafe_allow_html=True)
            st.download_button(
                label="📥 تحميل تقرير الاستعادة والنسب (Ithaca Report Markdown)",
                data=st.session_state["ithaca_report_output"],
                file_name="Predicting_The_Past_Epigraphic_Report.md",
                mime="text/markdown",
                key="btn_dl_ithaca_report"
            )
        else:
            st.info("اختر العينة النقشية واضغط على زر تشغيل النموذج لاستعراض مقترحات الاستعادة وتوزيع الاحتمالات الجغرافية والزمنية.")

# =============================================================================
# TAB 6: العرض التقديمي الكامل (PDF) ودليل الورشة
# =============================================================================
with tab_presentation:
    st.header("📽️ العرض التقديمي الكامل ودليل الورشة المعتمد")
    st.write("استعراض شرائح العرض التقديمي الشامل للورشة (PDF) وملفات التوثيق القياسية لهيئة الشارقة للآثار.")

    pdf_path = find_presentation_pdf()

    col_pres_info, col_pres_actions = st.columns([2, 1], gap="medium")
    
    with col_pres_info:
        st.markdown("""
        **المحاور العلمية المشمولة في العرض:**
        - **المحور 1:** الذكاء الاصطناعي في علم الآثار، التحول من الأرشفة الساكنة إلى الفهرسة الدلالية الفورية للمسكوكات.
        - **المحور 2:** التوثيق الميداني بالرؤية الحاسوبية واستخراج مقاطع الفخار ونمذجة مصفوفة هاريس الطبقية.
        - **المحور 3:** الاستشعار عن بعد ومؤشرات التباين الطيفي (ANDI) لرصد الشواهد والأساسات المدفونة في مليحة.
        - **المحور 4:** الرصد الإنشائي للشروخ وتقارير الصيانة الوقائية وإدارة المخاطر وفق بروتوكول EAMENA الدولي.
        """)

    with col_pres_actions:
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_bytes_data = f.read()
            st.download_button(
                label="📥 تحميل ملف العرض التقديمي الكامل (PDF)",
                data=pdf_bytes_data,
                file_name="ورشة_الذكاء_الاصطناعي_في_توثيق_المواقع_والقطع_الأثرية.pdf",
                mime="application/pdf",
                key="btn_dl_pres_pdf"
            )
            st.success("الملف جاهز للاستعراض والتنزيل المباشر.")
        else:
            st.warning("تعذر العثور على ملف العرض التقديمي PDF في المجلد الحالي.")

        if os.path.exists("presentation.html"):
            with open("presentation.html", "r", encoding="utf-8") as f_h:
                html_presentation_code = f_h.read()
            st.download_button(
                label="🌐 تنزيل العرض التفاعلي (HTML)",
                data=html_presentation_code,
                file_name="presentation.html",
                mime="text/html",
                key="btn_dl_pres_html"
            )

        if os.path.exists("colab/Predicting the Past.ipynb"):
            with open("colab/Predicting the Past.ipynb", "rb") as f_nb:
                nb_bytes = f_nb.read()
            st.download_button(
                label="📓 تنزيل دفتر (Predicting the Past.ipynb)",
                data=nb_bytes,
                file_name="Predicting_the_Past.ipynb",
                mime="application/x-ipynb+json",
                key="btn_dl_pred_nb_tab6"
            )

    # -------------------------------------------------------------------------
    # PowerPoint PPTX Presentation Builder (from Predicting the Past.ipynb)
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("📊 مولّد حزم العروض التقديمية الرسمية (PowerPoint .pptx)")
    st.caption("ميزة مستوحاة ومطابقة لكود دفتر `Predicting the Past.ipynb` لإنشاء عروض تقديمية سيادية مصممة خصيصاً لهيئة الشارقة للآثار.")

    if HAS_PPTX:
        COLOR_TERRACOTTA = RGBColor(178, 58, 34)
        COLOR_SAND_GOLD = RGBColor(212, 163, 115)
        COLOR_CYAN = RGBColor(6, 182, 212)
        COLOR_EMERALD = RGBColor(16, 185, 129)

        pptx_modules = [
            {
                "id": "1",
                "title": "مقدمة في الذكاء الاصطناعي وتطبيقاته الأثرية",
                "filename": "العرض_1_مقدمة_الذكاء_الاصطناعي_الآثار.pptx",
                "accent": COLOR_TERRACOTTA,
                "badge": "المحور الأول: المفاهيم والتأسيس الأكاديمي",
                "s2_title": "التحول من الأرشفة الساكنة إلى التحليل الدلالي",
                "s2_left_head": "الرقمنة الساكنة التقليدية",
                "s2_left_body": "• جداول Excel وقواعد بيانات معزولة وغير مترابطة.\n• صور فوتوغرافية وأوراق مسح تفتقر للمعلومات الحاسوبية الدلالية.\n• استرجاع وتصنيف يدوي يستنزف أكثر من 70% من وقت الباحث الأثري.",
                "s2_right_head": "التوثيق الذكي التنبؤي (2026)",
                "s2_right_body": "• تعرف آلي على الأنماط واستخراج السمات الزخرفية للقطع.\n• نماذج متعددة الوسائط (Multimodal AI) للفهرسة الفورية من الصور.\n• تطبيق معايير FAIR الدولية للربط بين مكتشفات متاحف ومواقع الشارقة.",
                "s3_steps": [
                    ("التقاط الصورة/النقش", "تصوير الكسرة أو المسكوكة عبر كاميرا عالية الدقة"),
                    ("معالجة الرؤية (Vision AI)", "عزل التآكل واستخراج معالم الخطوط والكتابات"),
                    ("المطابقة بنموذج Ithaca", "استكمال الكلمات المتآكلة وتحديد عصر وتاريخ القطعة"),
                    ("التصدير القياسي", "إنتاج بطاقة تعريفية آلية وفق معيار Dublin Core")
                ],
                "s4_kpis": [
                    ("71%", "دقة نموذج Ithaca في ترميم واستكمال النقوش التاريخية التالفة"),
                    ("84%", "دقة تحديد الموطن الجغرافي الأصلي للنصوص والمسكوكات"),
                    ("80%", "تخفيض في الوقت المستهلك لإعداد بطاقات التوثيق المتحفية"),
                    ("0.1mm", "دقة مطابقة قوالب ضرب المسكوكات الإسلامية المكتشفة بالشارقة")
                ],
                "notes": "التركيز على مسكوكات موقع المدام ودراهم مليحة لإثبات الجدوى الميدانية لأدوات الذكاء الاصطناعي أمام الإدارة."
            },
            {
                "id": "2",
                "title": "توثيق المواقع والتسجيل الميداني 3D",
                "filename": "العرض_2_توثيق_المواقع_والتسجيل_الميداني.pptx",
                "accent": COLOR_SAND_GOLD,
                "badge": "المحور الثاني: التوثيق والنمذجة الميدانية",
                "s2_title": "طفرة النمذجة ثلاثية الأبعاد: من SfM إلى 3DGS",
                "s2_left_head": "التصوير المساحي الكلاسيكي (SfM)",
                "s2_left_body": "• يتطلب مئات الصور المتداخلة وزمن معالجة طويل جداً.\n• يعاني أمام التباينات الحادة لضوء الشمس في صحراء الشارقة.\n• حاجة ماسة لمحطات عمل حاسوبية فائقة التعقيد بالموقع.",
                "s2_right_head": "رذاذ غاوس (3D Gaussian Splatting)",
                "s2_right_body": "• طفرة النمذجة: تمثيل المشهد كاملاً بسرعة معالجة فورية.\n• تصفح تفاعلي سلس للمواقع والمربعات بمعدل 60 إطاراً في الثانية.\n• العمل مباشرة من الهاتف والدرون دون الحاجة لأجهزة عملاقة.",
                "s3_steps": [
                    ("المسح بالهاتف (LiDAR)", "استخدام Polycam لمسح المربع الأثري أو اللقية"),
                    ("التسجيل الصوتي الحقلي", "تحويل إملاء الباحث الأثري الميداني إلى سجل حفر رقمي"),
                    ("مقاطع الفخار الآلية", "استخراج Rim Profiles تلقائياً دون رسم يدوي مجهد"),
                    ("المزامنة مع QGIS", "ربط السحابة النقطية والتوأم الرقمي بقواعد بيانات الهيئة")
                ],
                "s4_kpis": [
                    ("60 FPS", "سرعة التصفح السلس للتوائم الرقمية بمواقع التنقيب"),
                    ("75%", "توفير في زمن استخراج ورسم مقاطع حواف الأواني الفخارية"),
                    ("1mm", "دقة قياس الأبعاد الواقعية عبر مستشعرات الليدار المحمولة"),
                    ("100%", "حفظ رقمي دائم للسياق الطبقي للموقع قبل إزالة الطبقات")
                ],
                "notes": "التأكيد على أن الحفرية الأثرية بطبيعتها عملية تدميرية متحكم بها؛ ما يُحفر لا يمكن إعادته، لذا فإن التوأم الرقمي يحفظ الموقع للأبد."
            },
            {
                "id": "3",
                "title": "الكشف والتنبؤ بالآثار المدفونة والاستشعار عن بعد",
                "filename": "العرض_3_الكشف_والتنبؤ_والاستشعار_عن_بعد.pptx",
                "accent": COLOR_CYAN,
                "badge": "المحور الثالث: الاستشعار عن بعد والذكاء المكاني",
                "s2_title": "اختراق الرمال الصحراوية عبر رادار الفضاء (SAR)",
                "s2_left_head": "التصوير الضوئي الفضائي المحدود",
                "s2_left_body": "• يلتقط فقط المعالم السطحية الظاهرة للعين البشرية المجردة.\n• تغطية الرمال الصحراوية الزاحفة تحجب بالكامل الآثار المدفونة.\n• صعوبة تتبع قنوات المياه القديمة والأسوار المطمورة تحت السطح.",
                "s2_right_head": "الرادار الفضائي والليدار (SAR & LiDAR)",
                "s2_right_body": "• موجات الرادار الميكروية (L-band) تخترق الرمال الجافة لعمق 1-3 أمتار.\n• الارتداد التفاضلي يكشف كثافة الأساسات الحجرية المطمورة.\n• الليدار الجوي يعزل الكثبان الرملية والنباتات لإنتاج نماذج DTM عارية.",
                "s3_steps": [
                    ("استدعاء صور Sentinel-1/2", "تحميل النطاقات الطيفية ورادار الفتحة الاصطناعية للمنطقة"),
                    ("حساب مؤشر ANDI الأثري", "مقارنة النطاق الأحمر بنطاق الأشعة تحت الحمراء القريبة"),
                    ("التصنيف بنموذج YOLO", "اكتشاف الأنماط الدائرية للمدافن والمستطيلة للأسوار"),
                    ("توليد الإحداثيات الجغرافية", "تصدير خريطة اشتباه أثري عالية الاحتمالية لفرق المسح")
                ],
                "s4_kpis": [
                    ("1 - 3m", "عمق اختراق موجات رادار SAR للرمال الصحراوية الجافة بالشارقة"),
                    ("1000s", "كيلومترات مربعة تُفحص وتُحلل آلياً عبر الذكاء الاصطناعي في دقائق"),
                    ("92%", "دقة النماذج التنبؤية في تمييز مدافن العصر البرونزي وقنوات الأفلاج"),
                    ("Zero", "حفريات عشوائية؛ توجيه فرق المسح مباشرة لنقاط مؤكدة بنسب احتمالية")
                ],
                "notes": "استعراض كود Colab التفاعلي وشرح كيف تبرز الأساسات الأثرية في خريطة التباين الطيفي بالألوان الفسفورية."
            },
            {
                "id": "4",
                "title": "مراقبة حالة المواقع والقطع الأثرية ورصد التدهور",
                "filename": "العرض_4_مراقبة_حالة_المواقع_ورصد_التدهور.pptx",
                "accent": COLOR_EMERALD,
                "badge": "المحور الرابع: الصيانة التنبؤية وإدارة المخاطر",
                "s2_title": "المراقبة رباعية الأبعاد (4D Time-Lapse) وحماية التراث",
                "s2_left_head": "الترميم العلاجي الكلاسيكي (رد الفعل)",
                "s2_left_body": "• التدخل فقط بعد حدوث التصدع الكبير أو انهيار جزء من الجدار.\n• تكاليف مالية باهظة وصعوبة بالغة في استعادة الحالة الأصلية.\n• غياب القياس الدقيق لمعدلات التآكل البطيئة الناتجة عن الرياح والأمطار.",
                "s2_right_head": "الصيانة التنبؤية الذكية (الاستباق)",
                "s2_right_body": "• مقارنة السحب النقطية (خوارزمية M3C2) لرصد الإزاحات المليمترية مبكراً.\n• التعرف الآلي على الشروخ ومعدل اتساعها عبر الرؤية الحاسوبية.\n• الكشف المبكر عن مرض البرونز والصدأ بالقطع المعدنية في المستودعات.",
                "s3_steps": [
                    ("المسح الدوري المقارن", "إجراء مسح ليزري أو تصويري سنوي لنفس الموقع أو المبنى"),
                    ("المطابقة السحابية (M3C2)", "مقارنة هندسية فائقة الدقة لعزل الفروق الناتجة عن التآكل"),
                    ("التجزئة الدلالية للشروخ", "تصنيف عمق واتساع الشقوق وتحديد درجة خطورتها آلياً"),
                    ("تقرير الاستجابة المؤتمت", "إصدار تنبيه عاجل لفرق الصيانة وفق مصفوفة المخاطر المعتمدة")
                ],
                "s4_kpis": [
                    ("0.5mm", "أصغر إزاحة هيكلية أو تآكل يمكن للنظام رصده وتنبيه الإدارة به"),
                    ("65%", "تخفيض في كلفة أعمال الترميم بفضل التدخل الوقائي الاستباقي"),
                    ("100%", "أتمتة تقارير الحالة الإنشائية وتصنيف المخاطر وفق معايير EAMENA"),
                    ("24/7", "استجابة ذكية لحماية القلاع والمواقع الأثرية المفتوحة من عوامل الطقس")
                ],
                "notes": "الختام باستعراض خارطة طريق التحول الرقمي وتأسيس وحدة الرصد الذكي داخل هيئة الشارقة للآثار."
            }
        ]

        def build_pptx_deck_bytes(mod):
            prs = Presentation()
            prs.slide_width = Inches(13.333)
            prs.slide_height = Inches(7.5)
            blank_layout = prs.slide_layouts[6]

            accent = mod["accent"]
            NAVY = RGBColor(15, 23, 42)
            SLATE = RGBColor(30, 41, 59)
            GOLD = RGBColor(212, 163, 115)
            WHITE = RGBColor(255, 255, 255)
            MUTED = RGBColor(148, 163, 184)
            LIGHT = RGBColor(248, 250, 252)
            TERRA = RGBColor(178, 58, 34)

            def header(s, badge, title):
                hb = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(1.15))
                hb.fill.solid()
                hb.fill.fore_color.rgb = NAVY
                hb.line.fill.background()
                ln = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(1.15), Inches(13.333), Inches(0.06))
                ln.fill.solid()
                ln.fill.fore_color.rgb = accent
                ln.line.fill.background()
                tf = hb.text_frame
                tf.word_wrap = True
                tf.margin_right = Inches(0.8)
                tf.margin_top = Inches(0.15)
                p0 = tf.paragraphs[0]
                p0.text = f"حكومة الشارقة — هيئة الشارقة للآثار | {badge}"
                p0.font.size = Pt(11)
                p0.font.bold = True
                p0.font.color.rgb = GOLD
                p0.alignment = PP_ALIGN.RIGHT
                p1 = tf.add_paragraph()
                p1.text = title
                p1.font.size = Pt(20)
                p1.font.bold = True
                p1.font.color.rgb = WHITE
                p1.alignment = PP_ALIGN.RIGHT

            # Slide 1: Hero
            s1 = prs.slides.add_slide(blank_layout)
            b1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
            b1.fill.solid()
            b1.fill.fore_color.rgb = NAVY
            b1.line.fill.background()
            bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(13.1), 0, Inches(0.233), Inches(7.5))
            bar.fill.solid()
            bar.fill.fore_color.rgb = accent
            bar.line.fill.background()
            card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(1.3), Inches(10.9), Inches(4.9))
            card.fill.solid()
            card.fill.fore_color.rgb = SLATE
            card.line.color.rgb = GOLD
            card.line.width = Pt(1.5)
            ctf = card.text_frame
            ctf.word_wrap = True
            ctf.margin_right = Inches(0.8)
            ctf.margin_top = Inches(0.6)
            ctf.margin_left = Inches(0.8)
            cp0 = ctf.paragraphs[0]
            cp0.text = "حكومة الشارقة — هيئة الشارقة للآثار | المذكرة الرسمية SAA-CCS/1147/2026"
            cp0.font.size = Pt(14)
            cp0.font.bold = True
            cp0.font.color.rgb = GOLD
            cp0.alignment = PP_ALIGN.RIGHT
            cp1 = ctf.add_paragraph()
            cp1.text = mod["title"]
            cp1.font.size = Pt(30)
            cp1.font.bold = True
            cp1.font.color.rgb = WHITE
            cp1.alignment = PP_ALIGN.RIGHT
            cp2 = ctf.add_paragraph()
            cp2.text = f"\nورشة عمل: الذكاء الاصطناعي في توثيق المواقع والقطع الأثرية — {mod['badge']}"
            cp2.font.size = Pt(16)
            cp2.font.color.rgb = MUTED
            cp2.alignment = PP_ALIGN.RIGHT

            # Slide 2: Comparison
            s2 = prs.slides.add_slide(blank_layout)
            b2 = s2.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
            b2.fill.solid()
            b2.fill.fore_color.rgb = LIGHT
            b2.line.fill.background()
            header(s2, mod["badge"], mod["s2_title"])
            br = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2))
            br.fill.solid()
            br.fill.fore_color.rgb = WHITE
            br.line.color.rgb = RGBColor(226, 232, 240)
            br.line.width = Pt(1.5)
            rtf = br.text_frame
            rtf.word_wrap = True
            rtf.margin_right = Inches(0.4)
            rtf.margin_left = Inches(0.4)
            rtf.margin_top = Inches(0.4)
            rp0 = rtf.paragraphs[0]
            rp0.text = f"❌ {mod['s2_left_head']}"
            rp0.font.size = Pt(18)
            rp0.font.bold = True
            rp0.font.color.rgb = TERRA
            rp0.alignment = PP_ALIGN.RIGHT
            rp1 = rtf.add_paragraph()
            rp1.text = f"\n{mod['s2_left_body']}"
            rp1.font.size = Pt(14)
            rp1.font.color.rgb = NAVY
            rp1.alignment = PP_ALIGN.RIGHT

            bl = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.2))
            bl.fill.solid()
            bl.fill.fore_color.rgb = WHITE
            bl.line.color.rgb = accent
            bl.line.width = Pt(2)
            ltf = bl.text_frame
            ltf.word_wrap = True
            ltf.margin_right = Inches(0.4)
            ltf.margin_left = Inches(0.4)
            ltf.margin_top = Inches(0.4)
            lp0 = ltf.paragraphs[0]
            lp0.text = f"✨ {mod['s2_right_head']}"
            lp0.font.size = Pt(18)
            lp0.font.bold = True
            lp0.font.color.rgb = accent
            lp0.alignment = PP_ALIGN.RIGHT
            lp1 = ltf.add_paragraph()
            lp1.text = f"\n{mod['s2_right_body']}"
            lp1.font.size = Pt(14)
            lp1.font.color.rgb = NAVY
            lp1.alignment = PP_ALIGN.RIGHT

            # Slide 3: Flow
            s3 = prs.slides.add_slide(blank_layout)
            b3 = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
            b3.fill.solid()
            b3.fill.fore_color.rgb = LIGHT
            b3.line.fill.background()
            header(s3, mod["badge"], "خارطة الإجراءات والتدفق الحقلي والمكتبي (Field-to-Lab Pipeline)")
            x_pos = [Inches(9.8), Inches(6.8), Inches(3.8), Inches(0.8)]
            for idx, (st_t, st_d) in enumerate(mod["s3_steps"]):
                bst = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x_pos[idx], Inches(1.7), Inches(2.7), Inches(4.8))
                bst.fill.solid()
                bst.fill.fore_color.rgb = WHITE
                bst.line.color.rgb = RGBColor(203, 213, 225)
                bst.line.width = Pt(1.5)
                stf = bst.text_frame
                stf.word_wrap = True
                stf.margin_right = Inches(0.25)
                stf.margin_left = Inches(0.25)
                stf.margin_top = Inches(0.4)
                sp0 = stf.paragraphs[0]
                sp0.text = f"الخطوة {idx+1}"
                sp0.font.size = Pt(14)
                sp0.font.bold = True
                sp0.font.color.rgb = accent
                sp0.alignment = PP_ALIGN.CENTER
                sp1 = stf.add_paragraph()
                sp1.text = st_t
                sp1.font.size = Pt(16)
                sp1.font.bold = True
                sp1.font.color.rgb = NAVY
                sp1.alignment = PP_ALIGN.CENTER
                sp2 = stf.add_paragraph()
                sp2.text = f"\n{st_d}"
                sp2.font.size = Pt(12)
                sp2.font.color.rgb = RGBColor(71, 85, 105)
                sp2.alignment = PP_ALIGN.RIGHT

            # Slide 4: KPIs
            s4 = prs.slides.add_slide(blank_layout)
            b4 = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
            b4.fill.solid()
            b4.fill.fore_color.rgb = NAVY
            b4.line.fill.background()
            header(s4, mod["badge"], "الأثر التشغيلي والمؤشرات الرقمية الميدانية (Key Impact Metrics)")
            kpi_pos = [(Inches(6.9), Inches(1.7)), (Inches(0.8), Inches(1.7)), (Inches(6.9), Inches(4.5)), (Inches(0.8), Inches(4.5))]
            for idx, (val, desc) in enumerate(mod["s4_kpis"]):
                gx, gy = kpi_pos[idx]
                kc = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, gx, gy, Inches(5.6), Inches(2.4))
                kc.fill.solid()
                kc.fill.fore_color.rgb = SLATE
                kc.line.color.rgb = accent
                kc.line.width = Pt(1)
                ktf = kc.text_frame
                ktf.word_wrap = True
                ktf.margin_right = Inches(0.4)
                ktf.margin_top = Inches(0.3)
                ktf.margin_left = Inches(0.4)
                kp0 = ktf.paragraphs[0]
                kp0.text = val
                kp0.font.size = Pt(36)
                kp0.font.bold = True
                kp0.font.color.rgb = GOLD
                kp0.alignment = PP_ALIGN.RIGHT
                kp1 = ktf.add_paragraph()
                kp1.text = desc
                kp1.font.size = Pt(13)
                kp1.font.color.rgb = WHITE
                kp1.alignment = PP_ALIGN.RIGHT

            for s in [s1, s2, s3, s4]:
                ntf = s.notes_slide.notes_text_frame
                ntf.text = f"إرشادات المتحدث الرسمية أمام الحضور:\n{mod['notes']}"

            buf = io.BytesIO()
            prs.save(buf)
            buf.seek(0)
            return buf.getvalue()

        col_pptx_sel, col_pptx_btn = st.columns([2, 1], gap="medium")
        with col_pptx_sel:
            chosen_module_idx = st.selectbox(
                "اختر المحور لتوليد عرض PowerPoint مخصص له:",
                range(len(pptx_modules)),
                format_func=lambda i: f"المحور {pptx_modules[i]['id']}: {pptx_modules[i]['title']}",
                key="pptx_module_sel"
            )
        with col_pptx_btn:
            selected_mod = pptx_modules[chosen_module_idx]
            pptx_data = build_pptx_deck_bytes(selected_mod)
            st.download_button(
                label=f"📊 تنزيل عرض ({selected_mod['filename']})",
                data=pptx_data,
                file_name=selected_mod["filename"],
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                key="btn_dl_pptx_deck"
            )
    else:
        st.info("مكتبة python-pptx متوفرة في requirements.txt وسيتم تفعيل توليد شرائح PPTX تلقائياً على Streamlit Cloud.")

    st.markdown("---")
    st.subheader("📽️ مستعرض شرائح العرض التقديمي التفاعلي (Presentation Slide Viewer)")
    st.caption("تنقّل بين شرائح العرض داخل المنصة شريحة بشريحة، أو افتح الملف بملء الشاشة في تبويب مستقل.")

    if pdf_path and os.path.exists(pdf_path):
        static_pdf_path = ensure_presentation_static_copy(pdf_path)

        col_viewer, col_viewer_actions = st.columns([3, 1], gap="medium")

        with col_viewer_actions:
            if static_pdf_path:
                st.markdown(
                    '<a href="app/static/presentation_workshop.pdf" target="_blank" rel="noopener noreferrer" '
                    'style="display:block;text-align:center;padding:14px 10px;border-radius:10px;'
                    'background:linear-gradient(135deg,#d4a373 0%,#b23a22 100%);color:#ffffff !important;'
                    'font-weight:800;text-decoration:none;line-height:1.7;">'
                    '🔗 فتح العرض بملء الشاشة<br><span style="font-size:0.8rem;">(تبويب مستقل — Full Screen PDF)</span></a>',
                    unsafe_allow_html=True
                )
            else:
                st.info("لعرض الملف في تبويب مستقل، أضف `enableStaticServing = true` في `.streamlit/config.toml`.")

            st.caption("💡 يمكنك أيضاً تنزيل ملف الـ PDF أو العرض التفاعلي (HTML) من الأزرار أعلاه.")

        with col_viewer:
            if HAS_FITZ:
                try:
                    pdf_mtime = os.path.getmtime(pdf_path)
                    with fitz.open(pdf_path) as _pdf_doc:
                        total_slides = _pdf_doc.page_count

                    if "pres_page_num" not in st.session_state:
                        st.session_state["pres_page_num"] = 1
                    if st.session_state["pres_page_num"] > total_slides:
                        st.session_state["pres_page_num"] = total_slides

                    def _pres_move(delta):
                        st.session_state["pres_page_num"] = min(max(1, st.session_state["pres_page_num"] + delta), total_slides)

                    ctrl_prev, ctrl_page, ctrl_next, ctrl_zoom = st.columns([1, 1.1, 1, 1.6])
                    with ctrl_prev:
                        st.button("⬅️ الشريحة السابقة", key="btn_pres_prev", on_click=_pres_move, args=(-1,))
                    with ctrl_page:
                        st.number_input("رقم الشريحة:", min_value=1, max_value=total_slides, step=1, key="pres_page_num")
                    with ctrl_next:
                        st.button("الشريحة التالية ➡️", key="btn_pres_next", on_click=_pres_move, args=(1,))
                    with ctrl_zoom:
                        pres_zoom = st.select_slider("مستوى التكبير والوضوح:", options=[1.0, 1.4, 1.8, 2.4, 3.0], value=1.8, key="pres_zoom")

                    current_slide_idx = int(st.session_state["pres_page_num"]) - 1
                    slide_png_bytes = render_pdf_slide_png(pdf_path, pdf_mtime, current_slide_idx, pres_zoom)

                    st.markdown(
                        f'<div style="text-align:center;font-weight:800;color:#d4a373;margin:8px 0;">'
                        f'الشريحة {current_slide_idx + 1} من {total_slides}</div>',
                        unsafe_allow_html=True
                    )
                    st.image(slide_png_bytes, use_container_width=True)
                    st.download_button(
                        label="🖼️ تنزيل الشريحة الحالية كصورة عالية الدقة (PNG)",
                        data=slide_png_bytes,
                        file_name=f"workshop_slide_{current_slide_idx + 1:02d}.png",
                        mime="image/png",
                        key="btn_dl_current_slide"
                    )
                except Exception as e:
                    st.error(f"خطأ أثناء تجهيز مستعرض الشرائح: {e}")
            else:
                st.warning("المستعرض التفاعلي يحتاج مكتبة `pymupdf` (مضافة إلى requirements.txt) وسيتم تفعيلها تلقائياً بعد إعادة البناء.")
                try:
                    with open(pdf_path, "rb") as f_pdf:
                        b64_pdf = base64.b64encode(f_pdf.read()).decode("utf-8")
                    st.markdown(
                        f'<iframe src="data:application/pdf;base64,{b64_pdf}#toolbar=1&navpanes=1&scrollbar=1" '
                        f'width="100%" height="850px" type="application/pdf" style="border:none;"></iframe>',
                        unsafe_allow_html=True
                    )
                except Exception as e:
                    st.error(f"خطأ أثناء تجهيز مستعرض الـ PDF: {e}")
    else:
        st.info("قم برفع ملف العرض التقديمي PDF إلى المجلد الرئيسي للاستعراض التفاعلي.")
