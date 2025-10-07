import streamlit as st
from PIL import Image
import numpy as np
import pandas as pd
from streamlit_image_coordinates import streamlit_image_coordinates

# ===============================
# Setup dasar
# ===============================
st.set_page_config(page_title="🧪 Color Inspector (RGB/HEX)", layout="wide")
st.title("🧪 Color Inspector (RGB/HEX)")
st.write("Unggah gambar → klik titik untuk ambil warna → lihat grid → unduh CSV.")

# Utilitas
def contrast_text_for(hex_color: str) -> str:
    s = hex_color.lstrip("#")
    r, g, b = (int(s[i:i+2], 16) for i in (0, 2, 4))
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "white" if luminance < 0.5 else "black"

def rgb_to_hex_upper(rgb_tuple) -> str:
    r, g, b = (int(v) for v in rgb_tuple)
    return f"#{r:02X}{g:02X}{b:02X}"

# Upload
uploaded_file = st.file_uploader(
    "Tarik & letakkan gambar (PNG/JPG/JPEG) di sini",
    type=["png", "jpg", "jpeg"]
)

if not uploaded_file:
    st.info("Belum ada gambar. Unggah dulu untuk mulai inspeksi warna.")
    st.stop()

# Baca + resize otomatis (tanpa kontrol)
img = Image.open(uploaded_file).convert("RGB")

# target lebar preview ~900 (tanpa slider)
MAX_W = 900
ratio = min(1.0, MAX_W / img.width)
display_img = img.resize((int(img.width * ratio), int(img.height * ratio)))
img_array = np.asarray(display_img)  # numpy array (uint8)
height, width, _ = img_array.shape

st.caption(f"Pratinjau: **{width}×{height}px** (asli **{img.width}×{img.height}px**).")

# Layout
left, right = st.columns([2.05, 1], gap="large")

with left:
    st.subheader("Ambil Warna per Titik")
    st.write("Klik pada gambar untuk mendapatkan koordinat dan nilai warnanya.")
    coords = streamlit_image_coordinates(display_img, key="tap_color_no_controls")

    if coords is not None:
        x, y = int(coords["x"]), int(coords["y"])
        if 0 <= x < width and 0 <= y < height:
            r, g, b = (int(v) for v in img_array[y, x])  # pastikan int Python
            hex_code = rgb_to_hex_upper((r, g, b))
            st.success(f"**Koordinat:** ({x}, {y})\n\n**RGB:** ({r}, {g}, {b})\n\n**HEX:** {hex_code}")
            st.markdown(
                f"""
                <div style="
                    width:150px;height:60px;border-radius:10px;border:1px solid #bbb;
                    background:{hex_code};display:flex;align-items:center;justify-content:center;
                    font-family:monospace;font-weight:700;color:{contrast_text_for(hex_code)};">
                    {hex_code}
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Rata-rata warna (konversi ke int Python)
    st.markdown("#### 🧮 Rata-rata Warna Gambar")
    avg_rgb = tuple(map(int, np.round(img_array.reshape(-1, 3).mean(axis=0))))  # (R,G,B) -> int
    avg_hex = rgb_to_hex_upper(avg_rgb)
    r_avg, g_avg, b_avg = avg_rgb
    st.write(f"RGB: ({r_avg}, {g_avg}, {b_avg})  |  HEX: {avg_hex}")
    st.markdown(
        f"""
        <div style="
            width:150px;height:40px;border-radius:8px;border:1px solid #bbb;
            background:{avg_hex};display:flex;align-items:center;justify-content:center;
            font-family:monospace;color:{contrast_text_for(avg_hex)};">
            {avg_hex}
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    st.subheader("🎨 Grid Sampel Warna")

    # TANPA kontrol: step ditentukan otomatis agar ~40 kolom
    target_cols = 40
    step = max(4, int(round(width / target_cols)))

    ys = list(range(0, height, step))
    xs = list(range(0, width, step))

    grid_hex = []
    for y in ys:
        row = []
        for x in xs:
            r, g, b = (int(v) for v in img_array[y, x])  # pastikan int Python
            row.append(rgb_to_hex_upper((r, g, b)))
        grid_hex.append(row)

    # label selalu tampil
    x_labels = [str(x) for x in xs]
    y_labels = [str(y) for y in ys]

    df_grid = pd.DataFrame(grid_hex, index=y_labels, columns=x_labels)

    def style_cell(v: str):
        return (
            f"background-color:{v};"
            f"color:{contrast_text_for(v)};"
            "font-family:monospace;font-size:12px;text-align:center;"
        )

    st.dataframe(df_grid.style.applymap(style_cell), use_container_width=True)
    st.caption(f"Grid warna otomatis • sampling tiap **{step}px** • Kolom = X, Baris = Y.")

    # Export CSV (format panjang) — paksa int Python agar bersih
    coords_long = [(x, y) for y in ys for x in xs]
    rgb_long = [tuple(int(v) for v in img_array[y, x]) for (x, y) in coords_long]
    hex_long = [rgb_to_hex_upper(rgb) for rgb in rgb_long]

    df_long = pd.DataFrame(coords_long, columns=["X", "Y"])
    df_long["R"], df_long["G"], df_long["B"] = zip(*rgb_long)
    df_long["HEX"] = hex_long

    base_name = uploaded_file.name.rsplit(".", 1)[0]
    csv_bytes = df_long.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Unduh CSV warna",
        data=csv_bytes,
        file_name=f"{base_name}_samples_step{step}.csv",
        mime="text/csv",
    )