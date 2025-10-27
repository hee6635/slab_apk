# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.modalview import ModalView
from kivy.core.window import Window
from kivy.properties import NumericProperty, ListProperty, BooleanProperty
from kivy.graphics import Color, RoundedRectangle

FONT = "NanumGothic"  # 루트에 NanumGothic.ttf 포함

# ---------- 공통: 둥근 버튼 ----------
class RoundedButton(Button):
    radius = NumericProperty(dp(8))
    bg = ListProperty([0.23, 0.53, 0.23, 1])
    fg = ListProperty([1, 1, 1, 1])

    def __init__(self, **kw):
        super().__init__(**kw)
        self.background_normal = ""
        self.background_down = ""
        self.color = self.fg
        with self.canvas.before:
            self._c = Color(*self.bg)
            self._r = RoundedRectangle(pos=self.pos, size=self.size,
                                       radius=[(self.radius, self.radius)]*4)
        self.bind(pos=self._sync, size=self._sync, bg=self._recolor)

    def _sync(self, *_):
        self._r.pos = self.pos
        self._r.size = self.size

    def _recolor(self, *_):
        self._c.rgba = self.bg

# ---------- 숫자 입력(자릿수/소수점 제한) ----------
class DigitInput(TextInput):
    max_len = NumericProperty(10)
    allow_float = BooleanProperty(True)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.multiline = False
        self.font_name = FONT
        self.halign = "center"

    def insert_text(self, substring, from_undo=False):
        if self.allow_float:
            s = "".join(ch for ch in substring if ch.isdigit() or ch == ".")
            if "." in self.text and "." in s:
                s = s.replace(".", "")
        else:
            s = "".join(ch for ch in substring if ch.isdigit())

        remain = max(0, self.max_len - len(self.text))
        if remain <= 0:
            return
        if len(s) > remain:
            s = s[:remain]
        return super().insert_text(s, from_undo=from_undo)

def _num(s):
    try:
        s = (s or "").strip()
        if not s: return None
        return float(s)
    except Exception:
        return None

def _rint(x):  # round half up to int
    return int(float(x) + 0.5)

