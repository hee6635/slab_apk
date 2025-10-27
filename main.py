# -*- coding: utf-8 -*-
import os
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.uix.modalview import ModalView
from kivy.properties import NumericProperty, ListProperty, BooleanProperty
from kivy.graphics import Color, RoundedRectangle, Rectangle

FONT = "NanumGothic"  # 프로젝트 루트에 NanumGothic.ttf 포함

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

# ===== 둥근 버튼 =====
class RoundedButton(Button):
    radius = NumericProperty(dp(8))
    bg_color = ListProperty([0.85, 0.85, 0.85, 1])  # 기본 연회색
    fg_color = ListProperty([0, 0, 0, 1])           # 기본 검정 글씨

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.color = self.fg_color
        with self.canvas.before:
            self._c = Color(*self.bg_color)
            self._r = RoundedRectangle(pos=self.pos, size=self.size,
                                       radius=[(self.radius, self.radius)]*4)
        self.bind(pos=self._sync, size=self._sync, bg_color=self._recolor)

    def _sync(self, *_):
        self._r.pos = self.pos
        self._r.size = self.size

    def _recolor(self, *_):
        self._c.rgba = self.bg_color

# ===== 숫자 입력(자릿수 제한 / 소수점 허용 선택) =====
class DigitInput(TextInput):
    max_len = NumericProperty(3)           # 기본 최대 길이
    allow_float = BooleanProperty(False)   # True면 소수점 허용

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multiline = False
        self.halign = "center"
        self.font_name = FONT

    def insert_text(self, substring, from_undo=False):
        if self.allow_float:
            filtered = "".join(ch for ch in substring if ch.isdigit() or ch == ".")
            # 소수점은 하나만
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

