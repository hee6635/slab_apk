# 버전 10 - 전체 화면 설정(1~3항목) 추가 / 즉시 반영 / settings.json 영속화
# -*- coding: utf-8 -*-
import os, sys, json, traceback
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.uix.modalview import ModalView  # 남겨둠(미사용)
from kivy.properties import NumericProperty, ListProperty, BooleanProperty, StringProperty
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.checkbox import CheckBox
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition

SETTINGS_FILE = "settings.json"
FONT = "NanumGothic"

# ---------- 공통 유틸 ----------
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

# ---------- 공통 위젯 ----------
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

# ---------- 설정 로드/세이브 ----------
def load_settings():
    defaults = {
        "prefix": "SG94",   # 1
        "round": False,     # 2
        "font": "20",       # 3 (문자열로 저장되어 있어도 허용)
        # 이후 항목 확장 가능
    }
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                defaults.update(data or {})
    except Exception:
        pass
    return defaults

def save_settings(data: dict):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ---------- 메인 화면 ----------
class MainScreen(Screen):
    prefix = StringProperty("SG94")
    round_result = BooleanProperty(False)
    result_font_dp = NumericProperty(dp(20))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.clearcolor = (0.93, 0.93, 0.93, 1)
        root = BoxLayout(orientation="vertical", padding=[dp(12), dp(8)], spacing=dp(8))
        self.add_widget(root)

        # 상단 바(설정)
        topbar = BoxLayout(size_hint=(1, None), height=dp(40))
        topbar.add_widget(Widget())
        btn_settings = RoundedButton(text="설정", size_hint=(None, 1), width=dp(66),
                                     bg_color=[0.27, 0.27, 0.27, 1], fg_color=[1,1,1,1])
        btn_settings.bind(on_release=self._open_settings)
        topbar.add_widget(btn_settings)
        root.add_widget(topbar)

        # 제목
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
        self.lbl_prefix = Label(text=self.prefix, font_name=FONT, color=(0,0,0,1),
                                size_hint=(None,1), width=dp(44))
        row_code.add_widget(self.lbl_prefix)
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
        btn_calc.bind(on_release=self.calculate)
        root.add_widget(btn_calc)

        # 경고 바
        self.warn_bar = BoxLayout(orientation="horizontal", spacing=dp(6),
                                  size_hint=(1, None), height=0, opacity=0)
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

        # 결과 영역(스크롤)
        wrapper = BoxLayout(orientation="vertical")
        self.result_label = Label(text="", font_name=FONT, color=(0,0,0,1),
                                  size_hint=(1,None), halign="left", valign="top")
        self.result_label.font_size = self.result_font_dp
        self.result_label.bind(texture_size=lambda *_: self._resize_result())
        sv = ScrollView(size_hint=(1,1))
        with self.result_label.canvas.before:
            Color(1,1,1,1)
            self._bg_rect = RoundedRectangle(size=self.result_label.size, pos=self.result_label.pos,
                                             radius=[(dp(6), dp(6))]*4)
        self.result_label.bind(size=self._bg_follow, pos=self._bg_follow)
        sv.add_widget(self.result_label)
        wrapper.add_widget(sv)

        # 하단 버전 표기
        sig = Label(text="버전 10", font_name=FONT, color=(0.4,0.4,0.4,1),
                    halign="right", valign="middle", size_hint=(1,None), height=dp(22))
        sig.bind(size=lambda *_: setattr(sig, "text_size", sig.size))
        wrapper.add_widget(sig)
        root.add_widget(wrapper)

        # 초기 설정 로딩 반영
        self.apply_settings(load_settings())

    # ---- 메인 helpers/동작 ----
    def _open_settings(self, *_):
        app = App.get_running_app()
        app.sm.transition = SlideTransition(direction="left")
        app.sm.current = "settings"

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

    def _bg_follow(self, *_):
        self._bg_rect.pos, self._bg_rect.size = self.result_label.pos, self.result_label.size

    def _resize_result(self, *_):
        self.result_label.text_size = (self.result_label.width - dp(12), None)
        self.result_label.height = self.result_label.texture_size[1] + dp(12)

    def _fmt_num(self, n):
        # 반올림 옵션에 따라 표시 형식 결정
        if self.round_result:
            return f"{round_half_up(n):,d}"
        else:
            return f"{n:,.1f}"

    def calculate(self, *_):
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

            cf = (self.in_code_front.text or "").strip()
            cb = (self.in_code_back.text or "").strip()

            lines = []
            if cf and cb:
                lines.append(f"▶ 강번: {self.prefix}{cf}-0{cb}\n")

            lines.append(f"▶ Slab 실길이: {self._fmt_num(slab)} mm")
            for i, g in enumerate(guides, 1):
                lines.append(f"▶ {i}번 지시길이: {self._fmt_num(g)} mm")
            lines.append(f"▶ 절단 손실: {self._fmt_num(loss)} mm × {len(guides)-1} = {self._fmt_num(total_loss)} mm")
            lines.append(f"▶ 전체 여유길이: {self._fmt_num(remain)} mm → 각 +{self._fmt_num(add_each)} mm\n")

            lines.append("▶ 절단 후 예상 길이:")
            for i, r in enumerate(real, 1):
                lines.append(f"   {i}번: {self._fmt_num(r)} mm")

            # 시각화
            visual = "H"
            for i, r in enumerate(real, 1):
                mark = r + loss/2
                mark_out = f"{round_half_up(mark)}" if self.round_result else f"{mark:,.0f}"
                visual += f"-{i}번({mark_out})-"
            visual += "T"
            lines.append("\n▶ 시각화 (절단 마킹 포인트):")
            lines.append(visual)

            self.result_label.text = "\n".join(lines)

        except Exception as e:
            self._show_warn(f"오류: {e}")
            raise

    def apply_settings(self, st: dict):
        # 1) 접두어
        self.prefix = st.get("prefix", "SG94") or "SG94"
        self.lbl_prefix.text = self.prefix
        # 2) 반올림
        self.round_result = bool(st.get("round", False))
        # 3) 결과 폰트 크기
        try:
            f = float(st.get("font", "20"))
        except Exception:
            f = 20.0
        self.result_font_dp = dp(f)
        self.result_label.font_size = self.result_font_dp

