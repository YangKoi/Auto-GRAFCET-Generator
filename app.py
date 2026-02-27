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
    2. Viết mô tả quy trình chạy máy bằng tiếng Việt (càng chi tiết logic Cảm biến/Van/Động cơ càng tốt).
    3. Bấm **Tạo sơ đồ** và đợi AI xử lý.
    """)

st.title("🤖 Riken Viet - Auto GRAFCET Generator")
st.markdown("Biến mô tả ngôn ngữ tự nhiên thành Sơ đồ điều khiển tuần tự (GRAFCET) trong 5 giây!")

# ==========================================
# PROMPT KỸ THUẬT DÀNH CHO AI (SYSTEM PROMPT)
# ==========================================
SYSTEM_PROMPT = """
Bạn là một Kỹ sư Tự động hóa PLC chuyên nghiệp, bậc thầy về phương pháp GRAFCET (IEC 61131-3 SFC).
Nhiệm vụ của bạn là đọc mô tả quy trình của người dùng và chuyển nó thành mã Graphviz DOT language để vẽ sơ đồ GRAFCET.

Hãy tuân thủ NGHIÊM NGẶT quy tắc vẽ Graphviz DOT sau đây để trông giống GRAFCET nhất:
1. Chiều vẽ: rankdir=TB;
2. BƯỚC KHỞI TẠO (Initial Step): Dùng `shape=doublebox`. Ví dụ: `S0 [shape=doublebox, label="Step 0: Khởi động"];`
3. BƯỚC THƯỜNG & HÀNH ĐỘNG (Step & Action): Dùng `shape=box`. Gộp chung Hành động vào label của Bước. 
   Ví dụ: `S1 [shape=box, label="Step 1\nAction: Bật Bơm 1 & Mở Van"];`
4. CHUYỂN TIẾP (Transition): Dùng mũi tên nối giữa 2 Bước, ghi Điều kiện chuyển tiếp vào `label` của mũi tên. Dùng font đậm, màu xanh hoặc đỏ cho dễ nhìn.
   Ví dụ: `S0 -> S1 [label=" Nút nhấn START ", fontcolor="blue", penwidth=2];`
5. Nếu có rẽ nhánh (OR) hoặc vòng lặp (Loop), hãy nối đúng tên Bước.

Chỉ xuất ra MÃ DOT thuần túy, bọc trong block ```dot ... ```. KHÔNG giải thích gì thêm.
"""

# ==========================================
# KHU VỰC NHẬP LIỆU & XỬ LÝ
# ==========================================
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📝 Nhập yêu cầu bài toán (Sequence)")
    user_input = st.text_area(
        "Mô tả quy trình hoạt động của hệ thống:", 
        height=300,
        value="Khi hệ thống có điện, nằm ở Bước Khởi tạo.\nNgười dùng ấn nút START, chuyển sang Bước 1: Bật Bơm cấp nước.\nKhi Cảm biến Mức Cao (High Level) kích hoạt, chuyển sang Bước 2: Tắt Bơm cấp nước, Mở Van Xả và Bật Động cơ khuấy.\nĐợi Timer 10 giây đếm xong, chuyển sang Bước 3: Tắt Động cơ khuấy.\nKhi Cảm biến Mức Thấp (Low Level) kích hoạt, Tắt Van Xả và quay ngược lại Bước Khởi tạo để chờ chu kỳ mới."
    )
    
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
                    # 1. Cấu hình AI
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-2.5-pro') # Dùng model Pro cho logic lập trình
                    
                    # 2. Gửi lệnh cho AI
                    prompt = f"{SYSTEM_PROMPT}\n\nMô tả của người dùng:\n{user_input}"
                    response = model.generate_content(prompt)
                    
                    # 3. Trích xuất mã DOT từ kết quả của AI
                    response_text = response.text
                    dot_match = re.search(r'```dot\n(.*?)\n```', response_text, re.DOTALL)
                    
                    if dot_match:
                        dot_code = dot_match.group(1)
                        
                        # Hiển thị sơ đồ
                        st.graphviz_chart(dot_code)
                        
                        # Hiện nút xem code cho dân kỹ thuật
                        with st.expander("👀 Xem mã Graphviz DOT"):
                            st.code(dot_code, language="dot")
                    else:
                        st.error("AI không trả về đúng định dạng biểu đồ. Dưới đây là câu trả lời thô:")
                        st.write(response_text)
                        
                except Exception as e:
                    st.error(f"Đã xảy ra lỗi khi kết nối API: {e}")
