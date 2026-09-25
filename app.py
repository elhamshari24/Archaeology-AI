import os
import io
import json
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

# Load local environment variables if available
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="منصة الذكاء الاصطناعي الأثري — هيئة الشارقة للآثار",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Sharjah Archaeology Heritage Palette)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl;
        text-align: right;
    }
    
    .stApp {
        background: radial-gradient(circle at 85% 15%, #1e293b 0%, #0f172a 100%);
        color: #f8fafc;
    }

    h1, h2, h3, h4 {
        font-family: 'Cairo', sans-serif !important;
        font-weight: 800 !important;
        color: #d4a373 !important;
    }

    .main-header {
        background: linear-gradient(135deg, rgba(212, 163, 115, 0.12) 0%, rgba(30, 41, 59, 0.85) 100%);
        border: 1px solid rgba(212, 163, 115, 0.35);
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
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

    .metric-card {
        background: #1e293b;
        border: 1px solid rgba(212, 163, 115, 0.25);
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        margin-bottom: 15px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 900;
        color: #d4a373;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
    }

    .report-box {
        background-color: #0b1120;
        border: 1px solid rgba(212, 163, 115, 0.3);
        border-radius: 10px;
        padding: 20px;
        direction: rtl;
        text-align: right;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        border-bottom: 2px solid rgba(212, 163, 115, 0.2);
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Cairo', sans-serif !important;
        font-weight: 700;
        padding: 12px 20px;
        border-radius: 8px 8px 0 0;
        color: #94a3b8;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(212, 163, 115, 0.15) !important;
        color: #d4a373 !important;
        border-bottom: 3px solid #d4a373 !important;
    }

    /* Buttons */
    .stButton > button {
        font-family: 'Cairo', sans-serif !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, #d4a373 0%, #b23a22 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 24px !important;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(212, 163, 115, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# API Key and Model Helpers
# -----------------------------------------------------------------------------
def get_api_key():
    """Retrieve Gemini API key from user input, Streamlit Secrets, or environment."""
    key = st.session_state.get("gemini_key", "").strip()
    if not key and "GEMINI_API_KEY" in st.secrets:
        key = st.secrets["GEMINI_API_KEY"]
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
# Sidebar Configuration
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Sharjah_Archaeology_Authority_Logo.png/320px-Sharjah_Archaeology_Authority_Logo.png", 
             fallback="images/Gemini.png", width=180)
    
    st.markdown("### ⚙️ إعدادات المنصة")
    
    # Pre-fill from secrets or env if present
    default_key = ""
    if "GEMINI_API_KEY" in st.secrets:
        default_key = st.secrets["GEMINI_API_KEY"]
    elif os.getenv("GEMINI_API_KEY"):
        default_key = os.getenv("GEMINI_API_KEY")

    user_api_key = st.text_input(
        "🔑 مفتا�� Google Gemini API:",
        type="password",
        value=default_key,
        help="يمكنك الحصول على المفتاح مجاناً من Google AI Studio (aistudio.google.com)",
        key="gemini_key"
    )

    model_options = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.5-pro", "gemini-1.5-pro"]
    selected_model = st.selectbox("🤖 النموذج المعتمد:", model_options, index=0)
    
    st.markdown("---")
    st.markdown("""
    **محاور الورشة والتطبيقات:**
    - 🪙 **المحور 1:** الفهرسة اللحظية وفك النقوش والمسكوكات.
    - 🏺 **المحور 2:** استخراج مقاطع الفخار واستمارة الحفر الطبقي.
    - 🛰️ **المحور 3:** كشف الشذوذ الأثري بالاستشعار عن بعد (مليحة).
    - 🧱 **المحور 4:** الرصد الإنشائي للشروخ وتقارير الصيانة الوقائية (EAMENA).
    """)
    st.markdown("---")
    st.caption("هيئة الشارقة للآثار — ورشة الذكاء الاصطناعي في توثيق المواقع والقطع الأثرية")

# -----------------------------------------------------------------------------
# Main Header
# -----------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <span class="stat-badge">ورشة عمل متقدمة — 2026</span>
    <h1 style="margin: 0; font-size: 2.2rem;">🏛️ منصة الذكاء الاصطناعي في علم الآثار</h1>
    <p style="margin-top: 8px; color: #94a3b8; font-size: 1.05rem;">
        منصة موحدة ومدمجة لتحليل القطع والمواقع الأثرية بالرؤية الحاسوبية، والاستشعار عن بعد، والنماذج متعددة الوسائط (Multimodal AI).
    </p>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Navigation Tabs
# -----------------------------------------------------------------------------
tab_coin, tab_pottery, tab_satellite, tab_structural, tab_guide = st.tabs([
    "🪙 المحور 1: فك النقوش والمسكوكات",
    "🏺 المحور 2: مقاطع الفخار والتوثيق الطبقي",
    "🛰️ المحور 3: الاستشعار عن بعد وكشف الشذوذ",
    "🧱 المحور 4: الرصد الإنشائي للشروخ (EAMENA)",
    "📖 دليل المنصة والعرض التقديمي"
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
        st.subheader("📤 رفع صورة اللقية الأثرية")
        uploaded_coin = st.file_uploader(
            "اختر صورة المسكوكة أو اللقية (JPG, PNG):",
            type=["jpg", "jpeg", "png"],
            key="coin_file"
        )
        
        # Sample option
        use_sample_coin = st.checkbox("أو تجربة صورة نموذجية من الأرشيف", key="sample_coin_chk")
        coin_image_to_process = None

        if use_sample_coin and os.path.exists("images/17-gr9.jpg"):
            coin_image_to_process = Image.open("images/17-gr9.jpg").convert("RGB")
            st.image(coin_image_to_process, caption="عينة من أرشيف ا��شارقة (17-gr9.jpg)", use_container_width=True)
        elif uploaded_coin is not None:
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
                            response = client.models.generate_content(
                                model=selected_model,
                                contents=[coin_image_to_process, custom_coin_prompt]
                            )
                            st.session_state["coin_report_output"] = response.text
                        except Exception as e:
                            st.error(f"حدث خطأ أثناء معالجة الطلب: {e}")

        if "coin_report_output" in st.session_state:
            st.markdown(f'<div class="report-box">{st.session_state["coin_report_output"]}</div>', unsafe_allow_html=True)
            st.download_button(
                label="📥 تحميل التقرير (Markdown)",
                data=st.session_state["coin_report_output"],
                file_name="Archaeological_Coin_Report.md",
                mime="text/markdown"
            )
        else:
            st.info("قم برفع صورة واضغط على 'بدء التحليل' لظهور التقرير الأثري هنا.")

# =============================================================================
# TAB 2: مقاطع الفخار والتوثيق الطبقي (2.ipynb)
# =============================================================================
with tab_pottery:
    st.header("🏺 استخراج مقاطع الفخار وأتمتة استمارات الحفر الطبقي")
    st.write("دمج خوارزميات الرؤية الحاسوبية (Computer Vision) لاستخراج الحافة (Rim Profile) وتقدير القطر الهندسي، ثم توليد استمارة سي��ق طبقي رقمية (JSON) متوافقة مع مصفوفة هاريس.")

    col_p1, col_p2 = st.columns([1, 1], gap="large")

    with col_p1:
        st.subheader("📤 صورة الكسرة الفخارية ومحاكاة الحافة")
        up_pottery = st.file_uploader("ارفع صورة الكسرة الفخارية (Rim / Sherd):", type=["jpg", "jpeg", "png"], key="pot_file")
        
        canny_low = st.slider("عتبة Canny السفلى (Edge Low):", 10, 100, 40)
        canny_high = st.slider("عتبة Canny العليا (Edge High):", 80, 250, 130)
        
        pottery_img = None
        if up_pottery:
            pottery_img = Image.open(up_pottery).convert("RGB")
        elif os.path.exists("images/17-gr9.jpg"):
            if st.checkbox("استخدام عينة تجريبية للكسرة", key="chk_pot_sample"):
                pottery_img = Image.open("images/17-gr9.jpg").convert("RGB")

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

                st.image([img_np, rim_vis], caption=["الكسرة الأصلية", f"الحافة المستخرجة (القطر التقديري: {estimated_diameter_cm} سم)"], use_container_width=True)
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
  "Field_Curator_Recommendation": "توصيات الترميم والمعالجة الحق��ية"
}}
"""
                        try:
                            res_ai = client.models.generate_content(
                                model=selected_model,
                                contents=[pottery_img, prompt_pot]
                            )
                            raw_text = res_ai.text.strip()
                            if raw_text.startswith("```json"):
                                raw_text = raw_text[7:]
                            if raw_text.endswith("```"):
                                raw_text = raw_text[:-3]
                            st.session_state["pottery_json_output"] = raw_text.strip()
                        except Exception as e:
                            st.error(f"حدث خطأ أثناء معالجة الطلب: {e}")

        if "pottery_json_output" in st.session_state:
            try:
                parsed_json = json.loads(st.session_state["pottery_json_output"])
                st.json(parsed_json)
                st.download_button(
                    label="📥 تحميل الاستمارة (JSON)",
                    data=json.dumps(parsed_json, ensure_ascii=False, indent=2),
                    file_name="Stratigraphic_Context_Unit_Record.json",
                    mime="application/json"
                )
            except Exception:
                st.code(st.session_state["pottery_json_output"], language="json")
                st.download_button(
                    label="📥 تحميل الاستمارة (JSON)",
                    data=st.session_state["pottery_json_output"],
                    file_name="Stratigraphic_Context_Unit_Record.json",
                    mime="application/json"
                )
        else:
            st.info("قم برفع صورة كسرة فخار واضغط على زر التوليد لإنتاج الاستمارة الميدانية.")

# =============================================================================
# TAB 3: الاستشعار عن بعد وكشف الشذوذ (3.ipynb & Untitled1.ipynb)
# =============================================================================
with tab_satellite:
    st.header("🛰️ الاستشعار عن بعد وكشف الشذوذ الأثري الصحراوي")
    st.write("رصد وتتبع الشواهد الأثرية المدفونة عبر النطاقات الطيفية للقمر الصناعي Sentinel-2، ومؤشر التباين الهيكلي للأساسات والرطوبة (ANDI).")

    sub_mode = st.radio(
        "اختر نمط التشغيل:",
        ["محاكاة طيفية تفاعلية فورية (Interactive Simulation)", "استعلام حي من قمر Sentinel-2 الحقيقي (Planetary Computer STAC)"],
        horizontal=True
    )

    # -------------------------------------------------------------
    # نمط 1: المحاكاة الطيفية التفاعلية الفورية (Untitled1.ipynb)
    # -------------------------------------------------------------
    if sub_mode.startswith("محاكاة"):
        st.subheader("🎮 محاكاة تفاعلية: كشف الأساسات والمدافن والأفلاج القديمة")
        st.caption("نمذجة بيئة صحراوية رملية مع شواهد مدفونة (أساسات سور مستطيل، مدافن ركامية Tumuli، وقناة فلج قديم)")

        col_sim_ctrl, col_sim_view = st.columns([1, 2], gap="large")

        with col_sim_ctrl:
            st.markdown("#### 🎛️ معايير خوارزمية الرؤية الحاسوبية:")
            sim_sensitivity = st.slider("حساسية الكشف (Sensitivity):", min_value=0.05, max_value=0.40, value=0.18, step=0.01)
            sim_min_area = st.slider("الحد الأدنى للمساحة (Min Area Pixels):", min_value=10, max_value=200, value=30, step=5)
            sim_blur = st.slider("حجم مرشح التنعيم وتصفية الضوضاء (Blur Kernel):", min_value=1, max_value=15, value=5, step=2)

        # Synthetic generator function from Untitled1.ipynb
        def generate_synthetic_scene():
            np.random.seed(42)
            size = 400
            base_sand = np.random.normal(0.65, 0.05, (size, size))
            sand_dunes = np.sin(np.linspace(0, 10, size))[:, None] * 0.08
            soil_background = np.clip(base_sand + sand_dunes, 0.2, 0.9)

            red_band = soil_background.copy()
            green_band = soil_background * 0.85
            blue_band = soil_background * 0.70
            nir_band = soil_background * 0.90

            # 1. Buried rectangular wall foundations
            rr, cc = np.meshgrid(np.arange(size), np.arange(size))
            wall_mask = ((rr > 80) & (rr < 220) & ((cc == 80) | (cc == 220))) | \
                        ((cc > 80) & (cc < 220) & ((rr == 80) | (rr == 220)))
            wall_mask = cv2.dilate(wall_mask.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
            red_band[wall_mask] += 0.18
            nir_band[wall_mask] -= 0.12

            # 2. Circular cairn burials
            cairn_centers = [(150, 320), (300, 120), (320, 290)]
            for cy, cx in cairn_centers:
                dist_sq = (rr - cy)**2 + (cc - cx)**2
                cairn_mask = dist_sq < 14**2
                red_band[cairn_mask] += 0.22
                nir_band[cairn_mask] -= 0.15

            # 3. Falaj paleochannel
            falaj_curve = (np.sin(np.linspace(0, 3, size)) * 50 + 260).astype(int)
            for r in range(size):
                c = falaj_curve[r]
                if 0 <= c < size:
                    falaj_mask = (abs(cc - c) < 3) & (rr == r)
                    nir_band[falaj_mask] += 0.15
                    red_band[falaj_mask] -= 0.08

            rgb = (np.stack([np.clip(red_band, 0, 1),
                             np.clip(green_band, 0, 1),
                             np.clip(blue_band, 0, 1)], axis=-1) * 255).astype(np.uint8)

            return rgb, red_band, nir_band

        rgb_sc, b_red_s, b_nir_s = generate_synthetic_scene()
        
        # Calculate ANDI
        andi_s = (b_red_s - b_nir_s) / (b_red_s + b_nir_s + 1e-6)
        andi_norm_s = cv2.normalize(andi_s, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        k_s = sim_blur if sim_blur % 2 == 1 else sim_blur + 1
        blurred_s = cv2.GaussianBlur(andi_norm_s, (k_s, k_s), 0)
        thresh_val_s = int(255 * (1.0 - sim_sensitivity))
        _, thresh_s = cv2.threshold(blurred_s, thresh_val_s, 255, cv2.THRESH_BINARY)
        contours_s, _ = cv2.findContours(thresh_s, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        overlay_s = rgb_sc.copy()
        det_cnt = 0
        for cnt in contours_s:
            if cv2.contourArea(cnt) > sim_min_area:
                det_cnt += 1
                x, y, w, h = cv2.boundingRect(cnt)
                cv2.rectangle(overlay_s, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(overlay_s, f"#{det_cnt}", (x, max(14, y - 4)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)

        with col_sim_ctrl:
            st.metric("عدد الشواهد المرصودة:", f"{det_cnt} موقع")

        with col_sim_view:
            col_v1, col_v2, col_v3 = st.columns(3)
            with col_v1:
                st.image(rgb_sc, caption="1. المشهد الفضائي الطبيعي (RGB)", use_container_width=True)
            with col_v2:
                # Apply inferno colormap
                heatmap_img = cv2.applyColorMap(andi_norm_s, cv2.COLORMAP_INFERNO)
                st.image(cv2.cvtColor(heatmap_img, cv2.COLOR_BGR2RGB), caption="2. مؤشر التباين الهيكلي (ANDI)", use_container_width=True)
            with col_v3:
                st.image(overlay_s, caption=f"3. الرصد الآلي ({det_cnt} شذوذ)", use_container_width=True)

    # -------------------------------------------------------------
    # نمط 2: بيانات قمر Sentinel-2 الحقيقي (3.ipynb)
    # -------------------------------------------------------------
    else:
        st.subheader("🛰️ الاستعلام الفعلي لقطاع مليحة الأثري بالشارقة")
        if not HAS_GEO:
            st.error("مكتبات الاستشعار عن بعد (rasterio, pystac_client, planetary_computer) غير مثبتة بالكامل في البيئة الحالية.")
        else:
            col_sat_in1, col_sat_in2 = st.columns([1, 1], gap="large")

            with col_sat_in1:
                st.markdown("**إحداثيات النطاق الجغرافي (Bounding Box):**")
                s_west = st.number_input("غرب (West Lon):", value=55.870, format="%.4f")
                s_south = st.number_input("جنوب (South Lat):", value=25.105, format="%.4f")
                s_east = st.number_input("شرق (East Lon):", value=55.910, format="%.4f")
                s_north = st.number_input("شمال (North Lat):", value=25.145, format="%.4f")
                
                max_cloud = st.slider("الحد الأقصى لنسبة الغيوم (%):", 0, 20, 5)
                
                run_real_satellite_btn = st.button("📡 جلب المشهد الفضائي وتحليله", key="btn_run_sat_real")

            with col_sat_in2:
                if run_real_satellite_btn:
                    with st.spinner("جاري الاتصال بـ Microsoft Planetary Computer والبحث عن المشاهد..."):
                        try:
                            bbox_coords = [s_west, s_south, s_east, s_north]
                            catalog = pystac_client.Client.open(
                                "https://planetarycomputer.microsoft.com/api/stac/v1",
                                modifier=pc.sign_inplace
                            )
                            search = catalog.search(
                                collections=["sentinel-2-l2a"],
                                bbox=bbox_coords,
                                datetime="2023-01-01/2026-06-01",
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
                st.subheader("🗺️ خريطة الاستكشاف الفضائي التفاعلية")
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
                        with st.spinner("جاري صياغة التقرير الجيوفيزيائي والأثري..."):
                            summary_anom = "\n".join([
                                f"- موقع #{a['id']}: إحداثيات ({a['lat']:.5f} N, {a['lon']:.5f} E) | المساحة التقديرية: {a['area_m2']} م² | قوة الشذوذ: {a['intensity']:.3f}"
                                for a in anoms[:5]
                            ])
                            prompt_sat_ai = f"""
بصفتك مستشار الاستشعار عن بعد والآثار الفضائية بهيئة الشارقة للآثار:
إليك مخرجات التحليل ��لطيفي الفضائي الحقيقي لبيانات قمر Sentinel-2 فوق موقع مليحة الأثري:
قائمة بأبرز نقاط الشذوذ الطيفي الحقيقية:
{summary_anom}

المطلوب: إعداد "تقرير استكشاف أثري تنبؤي" بصيغة Markdown يتضمن:
1. التفسير الجيوفيزيائي والأثري للشذوذ الطيفي المرصود في بيئة مليحة الصحراوية.
2. تقييم الإحداثيات المرصودة وترتيب أولويات التحقق الميداني لفرق التنقيب بالهيئة.
3. التوصيات الإجرائية المباشرة (مثل استخدام الرادار الأرضي GPR أو طائرات الدرون الحرارية عند هذه الإحداثيات قبل بدء الحفر).
"""
                            try:
                                res_sat = client.models.generate_content(
                                    model=selected_model,
                                    contents=prompt_sat_ai
                                )
                                st.session_state["sat_report_output"] = res_sat.text
                            except Exception as e:
                                st.error(f"خطأ أثناء توليد التقرير: {e}")

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
        up_wall = st.file_uploader("ارفع صورة الجدار الأثري المصاب بالشروخ:", type=["jpg", "jpeg", "png"], key="wall_file")

        # Morphology kernel slider
        kernel_sz = st.slider("حجم مرشح استخلاص الشقوق (Kernel Size):", min_value=7, max_value=31, value=17, step=2)
        thresh_crack_val = st.slider("عتبة حساسية الشق (Crack Threshold):", min_value=10, max_value=80, value=30, step=5)

        wall_img_process = None
        if up_wall:
            wall_img_process = Image.open(up_wall).convert("RGB")
        elif os.path.exists("images/17-gr9.jpg"):
            if st.checkbox("استخدام صورة تجريبية للمبنى الأثري", key="chk_wall_sample"):
                wall_img_process = Image.open("images/17-gr9.jpg").convert("RGB")

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
بص��تك مهندس ترميم وصيانة المواقع الأثرية بهيئة الشارقة للآثار:
حلل صورة الجدار المرفقة وخريطة الشروخ المستخرجة آلياً بنسبة تضرر سطحي {damage_pct}%:
أعد تقرير تقييم حالة ومخاطر إنشائية (Structural Condition Assessment) بصيغة Markdown يتضمن:
1. التشخيص المورفولوجي:
   - تحديد نوع الشروخ (شروخ إجهاد إنشائي، شروخ حرارية، أو تفتت ناجم عن الرطوبة والأملاح).
2. تصنيف درجة الخطورة والاستجابة:
   - [أخضر: مستقر] أو [أصفر: مراقبة فنائية مستمرة] أو [أحمر: تدخل هندسي عاجل].
3. خطة التدخل الوقائي الموصى بها لفريق الترميم بالهيئة لحماية المنشأة من تفاقم الأضرار.
"""
                        try:
                            overlay_pil = Image.fromarray(crack_overlay_img)
                            res_wall = client.models.generate_content(
                                model=selected_model,
                                contents=[overlay_pil, prompt_wall]
                            )
                            st.session_state["wall_report_output"] = res_wall.text
                        except Exception as e:
                            st.error(f"خطأ أثناء توليد التقرير: {e}")

        if "wall_report_output" in st.session_state:
            st.markdown(f'<div class="report-box">{st.session_state["wall_report_output"]}</div>', unsafe_allow_html=True)
            st.download_button(
                label="📥 تحميل تقرير الصيانة (Markdown)",
                data=st.session_state["wall_report_output"],
                file_name="EAMENA_Structural_Condition_Report.md",
                mime="text/markdown"
            )
        else:
            st.info("قم برفع صورة الجدار واضغط على 'توليد تقرير الصيانة' لعرض التقييم المعتمد هنا.")

# =============================================================================
# TAB 5: دليل الورشة والعرض التقديمي
# =============================================================================
with tab_guide:
    st.header("📖 دليل الورشة والعرض التقديمي التفاعلي")
    st.write("نظرة عامة على المنهجية المعتمدة في ورشة العمل والمخرجات المعيارية.")

    col_g1, col_g2 = st.columns([1, 1], gap="large")

    with col_g1:
        st.markdown("""
        ### 🎯 أهداف الورشة والمنصة:
        1. **التحول الرقمي الأثري:** الانتقال من الأرشفة اليدوية والتقليدية إلى التوثيق الآلي الدلالي المترابط.
        2. **المعايير الدولية المعتمدة:**
           - **Dublin Core Metadata:** للأرشفة القياسية للمسكوكات.
           - **Harris Matrix:** لتوثيق الطبقات والسياقات الأثرية للقطع الفخارية.
           - **EAMENA Standard:** لرصد التدهور الإنشائي وإدارة المخاطر.
        3. **التقنيات المستخدمة:**
           - رؤية حاسوبية (OpenCV & Morphological Operations).
           - استشعار عن بعد (Sentinel-2 L2A & Planetary Computer STAC).
           - ذكاء اصطناعي توليدي متعدد الوسائط (Google Gemini Multimodal API).
        """)

    with col_g2:
        st.markdown("### 🖥️ استعراض العرض التقديمي (HTML Presentation):")
        if os.path.exists("presentation.html"):
            st.success("ملف `presentation.html` متوفر وجاهز للعرض.")
            with open("presentation.html", "r", encoding="utf-8") as f:
                html_data = f.read()
            st.download_button(
                label="📥 تحميل العرض التقديمي (presentation.html)",
                data=html_data,
                file_name="presentation.html",
                mime="text/html"
            )
        else:
            st.info("ملف presentation.html غير موجود في المسار الحالي.")
