import cv2
import numpy as np
import streamlit as st
from PIL import Image

A4_W_MM = 210.0
A4_H_MM = 297.0


def order_points(pts):
    pts = np.asarray(pts, dtype=np.float32).reshape(4, 2)
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).ravel()
    top_left = pts[np.argmin(s)]
    bottom_right = pts[np.argmax(s)]
    top_right = pts[np.argmin(d)]
    bottom_left = pts[np.argmax(d)]
    return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)


def four_point_transform(image, pts, output_width=2480, output_height=3508):
    pts = np.asarray(pts, dtype=np.float32).reshape(4, 2)
    rect = order_points(pts)
    dst = np.array(
        [
            [0, 0],
            [output_width - 1, 0],
            [output_width - 1, output_height - 1],
            [0, output_height - 1],
        ],
        dtype=np.float32,
    )
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (output_width, output_height))
    return warped, rect, M


def contour_to_box_points(c):
    rect = cv2.minAreaRect(c)
    box = cv2.boxPoints(rect)
    return order_points(box.astype(np.float32))


def score_a4_candidate(pts, area, img_area):
    rect = order_points(pts)
    w_top = np.linalg.norm(rect[1] - rect[0])
    w_bottom = np.linalg.norm(rect[2] - rect[3])
    h_left = np.linalg.norm(rect[3] - rect[0])
    h_right = np.linalg.norm(rect[2] - rect[1])
    w = 0.5 * (w_top + w_bottom)
    h = 0.5 * (h_left + h_right)
    if min(w, h) <= 1:
        return None
    ratio = max(w, h) / min(w, h)
    a4_ratio = A4_H_MM / A4_W_MM
    ratio_err = abs(ratio - a4_ratio)
    area_frac = area / img_area
    score = area_frac - 0.8 * ratio_err
    return {
        "rect": rect,
        "score": score,
        "ratio": ratio,
        "ratio_err": ratio_err,
        "area": area,
        "area_frac": area_frac,
    }


