# -*- coding: utf-8 -*-
# 버전 18R3 - 환경설정 타이틀↔1번 간격 여백 제거 / 타이틀 34dp / 버튼 상단 여백 통일 / 버전 1.0
import os, sys, json, traceback
from kivy.app import App
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import NumericProperty, ListProperty, BooleanProperty
from kivy.graphics import Color, RoundedRectangle, Ellipse
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition

FONT = "NanumGothic"
SETTINGS_FILE = "settings.json"

# ===== 유틸 =====
def _num_or_none(s):
    try:
        s = (s or "").strip()
        if not s or s == ".":
            return None
        return float(s)
    except Exception:
        return None

def round_half_up(n):
    return int(float(n) + 0.5)

def _install_global_crash_hook(user_data_dir: str):
    def _write(path, text):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception:
            pass
    def _hook(exc_type, exc, tb):
        txt = "Traceback (most recent call last):\n" + "".join(traceback.format_tb(tb))
        txt += f"{exc_type.__name__}: {exc}\n"
        if user_data_dir:
            _write(os.path.join(user_data_dir, "last_crash.txt"), txt)
        _write("/storage/emulated/0/.kivy/last_crash.txt", txt)
        sys.__excepthook__(exc_type, exc, tb)
    sys.excepthook = _hook

# ===== 공통 위젯 =====
class RoundedButton(ButtonBehavior, Label):
    radius = NumericProperty(dp(8))
    bg_color = ListProperty([0.23, 0.53, 0.23, 1])
    fg_color = ListProperty([1, 1, 1, 1])
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_name = FONT
        self.color = self.fg_color
        self.halign = "center"
        self.valign = "middle"
        self.bind(size=lambda *_: setattr(self, "text_size", self.size))
        with self.canvas.before:
            self._c = Color(*self.bg_color)
            self._r = RoundedRectangle(pos=self.pos, size=self.size,
                                       radius=[(self.radius, self.radius)]*4)
        self.bind(pos=self._sync_bg, size=self._sync_bg, bg_color=self._recolor)
    def _sync_bg(self, *_):
        self._r.pos, self._r.size = self.pos, self.size
    def _recolor(self, *_):
        self._c.rgba = self.bg_color

class DigitInput(TextInput):
    max_len = NumericProperty(3)
    allow_float = BooleanProperty(False)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_x = None
        self.multiline = False
        self.halign = "left"
        self.padding = (dp(6), dp(5))
        self.font_name = FONT
        self.font_size = dp(17)
        self.height = dp(30)
        self.background_normal = ""
        self.background_active = ""
        self.cursor_width = dp(2)
    def insert_text(self, substring, from_undo=False):
        if self.allow_float:
            filtered = "".join(ch for ch in substring if ch.isdigit() or ch == ".")
            if "." in self.text and "." in filtered:
                filtered = filtered.replace(".", "")
        else:
            filtered = "".join(ch for ch in substring if ch.isdigit())
        remain = max(0, self.max_len - len(self.text))
        if remain <= 0:
            return
        if len(filtered) > remain:
            filtered = filtered[:remain]
        return super().insert_text(filtered, from_undo=from_undo)

class AlnumInput(TextInput):
    max_len = NumericProperty(6)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_x = None
        self.multiline = False
        self.halign = "left"
        self.padding = (dp(6), dp(5))
        self.font_name = FONT
        self.font_size = dp(17)
        self.height = dp(30)
        self.background_normal = ""
        self.background_active = ""
        self.cursor_width = dp(2)
    def insert_text(self, substring, from_undo=False):
        filtered = "".join(ch for ch in substring.upper() if ch.isalnum())
        remain = max(0, self.max_len - len(self.text))
        if remain <= 0:
            return
        if len(filtered) > remain:
            filtered = filtered[:remain]
        return super().insert_text(filtered, from_undo=from_undo)

class PillSwitch(ButtonBehavior, Widget):
    active = BooleanProperty(False)
    def __init__(self, active=False, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.width, self.height = dp(60), dp(32)
        self.active = bool(active)
        with self.canvas:
            self._bg_color = Color(0.65, 0.65, 0.65, 1)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size,
                                        radius=[(self.height/2, self.height/2)]*4)
            self._knob_color = Color(1, 1, 1, 1)
            self._knob = Ellipse(pos=(self.x+dp(2), self.y+dp(2)),
                                 size=(self.height-dp(4), self.height-dp(4)))
        self.bind(pos=self._sync, size=self._sync, active=self._render)
        self._render()
    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        pad = dp(2)
        r = self.height - pad*2
        if self.active:
            self._knob.pos = (self.right - r - pad, self.y + pad)
        else:
            self._knob.pos = (self.x + pad, self.y + pad)
        self._knob.size = (r, r)
    def _render(self, *_):
        self._bg_color.rgba = (0.15, 0.6, 0.2, 1) if self.active else (0.65, 0.65, 0.65, 1)
        self._sync()
    def on_release(self, *_):
        self.active = not self.active
        self._render()

