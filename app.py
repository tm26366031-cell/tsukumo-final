import streamlit as st

# ⚠️ 最も重要な注意点: st.set_page_config は常にコードの最上部に1回だけ配置する必要があります。
st.set_page_config(page_title="TSUKUMO", page_icon="♻️", layout="wide")

import cv2
import numpy as np
try:
    import tensorflow as tf
    MODEL_ENABLED = True
except Exception:
    tf = None
    MODEL_ENABLED = False
from PIL import Image
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import LocateControl
from streamlit_option_menu import option_menu
from streamlit_calendar import calendar
import datetime
import base64
import random
import os
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# --- TSUKUMO CSS ---
css_path = BASE_DIR / "style.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as css_file:
        st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)
else:
    st.warning(f"CSS file not found: {css_path.name}")

# --- 1. データ読み込みとキャッシング ---
@st.cache_data
def load_garbage_data():
    try:
        # Excelファイルの読み込みを試みる
        df = pd.read_excel(BASE_DIR / "shinjuku_garbage_schedule_2026.xlsx", sheet_name='収集日一覧')
        df_cleaned = df.iloc[4:].copy()
        df_cleaned.columns = ['Empty', 'Region', 'Recyclables', 'Burnable', 'Metal_Glass_Ceramic', 'Office']
        df_cleaned = df_cleaned.drop(columns=['Empty']).dropna(subset=['Region'])
        return df_cleaned
    except Exception as e:
        # ファイルがない場合はサンプルデータを表示
        return pd.DataFrame({
            "Region": ["新宿1丁目 🐼", "新宿2丁目 🦊", "西新宿1丁目 🐰"],
            "Recyclables": ["月曜日", "火曜日", "水曜日"],
            "Burnable": ["火・金", "水・土", "木・日"],
            "Metal_Glass_Ceramic": ["第1・第3水曜", "第2木曜", "第1・第3金曜"],
            "Office": ["-", "-", "-"]
        })

@st.cache_data
def load_shinjuku_csv():
    try:
        return pd.read_csv(BASE_DIR / "shinjuku_nann.csv", encoding="cp932")
    except Exception as e:
        return pd.DataFrame({
            'Item_Name': ['新宿御苑 🌸', 'ロボットレストラン 🤖'],
            'lat': [35.6852, 35.6943],
            'lon': [139.7101, 139.7028]
        })

df_garbage = load_garbage_data()
df_shinjuku = load_shinjuku_csv()


# --- 2. 言語ディクショナリの設定 (日本語に翻訳) ---
languages = {
    "日本語": {
        "title": "📷 画像スキャナー",
        "sidebar": "ユーザー情報",
        "name": "お名前",
        "age": "年齢",
        "address": "ご住所",
        "btn": "情報を保存する ✨",
        "radio": "写真の選択方法",
        "options": ["カメラで撮影する 📸", "画像をアップロードする 📂"],
        "success": "情報が保存されました。",
        "cam_caption": "カメラで写真を撮影してください",
        "file_caption": "画像をアップロードしてください",
        "result_title": "📊 ごみ分別判定結果",
        "welcome": "さん、ご利用ありがとうございます！",
        "menu_home": "ホーム",
        "menu_camera": "画像スキャナー",
        "menu_info": "ごみ検索・一覧",
        "menu_map": "収集マップ",
        "menu_calendar": "収集カレンダー",
        "menu_guide": "ごみの出し方",
        "menu_contact": "お問い合わせ",
        "menu_faq": "よくある質問",
        "menu_tips": "分別のポイント",
        "hero_sub": "新宿区ごみ分別サポートアプリ",
        "hero_text": "新宿区の住民や来訪者が、ごみを正しく分別できるようにサポートします。",
        "card_search": "ごみ検索",
        "card_search_text": "分別区分、収集日、正しい出し方を確認できます。",
        "card_scanner": "画像スキャナー",
        "card_scanner_text": "写真を撮影またはアップロードして、ごみの種類を確認できます。",
        "card_calendar": "収集日ガイド",
        "card_calendar_text": "地域ごとの収集日とルールを確認できます。",
        "list_text": "新宿区の地域別ごみ情報一覧です。",
        "map_title": "ごみ収集マップ",
        "select_area": "地域・地区を選択してください",
        "schedule": "ごみ収集スケジュール",
        "resource": "資源ごみ",
        "burnable": "可燃ごみ",
        "nonburnable": "不燃ごみ・金属・ガラス・陶器",
        "office": "管轄清掃事務所",
        "guide_title": "新宿区のごみの出し方ガイド",
        "guide_text": "各種案内画像は以下から確認できます。",
        "image_missing": "imagesフォルダが見つかりません。",
        "calendar_title": "新宿区ごみ収集カレンダー 2026",
        "calendar_text": "お住まいの地域を選択して、収集日を確認しましょう。",
        "select_region": "お住まいの地域・町名を選択してください",
        "contact_title": "お問い合わせ先一覧（新宿区）",
        "faq_title": "新宿区ごみ分別・処分 FAQ",
        "tips_title": "正しいごみ排出方法の心得",
        "tips_text": "ルールを守って、美しく住みやすい新宿区を作りましょう。",
        "uploaded_caption": "アップロードされた画像",
        "result": "判定結果",
        "all_results": "すべての判定結果を見る",
        "demo_warning": "モデルファイルが見つからないため、デモモードで表示しています。"
    },
    "English": {
        "title": "📷 Image Scanner",
        "sidebar": "User Information",
        "name": "Name",
        "age": "Age",
        "address": "Address",
        "btn": "Save Information ✨",
        "radio": "Choose an image source",
        "options": ["Take a photo 📸", "Upload an image 📂"],
        "success": "Information saved successfully.",
        "cam_caption": "Take a photo",
        "file_caption": "Upload an image",
        "result_title": "📊 Waste Sorting Result",
        "welcome": ", thank you for using TSUKUMO!",
        "menu_home": "Home",
        "menu_camera": "Image Scanner",
        "menu_info": "Waste Search & List",
        "menu_map": "Collection Map",
        "menu_calendar": "Collection Calendar",
        "menu_guide": "Disposal Guide",
        "menu_contact": "Contact",
        "menu_faq": "FAQ",
        "menu_tips": "Recycling Tips",
        "hero_sub": "Shinjuku Waste Sorting Assistant",
        "hero_text": "Helping residents and visitors sort waste correctly in Shinjuku Ward.",
        "card_search": "Waste Search",
        "card_search_text": "Check the category, collection day, and correct disposal method.",
        "card_scanner": "Image Scanner",
        "card_scanner_text": "Take or upload a photo to check the waste category.",
        "card_calendar": "Collection Guide",
        "card_calendar_text": "Check area-specific collection days and local rules.",
        "list_text": "Waste information for different areas of Shinjuku Ward.",
        "map_title": "Waste Collection Map",
        "select_area": "Select an area or district",
        "schedule": "Waste Collection Schedule",
        "resource": "Recyclables",
        "burnable": "Burnable Waste",
        "nonburnable": "Non-burnable, Metal, Glass and Ceramic Waste",
        "office": "Cleaning Office",
        "guide_title": "Shinjuku Waste Disposal Guide",
        "guide_text": "Please check the guide images below.",
        "image_missing": "The images folder was not found.",
        "calendar_title": "Shinjuku Waste Collection Calendar 2026",
        "calendar_text": "Select your area to check collection days.",
        "select_region": "Select your area or town",
        "contact_title": "Contact Information (Shinjuku Ward)",
        "faq_title": "Shinjuku Waste Sorting FAQ",
        "tips_title": "Recycling and Disposal Tips",
        "tips_text": "Follow the rules and help keep Shinjuku clean and comfortable.",
        "uploaded_caption": "Selected image",
        "result": "Result",
        "all_results": "Show all results",
        "demo_warning": "The model file was not found, so demo mode is being used."
    }
}

