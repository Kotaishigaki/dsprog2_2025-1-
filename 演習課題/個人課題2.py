import flet as ft
import requests

def main(page: ft.Page):
    # ページの設定
    page.title = "天気予報アプリ"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0  # 画面の端まで色を塗るためにパディングをなくす
    
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

    # 1. 天気予報を表示するエリア（右側）
    weather_display_column = ft.Column(scroll=ft.ScrollMode.AUTO)
    
    # 右側のコンテナ
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

    # --- ロジック部分 ---

    API_REDIRECT_MAP = {
        "014030": "014100", # 十勝 -> 釧路
        "460040": "460100", # 奄美 -> 鹿児島
    }

    # 天気予報を取得して表示する関数
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

            found_data = False
            for area in areas:
                sub_area_name = area["area"]["name"]
                weathers = area["weathers"]

                # サブエリア名
                weather_display_column.controls.append(
                    ft.Container(
                        content=ft.Text(f"📍 {sub_area_name}", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                        padding=ft.padding.symmetric(horizontal=15, vertical=5),
                        bgcolor=ft.Colors.WHITE,
                        border_radius=20,
                        margin=ft.margin.only(top=20, bottom=10)
                    )
                )

                cards_row = ft.Row(wrap=True, spacing=15)

                for time, weather in zip(times, weathers):
                    date_str = time.split("T")[0]
                    icon, main_color, bg_color = get_weather_style(weather)

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
                                ft.Text(date_str, size=12, color=ft.Colors.GREY_600),
                                ft.Text(weather, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87, width=150),
                            ], spacing=2)
                        ], alignment=ft.MainAxisAlignment.START)
                    )
                    cards_row.controls.append(card)
                
                weather_display_column.controls.append(cards_row)
                found_data = True

            if not found_data:
                 weather_display_column.controls.append(ft.Text("データが見つかりませんでした。", color=ft.Colors.RED_100))

        except Exception as err:
            weather_display_column.controls.append(ft.Text(f"エラー: {err}", color=ft.Colors.RED_100))
        
        page.update()

    # --- 初期データ取得とリスト作成 ---

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
            # グラデーション背景
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
                    # 左側のサイドバー（ここを修正しました）
                    ft.Container(
                        content=area_list_view, 
                        width=300, 
                        bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.WHITE),
                        # 修正箇所: border_right ではなく border を使用
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