# ===== 설정 화면 =====
class SettingsScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.build_ui()

    def _title(self, text):
        lab = Label(text=text, font_name=FONT, font_size=dp(32),
                    color=(0,0,0,1), halign="center", valign="middle",
                    size_hint=(1,None), height=dp(34))
        lab.bind(size=lambda *_: setattr(lab, "text_size", lab.size))
        return lab

    def _black(self, text):
        lab = Label(text=text, font_name=FONT, color=(0,0,0,1),
                    size_hint=(1,None), height=dp(24),
                    halign="left", valign="middle")
        lab.bind(size=lambda *_: setattr(lab, "text_size", lab.size))
        return lab

    def _gray(self, text):
        lab = Label(text=text, font_name=FONT, color=(0.4,0.4,0.4,1),
                    size_hint=(1,None), height=dp(24),
                    halign="left", valign="middle")
        lab.bind(size=lambda *_: setattr(lab, "text_size", lab.size))
        return lab

    def _indent_row(self, *widgets):
        row = BoxLayout(orientation="horizontal", size_hint=(1,None),
                        height=dp(30), spacing=dp(8), padding=[dp(12), 0, 0, 0])
        for w in widgets:
            row.add_widget(w)
        return row

    def build_ui(self):
        Window.clearcolor = (0.93, 0.93, 0.93, 1)
        root = BoxLayout(orientation="vertical",
                         padding=[dp(12), dp(10), dp(12), dp(6)],
                         spacing=dp(6))
        self.add_widget(root)

        topbar = BoxLayout(size_hint=(1,None), height=dp(40), spacing=0)
        topbar.add_widget(Widget())
        btn_save = RoundedButton(text="저장", size_hint=(None,1), width=dp(72),
                                 bg_color=[0.23,0.53,0.23,1], fg_color=[1,1,1,1])
        btn_save.bind(on_release=lambda *_: self._save_and_back())
        topbar.add_widget(btn_save)
        root.add_widget(topbar)

        root.add_widget(self._title("환경설정"))
        # 여백 Widget 제거됨 ✅

        body = BoxLayout(orientation="vertical", spacing=dp(12))
        root.add_widget(body)

        body.add_widget(self._black("1. 강번 고정부 변경"))
        self.ed_prefix = AlnumInput(max_len=6, width=dp(70))
        self.ed_prefix.text = self.app.st.get("prefix", "SG94")
        body.add_widget(self._indent_row(self.ed_prefix, self._gray("강번 맨앞 영문 + 숫자 고정부 변경")))

        body.add_widget(self._black("2. 정수 결과 반올림"))
        self.sw_round = PillSwitch(active=bool(self.app.st.get("round", False)))
        body.add_widget(self._indent_row(self.sw_round, self._gray("출력부 소수값을 정수로 표시")))

        body.add_widget(self._black("3. 결과값 글자 크기"))
        self.ed_out_font = DigitInput(max_len=2, allow_float=False, width=dp(45))
        try:
            self.ed_out_font.text = str(int(self.app.st.get("out_font", 15)))
        except Exception:
            self.ed_out_font.text = "15"
        body.add_widget(self._indent_row(self.ed_out_font, self._gray("결과 표시 라벨 폰트 크기")))

        body.add_widget(self._black("4. 결과값 mm 표시 제거"))
        self.sw_hide_mm = PillSwitch(active=bool(self.app.st.get("hide_mm", False)))
        body.add_widget(self._indent_row(self.sw_hide_mm, self._gray("단위(mm) 문구 숨김")))

        body.add_widget(self._black("5. 절단 손실 길이 조정"))
        self.ed_loss = DigitInput(max_len=2, allow_float=True, width=dp(45))
        self.ed_loss.text = f"{float(self.app.st.get('loss_mm', 15.0)):.0f}"
        body.add_widget(self._indent_row(self.ed_loss, self._gray("절단 시 손실 보정 길이 (mm)")))

        body.add_widget(self._black("6. 모바일 대응 자동 폰트 크기 조절"))
        self.sw_auto_font = PillSwitch(active=bool(self.app.st.get("auto_font", False)))
        body.add_widget(self._indent_row(self.sw_auto_font, self._gray("해상도에 맞게 입력부 폰트 조절")))

        body.add_widget(self._black("7. 출력값 위치 이동"))
        self.sw_swap = PillSwitch(active=bool(self.app.st.get("swap_sections", False)))
        body.add_widget(self._indent_row(self.sw_swap, self._gray("‘절단 예상 길이’를 아래로 위치")))

        sig = Label(text="버전 1.0", font_name=FONT, color=(0.4,0.4,0.4,1),
                    size_hint=(1,None), height=dp(22), halign="right", valign="middle")
        sig.bind(size=lambda *_: setattr(sig, "text_size", sig.size))
        root.add_widget(sig)

    def _save_and_back(self):
        try:
            prefix = (self.ed_prefix.text or "SG94").upper()
            if not prefix:
                prefix = "SG94"
            try:
                out_font = int(self.ed_out_font.text or "15")
            except Exception:
                out_font = 15
            out_font = max(8, min(40, out_font))
            loss = _num_or_none(self.ed_loss.text)
            if loss is None or loss <= 0:
                loss = 15.0

            st = dict(self.app.st)
            st.update({
                "prefix": prefix,
                "round": bool(self.sw_round.active),
                "out_font": out_font,
                "hide_mm": bool(self.sw_hide_mm.active),
                "loss_mm": float(loss),
                "auto_font": bool(self.sw_auto_font.active),
                "swap_sections": bool(self.sw_swap.active),
            })
            save_settings(st)
            self.app.st = st
            self.app.main_screen.apply_settings(st)
            self.app.open_main()
        except Exception:
            self.app.open_main()

# ===== 앱 =====
class SlabApp(App):
    def build(self):
        _install_global_crash_hook(self.user_data_dir)
        self.st = load_settings()
        self.sm = ScreenManager(transition=NoTransition())
        from kivy.uix.label import Label
        self.main_screen = Label(text="메인 화면(테스트용)")
        self.settings_screen = SettingsScreen(self, name="settings")
        self.sm.add_widget(Screen(name="main", children=[self.main_screen]))
        self.sm.add_widget(self.settings_screen)
        self.sm.current = "settings"
        return self.sm
    def open_settings(self):
        self.sm.current = "settings"
    def open_main(self):
        self.sm.current = "main"

if __name__ == "__main__":
    SlabApp().run()