# ---------- 설정 화면(풀스크린, 항목 1~3) ----------
class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=[dp(12), dp(8)], spacing=dp(8))
        self.add_widget(root)

        # 상단 바: 제목 + 뒤로
        top = BoxLayout(size_hint=(1,None), height=dp(44))
        title = Label(text="환경설정", font_name=FONT, font_size=dp(24),
                      color=(0,0,0,1), halign="center", valign="middle")
        title.bind(size=lambda *_: setattr(title, "text_size", title.size))
        btn_back = RoundedButton(text="뒤로", size_hint=(None,1), width=dp(66),
                                 bg_color=[0.27,0.27,0.27,1], fg_color=[1,1,1,1])
        btn_back.bind(on_release=self._save_and_back)
        top.add_widget(title); top.add_widget(btn_back)
        root.add_widget(top)

        # 본문
        body = BoxLayout(orientation="vertical", spacing=dp(10))
        root.add_widget(body)

        # 1) 접두어
        row1 = BoxLayout(orientation="horizontal", size_hint=(1,None), height=dp(30), spacing=dp(6))
        row1.add_widget(Label(text="1. 강번 접두어:", font_name=FONT, color=(0,0,0,1),
                              size_hint=(None,1), width=dp(110), halign="right", valign="middle"))
        self.in_prefix = DigitInput(max_len=4, allow_float=False, size_hint=(None,1), width=dp(80))
        # 접두어는 영문+숫자 허용 필요 시 TextInput 커스텀 가능. 간단히 그대로 사용.
        row1.add_widget(self.in_prefix)
        body.add_widget(row1)

        # 2) 반올림 체크
        row2 = BoxLayout(orientation="horizontal", size_hint=(1,None), height=dp(30), spacing=dp(6))
        row2.add_widget(Label(text="2. 결과 정수 반올림:", font_name=FONT, color=(0,0,0,1),
                              size_hint=(None,1), width=dp(110), halign="right", valign="middle"))
        self.chk_round = CheckBox(size_hint=(None,None), size=(dp(22),dp(22)))
        row2.add_widget(self.chk_round)
        row2.add_widget(Label(text="켜면 정수로 표시", font_name=FONT, color=(0.3,0.3,0.3,1)))
        body.add_widget(row2)

        # 3) 결과 폰트 크기
        row3 = BoxLayout(orientation="horizontal", size_hint=(1,None), height=dp(30), spacing=dp(6))
        row3.add_widget(Label(text="3. 결과 폰트 크기:", font_name=FONT, color=(0,0,0,1),
                              size_hint=(None,1), width=dp(110), halign="right", valign="middle"))
        self.in_font = DigitInput(max_len=2, allow_float=True, size_hint=(None,1), width=dp(60))
        row3.add_widget(self.in_font)
        row3.add_widget(Label(text="(예: 20)", font_name=FONT, color=(0.3,0.3,0.3,1),
                              size_hint=(None,1), width=dp(60)))
        body.add_widget(row3)

        # 저장 버튼
        btn_save = RoundedButton(text="저장", size_hint=(1,None), height=dp(42),
                                 bg_color=[0.23,0.53,0.23,1], fg_color=[1,1,1,1], radius=dp(10))
        btn_save.bind(on_release=self._save_and_back)
        root.add_widget(btn_save)

        # 로드
        self._load_into_fields()

    def _load_into_fields(self):
        st = load_settings()
        self.in_prefix.text = st.get("prefix", "SG94")
        self.chk_round.active = bool(st.get("round", False))
        self.in_font.text = str(st.get("font", "20"))

    def _save_and_back(self, *_):
        # 저장
        st = load_settings()
        st["prefix"] = (self.in_prefix.text or "SG94")
        st["round"] = bool(self.chk_round.active)
        st["font"]  = (self.in_font.text or "20")
        save_settings(st)
        # 메인에 적용
        app = App.get_running_app()
        app.main_screen.apply_settings(st)
        # 뒤로
        app.sm.transition = SlideTransition(direction="right")
        app.sm.current = "main"

# ---------- 앱 ----------
class SlabApp(App):
    def build(self):
        _install_global_crash_hook(self.user_data_dir)
        self.sm = ScreenManager()
        self.main_screen = MainScreen(name="main")
        self.settings_screen = SettingsScreen(name="settings")
        self.sm.add_widget(self.main_screen)
        self.sm.add_widget(self.settings_screen)
        return self.sm

if __name__ == "__main__":
    SlabApp().run()