with st.sidebar:
    language_choice = st.selectbox(
        "🌐 Language / 言語",
        ["日本語", "English"],
        key="language_choice"
    )

lang = languages[language_choice]

# --- 3. 画像分類モデルの読み込み ---
MODEL_PATH = BASE_DIR / "model_unquant.tflite"
LABELS_PATH = BASE_DIR / "labels.txt"

@st.cache_resource
def load_model():
    """Load the local TFLite model and labels without hiding the real error."""
    if not MODEL_ENABLED:
        return None, [], "TensorFlow could not be imported. Use Python 3.12 and install tensorflow."

    if not MODEL_PATH.exists():
        return None, [], f"Model file not found: {MODEL_PATH}"

    if not LABELS_PATH.exists():
        return None, [], f"Labels file not found: {LABELS_PATH}"

    try:
        interpreter = tf.lite.Interpreter(model_path=str(MODEL_PATH))
        interpreter.allocate_tensors()

        with open(LABELS_PATH, "r", encoding="utf-8") as f:
            loaded_labels = [line.strip() for line in f if line.strip()]

        output_shape = interpreter.get_output_details()[0]["shape"]
        class_count = int(output_shape[-1])
        if len(loaded_labels) != class_count:
            return (
                None,
                [],
                f"Label count mismatch: model has {class_count} classes, "
                f"but labels.txt has {len(loaded_labels)} labels.",
            )

        return interpreter, loaded_labels, None
    except Exception as exc:
        return None, [], f"{type(exc).__name__}: {exc}"

interpreter, labels, model_error = load_model()
if interpreter is not None:
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

