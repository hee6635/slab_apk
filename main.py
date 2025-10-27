# -*- coding: utf-8 -*-
import os
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.uix.modalview import ModalView
from kivy.properties import NumericProperty, BooleanProperty, ListProperty
from kivy.uix.image import Image
from kivy.graphics import Color, RoundedRectangle

FONT = "NanumGothic"  # 루트에 NanumGothic.ttf
WARN_IMG = "warning.png"  # 루트에 warning.png

def _num_or_none(s):
    try:
        s = (s or "").strip()
        if not s:
            return None
        return float(s)
    except Exception:
        return None

def round_half_up(n):
    return int(float(n) + 0.5)

# ---- 둥근 버튼 ----------------------------------------------------
class RoundedButton(Button):
    radius = NumericProperty(dp(10))
    bg_color = ListProperty([0.23, 0.53, 0.23, 1])  # 기본 녹색
    fg_color = ListProperty([1, 1, 1, 1])

    def __init__(self, **kw):
        super().__init__(**kw)
        self.background_normal = ""
        self.background_down = ""
        self.color = self.fg_color
        with self.canvas.before:
            self._c = Color(*self.bg_color)
            self._r = RoundedRectangle(pos=self.pos, size=self.size,
                                       radius=[(self.radius, self.radius)]*4)
        self.bind(pos=self._sync, size=self._sync, bg_color=self._recolor)

    def _sync(self, *a):
        self._r.pos = self.pos
        self._r.size = self.size

    def _recolor(self, *a):
        self._c.rgba = self.bg_color

# ---- 숫자 입력(자릿수/소수점 제한) --------------------------------
class DigitInput(TextInput):
    max_len = NumericProperty(3)
    allow_float = BooleanProperty(False)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.multiline = False
        self.halign = "center"
        self.font_name = FONT

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

