import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io
import rawpy
import imageio

st.set_page_config(page_title="RE Photo Editor", page_icon="🏠", layout="wide")

st.title("🏠 Real Estate Photo Editor")
st.caption("Upload finished photos (JPEG or RAW + HDR brackets) → enhance → download")

# --- Helpers ---
def load_image(uploaded_file):
    """Load JPEG/PNG or RAW files"""
    name = uploaded_file.name.lower()
    data = uploaded_file.read()
    if name.endswith(('.cr2', '.nef', '.arw', '.dng', '.raf', '.orf', '.rw2')):
        with rawpy.imread(io.BytesIO(data)) as raw:
            rgb = raw.postprocess(use_camera_wb=True, half_size=False, no_auto_bright=False)
        return Image.fromarray(rgb)
    else:
        return Image.open(io.BytesIO(data)).convert("RGB")

def pil_to_cv2(pil_img):
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

def cv2_to_pil(cv_img):
    return Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))

def enhance(img, brightness, contrast, saturation):
    img = cv2.convertScaleAbs(img, alpha=contrast, beta=brightness)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:,:,1] = np.clip(hsv[:,:,1] * saturation, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

def auto_straighten(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 80, minLineLength=80, maxLineGap=10)
    if lines is None:
        return img
    angles = [np.degrees(np.arctan2(y2-y1, x2-x1)) for x1,y1,x2,y2 in lines[:,0] if abs(np.degrees(np.arctan2(y2-y1, x2-x1))) < 30]
    if not angles:
        return img
    angle = np.median(angles)
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

def sky_replace(img, color=(135, 206, 250)):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([90, 40, 40]), np.array([140, 255, 255]))
    mask[img.shape[0]//2:, :] = 0
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5,5), np.uint8))
    out = img.copy()
    out[mask > 0] = color
    return out

def hdr_blend(images):
    if len(images) < 2:
        return images[0]
    h, w = images[0].shape[:2]
    aligned = [cv2.resize(im, (w, h)) for im in images]
    merge = cv2.createMergeMertens()
    fused = merge.process(aligned)
    fused = np.clip(fused * 255, 0, 255).astype(np.uint8)
    return fused

# --- UI ---
uploaded_files = st.file_uploader(
    "Upload photos or HDR brackets (JPEG or RAW)",
    type=["jpg", "jpeg", "png", "webp", "cr2", "nef", "arw", "dng", "raf", "orf", "rw2"],
    accept_multiple_files=True,
    help="Supports RAW: CR2, NEF, ARW, DNG, etc. For HDR upload all brackets together."
)

if not uploaded_files:
    st.info("Drop photos above to start.")
    st.stop()

st.success(f"{len(uploaded_files)} file(s) uploaded")

mode = st.radio("Processing mode", ["Single / Batch enhance", "HDR Blend (brackets)"], horizontal=True)

with st.sidebar:
    st.header("Edit Settings")
    brightness = st.slider("Brightness", -40, 60, 15)
    contrast = st.slider("Contrast", 0.8, 1.8, 1.2)
    saturation = st.slider("Saturation", 0.7, 1.6, 1.1)
    straighten = st.checkbox("Auto straighten", True)
    sky = st.checkbox("Basic sky replace", False)
    enhance_on = st.checkbox("Apply color enhance", True)

if mode == "HDR Blend (brackets)":
    st.info("Select the bracketed exposures for one scene, then blend.")
    file_names = [f.name for f in uploaded_files]
    selected = st.multiselect("Choose exposures for this HDR blend", file_names, default=file_names[:min(3, len(file_names))])
    
    if st.button("Blend HDR") and len(selected) >= 2:
        imgs = []
        for uf in uploaded_files:
            if uf.name in selected:
                imgs.append(pil_to_cv2(load_image(uf)))
        blended = hdr_blend(imgs)
        
        if straighten:
            blended = auto_straighten(blended)
        if enhance_on:
            blended = enhance(blended, brightness, contrast, saturation)
        if sky:
            blended = sky_replace(blended)
        
        result_pil = cv2_to_pil(blended)
        st.image(result_pil, caption="HDR Blended Result", use_container_width=True)
        
        buf = io.BytesIO()
        result_pil.save(buf, format="JPEG", quality=95)
        st.download_button(
            "Download HDR Result",
            buf.getvalue(),
            file_name="hdr_blended.jpg",
            mime="image/jpeg"
        )
    else:
        st.warning("Select at least 2 exposures and click Blend HDR")

else:
    for i, uf in enumerate(uploaded_files):
        st.markdown(f"### {uf.name}")
        orig = load_image(uf)
        img = pil_to_cv2(orig)

        edited = img.copy()
        if straighten:
            edited = auto_straighten(edited)
        if enhance_on:
            edited = enhance(edited, brightness, contrast, saturation)
        if sky:
            edited = sky_replace(edited)

        edited_pil = cv2_to_pil(edited)

        c1, c2 = st.columns(2)
        with c1:
            st.image(orig, caption="Original", use_container_width=True)
        with c2:
            st.image(edited_pil, caption="Edited", use_container_width=True)

        buf = io.BytesIO()
        edited_pil.save(buf, format="JPEG", quality=92)
        st.download_button(
            f"Download {uf.name}",
            buf.getvalue(),
            file_name=f"edited_{uf.name.rsplit('.',1)[0]}.jpg",
            mime="image/jpeg",
            key=f"dl{i}"
        )
        st.divider()

st.caption("Internal tool • Supports RAW + HDR exposure fusion")