# --- 画像判定後に表示する分別詳細 ---
WASTE_DETAILS = {
    "ペットボトル": {
        "category": "資源ごみ / Recyclable waste",
        "collection": "地域の資源回収日 / Local recyclable collection day",
        "how_to": "キャップとラベルを外し、中をすすいで、できるだけつぶして出してください。 / Remove the cap and label, rinse the bottle, and flatten it when possible.",
        "note": "汚れが落ちない場合は可燃ごみになることがあります。 / Heavily soiled bottles may need to be disposed of as burnable waste.",
    },
    "紙": {
        "category": "資源ごみ / Recyclable waste",
        "collection": "地域の古紙回収日 / Local paper collection day",
        "how_to": "新聞、雑誌、紙箱などを種類ごとに分け、ひもで束ねてください。 / Separate by paper type and tie bundles with string.",
        "note": "濡れた紙、油で汚れた紙、感熱紙などは可燃ごみです。 / Wet, oily, or thermal paper should be disposed of as burnable waste.",
    },
    "金属管": {
        "category": "金属・陶器・ガラスごみ / Metal, ceramic and glass waste",
        "collection": "地域の金属・陶器・ガラス回収日 / Local non-burnable collection day",
        "how_to": "中身を完全に空にし、危険がない状態で透明または半透明の袋に入れてください。 / Empty the item completely and place it safely in a transparent or semi-transparent bag.",
        "note": "スプレー缶やカセットボンベは別のルールがあるため、必ず中身を使い切ってください。 / Spray cans and gas cartridges require special handling; make sure they are completely empty.",
    },
    "グラス": {
        "category": "びん・ガラス類 / Glass waste",
        "collection": "地域の資源または金属・陶器・ガラス回収日 / Local glass collection day",
        "how_to": "飲料びんはキャップを外してすすぎ、割れたガラスは紙などで包んで「危険」と表示してください。 / Rinse bottles after removing caps; wrap broken glass and label it as dangerous.",
        "note": "耐熱ガラス、鏡、割れたコップは通常のびん回収には出せません。 / Heat-resistant glass, mirrors, and broken cups are not accepted with ordinary bottles.",
    },
    "段ボール": {
        "category": "資源ごみ / Recyclable waste",
        "collection": "地域の古紙回収日 / Local paper collection day",
        "how_to": "伝票やテープを外し、平らに折りたたんで、ひもで十字に束ねてください。 / Remove labels and tape, flatten the cardboard, and tie it securely with string.",
        "note": "油や食品でひどく汚れた段ボールは可燃ごみです。 / Cardboard heavily soiled with oil or food should be burnable waste.",
    },
    "粗大": {
        "category": "粗大ごみ / Bulky waste",
        "collection": "事前申込による指定日 / Collection date assigned after reservation",
        "how_to": "粗大ごみ受付センターへ申し込み、処理券を購入して貼り、指定された日時・場所に出してください。 / Apply through the bulky-waste reception center, buy and attach a disposal ticket, then place the item at the assigned location and time.",
        "note": "一辺がおおむね30cmを超える家庭用品は粗大ごみになる場合があります。 / Household items with a side longer than about 30 cm may be treated as bulky waste.",
    },
    "プラスチック": {
        "category": "プラスチック資源または可燃ごみ / Plastic resource or burnable waste",
        "collection": "地域のプラスチック資源回収日 / Local plastic-resource collection day",
        "how_to": "中身を使い切り、汚れを落としてから透明または半透明の袋に入れてください。 / Empty and clean the item, then place it in a transparent or semi-transparent bag.",
        "note": "汚れが落ちないものや、プラスチック以外の部分が多いものは可燃ごみになることがあります。 / Items that cannot be cleaned or contain substantial non-plastic parts may be burnable waste.",
    },
}

def normalize_model_label(raw_label):
    """Teachable Machine labels such as '0 ペットボトル/pet bottle' are normalized."""
    label = str(raw_label).strip()
    if label and label.split(maxsplit=1)[0].isdigit():
        label = label.split(maxsplit=1)[1] if len(label.split(maxsplit=1)) > 1 else label
    return label.split("/")[0].strip()

def show_waste_details(raw_label):
    key = normalize_model_label(raw_label)
    details = WASTE_DETAILS.get(key)
    if not details:
        st.info("この品目の詳しい分別情報は現在準備中です。 / Detailed sorting information for this item is being prepared.")
        return

    st.markdown("### ♻️ 分別の詳しい情報 / Disposal Details")
    st.markdown(f"**分類 / Category:** {details['category']}")
    st.markdown(f"**収集日 / Collection:** {details['collection']}")
    st.markdown(f"**出し方 / How to dispose:** {details['how_to']}")
    st.warning(f"💡 **注意 / Note:** {details['note']}")

# --- 4. サイドバー ユーザー情報 ---
with st.sidebar:
    st.header(lang["sidebar"])
    name = st.text_input(lang["name"], placeholder="例：パンダ 🐼")
    age = st.number_input(lang["age"], min_value=1, max_value=100, value=20)
    address = st.text_area(lang["address"])
    if st.button(lang["btn"]):
        st.success(lang["success"])

