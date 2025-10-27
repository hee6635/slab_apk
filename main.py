
# -*- coding: utf-8 -*-
import os
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.uix.modalview import ModalView
from kivy.properties import NumericProperty, ListProperty, BooleanProperty
from kivy.graphics import Color, RoundedRectangle

FONT = "NanumGothic"

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

# 둥근 버튼
class RoundedButton(Label):
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
        self.bind(pos=self._sync_bg, size=self._sync_bg)

    def _sync_bg(self, *a):
        self._r.pos, self._r.size = self.pos, self.size

# 숫자 입력
class DigitInput(TextInput):
    max_len = NumericProperty(3)
    allow_float = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multiline = False
        self.halign = "center"
        self.font_name = FONT
        self.font_size = dp(16)
        self.height = dp(32)  # 입력창 높이 축소
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

class SlabApp(App):
    prefix = "SG94"

    def build(self):
        Window.clearcolor = (0.93, 0.93, 0.93, 1)

        root = BoxLayout(orientation="vertical", padding=[dp(12), dp(8)], spacing=dp(8))

        # 제목
        title = Label(text="후판 계산기", font_name=FONT, font_size=dp(28),
                      color=(0, 0, 0, 1), halign="left", valign="middle")
        title.bind(size=lambda *_: setattr(title, "text_size", title.size))
        top = BoxLayout(size_hint=(1, None), height=dp(44))
        top.add_widget(title)

        btn_settings = RoundedButton(text="설정", size_hint=(None, 1), width=dp(68),
                                     bg_color=[0.27, 0.27, 0.27, 1],
                                     fg_color=[1, 1, 1, 1])
        btn_settings.bind(on_touch_up=lambda *_: self.open_settings())
        top.add_widget(btn_settings)
        root.add_widget(top)

        # 강번 입력
        row_code = BoxLayout(orientation="horizontal", size_hint=(1, None),
                             height=dp(32), spacing=dp(6))
        row_code.add_widget(Label(text="강번 입력:", font_name=FONT, color=(0,0,0,1),
                                  size_hint=(None,1), width=dp(80), halign="right", valign="middle"))
        row_code.add_widget(Label(text=self.prefix, font_name=FONT, color=(0,0,0,1),
                                  size_hint=(None,1), width=dp(50)))
        self.in_code_front = DigitInput(max_len=3, allow_float=False, size_hint=(None,1), width=dp(60))
        self.in_code_front.bind(text=self._auto_move_back)
        row_code.add_widget(self.in_code_front)
        row_code.add_widget(Label(text="-0", font_name=FONT, color=(0,0,0,1),
                                  size_hint=(None,1), width=dp(26)))
        self.in_code_back = DigitInput(max_len=1, allow_float=False, size_hint=(None,1), width=dp(40))
        row_code.add_widget(self.in_code_back)
        root.add_widget(row_code)

        # Slab 길이 입력 (5자리 제한)
        row_total = BoxLayout(orientation="horizontal", size_hint=(1, None),
                              height=dp(32), spacing=dp(6))
        row_total.add_widget(Label(text="실제 Slab 길이:", font_name=FONT, color=(0,0,0,1),
                                   size_hint=(None,1), width=dp(110), halign="right", valign="middle"))
        self.in_total = DigitInput(max_len=5, allow_float=True, size_hint=(None,1), width=dp(130))
        row_total.add_widget(self.in_total)
        row_total.add_widget(Label(size_hint=(1,1)))
        root.add_widget(row_total)

        # 지시길이 (4자리 제한)
        grid = GridLayout(cols=4, size_hint=(1, None), height=dp(32*3+8*2),
                          row_default_height=dp(32), row_force_default=True, spacing=dp(8))

        self.in_p1 = DigitInput(max_len=4, allow_float=True, size_hint=(None,1), width=dp(100))
        self.in_p2 = DigitInput(max_len=4, allow_float=True, size_hint=(None,1), width=dp(100))
        self.in_p3 = DigitInput(max_len=4, allow_float=True, size_hint=(None,1), width=dp(100))

        grid.add_widget(Label(text="1번 지시길이:", font_name=FONT, color=(0,0,0,1),
                              size_hint=(None,1), width=dp(110), halign="right", valign="middle"))
        grid.add_widget(self.in_p1)
        grid.add_widget(Label()); grid.add_widget(Label())

        grid.add_widget(Label(text="2번 지시길이:", font_name=FONT, color=(0,0,0,1),
                              size_hint=(None,1), width=dp(110), halign="right", valign="middle"))
        grid.add_widget(self.in_p2)
        b21 = RoundedButton(text="← 1번", bg_color=[0.8,0.8,0.8,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(60))
        b21.bind(on_touch_up=lambda *_: self._copy(self.in_p1, self.in_p2))
        grid.add_widget(b21)
        grid.add_widget(Label())

        grid.add_widget(Label(text="3번 지시길이:", font_name=FONT, color=(0,0,0,1),
                              size_hint=(None,1), width=dp(110), halign="right", valign="middle"))
        grid.add_widget(self.in_p3)
        b31 = RoundedButton(text="← 1번", bg_color=[0.8,0.8,0.8,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(60))
        b31.bind(on_touch_up=lambda *_: self._copy(self.in_p1, self.in_p3))
        grid.add_widget(b31)
        b32 = RoundedButton(text="← 2번", bg_color=[0.8,0.8,0.8,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(60))
        b32.bind(on_touch_up=lambda *_: self._copy(self.in_p2, self.in_p3))
        grid.add_widget(b32)
        root.add_widget(grid)

        # 계산 버튼
        btn_calc = RoundedButton(text="계산하기", bg_color=[0.23, 0.53, 0.23, 1],
                                 fg_color=[1,1,1,1], size_hint=(1, None),
                                 height=dp(44), radius=dp(10))
        btn_calc.bind(on_touch_up=lambda *_: self.calculate())
        root.add_widget(btn_calc)

        # 결과 영역
        wrapper = BoxLayout(orientation="vertical")
        self.result_label = Label(text="", font_name=FONT, color=(0,0,0,1),
                                  size_hint=(1, None), halign="left", valign="top")
        self.result_label.bind(texture_size=lambda *_: self._resize_result())
        sv = ScrollView(size_hint=(1, 1))
        with self.result_label.canvas.before:
            Color(1,1,1,1)
            self._bg_rect = RoundedRectangle(size=self.result_label.size, pos=self.result_label.pos,
                                             radius=[(dp(6), dp(6))]*4)
        self.result_label.bind(size=self._bg_follow, pos=self._bg_follow)
        sv.add_widget(self.result_label)
        wrapper.add_widget(sv)

        # 시그니처
        sig = Label(text="made by ft10350", font_name=FONT, color=(0.4,0.4,0.4,1),
                    halign="right", valign="middle", size_hint=(1, None), height=dp(22))
        sig.bind(size=lambda *_: setattr(sig, "text_size", sig.size))
        wrapper.add_widget(sig)
        root.add_widget(wrapper)

        return root

    def _auto_move_back(self, instance, value):
        if len(value) >= 3:
            self.in_code_back.focus = True

    def _copy(self, src, dst):
        dst.text = src.text

    def _bg_follow(self, *a):
        self._bg_rect.pos, self._bg_rect.size = self.result_label.pos, self.result_label.size

    def _resize_result(self):
        self.result_label.text_size = (self.result_label.width - dp(12), None)
        self.result_label.height = self.result_label.texture_size[1] + dp(12)

    def calculate(self, *_):
        slab = _num_or_none(self.in_total.text)
        p1, p2, p3 = map(_num_or_none, [self.in_p1.text, self.in_p2.text, self.in_p3.text])
        if slab is None or slab <= 0:
            self.result_label.text = "⚠️ 실제 Slab 길이를 올바르게 입력하세요."
            return
        guides = [v for v in (p1,p2,p3) if v]
        if len(guides) < 2:
            self.result_label.text = "⚠️ 최소 2개 이상의 지시길이를 입력하세요."
            return
        loss = 15.0
        total_loss = loss*(len(guides)-1)
        remain = slab - (sum(guides)+total_loss)
        add_each = remain/len(guides)
        real = [g+add_each for g in guides]
        centers = []; acc=0
        for l in real[:-1]:
            acc += l+(loss/2); centers.append(acc); acc += (loss/2)
        mm=" mm"; cf=self.in_code_front.text.strip(); cb=self.in_code_back.text.strip()
        lines=[]
        if cf and cb: lines.append(f"▶ 강번: {self.prefix}{cf}-0{cb}\n")
        lines.append(f"▶ Slab 실길이: {slab:,.1f}{mm}")
        for i,g in enumerate(guides,1): lines.append(f"▶ {i}번 지시길이: {g:,.1f}{mm}")
        lines.append(f"▶ 절단 손실: {loss}{mm} × {len(guides)-1} = {total_loss}{mm}")
        lines.append(f"▶ 전체 여유길이: {remain:,.1f}{mm} → 각 +{add_each:,.1f}{mm}\n")
        lines.append("▶ 각 Slab별 실제 절단 길이:")
        for i,r in enumerate(real,1): lines.append(f"   {i}번: {r:,.1f}{mm}")
        lines.append(f"\n▶ 절단센터 위치(mm): {[round_half_up(c) for c in centers]}\n")
        visual="H"
        for i,r in enumerate(real,1):
            mark=round_half_up(r+loss/2); visual+=f"-{i}번({mark})-"
        visual+="T"
        lines.append("▶ 시각화 (실제 마킹 위치):"); lines.append(visual)
        self.result_label.text="\n".join(lines)

    def open_settings(self, *_):
        mv=ModalView(size_hint=(.9,.4))
        box=BoxLayout(orientation="vertical",padding=dp(14),spacing=dp(8))
        box.add_widget(Label(text="설정은 추후 추가 예정입니다.",font_name=FONT,color=(0,0,0,1)))
        close=RoundedButton(text="닫기",bg_color=[0.8,0.8,0.8,1],fg_color=[0,0,0,1],
                            size_hint=(1,None),height=dp(40))
        close.bind(on_touch_up=lambda *_: mv.dismiss())
        box.add_widget(close)
        mv.add_widget(box); mv.open()

if __name__ == "__main__":
    SlabApp().run()

