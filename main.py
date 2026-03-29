#-*- coding: utf-8 -*-
# 버전 36-RELEASE-BUILD
# - [빌드용] 폰트 및 이미지 경로를 상대 경로로 변경 (앱 패키징 용도)
# - [빌드용] 설정(settings.json) 및 기록(calc_history.json) 저장 위치를 
#            안드로이드 공식 쓰기 가능 폴더(user_data_dir)로 동적 할당되도록 수정
# - 초기화 팝업창(라이트 테마), 바깥 터치 닫기, 기록 페이징, 시간 표시 등 최종 기능 적용

import os, sys, json, traceback
from datetime import datetime
from kivy.app import App
from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import NumericProperty, ListProperty, BooleanProperty
from kivy.graphics import Color, RoundedRectangle, Ellipse
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup

# ===== 빌드용 파일 경로 설정 (상대 경로) =====
FONT = "NanumGothic"
FONT_PATH = "NanumGothic.ttf"
ICON_PATH = "1702.png"

# 폰트 등록 (빌드 환경에서는 파일이 같은 디렉토리에 포함됨)
try:
    LabelBase.register(name=FONT, fn_regular=FONT_PATH)
except Exception as e:
    print(f"폰트 등록 실패: {e}")

MAX_HISTORY = 10

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
        sys.__excepthook__(exc_type, exc, tb)
    sys.excepthook = _hook

# ===== 순수 계산 =====
def _compute(slab, guides, loss):
    total_loss = loss * (len(guides) - 1)
    remain = slab - (sum(guides) + total_loss)
    if remain < 0:
        return None
    add_each = remain / len(guides)
    real = [g + add_each for g in guides]
    return {
        "slab": slab, "guides": guides, "loss": loss,
        "total_loss": total_loss, "remain": remain,
        "add_each": add_each, "real": real,
    }

# ===== 기록 및 설정 저장/불러오기 (APK 호환용 수정) =====
def load_history(filepath) -> list:
    try:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        pass
    return []

def save_history(filepath, history: list):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _defaults():
    return {
        "prefix": "SG94",
        "round": False,
        "out_font": 15,
        "hide_mm": False,
        "loss_mm": 15.0,
        "show_history": False,
        "swap_sections": False
    }

def load_settings(filepath):
    st = _defaults()
    try:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                got = json.load(f) or {}
            st.update(got)
    except Exception:
        pass
    return st

def save_settings(filepath, data: dict):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

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

