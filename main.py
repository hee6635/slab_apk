# 버전 11 - 전체화면 환경설정(Screen) + 출력부 스크롤 제거 + 접두어 영문/숫자 제한
# 2025-10-28

# -*- coding: utf-8 -*-
import os, sys, json, traceback, re
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
from kivy.uix.checkbox import CheckBox
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition

SETTINGS_FILE = "settings.json"
FONT = "NanumGothic"

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

# ────────────────────────────────────────────────────────────────
# 공용 위젯
# ────────────────────────────────────────────────────────────────
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

# 접두어: 영문/숫자만 허용하는 입력
class AlnumInput(TextInput):
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

    def insert_text(self, substring, from_undo=False):
        filtered = "".join(ch for ch in substring if re.match(r"[A-Za-z0-9]", ch))
        return super().insert_text(filtered, from_undo=from_undo)

# ────────────────────────────────────────────────────────────────
# 메인 화면
# ────────────────────────────────────────────────────────────────
class MainScreen(Screen):
    prefix = StringProperty("SG94")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.clearcolor = (0.93, 0.93, 0.93, 1)

        root = BoxLayout(orientation="vertical", padding=[dp(12), dp(8)], spacing=dp(8))

        # 상단바(우측 설정)
        topbar = BoxLayout(size_hint=(1, None), height=dp(40))
        topbar.add_widget(Widget())
        btn_settings = RoundedButton(text="설정", size_hint=(None, 1), width=dp(66),
                                     bg_color=[0.27, 0.27, 0.27, 1], fg_color=[1,1,1,1])
        btn_settings.bind(on_release=lambda *_: self.manager.current_switch("settings"))
        topbar.add_widget(btn_settings)
        root.add_widget(topbar)

        # 타이틀
        title_row = BoxLayout(size_hint=(1, None), height=dp(44))
        title = Label(text="후판 계산기", font_name=FONT, font_size=dp(28),
                      color=(0,0,0,1), halign="center", valign="middle")
        title.bind(size=lambda *_: setattr(title, "text_size", title.size))
        title_row.add_widget(title)
        root.add_widget(title_row)

        # 강번 입력
        row_code = BoxLayout(orientation="horizontal", size_hint=(1, None),
                             height=dp(30), spacing=dp(4))
        row_code.add_widget(Label(text="강번 입력:", font_name=FONT, color=(0,0,0,1),
                                  size_hint=(None,1), width=dp(74),
                                  halign="right", valign="middle"))
        self.lab_prefix = Label(text=self.prefix, font_name=FONT, color=(0,0,0,1),
                                size_hint=(None,1), width=dp(44))
        row_code.add_widget(self.lab_prefix)
        self.in_code_front = DigitInput(max_len=3, allow_float=False, size_hint=(None,1), width=dp(60))
        self.in_code_front.bind(text=self._auto_move_back)
        row_code.add_widget(self.in_code_front)
        row_code.add_widget(Label(text="-0", font_name=FONT, color=(0,0,0,1),
                                  size_hint=(None,1), width=dp(22)))
        self.in_code_back = DigitInput(max_len=1, allow_float=False, size_hint=(None,1), width=dp(40))
        row_code.add_widget(self.in_code_back)
        root.add_widget(row_code)

        # 실제 Slab 길이
        row_total = BoxLayout(orientation="horizontal", size_hint=(1, None),
                              height=dp(30), spacing=dp(4))
        row_total.add_widget(Label(text="실제 Slab 길이:", font_name=FONT, color=(0,0,0,1),
                                   size_hint=(None,1), width=dp(104),
                                   halign="right", valign="middle"))
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

        grid.add_widget(Label(text="1번 지시길이:", font_name=FONT, color=(0,0,0,1),
                              size_hint=(None,1), width=dp(104),
                              halign="right", valign="middle"))
        grid.add_widget(self.in_p1)
        grid.add_widget(Label()); grid.add_widget(Label())

        grid.add_widget(Label(text="2번 지시길이:", font_name=FONT, color=(0,0,0,1),
                              size_hint=(None,1), width=dp(104),
                              halign="right", valign="middle"))
        grid.add_widget(self.in_p2)
        b21 = RoundedButton(text="← 1번", bg_color=[0.8,0.8,0.8,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(58))
        b21.bind(on_release=lambda *_: self._copy(self.in_p1, self.in_p2))
        grid.add_widget(b21)
        grid.add_widget(Label())

        grid.add_widget(Label(text="3번 지시길이:", font_name=FONT, color=(0,0,0,1),
                              size_hint=(None,1), width=dp(104),
                              halign="right", valign="middle"))
        grid.add_widget(self.in_p3)
        btn_row = BoxLayout(orientation="horizontal", spacing=dp(8),
                            size_hint=(None,1), width=dp(58*2 + 8))
        b31 = RoundedButton(text="← 1번", bg_color=[0.8,0.8,0.8,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(58))
        b32 = RoundedButton(text="← 2번", bg_color=[0.8,0.8,0.8,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(58))
        b31.bind(on_release=lambda *_: self._copy(self.in_p1, self.in_p3))
        b32.bind(on_release=lambda *_: self._copy(self.in_p2, self.in_p3))
        btn_row.add_widget(b31); btn_row.add_widget(b32)
        grid.add_widget(btn_row)
        grid.add_widget(Label())
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
                                       size_hint=(None,None), size=(dp(18),dp(18)))
        else:
            self.warn_icon = Label(text="⚠", font_name=FONT, color=(1,0.2,0.2,1),
                                   size_hint=(None,None), size=(dp(18),dp(18)))
        self.warn_msg = Label(text="", font_name=FONT, color=(0,0,0,1), halign="left", valign="middle")
        self.warn_msg.bind(size=lambda *_: setattr(self.warn_msg, "text_size", self.warn_msg.size))
        self.warn_bar.add_widget(self.warn_icon); self.warn_bar.add_widget(self.warn_msg)
        root.add_widget(self.warn_bar)

        # 결과(스크롤 제거, 고정박스/복사 가능)
        self.out_box = TextInput(readonly=True, cursor_blink=False,
                                 size_hint=(1,None), height=dp(240),
                                 font_name=FONT, font_size=dp(11),
                                 background_normal="", background_active="",
                                 padding=(dp(8), dp(8)))
        root.add_widget(self.out_box)

        # 하단 버전 표기
        sig = Label(text="버전 11", font_name=FONT, color=(0.4,0.4,0.4,1),
                    halign="right", valign="middle", size_hint=(1, None), height=dp(22))
        sig.bind(size=lambda *_: setattr(sig, "text_size", sig.size))
        root.add_widget(sig)

        self.add_widget(root)

        # 설정값 로드 후 반영
        self._apply_settings_from_file()

    # ── helpers
    def _show_warn(self, msg):
        self.warn_msg.text = msg
        self.warn_bar.height = dp(28)
        self.warn_bar.opacity = 1

    def _hide_warn(self):
        self.warn_msg.text = ""
        self.warn_bar.height = 0
        self.warn_bar.opacity = 0

    def _auto_move_back(self, instance, value):
        if len(value) >= 3:
            self.in_code_back.focus = True

    def _copy(self, src, dst):
        dst.text = src.text

    # ── settings load
    def _apply_settings_from_file(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    s = json.load(f)
                self.prefix = s.get("prefix", "SG94") or "SG94"
                self.lab_prefix.text = self.prefix
                # 출력 폰트 크기
                size = 11
                try:
                    size = int(str(s.get("font", "11")))
                except Exception:
                    size = 11
                self.out_box.font_size = dp(size)
                self._round_int = bool(s.get("round", False))
                self._remove_mm = bool(s.get("remove_mm", False))  # 미래용
                # 절단손실 값이 설정에 있을 수 있음(미래 확장)
                self._loss_override = s.get("loss", None)
            except Exception:
                pass
        else:
            self._round_int = False
            self._remove_mm = False
            self._loss_override = None

    # ── 계산
    def calculate(self, *_):
        try:
            slab = _num_or_none(self.in_total.text)
            p1, p2, p3 = map(_num_or_none, [self.in_p1.text, self.in_p2.text, self.in_p3.text])

            if slab is None or slab <= 0:
                self.out_box.text = ""
                self._show_warn("실제 Slab 길이를 올바르게 입력하세요.")
                return

            guides = [v for v in (p1, p2, p3) if v is not None and v > 0]
            if len(guides) < 2:
                self.out_box.text = ""
                self._show_warn("최소 2개 이상의 지시길이를 입력하세요.")
                return

            self._hide_warn()

            loss = float(self._loss_override) if self._loss_override not in (None, "") else 15.0
            total_loss = loss * (len(guides) - 1)
            remain = slab - (sum(guides) + total_loss)
            add_each = remain / len(guides) if len(guides) else 0.0
            real = [g + add_each for g in guides]

            # 표시 포맷
            def fmt(x):
                if self._round_int:
                    return f"{round_half_up(x):,d}"
                else:
                    return f"{x:,.1f}"

            mm = "" if getattr(self, "_remove_mm", False) else " mm"

            cf = (self.in_code_front.text or "").strip()
            cb = (self.in_code_back.text or "").strip()
            lines = []
            if cf and cb:
                lines.append(f"▶ 강번: {self.prefix}{cf}-0{cb}\n")
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
                mark_val = r + loss / 2
                mark = round_half_up(mark_val) if self._round_int else f"{mark_val:,.1f}"
                visual += f"-{i}번({mark})-"
            visual += "T"
            lines.append("\n▶ 시각화 (절단 마킹 포인트):")
            lines.append(visual)

            self.out_box.text = "\n".join(lines)

        except Exception as e:
            self._show_warn(f"오류: {e}")
            raise

# ────────────────────────────────────────────────────────────────
# 설정 화면 (전체화면)
# ────────────────────────────────────────────────────────────────
class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = BoxLayout(orientation="vertical", padding=[dp(12), dp(8)], spacing=dp(8))

        # 상단바(우측 저장)
        topbar = BoxLayout(size_hint=(1, None), height=dp(40))
        topbar.add_widget(Widget())
        btn_save = RoundedButton(text="저장", size_hint=(None, 1), width=dp(66),
                                 bg_color=[0.27, 0.27, 0.27, 1], fg_color=[1,1,1,1])
        btn_save.bind(on_release=lambda *_: self._save_and_back())
        topbar.add_widget(btn_save)
        root.add_widget(topbar)

        # 타이틀 + 3줄 공백
        title_row = BoxLayout(size_hint=(1, None), height=dp(44))
        title = Label(text="환경설정", font_name=FONT, font_size=dp(28),
                      color=(0,0,0,1), halign="center", valign="middle")
        title.bind(size=lambda *_: setattr(title, "text_size", title.size))
        title_row.add_widget(title)
        root.add_widget(title_row)

        root.add_widget(Widget(size_hint=(1, None), height=dp(12)))  # 줄바꿈 #1
        root.add_widget(Widget(size_hint=(1, None), height=dp(12)))  # 줄바꿈 #2
        root.add_widget(Widget(size_hint=(1, None), height=dp(12)))  # 줄바꿈 #3

        # 항목 컨테이너
        items = BoxLayout(orientation="vertical", spacing=dp(10))

        # 1) 접두어
        row1t = Label(text="1. 강번 접두어", font_name=FONT, color=(0,0,0,1),
                      size_hint=(1,None), height=dp(20), halign="left", valign="middle")
        row1t.bind(size=lambda *_: setattr(row1t, "text_size", row1t.size))
        items.add_widget(row1t)

        row1 = BoxLayout(orientation="horizontal", size_hint=(1,None), height=dp(30), spacing=dp(6))
        lab_pref = Label(text="영문/숫자만", font_name=FONT, color=(0,0,0,1),
                         size_hint=(None,1), width=dp(80), halign="right", valign="middle")
        lab_pref.bind(size=lambda *_: setattr(lab_pref, "text_size", lab_pref.size))
        self.in_prefix = AlnumInput(size_hint=(None,1), width=dp(120))
        row1.add_widget(lab_pref); row1.add_widget(self.in_prefix); row1.add_widget(Widget())
        items.add_widget(row1)

        # 2) 정수 반올림 체크
        row2t = Label(text="2. 정수 결과 반올림", font_name=FONT, color=(0,0,0,1),
                      size_hint=(1,None), height=dp(20), halign="left", valign="middle")
        row2t.bind(size=lambda *_: setattr(row2t, "text_size", row2t.size))
        items.add_widget(row2t)

        row2 = BoxLayout(orientation="horizontal", size_hint=(1,None), height=dp(30), spacing=dp(8))
        self.chk_round = CheckBox(size_hint=(None,None), size=(dp(22), dp(22)))
        row2.add_widget(self.chk_round)
        hint = Label(text="출력부 소수점 값을 정수로 표시", font_name=FONT,
                     color=(0.5,0.5,0.5,1), halign="left", valign="middle")
        hint.bind(size=lambda *_: setattr(hint, "text_size", hint.size))
        row2.add_widget(hint); row2.add_widget(Widget())
        items.add_widget(row2)

        # 3) 출력부 폰트 크기
        row3t = Label(text="3. 출력부 폰트 크기", font_name=FONT, color=(0,0,0,1),
                      size_hint=(1,None), height=dp(20), halign="left", valign="middle")
        row3t.bind(size=lambda *_: setattr(row3t, "text_size", row3t.size))
        items.add_widget(row3t)

        row3 = BoxLayout(orientation="horizontal", size_hint=(1,None), height=dp(30), spacing=dp(6))
        lab_fs = Label(text="기본 11", font_name=FONT, color=(0,0,0,1),
                       size_hint=(None,1), width=dp(60), halign="right", valign="middle")
        lab_fs.bind(size=lambda *_: setattr(lab_fs, "text_size", lab_fs.size))
        self.in_font = DigitInput(max_len=2, allow_float=False, size_hint=(None,1), width=dp(60))
        self.in_font.text = "11"
        row3.add_widget(lab_fs); row3.add_widget(self.in_font); row3.add_widget(Widget())
        items.add_widget(row3)

        root.add_widget(items)

        # 하단 버전
        sig = Label(text="버전 11", font_name=FONT, color=(0.4,0.4,0.4,1),
                    halign="right", valign="middle", size_hint=(1, None), height=dp(22))
        sig.bind(size=lambda *_: setattr(sig, "text_size", sig.size))
        root.add_widget(sig)

        self.add_widget(root)
        self._load()

    def _load(self):
        s = {}
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    s = json.load(f)
            except Exception:
                s = {}
        self.in_prefix.text = s.get("prefix", "SG94")
        self.chk_round.active = bool(s.get("round", False))
        font_val = str(s.get("font", "11")).strip()
        self.in_font.text = font_val if font_val.isdigit() else "11"

    def _save_and_back(self):
        data = {
            "prefix": (self.in_prefix.text or "SG94"),
            "round": bool(self.chk_round.active),
            "font": self.in_font.text or "11"
        }
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        # 메인으로 복귀 + 메인 화면에 즉시 반영
        self.manager.current_switch("main")
        main: MainScreen = self.manager.get_screen("main")
        main._apply_settings_from_file()

# ────────────────────────────────────────────────────────────────
# 스크린 매니저
# ────────────────────────────────────────────────────────────────
class SlabApp(App):
    def build(self):
        _install_global_crash_hook(self.user_data_dir)

        sm = ScreenManager(transition=NoTransition())
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(SettingsScreen(name="settings"))

        # helper for switching by name
        def current_switch(to_name):
            sm.current = to_name
        sm.current_switch = current_switch  # attach small helper
        return sm

if __name__ == "__main__":
    SlabApp().run()
