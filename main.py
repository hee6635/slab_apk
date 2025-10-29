# -*- coding: utf-8 -*-
# 버전 14 - 입력폭 v9 복원 + 전체화면 설정창 + 스크롤 제거 + 단위(mm) 표시 토글 (2025-10-29)

import os, sys, json, traceback
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.properties import NumericProperty, ListProperty, BooleanProperty, StringProperty
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.switch import Switch
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition

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

# ---------------- 공통 위젯 ----------------
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
    """영문/숫자만 허용(대문자 변환) - 접두어 입력"""
    max_len = NumericProperty(6)

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
        filtered = "".join(ch for ch in substring.upper() if ch.isalnum())
        remain = max(0, self.max_len - len(self.text))
        if remain <= 0:
            return
        if len(filtered) > remain:
            filtered = filtered[:remain]
        return super().insert_text(filtered, from_undo=from_undo)

# ---------------- 메인 스크린 ----------------
class MainScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.build_ui()

    def build_ui(self):
        Window.clearcolor = (0.93, 0.93, 0.93, 1)
        root = BoxLayout(orientation="vertical", padding=[dp(12), dp(8)], spacing=dp(6))

        # 상단바(우상단 설정)
        topbar = BoxLayout(size_hint=(1, None), height=dp(40), spacing=0)
        topbar.add_widget(Widget())
        btn_settings = RoundedButton(text="설정", size_hint=(None, 1), width=dp(66),
                                     bg_color=[0.27, 0.27, 0.27, 1], fg_color=[1, 1, 1, 1])
        btn_settings.bind(on_release=lambda *_: self.app.open_settings())
        topbar.add_widget(btn_settings)
        root.add_widget(topbar)

        # 제목
        title_row = BoxLayout(size_hint=(1, None), height=dp(40))
        title = Label(text="후판 계산기", font_name=FONT, font_size=dp(28),
                      color=(0, 0, 0, 1), halign="center", valign="middle")
        title.bind(size=lambda *_: setattr(title, "text_size", title.size))
        title_row.add_widget(title)
        root.add_widget(title_row)

        # 강번 입력 (v9 폭)
        row_code = BoxLayout(orientation="horizontal", size_hint=(1, None),
                             height=dp(30), spacing=dp(4))
        lab_code = Label(text="강번 입력:", font_name=FONT, color=(0,0,0,1),
                         size_hint=(None,1), width=dp(74), halign="right", valign="middle")
        lab_code.bind(size=lambda *_: setattr(lab_code, "text_size", lab_code.size))
        row_code.add_widget(lab_code)

        self.lab_prefix = Label(text=self.app.settings.get("prefix", self.app.prefix_default),
                                font_name=FONT, color=(0,0,0,1),
                                size_hint=(None,1), width=dp(44), halign="center", valign="middle")
        self.lab_prefix.bind(size=lambda *_: setattr(self.lab_prefix, "text_size", self.lab_prefix.size))
        row_code.add_widget(self.lab_prefix)

        self.in_code_front = DigitInput(max_len=3, allow_float=False,
                                        size_hint=(None,1), width=dp(60))
        self.in_code_front.bind(text=self._auto_move_back)
        row_code.add_widget(self.in_code_front)

        lab_dash = Label(text="-0", font_name=FONT, color=(0,0,0,1),
                         size_hint=(None,1), width=dp(22), halign="center", valign="middle")
        lab_dash.bind(size=lambda *_: setattr(lab_dash, "text_size", lab_dash.size))
        row_code.add_widget(lab_dash)

        self.in_code_back = DigitInput(max_len=1, allow_float=False,
                                       size_hint=(None,1), width=dp(40))
        row_code.add_widget(self.in_code_back)
        root.add_widget(row_code)

        # 실제 Slab 길이
        row_total = BoxLayout(orientation="horizontal", size_hint=(1, None),
                              height=dp(30), spacing=dp(4))
        lab_total = Label(text="실제 Slab 길이:", font_name=FONT, color=(0,0,0,1),
                          size_hint=(None,1), width=dp(104), halign="right", valign="middle")
        lab_total.bind(size=lambda *_: setattr(lab_total, "text_size", lab_total.size))
        row_total.add_widget(lab_total)

        self.in_total = DigitInput(max_len=5, allow_float=True, size_hint=(None,1), width=dp(124))
        row_total.add_widget(self.in_total)
        row_total.add_widget(Widget())
        root.add_widget(row_total)

        # 지시길이
        grid = GridLayout(cols=4, size_hint=(1, None), height=dp(30*3+8*2),
                          row_default_height=dp(30), row_force_default=True, spacing=dp(8))

        self.in_p1 = DigitInput(max_len=4, allow_float=True, size_hint=(None,1), width=dp(100))
        self.in_p2 = DigitInput(max_len=4, allow_float=True, size_hint=(None,1), width=dp(100))
        self.in_p3 = DigitInput(max_len=4, allow_float=True, size_hint=(None,1), width=dp(100))

        def _lab(text, w):
            L = Label(text=text, font_name=FONT, color=(0,0,0,1),
                      size_hint=(None,1), width=w, halign="right", valign="middle")
            L.bind(size=lambda *_: setattr(L, "text_size", L.size))
            return L

        grid.add_widget(_lab("1번 지시길이:", dp(104))); grid.add_widget(self.in_p1); grid.add_widget(Label()); grid.add_widget(Label())
        grid.add_widget(_lab("2번 지시길이:", dp(104))); grid.add_widget(self.in_p2)
        b21 = RoundedButton(text="← 1번", bg_color=[0.8,0.8,0.8,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(58))
        b21.bind(on_release=lambda *_: self._copy(self.in_p1, self.in_p2))
        grid.add_widget(b21); grid.add_widget(Label())

        grid.add_widget(_lab("3번 지시길이:", dp(104))); grid.add_widget(self.in_p3)
        btn_row = BoxLayout(orientation="horizontal", spacing=dp(8),
                            size_hint=(None,1), width=dp(58*2 + 8))
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
        btn_calc = RoundedButton(text="계산하기", bg_color=[0.23, 0.53, 0.23, 1],
                                 fg_color=[1,1,1,1], size_hint=(1, None),
                                 height=dp(44), radius=dp(10))
        btn_calc.bind(on_release=lambda *_: self.calculate())
        root.add_widget(btn_calc)

        # 경고 바
        self.warn_bar = BoxLayout(orientation="horizontal", spacing=dp(6),
                                  size_hint=(1, None), height=0, opacity=0)
        if os.path.exists("warning.png"):
            try:
                self.warn_icon = Image(source="warning.png", size_hint=(None, None), size=(dp(18), dp(18)))
            except Exception:
                self.warn_icon = Label(text="⚠", font_name=FONT, color=(1,0.2,0.2,1),
                                       size_hint=(None, None), size=(dp(18), dp(18)))
        else:
            self.warn_icon = Label(text="⚠", font_name=FONT, color=(1,0.2,0.2,1),
                                   size_hint=(None, None), size=(dp(18), dp(18)))
        self.warn_msg = Label(text="", font_name=FONT, color=(0,0,0,1),
                              halign="left", valign="middle")
        self.warn_msg.bind(size=lambda *_: setattr(self.warn_msg, "text_size", self.warn_msg.size))
        self.warn_bar.add_widget(self.warn_icon); self.warn_bar.add_widget(self.warn_msg)
        root.add_widget(self.warn_bar)

        # 출력부(간단: 남는 공간 채우는 흰 박스 + 라벨 1개)
        PAD = dp(8)
        self.result_area = BoxLayout(orientation="vertical",
                                     size_hint=(1, 1),
                                     padding=[PAD, PAD, PAD, PAD], spacing=0)
        with self.result_area.canvas.before:
            Color(1, 1, 1, 1)
            self._bg_rect = RoundedRectangle(size=(0, 0), pos=(0, 0),
                                             radius=[(dp(6), dp(6))] * 4)
        self.result_area.bind(size=self._bg_follow, pos=self._bg_follow)

        self.result_label = Label(text="",
                                  font_name=FONT, color=(0, 0, 0, 1),
                                  size_hint=(1, 1),
                                  halign="left", valign="top")
        self.result_label.bind(size=lambda *_: self._sync_text_wrap())
        self._apply_output_font()

        self.result_area.add_widget(self.result_label)
        root.add_widget(self.result_area)

        # 하단 버전 표기
        sig = Label(text="버전 14", font_name=FONT, color=(0.4,0.4,0.4,1),
                    halign="right", valign="middle", size_hint=(1, None), height=dp(22))
        sig.bind(size=lambda *_: setattr(sig, "text_size", sig.size))
        root.add_widget(sig)

        self.add_widget(root)

    # helpers
    def _sync_text_wrap(self):
        self.result_label.text_size = (self.result_label.width, self.result_label.height)

    def _bg_follow(self, *_):
        self._bg_rect.pos, self._bg_rect.size = self.result_area.pos, self.result_area.size

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

    def _apply_output_font(self):
        try:
            fs = int(self.app.settings.get("out_font", 15))
            self.result_label.font_size = dp(fs)
        except Exception:
            self.result_label.font_size = dp(15)

    # 계산
    def calculate(self):
        try:
            slab = _num_or_none(self.in_total.text)
            p1, p2, p3 = map(_num_or_none, [self.in_p1.text, self.in_p2.text, self.in_p3.text])

            if slab is None or slab <= 0:
                self.result_label.text = ""
                self._show_warn("실제 Slab 길이를 올바르게 입력하세요.")
                return

            guides = [v for v in (p1, p2, p3) if v is not None and v > 0]
            if len(guides) < 2:
                self.result_label.text = ""
                self._show_warn("최소 2개 이상의 지시길이를 입력하세요.")
                return

            self._hide_warn()

            loss = 15.0
            total_loss = loss * (len(guides) - 1)
            remain = slab - (sum(guides) + total_loss)
            add_each = remain / len(guides) if len(guides) else 0.0
            real = [g + add_each for g in guides]

            do_round_int = bool(self.app.settings.get("round", False))
            no_unit = bool(self.app.settings.get("no_unit", False))
            mm = "" if no_unit else " mm"

            def fmt(x):
                return f"{round_half_up(x)}" if do_round_int else f"{x:,.1f}"

            cf = (self.in_code_front.text or "").strip()
            cb = (self.in_code_back.text or "").strip()

            lines = []
            if cf and cb:
                lines.append(f"▶ 강번: {self.lab_prefix.text}{cf}-0{cb}\n")

            lines.append(f"▶ Slab 실길이: {fmt(slab)}{mm}")
            for i, g in enumerate(guides, 1):
                lines.append(f"▶ {i}번 지시길이: {fmt(g)}{mm}")
            lines.append(f"▶ 절단 손실: {fmt(loss)}{mm} × {len(guides)-1} = {fmt(total_loss)}{mm}")
            lines.append(f"▶ 전체 여유길이: {fmt(remain)}{mm} → 각 +{fmt(add_each)}{mm}\n")

            lines.append("▶ 절단 후 예상 길이:")
            for i, r in enumerate(real, 1):
                lines.append(f"   {i}번: {fmt(r)}{mm}")

            visual = "H"
            for i, r in enumerate(real, 1):
                mark = round_half_up(r + loss / 2) if do_round_int else (r + loss/2)
                mark_s = f"{int(mark)}" if do_round_int else f"{mark:,.1f}"
                visual += f"-{i}번({mark_s})-"
            visual += "T"
            lines.append("\n▶ 시각화 (절단 마킹 포인트):")
            lines.append(visual)

            self.result_label.text = "\n".join(lines)

        except Exception as e:
            self._show_warn(f"오류: {e}")
            raise

# ---------------- 설정 스크린 ----------------
class SettingsScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.build_ui()

    def build_ui(self):
        Window.clearcolor = (0.93, 0.93, 0.93, 1)
        root = BoxLayout(orientation="vertical", padding=[dp(12), dp(8)], spacing=dp(6))

        # 상단바
        topbar = BoxLayout(size_hint=(1, None), height=dp(40))
        topbar.add_widget(Widget())
        btn_save = RoundedButton(text="저장", size_hint=(None, 1), width=dp(66),
                                 bg_color=[0.23, 0.53, 0.23, 1], fg_color=[1, 1, 1, 1])
        btn_save.bind(on_release=lambda *_: self._save_and_back())
        topbar.add_widget(btn_save)
        root.add_widget(topbar)

        # 제목
        title = Label(text="환경설정", font_name=FONT, font_size=dp(24),
                      color=(0,0,0,1), halign="center", valign="middle",
                      size_hint=(1,None), height=dp(44))
        title.bind(size=lambda *_: setattr(title, "text_size", title.size))
        root.add_widget(title)

        # 1) 접두어 (입력 앞으로, 설명 뒤 회색)
        row1 = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(30), spacing=dp(6))
        self.in_prefix = AlnumInput(max_len=6, size_hint=(None,1), width=dp(53))
        self.in_prefix.text = self.app.settings.get("prefix", self.app.prefix_default)
        row1.add_widget(self.in_prefix)
        lab1_desc = Label(text=" 강번 앞에 붙는 접두어(영문/숫자)", font_name=FONT, color=(0.4,0.4,0.4,1),
                          halign="left", valign="middle")
        lab1_desc.bind(size=lambda *_: setattr(lab1_desc, "text_size", lab1_desc.size))
        row1.add_widget(lab1_desc)
        root.add_widget(row1)

        # 2) 정수 결과 반올림 (스위치)
        row2_title = Label(text="정수 결과 반올림", font_name=FONT, color=(0,0,0,1),
                           size_hint=(1,None), height=dp(24), halign="left", valign="middle")
        row2_title.bind(size=lambda *_: setattr(row2_title, "text_size", row2_title.size))
        root.add_widget(row2_title)

        row2 = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(30), spacing=dp(8))
        self.sw_round = Switch(active=bool(self.app.settings.get("round", False)),
                               size_hint=(None,None), size=(dp(48), dp(24)))
        row2.add_widget(self.sw_round)
        lab2_desc = Label(text=" 출력부 소수값을 정수로 표시", font_name=FONT, color=(0.4,0.4,0.4,1),
                          halign="left", valign="middle")
        lab2_desc.bind(size=lambda *_: setattr(lab2_desc, "text_size", lab2_desc.size))
        row2.add_widget(lab2_desc)
        root.add_widget(row2)

        # 3) 출력부 폰트 크기
        row3_title = Label(text="출력부 폰트 크기", font_name=FONT, color=(0,0,0,1),
                           size_hint=(1,None), height=dp(24), halign="left", valign="middle")
        row3_title.bind(size=lambda *_: setattr(row3_title, "text_size", row3_title.size))
        root.add_widget(row3_title)

        row3 = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(30), spacing=dp(6))
        self.in_out_font = DigitInput(max_len=2, allow_float=False, size_hint=(None,1), width=dp(40))
        try:
            self.in_out_font.text = str(int(self.app.settings.get("out_font", 15)))
        except Exception:
            self.in_out_font.text = "15"
        row3.add_widget(self.in_out_font)
        row3.add_widget(Label(text=" px", font_name=FONT, color=(0.4,0.4,0.4,1),
                              size_hint=(None,1), width=dp(20), halign="left", valign="middle"))
        row3.add_widget(Widget())
        root.add_widget(row3)

        # 4) 결과값 mm 표시 제거 (스위치)
        row4_title = Label(text="결과값 mm 표시 제거", font_name=FONT, color=(0,0,0,1),
                           size_hint=(1,None), height=dp(24), halign="left", valign="middle")
        row4_title.bind(size=lambda *_: setattr(row4_title, "text_size", row4_title.size))
        root.add_widget(row4_title)

        row4 = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(30), spacing=dp(8))
        self.sw_no_unit = Switch(active=bool(self.app.settings.get("no_unit", False)),
                                 size_hint=(None,None), size=(dp(48), dp(24)))
        row4.add_widget(self.sw_no_unit)
        lab4_desc = Label(text=" 체크 시 단위(mm) 문구 제거, 숫자만 표시", font_name=FONT, color=(0.4,0.4,0.4,1),
                          halign="left", valign="middle")
        lab4_desc.bind(size=lambda *_: setattr(lab4_desc, "text_size", lab4_desc.size))
        row4.add_widget(lab4_desc)
        root.add_widget(row4)

        # 하단 버전
        sig = Label(text="버전 14(설정)", font_name=FONT, color=(0.4,0.4,0.4,1),
                    halign="right", valign="middle", size_hint=(1, None), height=dp(22))
        sig.bind(size=lambda *_: setattr(sig, "text_size", sig.size))
        root.add_widget(sig)

        self.add_widget(root)

    def _save_and_back(self):
        prefix = (self.in_prefix.text or "").upper().strip() or self.app.prefix_default
        try:
            out_font = int(self.in_out_font.text or "15")
            out_font = max(8, min(40, out_font))
        except Exception:
            out_font = 15

        data = dict(self.app.settings)
        data.update({
            "prefix": prefix,
            "round": bool(self.sw_round.active),
            "out_font": out_font,
            "no_unit": bool(self.sw_no_unit.active),
        })
        self.app._save_settings(data)

        # 메인에 즉시 반영
        main = self.app.main_screen
        main.lab_prefix.text = prefix
        main._apply_output_font()

        # 메인으로 전환
        self.app.sm.current = "main"

# ---------------- 앱 ----------------
class SlabApp(App):
    prefix_default = "SG94"

    def build(self):
        _install_global_crash_hook(self.user_data_dir)
        self.settings = self._load_settings()

        self.sm = ScreenManager(transition=NoTransition())
        self.main_screen = MainScreen(self, name="main")
        self.settings_screen = SettingsScreen(self, name="settings")
        self.sm.add_widget(self.main_screen)
        self.sm.add_widget(self.settings_screen)
        self.sm.current = "main"
        return self.sm

    def open_settings(self):
        self.sm.current = "settings"

    def _load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {"prefix": self.prefix_default, "round": False, "out_font": 15, "no_unit": False}
        return {"prefix": self.prefix_default, "round": False, "out_font": 15, "no_unit": False}

    def _save_settings(self, data: dict):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.settings = data
        except Exception:
            pass

if __name__ == "__main__":
    SlabApp().run()