class ImageIconButton(ButtonBehavior, BoxLayout):
    def __init__(self, source, **kwargs):
        super().__init__(**kwargs)
        self.padding = dp(4) 
        with self.canvas.before:
            Color(0.85, 0.85, 0.85, 1) 
            self._rect = RoundedRectangle(radius=[dp(6)])
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        self.img = Image(source=source, allow_stretch=True, keep_ratio=True)
        self.add_widget(self.img)

    def _update_rect(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size

class DigitInput(TextInput):
    max_len = NumericProperty(3)
    allow_float = BooleanProperty(False)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_x = None
        self.padding = (dp(6), dp(5))
        self.multiline = False
        self.halign = "left"
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
        self.padding = (dp(6), dp(5))
        self.multiline = False
        self.halign = "left"
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

# ===== 메인 화면 =====
class MainScreen(Screen):
    W_LABEL_CODE  = dp(110)
    W_LABEL_LONG  = dp(120)
    W_PREFIX      = dp(64)
    W_INPUT_SHORT = dp(60)
    W_INPUT_BACK  = dp(32)
    W_INPUT_TOTAL = dp(74)
    W_INPUT_GUIDE = dp(66)

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self._showing_history = False
        self._history_idx = 0  
        self._last_result_text = ""
        self.build_ui()

    def build_ui(self):
        Window.clearcolor = (0.93, 0.93, 0.93, 1)
        root = BoxLayout(orientation="vertical",
                         padding=[dp(12), dp(10), dp(12), dp(6)],
                         spacing=dp(6))
        self.add_widget(root)

        # 상단바
        topbar = BoxLayout(size_hint=(1, None), height=dp(40))
        topbar.add_widget(Widget())
        btn_settings = RoundedButton(text="설정", size_hint=(None,1), width=dp(72),
                                     bg_color=[0.27,0.27,0.27,1], fg_color=[1,1,1,1])
        btn_settings.bind(on_release=lambda *_: self.app.open_settings())
        topbar.add_widget(btn_settings)
        root.add_widget(topbar)

        # 제목
        title = Label(text="후판 계산기", font_name=FONT, font_size=dp(32),
                      color=(0,0,0,1), halign="center", valign="middle",
                      size_hint=(1,None), height=dp(44))
        title.bind(size=lambda *_: setattr(title, "text_size", title.size))
        root.add_widget(title)

        # 강번 입력 행
        row_code = BoxLayout(orientation="horizontal", size_hint=(1,None),
                             height=dp(30), spacing=dp(6))
        self.lab_code = Label(text="강번 입력:", font_name=FONT, color=(0,0,0,1),
                              size_hint=(None,1), width=self.W_LABEL_CODE,
                              halign="right", valign="middle")
        self.lab_code.bind(size=lambda *_: setattr(self.lab_code, "text_size",
                                                    (self.lab_code.width, None)))
        row_code.add_widget(self.lab_code)

        self.lab_prefix = Label(text=self.app.st.get("prefix", "SG94"),
                                font_name=FONT, color=(0,0,0,1),
                                size_hint=(None,1), width=self.W_PREFIX,
                                halign="center", valign="middle")
        self.lab_prefix.bind(size=lambda *_: setattr(self.lab_prefix, "text_size",
                                                      self.lab_prefix.size))
        row_code.add_widget(self.lab_prefix)

        self.in_code_front = DigitInput(max_len=3, allow_float=False,
                                        width=self.W_INPUT_SHORT)
        self.in_code_front.bind(text=self._auto_move_back)
        row_code.add_widget(self.in_code_front)

        dash = Label(text="-0", font_name=FONT, color=(0,0,0,1),
                     size_hint=(None,1), width=dp(22),
                     halign="center", valign="middle")
        dash.bind(size=lambda *_: setattr(dash, "text_size", dash.size))
        row_code.add_widget(dash)

        self.in_code_back = DigitInput(max_len=1, allow_float=False,
                                       width=self.W_INPUT_BACK)
        row_code.add_widget(self.in_code_back)
        root.add_widget(row_code)

        # Slab 실길이 행 + 우측 초기화 버튼 (1702.png)
        row_total = BoxLayout(orientation="horizontal", size_hint=(1,None),
                              height=dp(30), spacing=dp(6))
        self.lab_total = Label(text="Slab 실길이:", font_name=FONT, color=(0,0,0,1),
                               size_hint=(None,1), width=self.W_LABEL_LONG,
                               halign="right", valign="middle")
        self.lab_total.bind(size=lambda *_: setattr(self.lab_total, "text_size",
                                                     (self.lab_total.width, None)))
        row_total.add_widget(self.lab_total)
        self.in_total = DigitInput(max_len=5, allow_float=True, width=self.W_INPUT_TOTAL)
        row_total.add_widget(self.in_total)
        
        row_total.add_widget(Widget(size_hint_x=1))
        
        # 빌드 환경에서 파일이 있는지 먼저 확인하고 생성
        if os.path.exists(ICON_PATH):
            self.btn_clear = ImageIconButton(source=ICON_PATH, size_hint=(None, 1), width=dp(36))
        else:
            self.btn_clear = RoundedButton(text="초기화", font_name=FONT, font_size=dp(11),
                                           size_hint=(None, 1), width=dp(45),
                                           bg_color=[0.7, 0.7, 0.7, 1], fg_color=[0, 0, 0, 1], radius=dp(6))
            
        self.btn_clear.bind(on_release=lambda *_: self._confirm_clear())
        row_total.add_widget(self.btn_clear)

        root.add_widget(row_total)

        # 지시길이 1~3
        grid = GridLayout(cols=4, size_hint=(1,None),
                          height=dp(30*3 + 8*2),
                          row_default_height=dp(30),
                          row_force_default=True,
                          spacing=dp(6))

        def _lab(text):
            L = Label(text=text, font_name=FONT, color=(0,0,0,1),
                      size_hint=(None,1), width=self.W_LABEL_LONG,
                      halign="right", valign="middle")
            L.bind(size=lambda *_: setattr(L, "text_size", (L.width, None)))
            return L

        self.in_p1 = DigitInput(max_len=4, allow_float=True, width=self.W_INPUT_GUIDE)
        self.in_p2 = DigitInput(max_len=4, allow_float=True, width=self.W_INPUT_GUIDE)
        self.in_p3 = DigitInput(max_len=4, allow_float=True, width=self.W_INPUT_GUIDE)

        grid.add_widget(_lab("1번 지시길이:"))
        grid.add_widget(self.in_p1)
        grid.add_widget(Label()); grid.add_widget(Label())

        grid.add_widget(_lab("2번 지시길이:"))
        grid.add_widget(self.in_p2)
        b21 = RoundedButton(text="← 1번", bg_color=[0.8,0.8,0.8,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(58), font_size=dp(17))
        b21.bind(on_release=lambda *_: self._copy(self.in_p1, self.in_p2))
        grid.add_widget(b21); grid.add_widget(Label())

        grid.add_widget(_lab("3번 지시길이:"))
        grid.add_widget(self.in_p3)
        btn_row = BoxLayout(orientation="horizontal", spacing=dp(6),
                            size_hint=(None,1), width=dp(58*2+6))
        b31 = RoundedButton(text="← 1번", bg_color=[0.8,0.8,0.8,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(58), font_size=dp(17))
        b32 = RoundedButton(text="← 2번", bg_color=[0.8,0.8,0.8,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(58), font_size=dp(17))
        b31.bind(on_release=lambda *_: self._copy(self.in_p1, self.in_p3))
        b32.bind(on_release=lambda *_: self._copy(self.in_p2, self.in_p3))
        btn_row.add_widget(b31); btn_row.add_widget(b32)
        grid.add_widget(btn_row); grid.add_widget(Label())
        root.add_widget(grid)

        # 계산 버튼
        btn_calc = RoundedButton(text="계산하기", bg_color=[0.23,0.53,0.23,1],
                                 fg_color=[1,1,1,1], size_hint=(1,None),
                                 height=dp(44), radius=dp(10))
        btn_calc.bind(on_release=lambda *_: self.calculate())
        root.add_widget(btn_calc)

        # 출력 박스 컨테이너
        out_container = BoxLayout(orientation="vertical", size_hint=(1,1), padding=[0, dp(6), 0, 0])

        text_bg = BoxLayout(orientation='vertical', size_hint=(1, 1), padding=[dp(8), dp(8), dp(8), dp(8)], spacing=dp(4))
        with text_bg.canvas.before:
            Color(1, 1, 1, 1)
            self._bg_rect = RoundedRectangle(radius=[(dp(6), dp(6))] * 4)
        def _bg_follow(*_):
            self._bg_rect.pos = text_bg.pos
            self._bg_rect.size = text_bg.size
        text_bg.bind(pos=_bg_follow, size=_bg_follow)

        # 내부 상단 버튼
        self.btn_bar_inner = BoxLayout(orientation='horizontal', size_hint=(1, None), height=0, opacity=0)
        self.btn_bar_inner.add_widget(Widget()) 
        self.btn_history = RoundedButton(
            text="기록", size_hint=(None, 1), width=dp(64),
            bg_color=[0.27,0.47,0.7,1], fg_color=[1,1,1,1]
        )
        self.btn_history.bind(on_release=lambda *_: self._toggle_history())
        self.btn_history.disabled = True
        self.btn_bar_inner.add_widget(self.btn_history)
        text_bg.add_widget(self.btn_bar_inner)

        # 스크롤 뷰
        self.scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=False)
        self.out = Label(text="", font_name=FONT, color=(0,0,0,1), markup=True,
                         size_hint_y=None, halign="left", valign="top")

        def _update_rect(*args):
            if self.out.width <= 0:
                return
            self.out.text_size = (self.out.width, None)
            self.out.texture_update()
            target_h = max(self.scroll_view.height, self.out.texture_size[1])
            self.out.height = target_h
            self.out.text_size = (self.out.width, target_h)

        self.out.bind(width=_update_rect, text=_update_rect)
        self.scroll_view.bind(size=_update_rect)
        self.scroll_view.add_widget(self.out)
        text_bg.add_widget(self.scroll_view)

        # 페이징 바
        self.nav_bar = BoxLayout(orientation='horizontal', size_hint=(1, None), height=0, opacity=0, spacing=dp(10), padding=[dp(10), 0, dp(10), dp(5)])
        
        self.btn_prev = RoundedButton(text="◀ 이전", size_hint=(None, 1), width=dp(80),
                                      bg_color=[0.5, 0.5, 0.5, 1], fg_color=[1, 1, 1, 1], radius=dp(6))
        self.btn_prev.bind(on_release=lambda *_: self._go_prev())
        
        self.lab_page = Label(text="", font_name=FONT, color=(0,0,0,1), halign="center", valign="middle")
        
        self.btn_next = RoundedButton(text="다음 ▶", size_hint=(None, 1), width=dp(80),
                                      bg_color=[0.5, 0.5, 0.5, 1], fg_color=[1, 1, 1, 1], radius=dp(6))
        self.btn_next.bind(on_release=lambda *_: self._go_next())

        self.nav_bar.add_widget(self.btn_prev)
        self.nav_bar.add_widget(self.lab_page)
        self.nav_bar.add_widget(self.btn_next)
        text_bg.add_widget(self.nav_bar)

        out_container.add_widget(text_bg)
        root.add_widget(out_container)

        sig = Label(text="made by ft10350", font_name=FONT, color=(0.4,0.4,0.4,1),
                    size_hint=(1,None), height=dp(22), halign="right", valign="middle")
        sig.bind(size=lambda *_: setattr(sig, "text_size", sig.size))
        root.add_widget(sig)

        self.apply_settings(self.app.st)

    # 초기화 확인 팝업 (라이트 테마 / 바깥 터치 닫기)
    def _confirm_clear(self):
        content = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        lbl = Label(text="모든 입력값과 결과를\n초기화하시겠습니까?", font_name=FONT, halign="center", valign="middle", color=(0,0,0,1))
        lbl.bind(size=lambda *_: setattr(lbl, "text_size", lbl.size))
        content.add_widget(lbl)

        btn_box = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(40))
        btn_cancel = RoundedButton(text="취소", bg_color=[0.6, 0.6, 0.6, 1], radius=dp(8))
        btn_ok = RoundedButton(text="지우기", bg_color=[0.8, 0.3, 0.3, 1], radius=dp(8))

        btn_box.add_widget(btn_cancel)
        btn_box.add_widget(btn_ok)
        content.add_widget(btn_box)

        popup = Popup(title="초기화 확인", title_font=FONT, title_color=(0,0,0,1),
                      separator_color=[0.4, 0.4, 0.4, 1],
                      content=content,
                      size_hint=(0.8, None), height=dp(180),
                      auto_dismiss=True,
                      background='', background_color=[0.95, 0.95, 0.95, 1],
                      overlay_color=[0, 0, 0, 0.3])

        btn_cancel.bind(on_release=popup.dismiss)
        btn_ok.bind(on_release=lambda *_: self._clear_all(popup))

        popup.open()

    def _clear_all(self, popup):
        popup.dismiss()
        self.in_code_front.text = ""
        self.in_code_back.text = ""
        self.in_total.text = ""
        self.in_p1.text = ""
        self.in_p2.text = ""
        self.in_p3.text = ""
        self.out.text = ""
        self._last_result_text = ""
        self._showing_history = False
        self.btn_history.text = "기록"
        self.nav_bar.height = 0
        self.nav_bar.opacity = 0
        self.scroll_view.scroll_y = 1.0
        self.in_code_front.focus = True

    def _auto_move_back(self, instance, value):
        if len(value) >= 3:
            self.in_code_back.focus = True

    def _copy(self, src, dst):
        dst.text = src.text

    def _show_error_in_box(self, title, msg):
        st = self.app.st
        base_size = int(st.get("out_font", 15))
        title_size = int(base_size * 1.6) 
        
        error_text = f"[color=#E53935][b][size={title_size}sp][!] {title}[/size][/b][/color]\n\n{msg}"
        
        self.out.text = error_text
        self._showing_history = False
        self.btn_history.text = "기록"
        self.scroll_view.do_scroll_y = False
        self.scroll_view.scroll_y = 1.0
        
        self.nav_bar.height = 0
        self.nav_bar.opacity = 0

    def _show_history_btn(self, show: bool):
        self.btn_history.disabled = not show
        self.btn_bar_inner.height = dp(32) if show else 0
        self.btn_bar_inner.opacity = 1 if show else 0

    def _go_prev(self):
        if self._history_idx > 0:
            self._history_idx -= 1
            self._update_history_page()

    def _go_next(self):
        history = self.app.calc_history
        if self._history_idx < len(history) - 1:
            self._history_idx += 1
            self._update_history_page()

    def _update_history_page(self):
        history = self.app.calc_history
        if not history:
            self.out.text = "(계산 기록이 없습니다)"
            self.nav_bar.height = 0
            self.nav_bar.opacity = 0
            return

        self.nav_bar.height = dp(40)
        self.nav_bar.opacity = 1

        rev_history = list(reversed(history))
        total = len(rev_history)
        
        self.lab_page.text = f"[b]{self._history_idx + 1} / {total}[/b]"
        self.lab_page.markup = True
        
        self.btn_prev.disabled = (self._history_idx == 0)
        self.btn_prev.opacity = 0.3 if self._history_idx == 0 else 1
        
        self.btn_next.disabled = (self._history_idx == total - 1)
        self.btn_next.opacity = 0.3 if self._history_idx == total - 1 else 1
        
        d = rev_history[self._history_idx]
        real_calc_num = total - self._history_idx
        self.out.text = self._build_single_history_text(d, real_calc_num)
        self.scroll_view.scroll_y = 1.0

    def _toggle_history(self):
        if self._showing_history:
            self._showing_history = False
            self.btn_history.text = "기록"
            self.out.text = self._last_result_text
            self.scroll_view.do_scroll_y = False
            self.scroll_view.scroll_y = 1.0
            
            self.nav_bar.height = 0
            self.nav_bar.opacity = 0
        else:
            self._showing_history = True
            self.btn_history.text = "돌아가기"
            self._history_idx = 0  
            self._update_history_page()
            self.scroll_view.do_scroll_y = True
            self.scroll_view.scroll_y = 1.0

    def _build_single_history_text(self, d: dict, real_idx: int) -> str:
        st = self.app.st
        do_round = bool(st.get("round", False))
        hide_mm  = bool(st.get("hide_mm", False))
        unit = "" if hide_mm else " mm"

        def fmt(x):
            return f"{round_half_up(x)}" if do_round else f"{x:.1f}"

        lines = []
        
        time_str = d.get("timestamp", "과거 기록")
        lines.append(f"━━ [ {time_str} ] ━━")
        
        if d.get("code"):
            lines.append(f"강번: {d['code']}")
        lines.append(f"Slab 실길이: {fmt(d['slab'])}{unit}")
        for i, g in enumerate(d["guides"], 1):
            lines.append(f"{i}번 지시길이: {fmt(g)}{unit}")
        lines.append("")
        lines.append("■ 절단 손실 계산 ■")
        n = len(d["guides"])
        lines.append(f"손실 1회: {fmt(d['loss'])}{unit}")
        lines.append(f"절단 횟수: {n-1}회")
        lines.append(f"전체 손실: {fmt(d['loss'])} × {n-1} = {fmt(d['total_loss'])}{unit}")
        lines.append("")
        lines.append("■ 여유길이 배분 ■")
        lines.append(f"지시길이 합계: {fmt(sum(d['guides']))}{unit}")
        lines.append(f"전체 손실: {fmt(d['total_loss'])}{unit}")
        lines.append(f"여유길이: {fmt(d['remain'])}{unit} → 각 +{fmt(d['add_each'])}{unit}")
        lines.append("")
        
        lines.append("■ 시각화 (절단 마킹 포인트) ■")
        visual = "H"
        loss_val = d.get("loss", 15.0)
        for i, r in enumerate(d["real"], 1):
            mark = round_half_up(r + loss_val/2) if do_round else (r + loss_val/2)
            mark_s = f"{int(mark)}" if do_round else f"{mark:.1f}"
            visual += f"-{i}번({mark_s})-"
        visual += "T"
        lines.append(visual)

        return "\n".join(lines)

    def apply_settings(self, st: dict):
        self.lab_prefix.text = st.get("prefix", "SG94") or "SG94"
        self.out.font_size = dp(int(st.get("out_font", 15)))
        show_hist = bool(st.get("show_history", False))
        self._show_history_btn(show_hist)

    def calculate(self):
        try:
            slab = _num_or_none(self.in_total.text)
            p1, p2, p3 = map(_num_or_none,
                             [self.in_p1.text, self.in_p2.text, self.in_p3.text])
            
            if slab is None or slab <= 0:
                self._show_error_in_box("입력 오류", "Slab 실길이를 올바르게 입력하세요.")
                return
            
            guides = [v for v in (p1, p2, p3) if v is not None and v > 0]
            
            if len(guides) < 2:
                self._show_error_in_box("입력 부족", "최소 2개 이상의 지시길이를 입력하세요.")
                return

            st   = self.app.st
            loss = float(st.get("loss_mm", 15.0))
            result = _compute(slab, guides, loss)
            
            if result is None:
                self._show_error_in_box("계산 불가", "절단 길이가 부족합니다.\n입력하신 길이를 다시 확인하세요.")
                return

            cf = (self.in_code_front.text or "").strip()
            cb = (self.in_code_back.text or "").strip()
            code_str = f"{self.lab_prefix.text}{cf}-0{cb}" if (cf and cb) else ""
            record = dict(result)
            record["code"] = code_str
            record["timestamp"] = datetime.now().strftime("%m-%d %H:%M:%S")
            
            self.app.calc_history.append(record)
            if len(self.app.calc_history) > MAX_HISTORY:
                self.app.calc_history.pop(0)
            
            # [빌드용] 전역 변수 대신, App 객체에 저장된 안전한 경로 사용
            save_history(self.app.history_file, self.app.calc_history)

            do_round = bool(st.get("round", False))
            hide_mm  = bool(st.get("hide_mm", False))
            unit = "" if hide_mm else " mm"
            def fmt(x):
                return f"{round_half_up(x)}" if do_round else f"{x:.1f}"

            lines_top = []
            if code_str:
                lines_top.append(f"▶ 강번: {code_str}\n")
            lines_top.append(f"▶ Slab 실길이: {fmt(slab)}{unit}")
            for i, g in enumerate(guides, 1):
                lines_top.append(f"▶ {i}번 지시길이: {fmt(g)}{unit}")
            lines_top.append(
                f"▶ 절단 손실: {fmt(loss)}{unit} × {len(guides)-1}"
                f" = {fmt(result['total_loss'])}{unit}"
            )
            lines_top.append(
                f"▶ 전체 여유길이: {fmt(result['remain'])}{unit}"
                f" → 각 +{fmt(result['add_each'])}{unit}\n"
            )

            sec_real = ["▶ 절단 후 예상 길이:"]
            for i, r in enumerate(result["real"], 1):
                sec_real.append(f"   {i}번: {fmt(r)}{unit}")

            visual = "H"
            for i, r in enumerate(result["real"], 1):
                mark = round_half_up(r + loss/2) if do_round else (r + loss/2)
                mark_s = f"{int(mark)}" if do_round else f"{mark:.1f}"
                visual += f"-{i}번({mark_s})-"
            visual += "T"
            sec_vis = ["\n▶ 시각화 (절단 마킹 포인트):", visual]

            if bool(st.get("swap_sections", False)):
                lines_bottom = sec_vis + [""] + sec_real
            else:
                lines_bottom = sec_real + [""] + sec_vis

            result_text = "\n".join(lines_top + [""] + lines_bottom)
            
            self._last_result_text = result_text
            self._showing_history  = False
            self.btn_history.text  = "기록"
            self.out.text          = result_text
            self.scroll_view.do_scroll_y = False
            
            self.nav_bar.height = 0
            self.nav_bar.opacity = 0

            show_hist = bool(st.get("show_history", False))
            self._show_history_btn(show_hist)

        except Exception as e:
            self._show_error_in_box("알 수 없는 오류", f"오류 내용: {e}")
            raise

# ===== 설정 화면 =====
class SettingsScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.build_ui()

    def on_enter(self):
        st = self.app.st
        self.ed_prefix.text      = st.get("prefix", "SG94")
        self.sw_round.active     = bool(st.get("round", False))
        try:
            self.ed_out_font.text = str(int(st.get("out_font", 15)))
        except Exception:
            self.ed_out_font.text = "15"
        self.sw_hide_mm.active   = bool(st.get("hide_mm", False))
        self.ed_loss.text        = f"{float(st.get('loss_mm', 15.0)):.0f}"
        self.sw_history.active   = bool(st.get("show_history", False))
        self.sw_swap.active      = bool(st.get("swap_sections", False))

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
                        height=dp(30), spacing=dp(8), padding=[dp(12),0,0,0])
        for w in widgets:
            row.add_widget(w)
        return row

    def build_ui(self):
        Window.clearcolor = (0.93, 0.93, 0.93, 1)
        root = BoxLayout(orientation="vertical",
                         padding=[dp(12), dp(10), dp(12), dp(6)],
                         spacing=dp(6))
        self.add_widget(root)

        # 상단바
        topbar = BoxLayout(size_hint=(1,None), height=dp(40))
        topbar.add_widget(Widget())
        btn_save = RoundedButton(text="저장", size_hint=(None,1), width=dp(72),
                                 bg_color=[0.23,0.53,0.23,1], fg_color=[1,1,1,1])
        btn_save.bind(on_release=lambda *_: self._save_and_back())
        topbar.add_widget(btn_save)
        root.add_widget(topbar)

        # 타이틀
        title = Label(text="환경설정", font_name=FONT, font_size=dp(32),
                      color=(0,0,0,1), halign="center", valign="middle",
                      size_hint=(1,None), height=dp(44))
        title.bind(size=lambda *_: setattr(title, "text_size", title.size))
        root.add_widget(title)

        root.add_widget(Widget(size_hint=(1,None), height=dp(20)))

        # 1. 강번 고정부
        root.add_widget(self._black("1. 강번 고정부 변경"))
        self.ed_prefix = AlnumInput(max_len=6, width=dp(70))
        self.ed_prefix.text = self.app.st.get("prefix", "SG96")
        root.add_widget(self._indent_row(self.ed_prefix,
                                         self._gray("강번 맨앞 영문+숫자 고정부")))

        # 2. 소수점 반올림
        root.add_widget(self._black("2. 소수점 반올림"))
        self.sw_round = PillSwitch(active=bool(self.app.st.get("round", False)))
        root.add_widget(self._indent_row(self.sw_round,
                                         self._gray("출력값을 정수로 표시")))

        # 3. 결과값 글씨 크기
        root.add_widget(self._black("3. 결과값 글씨 크기"))
        self.ed_out_font = DigitInput(max_len=2, allow_float=False, width=dp(45))
        try:
            self.ed_out_font.text = str(int(self.app.st.get("out_font", 15)))
        except Exception:
            self.ed_out_font.text = "15"
        root.add_widget(self._indent_row(self.ed_out_font,
                                         self._gray("결과 영역 폰트 크기")))

        # 4. mm 표시
        root.add_widget(self._black("4. 결과값 mm 표시"))
        self.sw_hide_mm = PillSwitch(active=bool(self.app.st.get("hide_mm", False)))
        root.add_widget(self._indent_row(self.sw_hide_mm,
                                         self._gray("단위(mm) 숨김")))

        # 5. 절단 손실 보정
        root.add_widget(self._black("5. 절단 손실 보정"))
        self.ed_loss = DigitInput(max_len=2, allow_float=False, width=dp(45))
        self.ed_loss.text = f"{float(self.app.st.get('loss_mm', 15.0)):.0f}"
        root.add_widget(self._indent_row(self.ed_loss,
                                         self._gray("절단 손실 길이 (mm)")))

        # 6. 계산 기록 보기
        root.add_widget(self._black("6. 계산 기록 보기"))
        self.sw_history = PillSwitch(active=bool(self.app.st.get("show_history", False)))
        root.add_widget(self._indent_row(self.sw_history,
                                         self._gray("결과창 상단에 기록 버튼 표시")))

        # 7. 결과값 위치 이동
        root.add_widget(self._black("7. 결과값 위치 이동"))
        self.sw_swap = PillSwitch(active=bool(self.app.st.get("swap_sections", False)))
        root.add_widget(self._indent_row(self.sw_swap,
                                         self._gray("절단 예상 길이를 아래로")))

        # 여백 + 버전
        root.add_widget(Widget(size_hint=(1,1)))
        sig = Label(text="버전 1.1", font_name=FONT, color=(0.4,0.4,0.4,1),
                    size_hint=(1,None), height=dp(22),
                    halign="right", valign="middle")
        sig.bind(size=lambda *_: setattr(sig, "text_size", sig.size))
        root.add_widget(sig)

    def _save_and_back(self):
        try:
            prefix = (self.ed_prefix.text or "SG94").upper() or "SG94"
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
                "prefix":        prefix,
                "round":         bool(self.sw_round.active),
                "out_font":      out_font,
                "hide_mm":       bool(self.sw_hide_mm.active),
                "loss_mm":       float(loss),
                "show_history":  bool(self.sw_history.active),
                "swap_sections": bool(self.sw_swap.active),
            })
            # [빌드용] 전역 변수 대신, App 객체에 저장된 안전한 경로 사용
            save_settings(self.app.settings_file, st)
            self.app.st = st
            self.app.main_screen.apply_settings(st)
            self.app.open_main()
        except Exception:
            self.app.open_main()

# ===== 앱 =====
class SlabApp(App):
    def build(self):
        # [빌드용] 앱 실행 시 안드로이드 내부의 쓰기 가능한 경로(user_data_dir) 확보
        _install_global_crash_hook(self.user_data_dir)
        
        # 파일 경로 동적 생성
        self.settings_file = os.path.join(self.user_data_dir, "settings.json")
        self.history_file = os.path.join(self.user_data_dir, "calc_history.json")
        
        self.st = load_settings(self.settings_file)
        self.calc_history = load_history(self.history_file)
        
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
