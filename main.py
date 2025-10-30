# -*- coding: utf-8 -*-
# 버전 18R2a - 설정 타이틀 높이 34dp / 타이틀↔1번 44dp / 상단 여백·버튼 크기 통일 / 버전 1.0
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

# ===== 공통 레이아웃 상수(요청 반영) =====
TOP_PAD = dp(10)                 # 저장/설정 버튼이 있는 상단 패딩(메인/설정 통일)
TOPBAR_H = dp(40)                # 상단바 높이(메인/설정 통일)
TOPBAR_BTN_W = dp(72)            # 상단 버튼 폭(메인/설정 통일)
SETTINGS_TITLE_TO_ITEM1 = dp(44) # 설정 타이틀 ↔ 1번 간격 (51→44)

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
               # 내부 여백 유지(요청 사항 기존 유지)
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

# ===== 설정 로드/저장 =====
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
    st = _defaults()
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                got = json.load(f) or {}
            st.update(got)
    except Exception:
        pass
    return st

def save_settings(data: dict):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ===== 메인 화면 =====
class MainScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.build_ui()

    def build_ui(self):
        Window.clearcolor = (0.93, 0.93, 0.93, 1)
        root = BoxLayout(orientation="vertical",
                         padding=[dp(12), TOP_PAD, dp(12), dp(6)],  # ← 상단 패딩 통일
                         spacing=dp(6))
        self.add_widget(root)

        # 상단바 (오른쪽 설정) — 버튼 크기 통일
        topbar = BoxLayout(size_hint=(1, None), height=TOPBAR_H, spacing=0)
        topbar.add_widget(Widget())
        btn_settings = RoundedButton(text="설정", size_hint=(None,1), width=TOPBAR_BTN_W,
                                     bg_color=[0.27,0.27,0.27,1], fg_color=[1,1,1,1])
        btn_settings.bind(on_release=lambda *_: self.app.open_settings())
        topbar.add_widget(btn_settings)
        root.add_widget(topbar)

        # 제목(메인 타이틀은 기존 유지)
        title = Label(text="후판 계산기", font_name=FONT, font_size=dp(32),
                      color=(0,0,0,1), halign="center", valign="middle",
                      size_hint=(1,None), height=dp(44))
        title.bind(size=lambda *_: setattr(title, "text_size", title.size))
        root.add_widget(title)

        # 강번 입력
        row_code = BoxLayout(orientation="horizontal", size_hint=(1,None),
                             height=dp(30), spacing=dp(4))
        lab = Label(text="강번 입력:", font_name=FONT, color=(0,0,0,1),
                    size_hint=(None,1), width=dp(92), halign="right", valign="middle")
        lab.bind(size=lambda *_: setattr(lab, "text_size", lab.size))
        row_code.add_widget(lab)

        self.lab_prefix = Label(text=self.app.st.get("prefix", "SG94"),
                                font_name=FONT, color=(0,0,0,1),
                                size_hint=(None,1), width=dp(44),
                                halign="center", valign="middle")
        self.lab_prefix.bind(size=lambda *_: setattr(self.lab_prefix, "text_size", self.lab_prefix.size))
        row_code.add_widget(self.lab_prefix)

        self.in_code_front = DigitInput(max_len=3, allow_float=False, width=dp(60))
        self.in_code_front.bind(text=self._auto_move_back)
        row_code.add_widget(self.in_code_front)

        dash = Label(text="-0", font_name=FONT, color=(0,0,0,1),
                     size_hint=(None,1), width=dp(22), halign="center", valign="middle")
        dash.bind(size=lambda *_: setattr(dash, "text_size", dash.size))
        row_code.add_widget(dash)

        self.in_code_back = DigitInput(max_len=1, allow_float=False, width=dp(32))
        row_code.add_widget(self.in_code_back)
        root.add_widget(row_code)

        # Slab 실길이
        row_total = BoxLayout(orientation="horizontal", size_hint=(1,None),
                              height=dp(30), spacing=dp(4))
        lab_t = Label(text="Slab 실길이:", font_name=FONT, color=(0,0,0,1),
                      size_hint=(None,1), width=dp(104), halign="right", valign="middle")
        lab_t.bind(size=lambda *_: setattr(lab_t, "text_size", lab_t.size))
        row_total.add_widget(lab_t)
        self.in_total = DigitInput(max_len=5, allow_float=True, width=dp(74))
        row_total.add_widget(self.in_total)
        row_total.add_widget(Widget())
        root.add_widget(row_total)

        # 지시길이 1~3
        grid = GridLayout(cols=4, size_hint=(1,None), height=dp(30*3+8*2),
                          row_default_height=dp(30), row_force_default=True, spacing=dp(8))
        def _lab(text, w):
            L = Label(text=text, font_name=FONT, color=(0,0,0,1),
                      size_hint=(None,1), width=w, halign="right", valign="middle")
            L.bind(size=lambda *_: setattr(L, "text_size", L.size))
            return L
        self.in_p1 = DigitInput(max_len=4, allow_float=True, width=dp(66))
        self.in_p2 = DigitInput(max_len=4, allow_float=True, width=dp(66))
        self.in_p3 = DigitInput(max_len=4, allow_float=True, width=dp(66))

        grid.add_widget(_lab("1번 지시길이:", dp(104))); grid.add_widget(self.in_p1); grid.add_widget(Label()); grid.add_widget(Label())

        grid.add_widget(_lab("2번 지시길이:", dp(104))); grid.add_widget(self.in_p2)
        b21 = RoundedButton(text="← 1번", bg_color=[0.8,0.8,0.8,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(58))
        b21.font_size = dp(17)
        b21.bind(on_release=lambda *_: self._copy(self.in_p1, self.in_p2))
        grid.add_widget(b21); grid.add_widget(Label())

        grid.add_widget(_lab("3번 지시길이:", dp(104))); grid.add_widget(self.in_p3)
        btn_row = BoxLayout(orientation="horizontal", spacing=dp(8),
                            size_hint=(None,1), width=dp(58*2+8))
        b31 = RoundedButton(text="← 1번", bg_color=[0.8,0.8,0.8,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(58))
        b31.font_size = dp(17)
        b32 = RoundedButton(text="← 2번", bg_color=[0.8,0.8,0.8,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(58))
        b32.font_size = dp(17)
        b31.bind(on_release=lambda *_: self._copy(self.in_p1, self.in_p3))
        b32.bind(on_release=lambda *_: self._copy(self.in_p2, self.in_p3))
        btn_row.add_widget(b31); btn_row.add_widget(b32)
        grid.add_widget(btn_row); grid.add_widget(Label())
        root.add_widget(grid)

        # 계산 버튼
        btn_calc = RoundedButton(text="계산하기", bg_color=[0.23, 0.53, 0.23, 1],
                                 fg_color=[1,1,1,1], size_hint=(1,None),
                                 height=dp(44), radius=dp(10))
        btn_calc.bind(on_release=lambda *_: self.calculate())
        root.add_widget(btn_calc)

        # 경고 바
        self.warn_bar = BoxLayout(orientation="horizontal", spacing=dp(6),
                                  size_hint=(1,None), height=0, opacity=0)
        icon = None
        if os.path.exists("warning.png"):
            try:
                icon = Image(source="warning.png", size_hint=(None,None), size=(dp(18),dp(18)))
            except Exception:
                pass
        if icon is None:
            icon = Label(text="⚠", font_name=FONT, color=(1,0.2,0.2,1),
                         size_hint=(None,None), size=(dp(18),dp(18)))
        self.warn_msg = Label(text="", font_name=FONT, color=(0,0,0,1),
                              halign="left", valign="middle")
        self.warn_msg.bind(size=lambda *_: setattr(self.warn_msg, "text_size", self.warn_msg.size))
        self.warn_bar.add_widget(icon); self.warn_bar.add_widget(self.warn_msg)
        root.add_widget(self.warn_bar)

        # 출력(하얀 박스)
        out_wrap = BoxLayout(orientation="vertical", size_hint=(1,1), padding=[0,0,0,0])
        self.out = Label(text="", font_name=FONT, color=(0,0,0,1),
                         size_hint=(1,1), halign="left", valign="top")
        with self.out.canvas.before:
            Color(1,1,1,1)
            self._bg_rect = RoundedRectangle(pos=self.out.pos, size=self.out.size,
                                             radius=[(dp(6),dp(6))]*4)
        self.out.bind(size=lambda *_: setattr(self.out, "text_size", (self.out.width - dp(12), None)))
        self.out.bind(size=self._bg_follow, pos=self._bg_follow)
        out_wrap.add_widget(self.out)
        root.add_widget(out_wrap)

        # 하단 표기 — 고정 문구
        sig = Label(text="버전 1.0", font_name=FONT, color=(0.4,0.4,0.4,1),
                    size_hint=(1,None), height=dp(22), halign="right", valign="middle")
        sig.bind(size=lambda *_: setattr(sig, "text_size", sig.size))
        root.add_widget(sig)

        self.apply_settings(self.app.st)

    def _bg_follow(self, *_):
        self._bg_rect.pos, self._bg_rect.size = self.out.pos, self.out.size

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

    def apply_settings(self, st: dict):
        self.lab_prefix.text = st.get("prefix", "SG94") or "SG94"
        fs = int(st.get("out_font", 15))
        self.out.font_size = dp(fs)
        if bool(st.get("auto_font", False)):
            scale = max(1.0, min(1.3, Window.width/360.0))
        else:
            scale = 1.0
        base = dp(17) * scale
        for w in (self.in_code_front, self.in_code_back, self.in_total,
                  self.in_p1, self.in_p2, self.in_p3):
            w.font_size = base

    def calculate(self):
        try:
            slab = _num_or_none(self.in_total.text)
            p1, p2, p3 = map(_num_or_none, [self.in_p1.text, self.in_p2.text, self.in_p3.text])
            if slab is None or slab <= 0:
                self.out.text = ""
                self._show_warn("Slab 실길이를 올바르게 입력하세요.")
                return
            guides = [v for v in (p1, p2, p3) if v is not None and v > 0]
            if len(guides) < 2:
                self.out.text = ""
                self._show_warn("최소 2개 이상의 지시길이를 입력하세요.")
                return
            self._hide_warn()

            st = self.app.st
            loss = float(st.get("loss_mm", 15.0))
            total_loss = loss * (len(guides) - 1)
            remain = slab - (sum(guides) + total_loss)

            if remain < 0:
                self.out.text = ""
                self._show_warn("절단 길이가 부족합니다. 길이를 다시 확인하세요.")
                return

            add_each = remain / len(guides)
            real = [g + add_each for g in guides]

            do_round = bool(st.get("round", False))
            hide_mm = bool(st.get("hide_mm", False))
            unit = "" if hide_mm else " mm"
            def fmt(x):
                return f"{round_half_up(x)}" if do_round else f"{x:.1f}"

            cf = (self.in_code_front.text or "").strip()
            cb = (self.in_code_back.text or "").strip()
            lines_top, lines_bottom = [], []

            if cf and cb:
                lines_top.append(f"▶ 강번: {self.lab_prefix.text}{cf}-0{cb}\n")

            lines_top.append(f"▶ Slab 실길이: {fmt(slab)}{unit}")
            for i, g in enumerate(guides, 1):
                lines_top.append(f"▶ {i}번 지시길이: {fmt(g)}{unit}")
            lines_top.append(f"▶ 절단 손실: {fmt(loss)}{unit} × {len(guides)-1} = {fmt(total_loss)}{unit}")
            lines_top.append(f"▶ 전체 여유길이: {fmt(remain)}{unit} → 각 +{fmt(add_each)}{unit}\n")

            sec_real = ["▶ 절단 후 예상 길이:"]
            for i, r in enumerate(real, 1):
                sec_real.append(f"   {i}번: {fmt(r)}{unit}")

            visual = "H"
            for i, r in enumerate(real, 1):
                mark = round_half_up(r + loss/2) if do_round else (r + loss/2)
                mark_s = f"{int(mark)}" if do_round else f"{mark:.1f}"
                visual += f"-{i}번({mark_s})-"
            visual += "T"
            sec_vis = ["\n▶ 시각화 (절단 마킹 포인트):", visual]

            if bool(st.get("swap_sections", False)):
                lines_bottom.extend(sec_vis + [""] + sec_real)
            else:
                lines_bottom.extend(sec_real + [""] + sec_vis)

            self.out.text = "\n".join(lines_top + [""] + lines_bottom)

        except Exception as e:
            self._show_warn(f"오류: {e}")
            raise

# ===== 설정 화면 =====
class SettingsScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.build_ui()

    def _title(self, text):
        # 폰트 크기는 유지(dp32), 높이만 34dp로 축소(44→34 아님, 요청은 36→34이지만 실제 코드는 박스 높이를 34로 조정)
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
                         padding=[dp(12), TOP_PAD, dp(12), dp(6)],  # ← 상단 패딩 통일
                         spacing=dp(6))
        self.add_widget(root)

        # 상단바(우측 저장) — 버튼 크기 메인과 동일
        topbar = BoxLayout(size_hint=(1,None), height=TOPBAR_H, spacing=0)
        topbar.add_widget(Widget())
        btn_save = RoundedButton(text="저장", size_hint=(None,1), width=TOPBAR_BTN_W,
                                 bg_color=[0.23,0.53,0.23,1], fg_color=[1,1,1,1])
        btn_save.bind(on_release=lambda *_: self._save_and_back())
        topbar.add_widget(btn_save)
        root.add_widget(topbar)

        # 타이틀(높이만 34dp로 축소)
        root.add_widget(self._title("환경설정"))

        # 타이틀 ↔ 1번 간격: 51dp → 44dp
        root.add_widget(Widget(size_hint=(1,None), height=SETTINGS_TITLE_TO_ITEM1))

        # 본문
        body = BoxLayout(orientation="vertical", spacing=dp(12))
        root.add_widget(body)

        # 1
        body.add_widget(self._black("1. 강번 고정부 변경"))
        self.ed_prefix = AlnumInput(max_len=6, width=dp(70))
        self.ed_prefix.text = self.app.st.get("prefix", "SG94")
        body.add_widget(self._indent_row(self.ed_prefix, self._gray("강번 맨앞 영문 + 숫자 고정부 변경")))

        # 2
        body.add_widget(self._black("2. 정수 결과 반올림"))
        self.sw_round = PillSwitch(active=bool(self.app.st.get("round", False)))
        body.add_widget(self._indent_row(self.sw_round, self._gray("출력부 소수값을 정수로 표시")))

        # 3
        body.add_widget(self._black("3. 결과값 글자 크기"))
        self.ed_out_font = DigitInput(max_len=2, allow_float=False, width=dp(45))
        try:
            self.ed_out_font.text = str(int(self.app.st.get("out_font", 15)))
        except Exception:
            self.ed_out_font.text = "15"
        body.add_widget(self._indent_row(self.ed_out_font, self._gray("결과 표시 라벨 폰트 크기")))

        # 4
        body.add_widget(self._black("4. 결과값 mm 표시 제거"))
        self.sw_hide_mm = PillSwitch(active=bool(self.app.st.get("hide_mm", False)))
        body.add_widget(self._indent_row(self.sw_hide_mm, self._gray("단위(mm) 문구 숨김")))

        # 5
        body.add_widget(self._black("5. 절단 손실 길이 조정"))
        self.ed_loss = DigitInput(max_len=2, allow_float=True, width=dp(45))
        self.ed_loss.text = f"{float(self.app.st.get('loss_mm', 15.0)):.0f}"
        body.add_widget(self._indent_row(self.ed_loss, self._gray("절단 시 손실 보정 길이 (mm)")))

        # 6
        body.add_widget(self._black("6. 모바일 대응 자동 폰트 크기 조절"))
        self.sw_auto_font = PillSwitch(active=bool(self.app.st.get("auto_font", False)))
        body.add_widget(self._indent_row(self.sw_auto_font, self._gray("해상도에 맞게 입력부 폰트 조절")))

        # 7
        body.add_widget(self._black("7. 출력값 위치 이동"))
        self.sw_swap = PillSwitch(active=bool(self.app.st.get("swap_sections", False)))
        body.add_widget(self._indent_row(self.sw_swap, self._gray("ON 시 '절단 예상 길이'를 맨 아래로")))

        # 하단 표기 — 고정
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
        self.main_screen = MainScreen(self, name="main")
        self.settings_screen = SettingsScreen(self, name="settings")
        self.sm.add_widget(self.main_screen)
        self.sm.add_widget(self.settings_screen)
        self.sm.current = "main"
        return self.sm
    def open_settings(self):
        self.sm.current = "settings"
    def open_main(self):
        self.sm.current = "main"

if __name__ == "__main__":
    SlabApp().run()