class SlabApp(App):
    prefix = "SG94"

    def build(self):
        Window.clearcolor = (0.93, 0.93, 0.93, 1)  # 아주 연한 회색 배경

        root = BoxLayout(orientation="vertical", padding=[dp(12), dp(8)], spacing=dp(8))

        # 상단: 제목 + 설정(진한 회색, 둥근)
        top = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(44))
        top.add_widget(Label(text="후판 절단 계산기",
                             font_name=FONT, font_size=dp(28),
                             color=(0, 0, 0, 1), halign="center", valign="middle"))
        btn_settings = RoundedButton(
            text="설정", size_hint=(None, 1), width=dp(64), font_name=FONT,
            bg_color=[0.27, 0.27, 0.27, 1], fg_color=[1, 1, 1, 1]
        )
        btn_settings.bind(on_release=self.open_settings)
        top.add_widget(btn_settings)
        root.add_widget(top)

        # 강번 입력 줄: SG94 [NNN] -0 [N]
        row_code = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(36), spacing=dp(6))
        row_code.add_widget(Label(text="강번 입력:", font_name=FONT, color=(0,0,0,1),
                                  size_hint=(None,1), width=dp(70), halign="right", valign="middle"))
        row_code.add_widget(Label(text=self.prefix, font_name=FONT, color=(0,0,0,1),
                                  size_hint=(None,1), width=dp(48)))

        # 앞자리: 3자리 제한 + 꽉 차면 뒤로 포커스
        self.in_code_front = DigitInput(max_len=3, allow_float=False,
                                        size_hint=(None,1), width=dp(56))
        self.in_code_front.bind(text=self._move_to_back_if_full)
        row_code.add_widget(self.in_code_front)

        row_code.add_widget(Label(text="-0", font_name=FONT, color=(0,0,0,1),
                                  size_hint=(None,1), width=dp(26)))
        # 뒷자리: 1자리 제한
        self.in_code_back = DigitInput(max_len=1, allow_float=False,
                                       size_hint=(None,1), width=dp(48))
        row_code.add_widget(self.in_code_back)
        root.add_widget(row_code)

        # 실제 Slab 길이
        row_total = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(36), spacing=dp(6))
        row_total.add_widget(Label(text="실제 Slab 길이:", font_name=FONT, color=(0,0,0,1),
                                   size_hint=(None,1), width=dp(110), halign="right", valign="middle"))
        self.in_total = DigitInput(max_len=10, allow_float=True,
                                   size_hint=(None,1), width=dp(160))
        row_total.add_widget(self.in_total)
        row_total.add_widget(Label(size_hint=(1,1)))  # 오른쪽 여백
        root.add_widget(row_total)

        # 지시길이 1~3 + 복사 버튼(둥근)
        grid = GridLayout(cols=4, size_hint=(1, None), height=dp(36*3+8*2),
                          row_default_height=dp(36), row_force_default=True, spacing=dp(8))
        # 1
        grid.add_widget(Label(text="1번 지시길이:", font_name=FONT, color=(0,0,0,1),
                              halign="right", valign="middle", size_hint=(None,1), width=dp(110)))
        self.in_p1 = DigitInput(max_len=10, allow_float=True, size_hint=(None,1), width=dp(120))
        grid.add_widget(self.in_p1)
        grid.add_widget(Label())  # 자리맞춤
        grid.add_widget(Label())
        # 2
        grid.add_widget(Label(text="2번 지시길이:", font_name=FONT, color=(0,0,0,1),
                              halign="right", valign="middle", size_hint=(None,1), width=dp(110)))
        self.in_p2 = DigitInput(max_len=10, allow_float=True, size_hint=(None,1), width=dp(120))
        grid.add_widget(self.in_p2)
        btn_copy21 = RoundedButton(text="← 1번", font_name=FONT, size_hint=(None,1), width=dp(56),
                                   bg_color=[0.7,0.7,0.7,1], fg_color=[1,1,1,1])
        btn_copy21.bind(on_release=lambda *_: self._copy(self.in_p1, self.in_p2))
        grid.add_widget(btn_copy21)
        grid.add_widget(Label())
        # 3
        grid.add_widget(Label(text="3번 지시길이:", font_name=FONT, color=(0,0,0,1),
                              halign="right", valign="middle", size_hint=(None,1), width=dp(110)))
        self.in_p3 = DigitInput(max_len=10, allow_float=True, size_hint=(None,1), width=dp(120))
        grid.add_widget(self.in_p3)
        btn_copy31 = RoundedButton(text="← 1번", font_name=FONT, size_hint=(None,1), width=dp(56),
                                   bg_color=[0.7,0.7,0.7,1], fg_color=[1,1,1,1])
        btn_copy31.bind(on_release=lambda *_: self._copy(self.in_p1, self.in_p3))
        grid.add_widget(btn_copy31)
        btn_copy32 = RoundedButton(text="← 2번", font_name=FONT, size_hint=(None,1), width=dp(56),
                                   bg_color=[0.7,0.7,0.7,1], fg_color=[1,1,1,1])
        btn_copy32.bind(on_release=lambda *_: self._copy(self.in_p2, self.in_p3))
        grid.add_widget(btn_copy32)
        root.add_widget(grid)

        # 계산 버튼(둥근, 녹색)
        btn_calc = RoundedButton(text="계산하기", font_name=FONT, size_hint=(1, None), height=dp(44),
                                 bg_color=[0.23, 0.53, 0.23, 1], fg_color=[1,1,1,1])
        btn_calc.bind(on_release=self.calculate)
        root.add_widget(btn_calc)

        # 결과 영역(하얀 배경)
        wrapper = BoxLayout(orientation="vertical")
        self.result_label = Label(text="", font_name=FONT, color=(0,0,0,1),
                                  size_hint=(1, None), halign="left", valign="top")
        self.result_label.bind(texture_size=lambda *_: self._resize_result())

        sv = ScrollView(size_hint=(1, 1))
        with self.result_label.canvas.before:
            Color(1,1,1,1)
            self._bg_rect = Rectangle(size=self.result_label.size, pos=self.result_label.pos)
        self.result_label.bind(size=lambda *_: self._bg_follow())
        self.result_label.bind(pos=lambda *_: self._bg_follow())

        sv.add_widget(self.result_label)
        wrapper.add_widget(sv)
        # 시그니처
        sig = BoxLayout(size_hint=(1, None), height=dp(22))
        sig.add_widget(Label(text="made by ft10350", font_name=FONT, color=(0.4,0.4,0.4,1),
                             halign="right", valign="middle"))
        root.add_widget(wrapper)
        root.add_widget(sig)

        return root

    # ===== helpers =====
    def _move_to_back_if_full(self, instance, value):
        # 앞자리 3자리 꽉 차면 자동으로 뒤 입력칸으로 포커스 이동
        if len(value) >= 3:
            self.in_code_back.focus = True

    def _bg_follow(self):
        if hasattr(self, "_bg_rect"):
            self._bg_rect.size = self.result_label.size
            self._bg_rect.pos = self.result_label.pos

    def _resize_result(self):
        self.result_label.text_size = (self.result_label.width - dp(12), None)
        self.result_label.height = self.result_label.texture_size[1] + dp(12)

    def _copy(self, src, dst):
        dst.text = src.text

    # ===== 계산 =====
    def calculate(self, *_):
        slab = _num_or_none(self.in_total.text)
        p1 = _num_or_none(self.in_p1.text)
        p2 = _num_or_none(self.in_p2.text)
        p3 = _num_or_none(self.in_p3.text)

        if slab is None or slab <= 0:
            self.result_label.text = "⚠️ 실제 Slab 길이를 올바르게 입력하세요."
            return

        guides = [v for v in (p1, p2, p3) if v is not None and v > 0]
        if len(guides) < 2:
            self.result_label.text = "⚠️ 최소 2개 이상의 지시길이를 입력하세요."
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
        # 강번
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

    # ===== 설정(간단 팝업) =====
    def open_settings(self, *_):
        mv = ModalView(size_hint=(.9,.4), auto_dismiss=True)
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(8))
        box.add_widget(Label(text="설정은 추후 단계적으로 추가됩니다.", font_name=FONT,
                             color=(0,0,0,1)))
        close = RoundedButton(text="닫기", font_name=FONT, size_hint=(1,None), height=dp(40),
                              bg_color=[0.7,0.7,0.7,1], fg_color=[1,1,1,1])
        close.bind(on_release=lambda *_: mv.dismiss())
        box.add_widget(close)
        mv.add_widget(box)
        mv.open()

if __name__ == "__main__":
    SlabApp().run()
