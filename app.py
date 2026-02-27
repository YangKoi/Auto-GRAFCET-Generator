import streamlit as st
import google.generativeai as genai
import graphviz
import re

# ==========================================
# CẤU HÌNH TRANG & GIAO DIỆN
# ==========================================
st.set_page_config(page_title="Riken Viet - Auto GRAFCET", layout="wide")

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Riken_Keiki_logo.svg/2560px-Riken_Keiki_logo.svg.png", width=150)
    st.markdown("### 🔑 CẤU HÌNH HỆ THỐNG")
    api_key = st.text_input("Nhập Google Gemini API Key:", type="password", help="Lấy API Key miễn phí tại Google AI Studio")
    
    st.markdown("---")
    st.markdown("### 💡 Hướng dẫn:")
    st.markdown("""
    1. Nhập API Key của bạn.
    2. Viết mô tả quy trình máy bằng tiếng Việt.
    3. Bấm **Tạo sơ đồ** và đợi AI xử lý.
    """)

st.title("🤖 Riken Viet - Auto GRAFCET Generator")
st.markdown("Biến mô tả ngôn ngữ tự nhiên thành Sơ đồ điều khiển tuần tự (GRAFCET chuẩn IEC) trong vài giây!")

# ==========================================
# PROMPT KỸ THUẬT DÀNH CHO AI (ĐÃ NÂNG CẤP CHUẨN IEC)
# ==========================================
SYSTEM_PROMPT = """
Bạn là một Kỹ sư Tự động hóa PLC chuyên nghiệp. Nhiệm vụ của bạn là đọc quy trình và viết mã Graphviz DOT language để vẽ sơ đồ GRAFCET chuẩn IEC 61131-3.

HÃY TUÂN THỦ NGHIÊM NGẶT CẤU TRÚC GRAPHVIZ DƯỚI ĐÂY ĐỂ VẼ ĐÚNG CHUẨN GRAFCET (Pháp):

1. KHUNG CƠ BẢN:
digraph G {
    rankdir=TB;
    node [fontname="Arial"];
    edge [penwidth=1.5, dir=none]; // Mặc định mũi tên ẩn, nối thẳng
    
2. BƯỚC KHỞI TẠO (Initial Step):
    S0 [shape=box, peripheries=2, width=0.5, height=0.5, fixedsize=true, label="0"];

3. BƯỚC THƯỜNG & HÀNH ĐỘNG (Nằm ngang hàng nhau):
    // Bước chỉ chứa số thứ tự
    S1 [shape=box, width=0.5, height=0.5, fixedsize=true, label="1"];
    // Hành động là ô chữ nhật nằm bên phải
    A1 [shape=box, label="Descente en\\ngrande vitesse"];
    // Ép ngang hàng và nối với nhau
    {rank=same; S1 -> A1;}

4. CHUYỂN TIẾP (Transition) - VẠCH NGANG:
    // Nút T là vạch ngang màu đen dẹt
    T1 [shape=box, style=filled, fillcolor=black, width=0.6, height=0.02, label=""];
    // Nút C là chữ chứa điều kiện
    C1 [shape=plaintext, label="Départ du cycle"];
    // Ép ngang hàng, nối tàng hình để xếp chữ ngay cạnh vạch
    {rank=same; T1 -> C1 [style=invis];}

5. LIÊN KẾT DỌC (Flow):
    S0 -> T1; 
    T1 -> S1;
    S1 -> T2;

6. VÒNG LẶP (Loop back):
    // Phải bật mũi tên khi quay lại bước đầu
    T3 -> S0 [dir=forward];
}

Hãy phân tích quy trình của người dùng và xuất ra DUY NHẤT mã DOT bọc trong block ```dot ... ```. Không giải thích gì thêm. Tuyệt đối không được sai cú pháp DOT.
"""

# ==========================================
# KHU VỰC NHẬP LIỆU & XỬ LÝ
# ==========================================
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📝 Nhập yêu cầu bài toán (Sequence)")
    # Tôi để sẵn đoạn text giống hệt bài toán "Máy khoan (Perceuse)" trong ảnh của bạn để test
    default_text = """Bắt đầu ở bước 0 (Chờ).
Khi có tín hiệu 'Départ du cycle', chuyển sang bước 1.
Ở bước 1, thực hiện hành động 'Descente en grande vitesse' (Hạ dao tốc độ cao).
Khi đạt 'Approche terminée' (Đến gần), chuyển sang bước 2.
Ở bước 2, thực hiện 'Descente en petite vitesse' (Hạ dao tốc độ chậm để khoan).
Khi 'Pièce percée' (Khoan xong), chuyển sang bước 3.
Ở bước 3, thực hiện 'Remonter la perceuse' (Rút mũi khoan lên).
Khi đạt 'Perceuse en position haute' (Mũi khoan ở vị trí trên cùng), quay lại bước 0."""
    
    user_input = st.text_area("Mô tả quy trình hoạt động của hệ thống:", height=300, value=default_text)
    generate_btn = st.button("🚀 SINH SƠ ĐỒ GRAFCET (BẰNG AI)", type="primary", use_container_width=True)

with col2:
    st.subheader("📊 Kết quả Sơ đồ (GRAFCET)")
    
    if generate_btn:
        if not api_key:
            st.error("⚠️ Vui lòng nhập Gemini API Key ở thanh Menu bên trái trước!")
        elif not user_input:
            st.warning("⚠️ Vui lòng nhập mô tả quy trình!")
        else:
            with st.spinner("🧠 AI đang phân tích logic tuần tự và biên dịch ra Graphviz..."):
                try:
                    # Cấu hình AI
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-2.5-flash') 
                    
                    # Gọi AI
                    prompt = f"{SYSTEM_PROMPT}\n\nMô tả của người dùng:\n{user_input}"
                    response = model.generate_content(prompt)
                    
                    # Lấy mã DOT
                    response_text = response.text
                    dot_match = re.search(r'```dot\n(.*?)\n```', response_text, re.DOTALL)
                    
                    if dot_match:
                        dot_code = dot_match.group(1)
                        
                        # Hiển thị biểu đồ
                        st.graphviz_chart(dot_code)
                        
                        # Xem mã nguồn
                        with st.expander("👀 Xem mã Graphviz DOT"):
                            st.code(dot_code, language="dot")
                    else:
                        st.error("AI không trả về đúng định dạng biểu đồ. Dưới đây là câu trả lời thô:")
                        st.write(response_text)
                        
                except Exception as e:
                    st.error(f"Đã xảy ra lỗi khi kết nối API: {e}")