# --- 5. サイドバー ナビゲーションメニュー ---
with st.sidebar:
    st.markdown(f"""
    <div style="padding:8px 6px 2px;">
      <div style="font-size:28px;font-weight:800;color:#a3e635;">♻️ TSUKUMO</div>
      <div style="font-size:13px;color:#cbd5e1;margin-top:4px;">{lang["hero_sub"]}</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    selected = option_menu(
        menu_title=None,
        options=[
            lang["menu_home"],
            lang["menu_camera"],
            lang["menu_info"],
            lang["menu_map"],
            lang["menu_calendar"],
            lang["menu_guide"],
            lang["menu_contact"],
            lang["menu_faq"],
            lang["menu_tips"]
        ],
        icons=[
            "house", "camera", "search", "map", "calendar",
            "trash", "telephone", "question-circle", "recycle"
        ],
        default_index=0,
        styles={
            "container": {
                "padding": "0",
                "background-color": "#101827",
            },
            "icon": {
                "color": "#84CC16",
                "font-size": "19px",
            },
            "nav-link": {
                "color": "#F8FAFC",
                "font-size": "15px",
                "text-align": "left",
                "margin": "5px 0",
                "padding": "11px 12px",
                "border-radius": "10px",
                "white-space": "nowrap",
                "--hover-color": "#1F2937",
            },
            "nav-link-selected": {
                "background-color": "#22C55E",
                "color": "white",
                "font-weight": "700",
            },
        },
    )

# --- 7. メインコンテンツ ---

# --- [ホーム] ---
if selected == lang["menu_home"]:
    st.markdown(f"""
    <div class="hero">
      <h1>♻️ TSUKUMO</h1>
      <h3>{lang['hero_sub']}</h3>
      <p>{lang['hero_text']}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="card"><h2>🔍 {lang["card_search"]}</h2><p>{lang["card_search_text"]}</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="card"><h2>📷 {lang["card_scanner"]}</h2><p>{lang["card_scanner_text"]}</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="card"><h2>📅 {lang["card_calendar"]}</h2><p>{lang["card_calendar_text"]}</p></div>', unsafe_allow_html=True)

# --- [画像分別カメラ] ---
elif selected == lang["menu_camera"]:
    st.title(lang["title"])
    choice = st.radio(lang["radio"], lang["options"])

    image = None
    if choice == lang["options"][0]: 
        image = st.camera_input(lang["cam_caption"])
    else: 
        image = st.file_uploader(lang["file_caption"], type=['jpg', 'jpeg', 'png'])

    if image:
        img_data = Image.open(image).convert('RGB')
        img_array = np.array(img_data)
        
        st.image(image, caption=lang["uploaded_caption"], width=400)
        st.subheader(lang["result_title"])

        if interpreter is not None:
            try:
                input_info = input_details[0]
                input_shape = input_info["shape"]
                input_height = int(input_shape[1])
                input_width = int(input_shape[2])
                input_dtype = input_info["dtype"]

                processed_img = cv2.resize(img_array, (input_width, input_height))
                processed_img = np.expand_dims(processed_img, axis=0)

                if input_dtype == np.float32:
                    processed_img = processed_img.astype(np.float32)
                    processed_img = (processed_img / 127.5) - 1.0
                else:
                    processed_img = processed_img.astype(input_dtype)

                interpreter.set_tensor(input_info["index"], processed_img)
                interpreter.invoke()
                prediction = interpreter.get_tensor(output_details[0]["index"])[0]

                highest_match_index = int(np.argmax(prediction))
                predicted_label = labels[highest_match_index]
                predicted_confidence = float(prediction[highest_match_index]) * 100

                st.success(
                    f"{lang['result']}: **{predicted_label}** "
                    f"({predicted_confidence:.1f}%)"
                )
                st.progress(max(0.0, min(predicted_confidence / 100.0, 1.0)))

                with st.expander(lang["all_results"]):
                    for i, label in enumerate(labels):
                        conf = float(prediction[i]) * 100
                        status = "✅" if i == highest_match_index else "▫️"
                        st.write(f"{status} {label} ({conf:.2f}%)")
                        st.progress(max(0.0, min(conf / 100.0, 1.0)))

                show_waste_details(predicted_label)
            except Exception as prediction_error:
                st.error("画像判定に失敗しました。 / Image classification failed.")
                st.exception(prediction_error)
        else:
            st.error("モデルを読み込めませんでした。 / The model could not be loaded.")
            st.code(model_error or "Unknown model-loading error")
            st.info("Place model_unquant.tflite and labels.txt beside app.py in GitHub, and set Streamlit Cloud to Python 3.12.")

        if name:
            st.info(f"💖 {name} {lang['welcome']}")

# --- [新宿区情報] ---
elif selected == lang["menu_info"]:
    st.title("🏙️ " + lang["menu_info"])
    st.write(lang["list_text"])
    st.dataframe(df_shinjuku, use_container_width=True)

#---------------- マップ ----------------
elif selected == lang["menu_map"]:
    st.title("🗺️ " + lang["map_title"])
    
    # 1. df_map を定義
    df_map = df_garbage.copy()
    
    # カラム名を設定
    df_map.columns = ["area", "resource_day", "burnable_day", "nonburnable_day", "office"]
    
    # サンプル用の緯度・経度を設定
    base_lat = 35.6938
    base_lon = 139.7035
    df_map["lat"] = [base_lat + (i % 10) * 0.001 for i in range(len(df_map))]
    df_map["lon"] = [base_lon + (i % 10) * 0.001 for i in range(len(df_map))]

    # 地域リストの取得と選択ボックスの配置
    areas = sorted(df_map["area"].unique())
    selected_area = st.selectbox(lang["select_area"], areas)

    selected_data = df_map[df_map["area"] == selected_area].iloc[0]

    # 地図の初期化
    m = folium.Map(location=[selected_data["lat"], selected_data["lon"]], zoom_start=15, tiles="CartoDB positron")

    # マーカーの追加
    folium.Marker(
        location=[selected_data["lat"], selected_data["lon"]],
        popup=f"<b>{selected_area}</b>",
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(m)

    # 地図の表示
    st_folium(m, use_container_width=True, height=400)

    # 詳細情報の表示
    st.subheader(f"📍 {selected_area} - {lang['schedule']}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"♻️ **{lang['resource']}:** {selected_data['resource_day']}")
        st.warning(f"🔥 **{lang['burnable']}:** {selected_data['burnable_day']}")
    with col2:
        st.error(f"🧱 **{lang['nonburnable']}:** {selected_data['nonburnable_day']}")
        st.success(f"🏢 **{lang['office']}:** {selected_data['office']}")
    
# --- [新宿区のごみの出し方] ---
elif selected == lang["menu_guide"]:
    st.title("🏙️ " + lang["guide_title"])
    st.write(lang["guide_text"])

    # images フォルダ内の画像ファイルを検索
    image_folder = BASE_DIR / "images"
    if image_folder.exists():
        image_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        image_files.sort()

        # 1行に3枚ずつ画像を表示
        cols_per_row = 3
        for i in range(0, len(image_files), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(image_files):
                    img_path = image_folder / image_files[i + j]
                    with cols[j]:
                        st.image(img_path, use_container_width=True)
                        st.caption(image_files[i + j])
    else:
        st.info(lang["image_missing"])

# --- [カレンダー] ---
elif selected == lang["menu_calendar"]:
    st.markdown(f"<h2 style='text-align: center; color: #FF6B8B;'>🐼 {lang['calendar_title']} 🐼</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #777;'>{lang['calendar_text']}</p>", unsafe_allow_html=True)
    st.write("---")

    regions = df_garbage['Region'].tolist()
    selected_region = st.selectbox("📍 " + lang["select_region"], regions)

    region_info = df_garbage[df_garbage['Region'] == selected_region].iloc[0]
    
    # 曜日マッピングの処理
    day_mapping_jap = {'月': 0, '火': 1, '水': 2, '木': 3, '金': 4, '土': 5, '日': 6,
                       'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6}

    def generate_events_for_2026(info):
        events = []
        start_date = datetime.date(2026, 1, 1)
        end_date = datetime.date(2026, 12, 31)
        delta = datetime.timedelta(days=1)
        
        current_date = start_date
        while current_date <= end_date:
            weekday_num = current_date.weekday()
            
            # --- ♻️ 資源ごみ ---
            recyclable_day = str(info['Recyclables']).strip()
            if recyclable_day in day_mapping_jap and weekday_num == day_mapping_jap[recyclable_day]:
                events.append({
                    "title": "♻️ 資源ごみ",
                    "start": current_date.isoformat(),
                    "backgroundColor": "#B3E5FC", 
                    "borderColor": "#B3E5FC",
                    "textColor": "#0D47A1"
                })
                
            # --- 🔥 可燃ごみ ---
            burnable_days = [d.strip() for d in str(info['Burnable']).split('・')]
            for bd in burnable_days:
                if bd in day_mapping_jap and weekday_num == day_mapping_jap[bd]:
                    events.append({
                        "title": "🔥 可燃ごみ",
                        "start": current_date.isoformat(),
                        "backgroundColor": "#FFCDD2", 
                        "borderColor": "#FFCDD2",
                        "textColor": "#B71C1C"
                    })
                    
            # --- 🏺 金属・ガラス・陶器・不燃ごみ ---
            mgc_info = str(info['Metal_Glass_Ceramic']).strip()
            if "・" in mgc_info and any(ch in mgc_info for ch in day_mapping_jap.keys()):
                weeks_part = mgc_info[:-1] 
                target_day_jap = mgc_info[-1] 
                try:
                    target_weeks = [int(w) for w in weeks_part.split('・') if w.isdigit()]
                    if target_day_jap in day_mapping_jap and weekday_num == day_mapping_jap[target_day_jap]:
                        nth_weekday = (current_date.day - 1) // 7 + 1
                        if nth_weekday in target_weeks:
                            events.append({
                                "title": "🏺 金属・ガラス・陶器",
                                "start": current_date.isoformat(),
                                "backgroundColor": "#FFE082", 
                                "borderColor": "#FFE082",
                                "textColor": "#E65100"
                            })
                except:
                    pass
            elif any(ch in mgc_info for ch in day_mapping_jap.keys()):
                parts = mgc_info.split()
                if len(parts) >= 2:
                    try:
                        target_week = int(parts[0])
                        target_day_jap = parts[1]
                        if target_day_jap in day_mapping_jap and weekday_num == day_mapping_jap[target_day_jap]:
                            nth_weekday = (current_date.day - 1) // 7 + 1
                            if nth_weekday == target_week:
                                events.append({
                                    "title": "🏺 金属・ガラス・陶器",
                                    "start": current_date.isoformat(),
                                    "backgroundColor": "#FFE082", 
                                    "borderColor": "#FFE082",
                                    "textColor": "#E65100"
                                })
                    except:
                        pass
                        
            current_date += delta
        return events

    calendar_events = generate_events_for_2026(region_info)

    calendar_options = {
        "editable": False,
        "selectable": True,
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek",
        },
        "initialView": "dayGridMonth",
        "initialDate": "2026-07-01",
    }

    state = calendar(events=calendar_events, options=calendar_options)

    st.info(f"""
    🗺️ **選択された地域:** {selected_region}  
    ♻️ **資源ごみ:** 毎週 ({region_info['Recyclables']})  
    🔥 **可燃ごみ:** 毎週 ({region_info['Burnable']})  
    🏺 **金属・ガラス・陶器:** 毎月 ({region_info['Metal_Glass_Ceramic']})  
    """)

    if state.get("selectInfo"):
        selected_date = state['selectInfo']['startStr'].split("T")[0]
        st.balloons()
        st.success(f"💖 選択された日付は **{selected_date}** です。ルールを守って正しくごみを分別しましょう ✨")

    st.write("---")
    st.markdown("""
    <h2 style='color:#ff65a3; font-family:"M PLUS Rounded 1c"; font-size:1.8rem; text-align:center;'>
        🔮 マジカルリマインダー通知アラーム (Magical Alarms)
    </h2>
    <p style='text-align:center; color:#708090; font-size:0.95rem; margin-bottom:20px;'>
        ごみの種類に合わせて、リマインダー通知時間を自由にカスタム設定できます ✨
    </p>
    """, unsafe_allow_html=True)
    
    burnable_info = str(region_info['Burnable'])
    resource_info = str(region_info['Recyclables'])
    nonburnable_info = str(region_info['Metal_Glass_Ceramic'])

    tab1, tab2, tab3 = st.tabs(["🔥 可燃ごみ", "♻️ 資源ごみ", "🚫 金属・ガラス・陶器・不燃ごみ"])
    
    with tab1:
        st.markdown(f"<h4 style='color:#ff4d4d;'>🔥 可燃ごみのアラーム設定 ({burnable_info})</h4>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            b_time = st.time_input("⏰ 通知時間 (可燃ごみ)", datetime.datetime.now().time(), key="b_time")
        with col2:
            b_day = st.selectbox("📅 通知タイミング", ["収集日の当日の朝", "収集日の前日の夜"], key="b_day")
        
        b_on = st.toggle("⭐ 可燃ごみのアラームを有効にする", key="b_on")
        if b_on:
            st.toast("🔥 可燃ごみアラームを設定しました！")
            st.success(f"✨ **【{b_day} の {b_time.strftime('%H:%M')}】** に可燃ごみの準備を優しくリマインドします！ 🎀")

    with tab2:
        st.markdown(f"<h4 style='color:#2b9348;'>♻️ 資源ごみのアラーム設定 ({resource_info})</h4>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            r_time = st.time_input("⏰ 通知時間 (資源ごみ)", datetime.datetime.now().time(), key="r_time")
        with col2:
            r_day = st.selectbox("📅 通知タイミング", ["収集日の当日の朝", "収集日の前日の夜"], key="r_day", index=0)
            
        r_on = st.toggle("⭐ 資源ごみのアラームを有効にする", key="r_on")
        if r_on:
            st.toast("♻️ 資源ごみアラームを設定しました！")
            st.success(f"✨ **【{r_day} の {r_time.strftime('%H:%M')}】** にボトルや缶の準備をするよう、環境の妖精がリマインドします！ 🌱")

    with tab3:
        st.markdown(f"<h4 style='color:#0369a1;'>🚫 不燃ごみ・金属・ガラス等のアラーム設定 ({nonburnable_info})</h4>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            n_time = st.time_input("⏰ 通知時間", datetime.datetime.now().time(), key="n_time")
        with col2:
            n_day = st.selectbox("📅 通知タイミング", ["収集日の当日の朝", "収集日の前日の夜"], key="n_day", index=0)
            
        n_on = st.toggle("⭐ アラームを有効にする", key="n_on")
        if n_on:
            st.toast("🚫 不燃ごみ等のアラームを設定しました！")
            st.success(f"✨ **【{n_day} の {n_time.strftime('%H:%M')}】** に、割れ物や電池などを出すマジカルリマインダーを開始します。 🔮")

    if b_on or r_on or n_on:
        st.balloons()  

# --- [お問い合わせ] ---
elif selected == lang["menu_contact"]:
    st.title("📞 " + lang["contact_title"])
    
    # 1. 粗大ごみ受付センター
    st.subheader("粗大ごみ受付センター")
    st.write("- **電話番号:** 03-5304-8080")
    st.write("- **受付時間:** 月曜日～土曜日 (午前8:00 ～ 午後7:00)")
    st.write("- [公式ウェブサイト](https://www.shinjuku-sodai.com/)")
    
    st.divider()
    
    # 2. 新宿清掃事務所
    st.subheader("新宿清掃事務所")
    st.write("- **電話番号:** 03-3950-2923")
    st.write("- **FAX:** 03-3950-2932")
    st.write("- **住所:** 〒161-0033 新宿区下落合2-1-1")
    st.write("- **業務時間:** 月曜日～土曜日 (午前7:40 ～ 午後4:25)")
    
    st.divider()
    
    # 3. 家電リサイクル受付センター
    st.subheader("家電リサイクル受付センター")
    st.write("- **電話番号:** 0570-08-7200")
    st.write("- **受付時間:** 月曜日～金曜日 (午前9:00 ～ 午後5:00)")
    
    st.divider()
    
    st.subheader("ごみ全般の管理について (新宿区ごみ減量リサイクル課)")
    st.write("- **電話番号:** 03-3950-2923")
    st.write("- **ご案内:** ごみの収集ルートや分別に関するお問い合わせ窓口です。")

# --- [よくある質問 (FAQ)] ---
elif selected == lang["menu_faq"]:
    st.title("📋 " + lang["faq_title"])

    faq_data = {
        "セクション 1 - ごみ出しの基本ルール": {
            "生ごみ(食品残渣)はどのように捨てれば良いですか？": "1. 水分を完全に切ってください。 2. 臭いや水分が気になる場合は新聞紙などで包んでください。 3. 袋の口をしっかり縛って指定の可燃ごみ日に出してください。",
            "食品ロスを減らすためのコツはありますか？": "1. 買い物前に冷蔵庫の在庫リストを確認しましょう。 2. 必要な分だけ調理しましょう。 3. 賞味期限と消費期限の違いを意識して使い切りましょう。",
            "古紙や雑誌はどうやって分別しますか？": "1. 汚れていない綺麗な紙だけを選別します。 2. 汚れた紙やピザの箱などは可燃ごみへ。 3. 種類（新聞・雑誌・ダンボール）ごとに紐で縛って資源の日に出します。",
            "シュレッダーにかけた紙くずの捨て方は？": "1. 飛散を防ぐため中身の見える透明な袋に入れます。 2. しっかりと口を縛ります。 3. 可燃ごみ、または地域指定の日に出してください。",
            "粗大ごみを捨てる時はどこに連絡すればいいですか？": "1. 粗大ごみ受付センター (03-5304-8080) へ電話するか、Webから申し込んでください。 2. 処理券（有料シール）を購入します。 3. シールを貼って指定日朝に出します。",
            "ごみ出しの許可や事前申請は必要ですか？": "1. 通常のごみは不要ですが、粗大ごみや事業系ごみは事前申請や処理券が必要です。 2. 処分する物の種類と大きさを確認のうえお申し込みください。",
            "自分の地域の正しいごみ収集日を知るには？": "1. 新宿区の公式ウェブサイトの「ごみカレンダー」をご確認ください。 2. お住まいの町名・丁目から検索できます。",
            "指定のごみ袋はどこで購入できますか？": "1. 地域のスーパー、コンビニ、ドラッグストア等で購入可能です。 2. 区で指定された形状・色（あるいは透明・半透明袋のルール）を守ってください。",
            "ごみは一日のうちいつ出せばいいですか？": "1. 指定された収集日の当日朝8時までに集積所へ出してください。 2. 前日夜からのごみ出しは近隣の迷惑や放火の原因となるためお控えください。",
            "不法投棄をした場合、どうなりますか？": "1. 法律により厳しく処罰・警察による捜査対象となります。 2. 非常に高額な罰金や懲役刑が科される場合があります。"
        },
        "セクション 2 - 家電・電化製品の処分": {
            "使わなくなった古家電はどう処分しますか？": "1. 家電リサイクル受付センター、または購入店に相談してください。 2. リサイクル料金と収集運搬費が必要な場合があります。",
            "パソコンを処分したいときは？": "1. パソコンメーカーの回収窓口に申し込むか、小型家電回収ボックスを利用します。 2. 処分前に必ず個人情報を完全に消去してください。",
            "使い古した乾電池の捨て方は？": "1. 不燃ごみではなく、区の指定する黄色い回収箱か特定の資源回収日に出してください。 2. 電池の端子にセロハンテープ等を貼り、絶縁してください。",
            "蛍光灯や電球の正しい捨て方は？": "1. 破損を防ぐため、購入時のケースなどに入れるか新聞紙に包みます。 2. 指定の有害ごみ・資源回収場所に持ち込んでください。",
            "冷蔵庫の処分方法は？": "1. 家電リサイクル法の対象です。 2. 新しく購入する店舗か、家電リサイクル受付センターに引き取りを依頼してください。",
            "洗濯機の処分方法は？": "1. 家電リサイクル法の対象です。 2. 収集運搬料金およびリサイクル券を準備し、正規のルートで処分してください。",
            "エアコンの処分方法は？": "1. 家電リサイクル法に基づき、専門業者や購入店に相談して取り外しと回収を依頼してください。",
            "テレビの処分方法は？": "1. 液晶・プラズマ・ブラウン管いずれも家電リサイクル法の対象です。集積所には出せません。 2. 指定の回収業者へ依頼してください。",
            "電子レンジを捨てるには？": "1. 大きさを計測してください。 2. 一辺が30cmを超える場合は粗大ごみ、それ未満であれば金属・ガラス・陶器ごみ（不燃）となります。",
            "古いスマートフォンの処分方法は？": "1. 各キャリアのショップの回収ポッドに入れるか、区の小型家電回収ボックスへ。 2. 内部データを確実に初期化してください。"
        },
        "セクション 3 - 資源ごみとリサイクル": {
            "地域の集団回収・資源回収とは何ですか？": "1. 自治会やPTAなどが主導するリサイクル活動です。 2. 地域の回収スケジュールに合わせて新聞やアルミ缶などを出します。",
            "リサイクル推進店（エコショップ）とは？": "1. レジ袋の削減や容器包装の回収などを積極的に行う、環境に優しい店舗です。 2. 区が認定し、お買い物時のエコ活動を推奨しています。",
            "マイボトル推奨店とは？": "1. 給水スポットを提供したり、マイボトル持参で割引がある店舗です。 2. プラスチックごみの削減を目的としています。",
            "まだ使える大型家具は売却できますか？": "1. 民間のリサイクルショップや、地域の不用品交換掲示板などを活用することをおすすめします。",
            "おもちゃの修理をしてくれる場所はありますか？": "1. 地域のおもちゃ病院（ボランティア団体など）に相談すると、無料または実費のみで修理してもらえる場合があります。",
            "ダンボールの正しい捨て方は？": "1. 粘着テープや配送伝票を完全に剥がします。 2. 平らに折り畳みます。 3. 紐で十字にしっかり縛って資源の日に出します。",
            "古い新聞紙を出すときの注意点は？": "1. 新聞と折り込みチラシは一緒にまとめて構いません。 2. 紐でバラバラにならないよう縛って資源の日に出します。",
            "古着や衣類を処分したいときは？": "1. 洗濯して乾燥させた綺麗な状態にします。 2. 透明な袋に入れ、雨の日の排出を避けて資源の日に出します。",
            "アルミ缶・スチール缶の捨て方は？": "1. 中身を飲み干し、軽く水ですすぎます。 2. タバコの吸殻などの異物を中に入れないでください。 3. 資源ごみのコンテナに出します。",
            "ガラス瓶（ビン）の捨て方は？": "1. キャップ（フタ）を取り外します。 2. 中を軽くすすいで、割らずに指定の資源回収コンテナに入れます。"
        },
        "セクション 4 - 行政サービスと講座": {
            "生ごみ処理機を購入すると補助金は出ますか？": "1. 区の環境課などで購入費用の補助金制度があるか確認してください。 2. 申請条件や対象機種に適合していれば支給される場合があります。",
            "学校や地域向けのごみ分別講座を依頼できますか？": "1. 清掃事務所や区の担当課に連絡することで、出前講座などの調整が可能です。 2. 事前の団体申し込みが必要です。",
            "電話で外国語によるサポートを受けられますか？": "1. 新宿区の清掃窓口や区役所では、多言語通訳システムや外国人向けのコールセンターを導入している場合があります。",
            "インターネットから粗大ごみの申し込みはできますか？": "1. 粗大ごみ受付センターの公式Webサイトから24時間いつでもオンライン申請が可能です。",
            "近所のごみ集積所トラブル（カラス被害等）の相談はどこへ？": "1. 管轄の清掃事務所へご相談ください。カラスよけネットの貸出などを行っています。",
            "引越し時の大量のごみはどうすればいいですか？": "1. 一度に多量に出す場合は有料（事前予約制）となるか、自身で清掃工場へ持ち込む必要があります。計画的に準備してください。",
            "多言語のごみ出しパンフレットはありますか？": "1. 区役所や清掃事務所の窓口で配布しているほか、新宿区のホームページからPDFで各国語版をダウンロードできます。",
            "そのほかの暮らしのごみトラブルに関する相談窓口は？": "1. まずは新宿区役所の代表番号、または地域を管轄する清掃事務所へ直接お電話ください。",
            "啓発用のポスターや分別シールはもらえますか？": "1. 集合住宅の管理者向けなどに、清掃事務所で無料配布している場合がありますのでご相談ください。",
            "ごみ収集車が来る正確な時間を知りたい": "1. 当日の天候や交通状況、ごみの量によってルートや時間が前後するため、正確な時間の約束はできません。必ず朝8時までに出してください。"
        },
        "セクション 5 - お役立ち豆知識": {
            "プラスチック製の容器包装はどう分別しますか？": "1. プラマークがあるものは、中身を使い切り汚れを落としてから「プラ容器包装」として出します。汚れが落ちないものは可燃ごみです。",
            "年末年始など、ごみ収集がお休みになる期間は？": "1. 年末の最終収集日と年始の開始日は特別ダイヤになります。12月中旬頃に広報やアプリ、WEBサイトで発表されます。",
            "地域の集積所（ごみ置き場）の管理は誰が行っていますか？": "1. その集積所を利用する地域の住民や、マンションの管理組合・大家さんが自主的に清掃・管理を行っています。",
            "ごみ収集作業員の方へメッセージを伝えたい": "1. メモ用紙等に感謝の言葉を書いてごみ袋に貼るなどの温かいお心遣いは、作業員の大きな励みになります。",
            "ごみ箱の嫌な臭いを防ぐ消臭のコツは？": "1. 生ごみの水分を切ったあと、重曹やクエン酸を振りかけると消臭効果があります。また新聞紙に水分を吸わせるのも有効です。",
            "家庭でコンポスト（たい肥化）を始めてもいいですか？": "1. ベランダ用の密閉式コンポストなど、虫や臭いが発生しにくい専用キットを使うことで、家庭でも手軽に堆肥作りが楽しめます。",
            "ペットボトルの正しい出し方は？": "1. キャップとラベルを剥がします（これらはプラスチック資源へ）。 2. 中をすすぎ、軽く潰して資源回収へ出します。",
            "小型家電リサイクル法とは何ですか？": "1. パソコンや携帯電話、ゲーム機等に含まれるレアメタルを回収し、再資源化するための法律です。",
            "家庭から出るごみを減らす一番効果的な方法は？": "1. リデュース（発生抑制）。そもそも「余計なものを買わない」「簡易包装のものを選ぶ」という意識が最も大切です。",
            "新宿区の家庭ごみで最も重量割合が多いものは？": "1. 生ごみ（水分を含む食品残渣）です。水分をしっかり絞って出すだけで大幅な軽量化とごみ減量に繋がります。"
        }
    }

    for section, questions in faq_data.items():
        st.subheader(section)
        for q, a in questions.items():
            with st.expander(f"❓ {q}"):
                st.write(f"📝 **詳細な回答・手順:**")
                st.write(a)

# --- [正しいごみ排出方法 / その他追加されたメニューのハンドリング] ---
elif selected == lang["menu_tips"]:
    st.title("🌱 " + lang["tips_title"])
    st.write(lang["tips_text"])