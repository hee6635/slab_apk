# -*- coding: utf-8 -*-
import os, sys, json, math, traceback
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.core.text import LabelBase
from kivy.utils import get_color_from_hex

# ---------- 강제 종료 시 로그 자동 저장 ----------
try:
    log_path = "/storage/emulated/0/1/kivy_full_log.txt"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    sys.stderr = open(log_path, "w", encoding="utf-8")
    sys.stdout = sys.stderr
except Exception as e:
    print(f"로그 초기화 실패: {e}")
# ---------------------------------------------------

# ---------- 나눔폰트 등록 ----------
font_path = os.path.join(os.path.dirname(__file__), "NanumGothic.ttf")
if os.path.exists(font_path):
    LabelBase.register(name="NanumGothic", fn_regular=font_path)
else:
    print("⚠️ NanumGothic.ttf 파일이 존재하지 않습니다.")
# ---------------------------------------------------

SETTINGS_FILE = "settings.json"

# 설정 로드/저장
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "prefix": "SG94",
        "round_result": False,
        "result_font_size": 11,
        "hide_mm": False,
        "loss": 15
    }

def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 반올림 함수
def round_half_up(n):
    return int(n + 0.5)

# 메인 앱 클래스
class SlabCalculator(App):
    def build(self):
        self.settings = load_settings()
        self.prefix = self.settings["prefix"]
        self.round_result = self.settings["round_result"]
        self.font_size = self.settings["result_font_size"]
        self.hide_mm = self.settings["hide_mm"]
        self.loss = self.settings["loss"]

        root = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # 타이틀
        root.add_widget(Label(text="후판 계산기", font_name="NanumGothic",
                              font_size="22sp", bold=True,
                              color=get_color_from_hex("#000000")))

        # 입력 필드
        self.total_input = TextInput(hint_text="Slab 총 길이 입력",
                                     multiline=False,
                                     font_name="NanumGothic",
                                     input_filter="float",
                                     font_size="18sp")
        root.add_widget(self.total_input)

        self.entries = []
        grid = GridLayout(cols=2, spacing=5, size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        for i in range(3):
            label = Label(text=f"{i+1}번 지시길이", font_name="NanumGothic",
                          font_size="16sp", color=get_color_from_hex("#000000"))
            grid.add_widget(label)
            e = TextInput(multiline=False, font_name="NanumGothic",
                          input_filter="float", font_size="16sp")
            self.entries.append(e)
            grid.add_widget(e)

        scroll = ScrollView(size_hint=(1, 0.6))
        scroll.add_widget(grid)
        root.add_widget(scroll)

        # 계산 버튼
        calc_btn = Button(text="계산하기", font_name="NanumGothic",
                          font_size="20sp", size_hint_y=None, height=60,
                          background_color=get_color_from_hex("#4CAF50"),
                          color=get_color_from_hex("#FFFFFF"),
                          on_press=self.calculate)
        root.add_widget(calc_btn)

        # 결과창
        self.result_label = Label(text="", font_name="NanumGothic",
                                  font_size=f"{self.font_size}sp",
                                  color=get_color_from_hex("#000000"))
        root.add_widget(self.result_label)

        return root

    def calculate(self, *args):
        try:
            slab_len = float(self.total_input.text)
            guides = [float(e.text) for e in self.entries if e.text]

            if len(guides) < 2:
                self.result_label.text = "⚠️ 최소 2개 이상 입력하세요."
                return

            num = len(guides) - 1
            total_loss = self.loss * num
            remain = slab_len - (sum(guides) + total_loss)
            add_each = remain / len(guides)
            real_lengths = [g + add_each for g in guides]

            if self.round_result:
                real_lengths = [round_half_up(r) for r in real_lengths]

            mm = "" if self.hide_mm else " mm"

            result = f"▶ 강번: {self.prefix}\n\n"
            result += f"▶ Slab 실길이: {slab_len:,.1f}{mm}\n"
            for i, g in enumerate(guides):
                result += f"▶ {i+1}번 지시길이: {g:,.1f}{mm}\n"
            result += f"▶ 절단 손실: {self.loss}{mm} × {num} = {total_loss}{mm}\n"
            result += f"▶ 전체 여유길이: {remain:,.1f}{mm}\n\n"
            result += "▶ 실제 절단 길이:\n"
            for i, r in enumerate(real_lengths):
                result += f"   {i+1}번: {r:,.1f}{mm}\n"

            self.result_label.text = result

        except Exception as e:
            err_msg = f"⚠️ 오류 발생: {e}"
            self.result_label.text = err_msg
            with open("/storage/emulated/0/1/kivy_calc_error.txt", "w", encoding="utf-8") as f:
                f.write(traceback.format_exc())

# 앱 실행
if __name__ == "__main__":
    SlabCalculator().run()
