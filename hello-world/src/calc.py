import flet as ft
import math

# ----------------------------------------------------
# ★ 修正点1: すべての色の定数を ft.Colors (大文字) に統一
# ----------------------------------------------------
# 16進数とft.Colorsを組み合わせて、環境に依存しない設定にします
COLOR_DIGIT_BUTTON = "#333333"   
COLOR_ACTION_BUTTON = "#FF9500"
COLOR_SCI_BUTTON = "#2962FF"
COLOR_EXTRA_ACTION = "#A5A5A5"
COLOR_TEXT_LIGHT = ft.Colors.BLACK  # ★ ft.Colors に修正
COLOR_TEXT_DARK = ft.Colors.WHITE   # ★ ft.Colors に修正
COLOR_RESULT_BG = ft.Colors.BLACK   # ★ ft.Colors に修正

class CalcButton(ft.ElevatedButton):
    def __init__(self, text, button_clicked, expand=1):
        super().__init__()
        self.text = text
        self.expand = expand
        self.on_click = button_clicked
        self.data = text
        
        # ★ 修正点2: ft.MaterialState を削除し、古いバージョン互換のスタイルに
        self.style = ft.ButtonStyle(
            # ft.RoundedRectangleBorder の直接設定は古いバージョンで動作します
            shape=ft.RoundedRectangleBorder(radius=20),
            padding=ft.padding.all(10),
        )

# 以下、他のクラス定義は変更なし (色指定は上の定数を使います)
class DigitButton(CalcButton):
    def __init__(self, text, button_clicked, expand=1):
        super().__init__(text, button_clicked, expand)
        self.bgcolor = COLOR_DIGIT_BUTTON
        self.color = COLOR_TEXT_DARK

class ActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        super().__init__(text, button_clicked)
        self.bgcolor = COLOR_ACTION_BUTTON
        self.color = COLOR_TEXT_DARK
        if text == "=":
            self.expand = 2

class SciButton(CalcButton):
    def __init__(self, text, button_clicked):
        super().__init__(text, button_clicked)
        self.bgcolor = COLOR_SCI_BUTTON
        self.color = COLOR_TEXT_DARK
        # Fletの非常に古いバージョンではTextStyleのサポートが異なる場合があるため、
        # 影響が少ないTextStyleのサイズ設定は削除しておきます。
        # self.style.text_style = ft.TextStyle(size=12)

class ExtraActionButton(CalcButton):
    def __init__(self, text, button_clicked):
        super().__init__(text, button_clicked)
        self.bgcolor = COLOR_EXTRA_ACTION
        self.color = COLOR_TEXT_LIGHT