def detect_a4_contour(image, debug=False):
    img_area = image.shape[0] * image.shape[1]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

    s = hsv[:, :, 1]
    l = lab[:, :, 0]

    gray_blur = cv2.GaussianBlur(gray, (5, 5), 0)
    l_blur = cv2.GaussianBlur(l, (5, 5), 0)

    edges1 = cv2.Canny(gray_blur, 50, 150)
    edges2 = cv2.Canny(l_blur, 40, 120)

    _, th_l_otsu = cv2.threshold(l_blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    s_inv = 255 - s
    _, th_s = cv2.threshold(s_inv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    candidate_maps = [
        edges1,
        edges2,
        th_l_otsu,
        th_s,
        cv2.bitwise_or(edges1, edges2),
        cv2.bitwise_or(th_l_otsu, th_s),
    ]

    best = None
    debug_map = None

    for candidate in candidate_maps:
        work = candidate.copy()
        work = cv2.morphologyEx(work, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8), iterations=2)
        work = cv2.dilate(work, np.ones((3, 3), np.uint8), iterations=1)

        contours, _ = cv2.findContours(work, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:50]

        for c in contours:
            area = cv2.contourArea(c)
            if area < 0.08 * img_area:
                continue

            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            candidates = []

            if len(approx) == 4 and cv2.isContourConvex(approx):
                pts = approx.reshape(4, 2).astype(np.float32)
                candidates.append(pts)

            candidates.append(contour_to_box_points(c))

            for pts in candidates:
                scored = score_a4_candidate(pts, area, img_area)
                if scored is None:
                    continue
                if scored["ratio_err"] > 0.55:
                    continue
                if scored["area_frac"] > 0.98:
                    continue
                if best is None or scored["score"] > best["score"]:
                    best = scored
                    debug_map = work.copy()

    if best is None:
        raise RuntimeError(
            "Could not detect an A4-like region. Try tighter crop, better lighting, or make sure the whole A4 sheet is visible."
        )

    return np.asarray(best["rect"], dtype=np.float32).reshape(4, 2), debug_map


def detect_objects_on_rectified_paper(rectified_img, dark_threshold=200, min_object_pixels=500, method="adaptive"):
    gray = cv2.cvtColor(rectified_img, cv2.COLOR_BGR2GRAY)

    blur_size = 201
    blur = cv2.GaussianBlur(gray, (blur_size, blur_size), 0)
    blur = np.maximum(blur, 1)

    norm_float = (gray.astype(np.float32) / blur.astype(np.float32)) * 128.0
    norm = np.clip(norm_float, 0, 255).astype(np.uint8)

    non_white_pixels_gray = int(np.sum(norm < dark_threshold))

    if method == "global":
        _, binary_mask = cv2.threshold(norm, dark_threshold, 255, cv2.THRESH_BINARY_INV)
    elif method == "otsu":
        _, binary_mask = cv2.threshold(norm, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    else:
        binary_mask = cv2.adaptiveThreshold(
            norm,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=51,
            C=5,
        )

    kernel = np.ones((3, 3), np.uint8)
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel, iterations=1)
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    clean_mask = np.zeros_like(binary_mask)
    object_count = 0
    h_img, w_img = rectified_img.shape[:2]

    for c in contours:
        area = cv2.contourArea(c)
        if area < min_object_pixels:
            continue

        x, y, w, h = cv2.boundingRect(c)
        aspect_ratio = max(w, h) / max(1, min(w, h))

        if aspect_ratio > 10:
            continue

        if area > 0.8 * (h_img * w_img):
            continue

        cv2.drawContours(clean_mask, [c], -1, 255, thickness=-1)
        object_count += 1

    covered_pixels = int(np.sum(clean_mask > 0))

    h, w = rectified_img.shape[:2]
    mm_per_pixel_x = A4_W_MM / w
    mm_per_pixel_y = A4_H_MM / h
    mm2_per_pixel = mm_per_pixel_x * mm_per_pixel_y

    covered_area_mm2 = covered_pixels * mm2_per_pixel
    covered_area_cm2 = covered_area_mm2 / 100.0

    overlay = rectified_img.copy()
    overlay[clean_mask > 0] = (0, 0, 255)
    vis = cv2.addWeighted(rectified_img, 0.7, overlay, 0.3, 0)

    return {
        "gray_image": gray,
        "normalized_gray": norm,
        "raw_non_white_pixels_gray": non_white_pixels_gray,
        "binary_mask": binary_mask,
        "clean_mask": clean_mask,
        "overlay": vis,
        "object_count": object_count,
        "covered_pixels": covered_pixels,
        "covered_area_mm2": covered_area_mm2,
        "covered_area_cm2": covered_area_cm2,
        "mm_per_pixel_x": mm_per_pixel_x,
        "mm_per_pixel_y": mm_per_pixel_y,
        "mm2_per_pixel": mm2_per_pixel,
    }


def rectify_and_measure_from_array(image_bgr, dpi=300, dark_threshold=200, min_object_pixels=100, method="adaptive"):
    corners, _ = detect_a4_contour(image_bgr)
    corners = np.asarray(corners, dtype=np.float32).reshape(4, 2)

    output_width = int(round((A4_W_MM / 25.4) * dpi))
    output_height = int(round((A4_H_MM / 25.4) * dpi))

    rectified, rect, M = four_point_transform(
        image_bgr,
        corners,
        output_width=output_width,
        output_height=output_height,
    )

    original_with_a4 = image_bgr.copy()
    cv2.polylines(original_with_a4, [rect.astype(int)], isClosed=True, color=(0, 255, 0), thickness=4)
    for i, p in enumerate(rect.astype(int)):
        cv2.circle(original_with_a4, tuple(p), 8, (0, 0, 255), -1)
        cv2.putText(
            original_with_a4,
            str(i),
            tuple(p + 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 0, 0),
            2,
        )

    objects = detect_objects_on_rectified_paper(
        rectified,
        dark_threshold=dark_threshold,
        min_object_pixels=min_object_pixels,
        method=method,
    )

    return {
        "corners": rect,
        "transform_matrix": M,
        "original_with_a4": original_with_a4,
        "rectified": rectified,
        "overlay": objects["overlay"],
        "clean_mask": objects["clean_mask"],
        "binary_mask": objects["binary_mask"],
        "gray_image": objects["gray_image"],
        "normalized_gray": objects["normalized_gray"],
        "raw_non_white_pixels_gray": objects["raw_non_white_pixels_gray"],
        "object_count": objects["object_count"],
        "covered_pixels": objects["covered_pixels"],
        "covered_area_mm2": objects["covered_area_mm2"],
        "covered_area_cm2": objects["covered_area_cm2"],
        "mm_per_pixel_x": objects["mm_per_pixel_x"],
        "mm_per_pixel_y": objects["mm_per_pixel_y"],
        "mm2_per_pixel": objects["mm2_per_pixel"],
    }


st.set_page_config(page_title="Earthworm area/mass Estimator", layout="wide")

st.image(
    "wormomatic_logo.png",
    # caption="Earthworm Area/Mass Estimator",
    width="stretch",
)

st.markdown("<h3 style='margin-top:0;'>Earthworm Area/Mass Estimator</h3>", unsafe_allow_html=True)
st.write(
    " Take a picture of earthworms on an A4 sheet. "
    " Ensure the entire A4 sheet is visible in the image for accurate measurements. "
    " Try to centre the photo close to the centre of the A4 sheet." 
    " Use good lighting for best results."
    " Turn the camera flash on to avoid strong shadows and reflections on the paper - if needed.  \n\n "
    " The app detects the A4 outline and object mask, and estimates area covered by earthworms in cm². "    
    " Adjust detection parameters in the sidebar if needed."
    " The Minimum object size (pixels) parameter can be used to exclude small debris or other noise."
)


with st.sidebar:
    st.header("Detection parameters")
    dpi = st.slider("DPI for rectification", 150, 600, 300, step=50)
    dark_threshold = st.slider("Dark threshold", 50, 250, 200, step=5)
    min_object_pixels = st.slider("Minimum object size (pixels)", 10, 2000, 500, step=10)
    method = st.selectbox("Thresholding method", ["adaptive", "global", "otsu"])

    st.markdown("---")
    st.image(
        "ukceh.png",
        caption="[UK Centre for Ecology & Hydrology](https://www.ceh.ac.uk)",
        use_column_width=True,
    )

st.subheader("Capture or upload image")
tab1, tab2 = st.tabs(["Use camera", "Upload image"])
image_bgr = None

with tab1:
    img_file_buffer = st.camera_input("Take a picture")
    if img_file_buffer is not None:
        img = Image.open(img_file_buffer).convert("RGB")
        img_rgb = np.array(img)
        image_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        st.image(img_rgb, caption="Captured image", width="stretch")

with tab2:
    uploaded = st.file_uploader("Or upload a photo", type=["jpg", "jpeg", "png"])
    if uploaded is not None:
        img = Image.open(uploaded).convert("RGB")
        img_rgb = np.array(img)
        image_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        st.image(img_rgb, caption="Uploaded image", width="stretch")

if image_bgr is not None:
    st.markdown("---")
    if st.button("Run measurement"):
        try:
            result = rectify_and_measure_from_array(
                image_bgr,
                dpi=dpi,
                dark_threshold=dark_threshold,
                min_object_pixels=min_object_pixels,
                method=method,
            )

            col1, col2, col3 = st.columns(3)
            with col1:
                st.subheader("Original with detected A4")
                st.image(
                    cv2.cvtColor(result["original_with_a4"], cv2.COLOR_BGR2RGB),
                    width="stretch",
                )
            with col2:
                st.subheader("Rectified A4 with objects")
                st.image(
                    cv2.cvtColor(result["overlay"], cv2.COLOR_BGR2RGB),
                    width="stretch",
                )
            with col3:
                st.subheader("Object mask")
                st.image(
                    result["clean_mask"],
                    caption="Binary mask of detected objects",
                    width="stretch",
                )

            st.markdown("### Measurements")
            m1, m2, m3 = st.columns(3)
            m1.metric("Number of detected objects/earthworms", int(result["object_count"]))
            m2.metric("Area covered by earthworms (cm²)", f"{result['covered_area_cm2']:.2f}")
            m3.metric("Pixels covered by earthworms", int(result["covered_pixels"]))

            st.caption(
                f"mm per pixel: x = {result['mm_per_pixel_x']:.4f}, "
                f"y = {result['mm_per_pixel_y']:.4f}"
            )

            with st.expander("Show intermediate images"):
                st.image(result["gray_image"], caption="Grayscale (rectified)", width="stretch")
                st.image(result["normalized_gray"], caption="Normalized grayscale", width="stretch")
                st.image(result["binary_mask"], caption="Raw binary mask", width="stretch")

        except Exception as e:
            st.error(f"Error during processing: {e}")
else:
    st.info("Capture or upload an image to begin.")