class SlabApp(App):
    prefix = "SG94"

    def build(self):
        Window.clearcolor = (0.94, 0.94, 0.94, 1)

        root = BoxLayout(orientation="vertical", padding=[dp(14), dp(12)], spacing=dp(10))

        # ===== 상단: 제목(센터) + 설정(우상단 고정) =====
        header = FloatLayout(size_hint=(1, None), height=dp(52))
        title = Label(text="후판 절단 계산기", font_name=FONT, font_size=dp(30),
                      color=(0,0,0,1), size_hint=(None, None))
        header.add_widget(title)
        title.bind(texture_size=lambda *_: setattr(title, "size", title.texture_size))
        title.bind(size=lambda *_: setattr(title, "pos",
                                           (header.width/2 - title.width/2,
                                            header.height/2 - title.height/2)))
        header.bind(size=lambda *_: title.dispatch("on_size"))

        btn_settings = RoundedButton(text="설정", size_hint=(None, None),
                                     width=dp(70), height=dp(40),
                                     bg=[0.27,0.27,0.27,1], fg=[1,1,1,1])
        btn_settings.pos = (header.width - btn_settings.width, header.height - btn_settings.height)
        header.bind(size=lambda *_: setattr(btn_settings, "pos",
                         (header.width - btn_settings.width, header.height - btn_settings.height)))
        btn_settings.bind(on_release=self.open_settings)
        header.add_widget(btn_settings)

        root.add_widget(header)

        # ===== 폼 영역 =====
        form = GridLayout(cols=3, col_force_default=False, spacing=dp(8), size_hint=(1, None))
        form.bind(minimum_height=lambda *_: setattr(form, "height", form.minimum_height))

        def add_row(label_txt, widget, right=None):
            lab = Label(text=label_txt, font_name=FONT, color=(0,0,0,1),
                        size_hint_x=None, width=dp(110), halign="right", valign="middle")
            lab.bind(size=lambda *_: setattr(lab, "text_size", lab.size))
            form.add_widget(lab)
            form.add_widget(widget)
            if right is None:
                form.add_widget(Label(size_hint_x=None, width=dp(64)))
            else:
                form.add_widget(right)

        # 강번 입력: [SG94] [NNN] [-0] [N]
        row1 = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(38), spacing=dp(6))
        lab_prefix = Label(text=self.prefix, font_name=FONT, color=(0,0,0,1),
                           size_hint=(None,1), width=dp(48), halign="center", valign="middle")
        lab_prefix.bind(size=lambda *_: setattr(lab_prefix, "text_size", lab_prefix.size))
        self.code_front = DigitInput(allow_float=False, max_len=3, size_hint=(None,1), width=dp(70))
        dash = Label(text="-0", font_name=FONT, color=(0,0,0,1),
                     size_hint=(None,1), width=dp(26), halign="center", valign="middle")
        dash.bind(size=lambda *_: setattr(dash, "text_size", dash.size))
        self.code_back = DigitInput(allow_float=False, max_len=1, size_hint=(None,1), width=dp(48))
        # 3자리 채워지면 바로 뒤로 포커스
        self.code_front.bind(text=lambda *_: self._auto_move())

        row1.add_widget(lab_prefix)
        row1.add_widget(self.code_front)
        row1.add_widget(dash)
        row1.add_widget(self.code_back)

        add_row("강번 입력:", row1)

        # 실제 길이
        self.total = DigitInput(max_len=10, allow_float=True, size_hint=(1,None), height=dp(38))
        add_row("실제 Slab 길이:", self.total)

        # 지시 1~3 + 복사 버튼(좁게)
        self.p1 = DigitInput(max_len=10, allow_float=True, size_hint=(1,None), height=dp(38))
        add_row("1번 지시길이:", self.p1)

        self.p2 = DigitInput(max_len=10, allow_float=True, size_hint=(1,None), height=dp(38))
        btn21 = RoundedButton(text="← 1번", size_hint=(None,None), width=dp(58), height=dp(36),
                              bg=[0.65,0.65,0.65,1], fg=[1,1,1,1])
        btn21.bind(on_release=lambda *_: self._copy(self.p1, self.p2))
        add_row("2번 지시길이:", self.p2, right=btn21)

        self.p3 = DigitInput(max_len=10, allow_float=True, size_hint=(1,None), height=dp(38))
        box_btns = BoxLayout(size_hint=(None, None), size=(dp(128), dp(36)), spacing=dp(6))
        btn31 = RoundedButton(text="← 1번", size_hint=(None,None), width=dp(58), height=dp(36),
                              bg=[0.65,0.65,0.65,1], fg=[1,1,1,1])
        btn32 = RoundedButton(text="← 2번", size_hint=(None,None), width=dp(58), height=dp(36),
                              bg=[0.65,0.65,0.65,1], fg=[1,1,1,1])
        btn31.bind(on_release=lambda *_: self._copy(self.p1, self.p3))
        btn32.bind(on_release=lambda *_: self._copy(self.p2, self.p3))
        box_btns.add_widget(btn31); box_btns.add_widget(btn32)
        add_row("3번 지시길이:", self.p3, right=box_btns)

        root.add_widget(form)

        # 계산 버튼
        calc = RoundedButton(text="계산하기", size_hint=(1,None), height=dp(46),
                             bg=[0.23,0.53,0.23,1], fg=[1,1,1,1])
        calc.bind(on_release=self.calculate)
        root.add_widget(calc)

        # 결과 카드
        card = BoxLayout(orientation="vertical", padding=dp(10), size_hint=(1,1))
        self.result = Label(text="", font_name=FONT, color=(0,0,0,1),
                            size_hint=(1,None), halign="left", valign="top")
        self.result.bind(texture_size=lambda *_: self._resize_result())
        sv = ScrollView()
        # 카드 배경
        with card.canvas.before:
            Color(1,1,1,1)
            self._card_bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[(dp(8),dp(8))]*4)
        card.bind(size=lambda *_: self._sync_card(card), pos=lambda *_: self._sync_card(card))

        sv.add_widget(self.result)
        card.add_widget(sv)
        root.add_widget(card)

        # 시그니처(우하단)
        sig_bar = BoxLayout(size_hint=(1,None), height=dp(24), padding=[0,0,dp(10),0])
        sig = Label(text="made by ft10350", font_name=FONT, color=(0.4,0.4,0.4,1),
                    halign="right", valign="middle")
        sig.bind(size=lambda *_: setattr(sig, "text_size", sig.size))
        sig_bar.add_widget(sig)
        root.add_widget(sig_bar)

        return root

    # ---- helpers
    def _sync_card(self, card):
        self._card_bg.pos = card.pos
        self._card_bg.size = card.size

    def _resize_result(self):
        self.result.text_size = (self.result.width - dp(8), None)
        self.result.height = self.result.texture_size[1] + dp(8)

    def _copy(self, src, dst):
        dst.text = src.text

    def _auto_move(self):
        if len(self.code_front.text) >= 3:
            self.code_back.focus = True

    # ---- 계산
    def calculate(self, *_):
        slab = _num(self.total.text)
        p1, p2, p3 = _num(self.p1.text), _num(self.p2.text), _num(self.p3.text)
        if not slab or slab <= 0:
            self.result.text = "⚠️ 실제 Slab 길이를 올바르게 입력하세요."
            return
        guides = [v for v in (p1, p2, p3) if v and v > 0]
        if len(guides) < 2:
            self.result.text = "⚠️ 최소 2개 이상의 지시길이를 입력하세요."
            return

        loss = 15.0
        total_loss = loss * (len(guides)-1)
        remain = slab - (sum(guides) + total_loss)
        add_each = remain / len(guides)
        real = [g + add_each for g in guides]

        centers, acc = [], 0.0
        for l in real[:-1]:
            acc += l + (loss/2); centers.append(acc); acc += (loss/2)

        cf = (self.code_front.text or "").strip()
        cb = (self.code_back.text or "").strip()
        lines = []
        if cf and cb:
            lines.append(f"▶ 강번: {self.prefix}{cf}-0{cb}\n")

        lines.append(f"▶ Slab 실길이: {slab:,.1f} mm")
        for i, g in enumerate(guides, 1):
            lines.append(f"▶ {i}번 지시길이: {g:,.1f} mm")
        lines.append(f"▶ 절단 손실: {loss} mm × {len(guides)-1} = {total_loss} mm")
        lines.append(f"▶ 전체 여유길이: {remain:,.1f} mm → 각 +{add_each:,.1f} mm\n")

        lines.append("▶ 각 Slab별 실제 절단 길이:")
        for i, r in enumerate(real, 1):
            lines.append(f"{i}번: {r:,.1f} mm")

        lines.append(f"\n▶ 절단센터 위치(mm): {[_rint(c) for c in centers]}\n")

        visual = "H"
        for i, r in enumerate(real, 1):
            visual += f"-{i}번({_rint(r + loss/2)})-"
        visual += "T"
        lines.append("▶ 시각화 (실제 마킹 위치):")
        lines.append(visual)

        self.result.text = "\n".join(lines)

    # ---- 설정(임시 팝업)
    def open_settings(self, *_):
        mv = ModalView(size_hint=(.9,.4))
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        box.add_widget(Label(text="설정은 추후 단계적으로 추가됩니다.", font_name=FONT, color=(0,0,0,1)))
        close = RoundedButton(text="닫기", size_hint=(1,None), height=dp(40),
                              bg=[0.7,0.7,0.7,1], fg=[1,1,1,1])
        close.bind(on_release=lambda *_: mv.dismiss())
        box.add_widget(close)
        mv.add_widget(box)
        mv.open()

if __name__ == "__main__":
    SlabApp().run()
