# -*- coding: utf-8 -*-
# 버전 19 - 여백/입력폭 최종조정 및 타이틀 간격 8dp
import os, sys, json, traceback
from kivy.app import App
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle, Ellipse
from kivy.properties import NumericProperty, ListProperty, BooleanProperty
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition

FONT = "NanumGothic"
SETTINGS_FILE = "settings.json"

# 숫자 변환
def _num_or_none(s):
    try:
        s = (s or "").strip()
        return float(s) if s else None
    except:
        return None

def round_half_up(n):
    return int(float(n) + 0.5)

def _defaults():
    return {
        "prefix": "SG94",
        "round": False,
        "out_font": 15,
        "hide_mm": False,
        "loss_mm": 15.0,
        "auto_font": False,
        "swap_sections": False
    }

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return {**_defaults(), **json.load(f)}
        except:
            pass
    return _defaults()

def save_settings(st):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)

# 공통 입력 위젯
class DigitInput(TextInput):
    max_len = NumericProperty(3)
    def __init__(self, **kw):
        super().__init__(**kw)
        self.size_hint_x = None
        self.multiline = False
        self.halign = "left"
        self.font_name = FONT
        self.font_size = dp(16)
        self.height = dp(30)
        self.background_normal = ""
        self.background_active = ""
    def insert_text(self, substring, from_undo=False):
        f = "".join(ch for ch in substring if ch.isdigit() or ch == ".")
        if "." in self.text and "." in f:
            f = f.replace(".", "")
        remain = max(0, self.max_len - len(self.text))
        return super().insert_text(f[:remain], from_undo=from_undo)

class AlnumInput(TextInput):
    max_len = NumericProperty(6)
    def __init__(self, **kw):
        super().__init__(**kw)
        self.size_hint_x = None
        self.multiline = False
        self.halign = "left"
        self.font_name = FONT
        self.font_size = dp(16)
        self.height = dp(30)
        self.background_normal = ""
        self.background_active = ""
    def insert_text(self, substring, from_undo=False):
        f = "".join(ch for ch in substring.upper() if ch.isalnum())
        remain = max(0, self.max_len - len(self.text))
        return super().insert_text(f[:remain], from_undo=from_undo)

# 스위치 버튼
class PillSwitch(ButtonBehavior, Widget):
    active = BooleanProperty(False)
    def __init__(self, active=False, **kw):
        super().__init__(**kw)
        self.size_hint = (None, None)
        self.width, self.height = dp(60), dp(32)
        self.active = bool(active)
        with self.canvas:
            self._bg_c = Color(0.6,0.6,0.6,1)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[(self.height/2, self.height/2)]*4)
            self._knob_c = Color(1,1,1,1)
            self._knob = Ellipse(pos=self.pos, size=(self.height-4, self.height-4))
        self.bind(pos=self._update, size=self._update, active=self._draw)
        self._draw()
    def _update(self, *_):
        pad = dp(2)
        r = self.height - pad*2
        self._bg.pos = self.pos
        self._bg.size = self.size
        if self.active:
            self._knob.pos = (self.right - r - pad, self.y + pad)
        else:
            self._knob.pos = (self.x + pad, self.y + pad)
        self._knob.size = (r, r)
    def _draw(self, *_):
        self._bg_c.rgba = (0.15,0.6,0.2,1) if self.active else (0.6,0.6,0.6,1)
        self._update()
    def on_release(self, *_):
        self.active = not self.active
        self._draw()

# 설정 화면
class SettingsScreen(Screen):
    def __init__(self, app, **kw):
        super().__init__(**kw)
        self.app = app
        self.build_ui()

    def _gray(self, text):
        lab = Label(text=text, font_name=FONT, color=(0.4,0.4,0.4,1),
                    halign="left", valign="middle", size_hint=(1,None), height=dp(20))
        lab.bind(size=lambda *_: setattr(lab, "text_size", lab.size))
        return lab

    def _title(self, text):
        lab = Label(text=text, font_name=FONT, font_size=dp(32),
                    color=(0,0,0,1), halign="center", valign="middle",
                    size_hint=(1,None), height=dp(38))
        lab.bind(size=lambda *_: setattr(lab, "text_size", lab.size))
        return lab

    def _leftlab(self, text, w):
        lab = Label(text=text, font_name=FONT, color=(0,0,0,1),
                    size_hint=(None,None), width=w, height=dp(28),
                    halign="left", valign="middle")
        lab.bind(size=lambda *_: setattr(lab, "text_size", lab.size))
        return lab

    def build_ui(self):
        root = BoxLayout(orientation="vertical", padding=[dp(12),dp(6),dp(12),dp(6)], spacing=dp(4))
        self.add_widget(root)

        top = BoxLayout(size_hint=(1,None), height=dp(40))
        top.add_widget(Widget())
        save = ButtonBehavior(Label(text="저장", font_name=FONT, color=(1,1,1,1),
                    size_hint=(None,1), width=dp(66)))
        top.add_widget(save)
        root.add_widget(top)

        root.add_widget(self._title("환경설정"))
        root.add_widget(Widget(size_hint=(1,None), height=dp(8)))  # ✅ 타이틀-1번 간격

        body = BoxLayout(orientation="vertical", spacing=dp(4))
        root.add_widget(body)

        BASE_W = dp(53)
        self.ed_prefix = AlnumInput(max_len=4, width=dp(70))
        self.ed_prefix.text = self.app.st.get("prefix", "SG94")

        self.ed_out_font = DigitInput(max_len=2, width=dp(45))
        self.ed_out_font.text = str(int(self.app.st.get("out_font",15)))

        self.ed_loss = DigitInput(max_len=2, width=dp(45))
        self.ed_loss.text = str(int(self.app.st.get("loss_mm",15)))

        self.sw_round = PillSwitch(active=self.app.st.get("round",False))
        self.sw_hide_mm = PillSwitch(active=self.app.st.get("hide_mm",False))
        self.sw_auto_font = PillSwitch(active=self.app.st.get("auto_font",False))
        self.sw_swap = PillSwitch(active=self.app.st.get("swap_sections",False))

        # 1~7 항목 정렬
        items = [
            ("1. 강번 고정부 변경", self.ed_prefix, "강번 맨앞 영문 + 숫자 고정부 변경"),
            ("2. 정수 결과 반올림", self.sw_round, "출력부 소수값을 정수로 표시"),
            ("3. 결과값 글자 크기", self.ed_out_font, "결과표시 글자 크기(px)"),
            ("4. 결과값 mm 표시 제거", self.sw_hide_mm, "단위(mm) 문구 숨김"),
            ("5. 절단 손실 길이 조정", self.ed_loss, "절단시 손실 보정 길이(mm)"),
            ("6. 모바일 대응 자동 폰트 크기 조절", self.sw_auto_font, "해상도에 맞게 입력부 폰트 조절"),
            ("7. 출력값 위치 이동", self.sw_swap, "절단 예상 길이를 맨 아래로"),
        ]
        for title, widget, desc in items:
            body.add_widget(self._leftlab(title, dp(260)))
            row = BoxLayout(size_hint=(1,None), height=dp(30), spacing=dp(6))
            row.add_widget(widget)
            row.add_widget(Widget())
            body.add_widget(row)
            body.add_widget(self._gray(desc))

        sig = Label(text="버전 1.0", font_name=FONT, color=(0.4,0.4,0.4,1),
                    size_hint=(1,None), height=dp(22), halign="right", valign="middle")
        sig.bind(size=lambda *_: setattr(sig,"text_size",sig.size))
        root.add_widget(sig)

# 앱 본체 생략 (MainScreen / 계산로직 동일)
