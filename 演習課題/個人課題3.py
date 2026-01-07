import flet as ft
import requests
import sqlite3
import datetime

def main(page: ft.Page):
    # --- ページの設定 ---
    page.title = "天気予報アプリ (課題3: DB連携・地域区別対応版)"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    
    # 【重要】エラー回避のため、保存するファイル名を新しいものに変更しました
    DB_NAME = "weather_task3.db"

    # --- 1. データベース初期化処理 ---
    def init_db():
        """
        データベースとテーブルを作成する関数
        今回は「詳細な地域名(sub_area)」を保存できるように設計しています。
        """
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # テーブル作成: sub_area (詳細地域) カラムを追加しています
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                area_name TEXT NOT NULL,
                sub_area TEXT,
                date TEXT NOT NULL,
                weather TEXT NOT NULL,
                created_at TEXT
            )
        """)
        conn.commit()
        conn.close()
        print(f"データベース({DB_NAME})の準備が完了しました。")

    # アプリ起動時に実行
    init_db()

    # --- ヘルパー関数: 天気の文字からアイコンと色を決める ---
    def get_weather_style(weather_text):
        text = weather_text or ""
        if "雪" in text:
            return ft.Icons.AC_UNIT, ft.Colors.CYAN, ft.Colors.CYAN_50
        elif "雷" in text:
            return ft.Icons.THUNDERSTORM, ft.Colors.YELLOW_900, ft.Colors.YELLOW_50
        elif "雨" in text:
            return ft.Icons.WATER_DROP, ft.Colors.BLUE, ft.Colors.BLUE_50
        elif "晴" in text:
            return ft.Icons.WB_SUNNY, ft.Colors.ORANGE, ft.Colors.ORANGE_50
        elif "曇" in text or "くもり" in text:
            return ft.Icons.CLOUD, ft.Colors.BLUE_GREY, ft.Colors.BLUE_GREY_50
        else:
            return ft.Icons.QUESTION_MARK, ft.Colors.BLACK, ft.Colors.WHITE

    # --- UIパーツの準備 ---
    weather_display_column = ft.Column(scroll=ft.ScrollMode.AUTO)
    
    weather_container = ft.Container(
        content=weather_display_column,
        expand=True,
        padding=30,
        alignment=ft.alignment.top_left,
    )
    
    # 初期メッセージ
    weather_display_column.controls.append(
        ft.Container(
            content=ft.Text("👈 地域を選択してください", size=24, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            alignment=ft.alignment.center,
            margin=ft.margin.only(top=50)
        )
    )

    # --- 2. データベース操作用関数 ---

    def save_weather_to_db(area_name, sub_area, date_str, weather_text):
        """
        取得したデータをDBに保存する (INSERT)
        詳細な地域名(sub_area)も一緒に記録します。
        """
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        sql = "INSERT INTO weather_forecasts (area_name, sub_area, date, weather, created_at) VALUES (?, ?, ?, ?, ?)"
        cursor.execute(sql, (area_name, sub_area, date_str, weather_text, now))
        
        conn.commit()
        conn.close()

    def delete_old_weather_from_db(area_name):
        """
        その地域の古いデータを削除してリセットする
        """
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM weather_forecasts WHERE area_name = ?", (area_name,))
        conn.commit()
        conn.close()

    def get_forecasts_from_db(area_name):
        """
        DBからデータを取得する (SELECT)
        地域名だけでなく、詳細地域(sub_area)や日付順で並び替えて取得します。
        """
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM weather_forecasts WHERE area_name = ? ORDER BY sub_area, date", (area_name,))
        rows = cursor.fetchall()
        
        conn.close()
        return rows

    # --- ロジック部分 ---

    API_REDIRECT_MAP = {
        "014030": "014100", # 十勝 -> 釧路
        "460040": "460100", # 奄美 -> 鹿児島
    }

    def get_weather(e):
        area_code = e.control.data
        area_name = e.control.title.value

        weather_display_column.controls.clear()
        
        # タイトル表示
        weather_display_column.controls.append(
            ft.Text(f"{area_name}", size=40, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
        )
        weather_display_column.controls.append(ft.Divider(color=ft.Colors.WHITE54))

        try:
            # 1. APIからデータ取得
            target_code = area_code
            if area_code in API_REDIRECT_MAP:
                target_code = API_REDIRECT_MAP[area_code]

            url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{target_code}.json"
            
            response = requests.get(url)
            response.raise_for_status()
            weather_data = response.json()

            forecasts = weather_data[0]["timeSeries"][0]
            times = forecasts["timeDefines"]
            areas = forecasts["areas"]

            # DBリセット（この地域の古いデータを削除）
            delete_old_weather_from_db(area_name)

            found_data = False
            for area in areas:
                sub_area_name = area["area"]["name"] # 例: 東京地方, 伊豆諸島
                weathers = area["weathers"]
                
                # 2. 取得したデータをDBへ保存 (ループ処理)
                for time, weather in zip(times, weathers):
                    date_str = time.split("T")[0]
                    # ここで詳細地域名(sub_area_name)も一緒に保存
                    save_weather_to_db(area_name, sub_area_name, date_str, weather)
                
                found_data = True

            if found_data:
                # 3. 画面表示はすべてDBから読み込んで行う
                db_rows = get_forecasts_from_db(area_name)
                
                # 取得したデータを「詳細地域ごと」に整理する
                grouped_data = {}
                for row in db_rows:
                    sub = row["sub_area"]
                    if sub not in grouped_data:
                        grouped_data[sub] = []
                    grouped_data[sub].append(row)

                # 整理したデータごとに表示を作る
                for sub_area, rows in grouped_data.items():
                    # 詳細地域の見出し（例: 📍 東京地方）
                    weather_display_column.controls.append(
                        ft.Container(
                            content=ft.Text(f"📍 {sub_area}", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                            margin=ft.margin.only(top=20, bottom=5),
                            padding=ft.padding.symmetric(horizontal=10, vertical=5),
                            bgcolor=ft.Colors.WHITE70,
                            border_radius=5
                        )
                    )

                    cards_row = ft.Row(wrap=True, spacing=15)

                    for row in rows:
                        db_date = row["date"]
                        db_weather = row["weather"]
                        
                        icon, main_color, bg_color = get_weather_style(db_weather)

                        # カードデザイン
                        card = ft.Container(
                            width=260,
                            padding=20,
                            border_radius=15,
                            bgcolor=ft.Colors.with_opacity(0.85, ft.Colors.WHITE),
                            shadow=ft.BoxShadow(
                                spread_radius=1,
                                blur_radius=10,
                                color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                            ),
                            content=ft.Row([
                                ft.Icon(icon, color=main_color, size=45),
                                ft.Column([
                                    ft.Text(db_date, size=12, color=ft.Colors.GREY_600),
                                    ft.Text(db_weather, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87, width=150),
                                ], spacing=2)
                            ], alignment=ft.MainAxisAlignment.START)
                        )
                        cards_row.controls.append(card)
                    
                    weather_display_column.controls.append(cards_row)

                # DBから取得したことを示す注釈
                weather_display_column.controls.append(
                    ft.Container(
                        content=ft.Text("※データはデータベース(SQLite)から取得して表示しています", size=12, color=ft.Colors.WHITE70),
                        margin=ft.margin.only(top=20)
                    )
                )

            else:
                 weather_display_column.controls.append(ft.Text("データが見つかりませんでした。", color=ft.Colors.RED_100))

        except Exception as err:
            weather_display_column.controls.append(ft.Text(f"エラー: {err}", color=ft.Colors.RED_100))
            print(f"Error: {err}")
        
        page.update()

    # --- 初期データ取得とリスト作成 (変更なし) ---
    area_list_view = ft.ListView(expand=True, spacing=0, padding=0)

    try:
        area_url = "http://www.jma.go.jp/bosai/common/const/area.json"
        area_data = requests.get(area_url).json()

        centers = area_data["centers"]
        offices = area_data["offices"]

        for center_code, center_info in centers.items():
            region_name = center_info["name"]
            children_codes = center_info["children"]

            prefecture_tiles = []
            for code in children_codes:
                if code in offices:
                    office_info = offices[code]
                    office_name = office_info["name"]
                    office_kana = office_info.get("kana", "")
                    
                    tile = ft.ListTile(
                        title=ft.Text(office_name, weight=ft.FontWeight.W_500, color=ft.Colors.BLUE_GREY_900),
                        subtitle=ft.Text(office_kana, size=10, color=ft.Colors.BLUE_GREY_400),
                        leading=ft.Icon(ft.Icons.LOCATION_ON, size=16, color=ft.Colors.BLUE_400),
                        data=code,
                        on_click=get_weather,
                        dense=True,
                        hover_color=ft.Colors.BLUE_50,
                    )
                    prefecture_tiles.append(tile)

            expansion_tile = ft.ExpansionTile(
                title=ft.Text(region_name, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                controls=prefecture_tiles,
                collapsed_text_color=ft.Colors.BLUE_800,
                icon_color=ft.Colors.BLUE_800,
                bgcolor=ft.Colors.TRANSPARENT,
            )
            area_list_view.controls.append(expansion_tile)

    except Exception as e:
        area_list_view.controls.append(ft.Text(f"リスト取得失敗: {e}", color=ft.Colors.RED))

    # --- レイアウト ---
    page.add(
        ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[
                    ft.Colors.LIGHT_BLUE_300,
                    ft.Colors.BLUE_GREY_100
                ],
            ),
            content=ft.Row(
                [
                    ft.Container(
                        content=area_list_view, 
                        width=300, 
                        bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.WHITE),
                        border=ft.border.only(right=ft.BorderSide(1, ft.Colors.WHITE54)),
                        padding=10
                    ),
                    weather_container
                ],
                expand=True,
                spacing=0
            )
        )
    )

ft.app(target=main)