# ---- 앱 -----------------------------------------------------------
class SlabApp(App):
    prefix = "SG94"

    def build(self):
        Window.clearcolor = (0.94, 0.94, 0.94, 1)

        root = BoxLayout(orientation="vertical", padding=[dp(14), dp(10)], spacing=dp(10))

        # 상단 바: [왼쪽 더미][중앙 제목][오른쪽 설정]
        top = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(56))
        left_dummy = Widget(size_hint=(None, 1), width=dp(92))
        title = Label(text="후판 계산기", font_name=FONT, font_size=dp(30),
                      color=(0,0,0,1), halign="center", valign="middle")
        title.bind(size=lambda *_: setattr(title, "text_size", title.size))
        btn_settings = RoundedButton(text="설정", size_hint=(None, 1), width=dp(92),
                                     bg_color=[0.27,0.27,0.27,1], fg_color=[1,1,1,1])
        btn_settings.bind(on_release=self.open_settings)
        top.add_widget(left_dummy); top.add_widget(title); top.add_widget(btn_settings)
        root.add_widget(top)

        # 강번 입력줄  SG94 [NNN] -0 [N]
        row_code = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(40), spacing=dp(8))
        lab_code = Label(text="강번 입력:", font_name=FONT, color=(0,0,0,1),
                         size_hint=(None,1), width=dp(78), halign="right", valign="middle")
        lab_code.bind(size=lambda *_: setattr(lab_code, "text_size", lab_code.size))
        lab_prefix = Label(text=self.prefix, font_name=FONT, color=(0,0,0,1),
                           size_hint=(None,1), width=dp(52), halign="center", valign="middle")
        lab_prefix.bind(size=lambda *_: setattr(lab_prefix, "text_size", lab_prefix.size))

        self.in_code_front = DigitInput(max_len=3, allow_float=False,
                                        size_hint=(None,1), width=dp(76))
        self.in_code_front.bind(text=self._move_to_back_if_full)

        lab_dash = Label(text="-0", font_name=FONT, color=(0,0,0,1),
                         size_hint=(None,1), width=dp(30), halign="center", valign="middle")
        lab_dash.bind(size=lambda *_: setattr(lab_dash, "text_size", lab_dash.size))

        self.in_code_back = DigitInput(max_len=1, allow_float=False,
                                       size_hint=(None,1), width=dp(50))

        row_code.add_widget(lab_code); row_code.add_widget(lab_prefix)
        row_code.add_widget(self.in_code_front); row_code.add_widget(lab_dash)
        row_code.add_widget(self.in_code_back)
        root.add_widget(row_code)

        # 실제 Slab 길이(5자리)
        row_total = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(40), spacing=dp(8))
        lab_total = Label(text="실제 Slab 길이:", font_name=FONT, color=(0,0,0,1),
                          size_hint=(None,1), width=dp(120), halign="right", valign="middle")
        lab_total.bind(size=lambda *_: setattr(lab_total, "text_size", lab_total.size))
        self.in_total = DigitInput(max_len=5, allow_float=False, size_hint=(None,1), width=dp(160))
        row_total.add_widget(lab_total); row_total.add_widget(self.in_total); row_total.add_widget(Widget())
        root.add_widget(row_total)

        # 지시길이 (각 4자리) + 복사 버튼(간격 고정)
        grid = GridLayout(cols=3, size_hint=(1, None), height=dp(40*3+8*2),
                          row_default_height=dp(40), row_force_default=True, spacing=dp(8))

        def add_row(idx, with_btns=False):
            lab = Label(text=f"{idx}번 지시길이:", font_name=FONT, color=(0,0,0,1),
                        size_hint=(None,1), width=dp(120), halign="right", valign="middle")
            lab.bind(size=lambda *_: setattr(lab, "text_size", lab.size))
            ti = DigitInput(max_len=4, allow_float=False, size_hint=(None,1), width=dp(160))
            grid.add_widget(lab); grid.add_widget(ti)
            if not with_btns:
                grid.add_widget(Widget())
                return ti
            btn_zone = BoxLayout(orientation="horizontal", size_hint=(None,1),
                                 width=dp(62*2 + 8), spacing=dp(8))
            b1 = RoundedButton(text="← 1번", bg_color=[0.7,0.7,0.7,1],
                               fg_color=[1,1,1,1], size_hint=(None,1), width=dp(62))
            b2 = RoundedButton(text="← 2번", bg_color=[0.7,0.7,0.7,1],
                               fg_color=[1,1,1,1], size_hint=(None,1), width=dp(62))
            btn_zone.add_widget(b1); btn_zone.add_widget(b2)
            grid.add_widget(btn_zone)
            return ti, b1, b2

        self.in_p1 = add_row(1, with_btns=False)
        self.in_p2, b21, _ = add_row(2, with_btns=True)
        self.in_p3, b31, b32 = add_row(3, with_btns=True)
        b21.bind(on_release=lambda *_: self._copy(self.in_p1, self.in_p2))
        b31.bind(on_release=lambda *_: self._copy(self.in_p1, self.in_p3))
        b32.bind(on_release=lambda *_: self._copy(self.in_p2, self.in_p3))
        root.add_widget(grid)

        # 계산 버튼
        btn_calc = RoundedButton(text="계산하기", size_hint=(1,None), height=dp(48),
                                 bg_color=[0.23,0.53,0.23,1], fg_color=[1,1,1,1])
        btn_calc.bind(on_release=self.calculate)
        root.add_widget(btn_calc)

        # 메시지 바(경고 아이콘 + 텍스트)
        self.msg_bar = BoxLayout(orientation="horizontal", size_hint=(1,None), height=dp(44),
                                 padding=[dp(10), dp(6)], spacing=dp(8))
        with self.msg_bar.canvas.before:
            Color(1,1,1,1)
            self._msg_bg = RoundedRectangle(radius=[(dp(8),dp(8))]*4,
                                            pos=self.msg_bar.pos, size=self.msg_bar.size)
        self.msg_bar.bind(pos=self._sync_msg_bg, size=self._sync_msg_bg)

        self.msg_icon = Image(source=WARN_IMG, size_hint=(None,1), width=dp(24))
        self.msg_text = Label(text="", font_name=FONT, color=(0,0,0,1),
                              halign="left", valign="middle")
        self.msg_text.bind(size=lambda *_: setattr(self.msg_text, "text_size", self.msg_text.size))
        self.msg_bar.add_widget(self.msg_icon); self.msg_bar.add_widget(self.msg_text)
        self._set_msg("")  # 처음엔 숨김
        root.add_widget(self.msg_bar)

        # 결과 영역(스크롤 + 라벨)
        wrapper = BoxLayout(orientation="vertical")
        self.result_label = Label(text="", font_name=FONT, color=(0,0,0,1),
                                  size_hint=(1, None), halign="left", valign="top")
        self.result_label.bind(texture_size=lambda *_: self._resize_result())

        sv = ScrollView(size_hint=(1, 1))
        with self.result_label.canvas.before:
            Color(1,1,1,1)
            self._bg_rect = RoundedRectangle(pos=self.result_label.pos,
                                             size=self.result_label.size,
                                             radius=[(dp(8),dp(8))]*4)
        self.result_label.bind(size=self._bg_follow, pos=self._bg_follow)
        sv.add_widget(self.result_label)
        wrapper.add_widget(sv)

        # 시그니처(오른쪽 하단 느낌)
        sig = BoxLayout(size_hint=(1, None), height=dp(22), padding=[0,0,dp(8),0])
        sig_lab = Label(text="made by ft10350", font_name=FONT, color=(0.4,0.4,0.4,1),
                        halign="right", valign="middle")
        sig_lab.bind(size=lambda *_: setattr(sig_lab, "text_size", sig_lab.size))
        sig.add_widget(sig_lab)
        wrapper.add_widget(sig)
        root.add_widget(wrapper)

        return root

    # --- helpers ---
    def _sync_msg_bg(self, *a):
        self._msg_bg.pos = self.msg_bar.pos
        self._msg_bg.size = self.msg_bar.size

    def _set_msg(self, text: str):
        if text:
            self.msg_bar.height = dp(44)
            self.msg_bar.opacity = 1
            self.msg_text.text = text
            self.msg_icon.source = WARN_IMG
        else:
            self.msg_bar.height = dp(0)
            self.msg_bar.opacity = 0
            self.msg_text.text = ""

    def _move_to_back_if_full(self, instance, value):
        if len(value) >= 3:
            self.in_code_back.focus = True

    def _bg_follow(self, *args):
        self._bg_rect.size = self.result_label.size
        self._bg_rect.pos = self.result_label.pos

    def _resize_result(self):
        self.result_label.text_size = (self.result_label.width - dp(12), None)
        self.result_label.height = self.result_label.texture_size[1] + dp(12)

    def _copy(self, src, dst):
        dst.text = src.text

    # --- 계산 ---
    def calculate(self, *_):
        # 에러바 초기화
        self._set_msg("")

        slab = _num_or_none(self.in_total.text)
        p1 = _num_or_none(self.in_p1.text)
        p2 = _num_or_none(self.in_p2.text)
        p3 = _num_or_none(self.in_p3.text)

        if slab is None or slab <= 0:
            self.result_label.text = ""
            self._set_msg("실제 Slab 길이를 올바르게 입력하세요.")
            return

        guides = [v for v in (p1, p2, p3) if v is not None and v > 0]
        if len(guides) < 2:
            self.result_label.text = ""
            self._set_msg("최소 2개 이상의 지시길이를 입력하세요.")
            return

        loss = 15.0
        num = len(guides) - 1
        total_loss = loss * num
        remain = slab - (sum(guides) + total_loss)
        add_each = remain / len(guides)
        real = [g + add_each for g in guides]

        centers = []
        acc = 0.0
        for l in real[:-1]:
            acc += l + (loss/2)
            centers.append(acc)
            acc += (loss/2)

        mm = " mm"
        lines = []
        cf = (self.in_code_front.text or "").strip()
        cb = (self.in_code_back.text or "").strip()
        if cf and cb:
            lines.append(f"▶ 강번: {self.prefix}{cf}-0{cb}\n")

        lines.append(f"▶ Slab 실길이: {slab:,.1f}{mm}")
        for i, g in enumerate(guides, 1):
            lines.append(f"▶ {i}번 지시길이: {g:,.1f}{mm}")
        lines.append(f"▶ 절단 손실: {loss}{mm} × {num} = {total_loss}{mm}")
        lines.append(f"▶ 전체 여유길이: {remain:,.1f}{mm} → 각 +{add_each:,.1f}{mm}\n")

        lines.append("▶ 각 Slab별 실제 절단 길이:")
        for i, r in enumerate(real, 1):
            lines.append(f"   {i}번: {r:,.1f}{mm}")

        lines.append("")
        lines.append(f"▶ 절단센터 위치(mm): {[round_half_up(c) for c in centers]}\n")

        visual = "H"
        for i, r in enumerate(real, 1):
            mark = round_half_up(r + 15/2)
            visual += f"-{i}번({mark})-"
        visual += "T"
        lines.append("▶ 시각화 (실제 마킹 위치):")
        lines.append(visual)

        self.result_label.text = "\n".join(lines)

    # --- 설정(임시) ---
    def open_settings(self, *_):
        mv = ModalView(size_hint=(.9,.4), auto_dismiss=True)
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        box.add_widget(Label(text="설정은 추후 단계적으로 추가됩니다.", font_name=FONT,
                             color=(0,0,0,1)))
        close = RoundedButton(text="닫기", size_hint=(1,None), height=dp(42),
                              bg_color=[0.7,0.7,0.7,1], fg_color=[1,1,1,1])
        close.bind(on_release=lambda *_: mv.dismiss())
        box.add_widget(close)
        mv.add_widget(box)
        mv.open()

if __name__ == "__main__":
    SlabApp().run()