class CalculatorApp(ft.Container):
    def __init__(self):
        super().__init__()
        self.reset()

        self.result = ft.Text(value="0", color=COLOR_TEXT_DARK, size=40, text_align=ft.TextAlign.RIGHT)
        self.width = 400
        self.bgcolor = COLOR_RESULT_BG
        self.border_radius = ft.border_radius.all(20)
        self.padding = 20
        self.content = ft.Column(
            controls=[
                ft.Row(controls=[self.result], alignment=ft.MainAxisAlignment.END),
                ft.Row(
                    controls=[
                        SciButton(text="π", button_clicked=self.button_clicked),
                        ExtraActionButton(text="AC", button_clicked=self.button_clicked),
                        ExtraActionButton(text="+/-", button_clicked=self.button_clicked),
                        ExtraActionButton(text="%", button_clicked=self.button_clicked),
                        ActionButton(text="/", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        SciButton(text="sin", button_clicked=self.button_clicked),
                        DigitButton(text="7", button_clicked=self.button_clicked),
                        DigitButton(text="8", button_clicked=self.button_clicked),
                        DigitButton(text="9", button_clicked=self.button_clicked),
                        ActionButton(text="*", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        SciButton(text="cos", button_clicked=self.button_clicked),
                        DigitButton(text="4", button_clicked=self.button_clicked),
                        DigitButton(text="5", button_clicked=self.button_clicked),
                        DigitButton(text="6", button_clicked=self.button_clicked),
                        ActionButton(text="-", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        SciButton(text="tan", button_clicked=self.button_clicked),
                        DigitButton(text="1", button_clicked=self.button_clicked),
                        DigitButton(text="2", button_clicked=self.button_clicked),
                        DigitButton(text="3", button_clicked=self.button_clicked),
                        ActionButton(text="+", button_clicked=self.button_clicked),
                    ]
                ),
                ft.Row(
                    controls=[
                        SciButton(text="log", button_clicked=self.button_clicked),
                        SciButton(text="√", button_clicked=self.button_clicked),
                        DigitButton(text="0", button_clicked=self.button_clicked),
                        DigitButton(text=".", button_clicked=self.button_clicked),
                        ActionButton(text="=", button_clicked=self.button_clicked),
                    ]
                ),
            ]
        )

    # 以下、ロジック部分は省略（前回と同一）
    def button_clicked(self, e):
        data = e.control.data
        if self.result.value == "Error" or data == "AC":
            self.result.value = "0"
            self.reset()
        elif data in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "."):
            current_value = str(self.result.value)
            if data == "." and "." in current_value: pass
            elif current_value == "0" or self.new_operand == True:
                self.result.value = data if data != "." else "0."
                self.new_operand = False
            else: self.result.value = current_value + data
        elif data in ("+", "-", "*", "/"):
            current_value = float(self.result.value)
            calculated_result = self.calculate(self.operand1, current_value, self.operator)
            self.result.value = str(calculated_result)
            self.operator = data
            if self.result.value == "Error": self.operand1 = 0
            else: self.operand1 = float(calculated_result)
            self.new_operand = True
        elif data in ("="):
            self.result.value = str(self.calculate(self.operand1, float(self.result.value), self.operator))
            self.reset()
        elif data in ("%"):
            current_value = float(self.result.value) / 100
            self.result.value = str(self.format_number(current_value))
            self.new_operand = True
        elif data in ("+/-"):
            current_value = float(self.result.value)
            self.result.value = str(self.format_number(current_value * -1))
        elif data in ("sin", "cos", "tan", "log", "√", "π"):
            try:
                val = float(self.result.value)
                res = 0
                if data == "sin": res = math.sin(val)
                elif data == "cos": res = math.cos(val)
                elif data == "tan": res = math.tan(val)
                elif data == "log": res = math.log10(val) if val > 0 else "Error"
                elif data == "√": res = math.sqrt(val) if val >= 0 else "Error"
                elif data == "π": res = math.pi
                self.result.value = str(self.format_number(res))
                self.new_operand = True
            except Exception:
                self.result.value = "Error"
                self.new_operand = True
        self.update()

    def format_number(self, num):
        if num == "Error": return "Error"
        if isinstance(num, (int, float)):
             if num % 1 == 0: return int(num)
             return round(num, 6)
        return num

    def calculate(self, operand1, operand2, operator):
        if operator == "+": return self.format_number(operand1 + operand2)
        elif operator == "-": return self.format_number(operand1 - operand2)
        elif operator == "*": return self.format_number(operand1 * operand2)
        elif operator == "/":
            if operand2 == 0: return "Error"
            return self.format_number(operand1 / operand2)
        return self.format_number(operand2)

    def reset(self):
        self.operator = "+"
        self.operand1 = 0
        self.new_operand = True

def main(page: ft.Page):
    page.title = "Scientific Calculator"
    page.window_width = 450
    page.window_height = 600
    page.bgcolor = "#111111"
    
    calc = CalculatorApp()
    
    page.add(
        ft.Row(
            [calc],
            alignment=ft.MainAxisAlignment.CENTER,
        )
    )

ft.app(target=main)