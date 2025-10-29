# -*- coding: utf-8 -*-
# 버전 13 - 입력폭 v9로 롤백 + 설정(1,2 토글, 3 입력폭) + 상단 여백 수정 + 출력부 고정
import os, sys, json, traceback, re

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import NumericProperty, ListProperty, BooleanProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition

# -------------------- 공통 --------------------
FONT = "NanumGothic"
SETTINGS_FILE = "settings.json"

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

def load_settings():
    default = {
        "prefix": "SG94",
        "round_int": False,   # 정수 반올림 표기
        "out_font": 11        # 출력부 폰트 크기
    }
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                got = json.load(f)
            default.update(got or {})
    except Exception:
        pass
    return default

def save_settings(data):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# -------------------- 위젯 --------------------
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
        self.multiline = False
        self.halign = "left"
        self.padding = (dp(6), dp(5))
        self.font_name = FONT
        self.font_size = dp(16)
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
    """영문 대소문자 + 숫자만 허용 (설정 1번 전용)"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multiline = False
        self.halign = "left"
        self.padding = (dp(6), dp(5))
        self.font_name = FONT
        self.font_size = dp(16)
        self.height = dp(30)
        self.background_normal = ""
        self.background_active = ""
        self.cursor_width = dp(2)

    def insert_text(self, substring, from_undo=False):
        filtered = "".join(ch for ch in substring if ch.isalnum())
        return super().insert_text(filtered, from_undo=from_undo)

class ToggleSwitch(ButtonBehavior, BoxLayout):
    """ON/OFF 토글 (설정 2번)"""
    state_on = BooleanProperty(False)
    text_on = StringProperty("ON")
    text_off = StringProperty("OFF")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint = (None, None)
        self.height = dp(28)
        self.width = dp(64)
        with self.canvas.before:
            self._bg_color = Color(0.75, 0.75, 0.75, 1)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[(dp(14), dp(14))])
        self.bind(pos=self._sync, size=self._sync)

        self._label = Label(font_name=FONT, color=(1,1,1,1),
                            halign="center", valign="middle")
        self._label.bind(size=lambda *_: setattr(self._label, "text_size", self._label.size))
        self.add_widget(self._label)
        self._render()

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def _render(self):
        if self.state_on:
            self._bg_color.rgba = (0.22, 0.55, 0.22, 1)
            self._label.text = self.text_on
        else:
            self._bg_color.rgba = (0.6, 0.6, 0.6, 1)
            self._label.text = self.text_off

    def on_release(self, *args):
        self.state_on = not self.state_on
        self._render()

# -------------------- 스크린: 메인 --------------------
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = load_settings()
        self.prefix = self.settings.get("prefix", "SG94")

        Window.clearcolor = (0.93, 0.93, 0.93, 1)

        root = BoxLayout(orientation="vertical", padding=[dp(12), dp(8)], spacing=dp(8))
        self.add_widget(root)

        # 상단바 (설정)
        topbar = BoxLayout(size_hint=(1, None), height=dp(40))
        topbar.add_widget(Widget(size_hint=(1,1)))
        btn_settings = RoundedButton(text="설정", size_hint=(None, 1), width=dp(66),
                                     bg_color=[0.27,0.27,0.27,1], fg_color=[1,1,1,1])
        btn_settings.bind(on_release=lambda *_: self.manager.current = "settings")
        topbar.add_widget(btn_settings)
        root.add_widget(topbar)

        # 제목
        title = Label(text="후판 계산기", font_name=FONT, font_size=dp(32),
                      color=(0,0,0,1), halign="center", valign="middle",
                      size_hint=(1,None), height=dp(48))
        title.bind(size=lambda *_: setattr(title, "text_size", title.size))
        root.add_widget(title)

        # 입력 영역 (v9 폭으로 롤백)
        # 강번
        row_code = BoxLayout(orientation="horizontal", size_hint=(1, None),
                             height=dp(30), spacing=dp(4))
        row_code.add_widget(Label(text="강번 입력:", font_name=FONT, color=(0,0,0,1),
                                  size_hint=(None,1), width=dp(74), halign="right", valign="middle"))
        self._lbl_prefix = Label(text=self.prefix, font_name=FONT, color=(0,0,0,1),
                                 size_hint=(None,1), width=dp(44))
        row_code.add_widget(self._lbl_prefix)

        self.in_code_front = DigitInput(max_len=3, allow_float=False, size_hint=(None,1), width=dp(53))
        self.in_code_front.bind(text=self._auto_move_back)
        row_code.add_widget(self.in_code_front)

        row_code.add_widget(Label(text="-0", font_name=FONT, color=(0,0,0,1),
                                  size_hint=(None,1), width=dp(22)))
        self.in_code_back = DigitInput(max_len=1, allow_float=False, size_hint=(None,1), width=dp(20))
        row_code.add_widget(self.in_code_back)
        root.add_widget(row_code)

        # 실제 Slab 길이
        row_total = BoxLayout(orientation="horizontal", size_hint=(1,None),
                              height=dp(30), spacing=dp(4))
        row_total.add_widget(Label(text="실제 Slab 길이:", font_name=FONT, color=(0,0,0,1),
                                   size_hint=(None,1), width=dp(104), halign="right", valign="middle"))
        self.in_total = DigitInput(max_len=5, allow_float=True, size_hint=(None,1), width=dp(70))
        row_total.add_widget(self.in_total)
        row_total.add_widget(Widget())
        root.add_widget(row_total)

        # 지시길이들
        grid = GridLayout(cols=4, size_hint=(1,None), height=dp(30*3+8*2),
                          row_default_height=dp(30), row_force_default=True, spacing=dp(8))
        self.in_p1 = DigitInput(max_len=4, allow_float=True, size_hint=(None,1), width=dp(65))
        self.in_p2 = DigitInput(max_len=4, allow_float=True, size_hint=(None,1), width=dp(65))
        self.in_p3 = DigitInput(max_len=4, allow_float=True, size_hint=(None,1), width=dp(65))

        grid.add_widget(Label(text="1번 지시길이:", font_name=FONT, color=(0,0,0,1),
                              size_hint=(None,1), width=dp(104), halign="right", valign="middle"))
        grid.add_widget(self.in_p1); grid.add_widget(Label()); grid.add_widget(Label())

        grid.add_widget(Label(text="2번 지시길이:", font_name=FONT, color=(0,0,0,1),
                              size_hint=(None,1), width=dp(104), halign="right", valign="middle"))
        grid.add_widget(self.in_p2)
        b21 = RoundedButton(text="← 1번", bg_color=[0.8,0.8,0.8,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(58))
        b21.bind(on_release=lambda *_: self._copy(self.in_p1, self.in_p2))
        grid.add_widget(b21); grid.add_widget(Label())

        grid.add_widget(Label(text="3번 지시길이:", font_name=FONT, color=(0,0,0,1),
                              size_hint=(None,1), width=dp(104), halign="right", valign="middle"))
        grid.add_widget(self.in_p3)
        btn_row = BoxLayout(orientation="horizontal", spacing=dp(8),
                            size_hint=(None,1), width=dp(58*2+8))
        b31 = RoundedButton(text="← 1번", bg_color=[0.8,0.8,0.8,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(58))
        b32 = RoundedButton(text="← 2번", bg_color=[0.8,0.8,0.8,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(58))
        b31.bind(on_release=lambda *_: self._copy(self.in_p1, self.in_p3))
        b32.bind(on_release=lambda *_: self._copy(self.in_p2, self.in_p3))
        btn_row.add_widget(b31); btn_row.add_widget(b32)
        grid.add_widget(btn_row); grid.add_widget(Label())
        root.add_widget(grid)

        # 계산 버튼
        btn_calc = RoundedButton(text="계산하기", bg_color=[0.23,0.53,0.23,1],
                                 fg_color=[1,1,1,1], size_hint=(1,None), height=dp(44), radius=dp(10))
        btn_calc.bind(on_release=lambda *_: self.calculate())
        root.add_widget(btn_calc)

        # 경고 바(아이콘/텍스트) - 기본 숨김
        self.warn_bar = BoxLayout(orientation="horizontal", spacing=dp(6),
                                  size_hint=(1,None), height=0, opacity=0)
        if os.path.exists("warning.png"):
            try:
                icon = Image(source="warning.png", size_hint=(None,None), size=(dp(18),dp(18)))
            except Exception:
                icon = Label(text="⚠", font_name=FONT, color=(1,0.2,0.2,1),
                             size_hint=(None,None), size=(dp(18),dp(18)))
        else:
            icon = Label(text="⚠", font_name=FONT, color=(1,0.2,0.2,1),
                         size_hint=(None,None), size=(dp(18),dp(18)))
        self.warn_msg = Label(text="", font_name=FONT, color=(0,0,0,1),
                              halign="left", valign="middle")
        self.warn_msg.bind(size=lambda *_: setattr(self.warn_msg, "text_size", self.warn_msg.size))
        self.warn_bar.add_widget(icon); self.warn_bar.add_widget(self.warn_msg)
        root.add_widget(self.warn_bar)

        # 출력부: 하단 고정(스크롤 제거, 선택/복사 가능)
        out_wrap = BoxLayout(orientation="vertical", size_hint=(1,1))
        self.out = TextInput(readonly=True, font_name=FONT, font_size=dp(self.settings.get("out_font", 11)),
                             background_normal="", background_active="", padding=(dp(8), dp(8)),
                             size_hint=(1,1))
        out_wrap.add_widget(self.out)

        # 하단 버전
        sig = Label(text="버전 13", font_name=FONT, color=(0.4,0.4,0.4,1),
                    size_hint=(1,None), height=dp(22), halign="right", valign="middle")
        sig.bind(size=lambda *_: setattr(sig, "text_size", sig.size))
        out_wrap.add_widget(sig)
        root.add_widget(out_wrap)

    # helpers
    def _auto_move_back(self, instance, value):
        if len(value) >= 3:
            self.in_code_back.focus = True

    def _copy(self, src, dst):
        dst.text = src.text

    def _show_warn(self, msg):
        self.warn_msg.text = msg
        self.warn_bar.height = dp(28)
        self.warn_bar.opacity = 1

    def _hide_warn(self):
        self.warn_msg.text = ""
        self.warn_bar.height = 0
        self.warn_bar.opacity = 0

    # 계산
    def calculate(self):
        try:
            slab = _num_or_none(self.in_total.text)
            p1, p2, p3 = map(_num_or_none, [self.in_p1.text, self.in_p2.text, self.in_p3.text])

            if slab is None or slab <= 0:
                self.out.text = ""
                self._show_warn("실제 Slab 길이를 올바르게 입력하세요.")
                return

            guides = [v for v in (p1, p2, p3) if v is not None and v > 0]
            if len(guides) < 2:
                self.out.text = ""
                self._show_warn("최소 2개 이상의 지시길이를 입력하세요.")
                return
            self._hide_warn()

            loss = 15.0
            total_loss = loss * (len(guides) - 1)
            remain = slab - (sum(guides) + total_loss)
            add_each = remain / len(guides)
            real = [g + add_each for g in guides]

            mm = " mm"
            cf = (self.in_code_front.text or "").strip()
            cb = (self.in_code_back.text or "").strip()

            as_int = self.settings.get("round_int", False)

            def fmt(x):
                return f"{round_half_up(x):,}" if as_int else f"{x:,.1f}"

            lines = []
            if cf and cb:
                lines.append(f"▶ 강번: {self.settings.get('prefix','SG94')}{cf}-0{cb}\n")

            lines.append(f"▶ Slab 실길이: {fmt(slab)}{'' if as_int else mm}")
            for i, g in enumerate(guides, 1):
                lines.append(f"▶ {i}번 지시길이: {fmt(g)}{'' if as_int else mm}")
            lines.append(f"▶ 절단 손실: {fmt(loss)}{'' if as_int else mm} × {len(guides)-1} = {fmt(total_loss)}{'' if as_int else mm}")
            lines.append(f"▶ 전체 여유길이: {fmt(remain)}{'' if as_int else mm} → 각 +{fmt(add_each)}{'' if as_int else mm}\n")

            lines.append("▶ 절단 후 예상 길이:")
            for i, r in enumerate(real, 1):
                lines.append(f"   {i}번: {fmt(r)}{'' if as_int else mm}")

            visual = "H"
            for i, r in enumerate(real, 1):
                mark = round_half_up(r + loss/2)
                visual += f"-{i}번({mark})-"
            visual += "T"
            lines.append("\n▶ 시각화 (절단 마킹 포인트):")
            lines.append(visual)

            self.out.font_size = dp(self.settings.get("out_font", 11))
            self.out.text = "\n".join(lines)
        except Exception as e:
            self._show_warn(f"오류: {e}")
            raise

    # 설정 저장 후 메인 반영
    def apply_settings(self, st):
        self.settings.update(st)
        self.prefix = self.settings.get("prefix", "SG94")
        self._lbl_prefix.text = self.prefix
        self.out.font_size = dp(self.settings.get("out_font", 11))

# -------------------- 스크린: 설정 --------------------
class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = load_settings()

        root = BoxLayout(orientation="vertical", padding=[dp(12), dp(8)], spacing=dp(8))
        self.add_widget(root)

        # 상단 저장 버튼
        topbar = BoxLayout(size_hint=(1,None), height=dp(40))
        topbar.add_widget(Widget())
        btn_save = RoundedButton(text="저장", size_hint=(None,1), width=dp(66),
                                 bg_color=[0.27,0.27,0.27,1], fg_color=[1,1,1,1])
        btn_save.bind(on_release=lambda *_: self._save_and_back())
        topbar.add_widget(btn_save)
        root.add_widget(topbar)

        # 제목
        title = Label(text="환경설정", font_name=FONT, font_size=dp(32),
                      color=(0,0,0,1), halign="center", valign="middle",
                      size_hint=(1,None), height=dp(48))
        title.bind(size=lambda *_: setattr(title, "text_size", title.size))
        root.add_widget(title)

        # 내용 컨테이너 (제목 바로 아래부터 시작하도록 여백 최소)
        wrap = BoxLayout(orientation="vertical", spacing=dp(10), size_hint=(1,1))
        root.add_widget(wrap)

        # 1. 강번 접두어
        wrap.add_widget(Label(text="1. 강번 접두어", font_name=FONT, color=(0,0,0,1),
                              size_hint=(1,None), height=dp(22), halign="left", valign="middle"))
        row1 = BoxLayout(orientation="horizontal", size_hint=(1,None), height=dp(30), spacing=dp(8))
        row1.add_widget(Label(text="영문/숫자만", font_name=FONT, color=(0,0,0,1),
                              size_hint=(None,1), width=dp(90), halign="left", valign="middle"))
        self.ed_prefix = AlnumInput(text=self.settings.get("prefix","SG94"),
                                    size_hint=(None,1), width=dp(53))
        row1.add_widget(self.ed_prefix)
        row1.add_widget(Widget())
        wrap.add_widget(row1)

        # 2. 정수 결과 반올림 (토글)
        wrap.add_widget(Label(text="2. 정수 결과 반올림", font_name=FONT, color=(0,0,0,1),
                              size_hint=(1,None), height=dp(22), halign="left", valign="middle"))
        row2 = BoxLayout(orientation="horizontal", size_hint=(1,None), height=dp(30), spacing=dp(8))
        self.tg_round = ToggleSwitch(state_on=bool(self.settings.get("round_int", False)))
        row2.add_widget(self.tg_round)
        row2.add_widget(Label(text="출력부 소수점 값을 정수로 표시",
                              font_name=FONT, color=(0.5,0.5,0.5,1),
                              size_hint=(1,1), halign="left", valign="middle"))
        row2.children[0].bind(size=lambda *_: setattr(row2.children[0], "text_size", row2.children[0].size))
        wrap.add_widget(row2)

        # 3. 출력부 폰트 크기
        wrap.add_widget(Label(text="3. 출력부 폰트 크기", font_name=FONT, color=(0,0,0,1),
                              size_hint=(1,None), height=dp(22), halign="left", valign="middle"))
        row3 = BoxLayout(orientation="horizontal", size_hint=(1,None), height=dp(30), spacing=dp(8))
        row3.add_widget(Label(text="기본 11", font_name=FONT, color=(0,0,0,1),
                              size_hint=(None,1), width=dp(60), halign="left", valign="middle"))
        self.ed_out_font = DigitInput(max_len=2, allow_float=False, size_hint=(None,1), width=dp(40))
        self.ed_out_font.text = str(int(self.settings.get("out_font", 11)))
        row3.add_widget(self.ed_out_font)
        row3.add_widget(Widget())
        wrap.add_widget(row3)

        # 하단 버전
        sig = Label(text="버전 13", font_name=FONT, color=(0.4,0.4,0.4,1),
                    size_hint=(1,None), height=dp(22), halign="right", valign="middle"))
        sig.bind(size=lambda *_: setattr(sig, "text_size", sig.size))
        wrap.add_widget(sig)

    def _save_and_back(self):
        # prefix: 영문숫자만
        prefix = (self.ed_prefix.text or "SG94")
        prefix = re.sub(r"[^0-9A-Za-z]", "", prefix)
        if not prefix:
            prefix = "SG94"

        # out_font: 최소 8~최대 32 정도로 클램프
        try:
            out_font = int(self.ed_out_font.text or "11")
        except Exception:
            out_font = 11
        out_font = max(8, min(32, out_font))

        st = {
            "prefix": prefix,
            "round_int": bool(self.tg_round.state_on),
            "out_font": out_font
        }
        save_settings(st)

        # 메인에 반영
        ms = self.manager.get_screen("main")
        ms.apply_settings(st)

        self.manager.current = "main"

# -------------------- 앱 --------------------
class SlabApp(App):
    def build(self):
        _install_global_crash_hook(self.user_data_dir)
        sm = ScreenManager(transition=NoTransition())
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(SettingsScreen(name="settings"))
        return sm

if __name__ == "__main__":
    SlabApp().run()
