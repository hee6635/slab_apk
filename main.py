# -*- coding: utf-8 -*-
import os
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.uix.modalview import ModalView
from kivy.properties import NumericProperty, ListProperty, BooleanProperty
from kivy.graphics import Color, RoundedRectangle

FONT = "NanumGothic"  # 프로젝트 루트에 NanumGothic.ttf 포함
WARN_ICON = "warning.png"  # 프로젝트 루트에 warning.png 포함

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

# ---------- 둥근 버튼(라벨 기반) ----------
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

# ---------- 숫자 입력 ----------
class DigitInput(TextInput):
    max_len = NumericProperty(3)
    allow_float = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multiline = False
        self.halign = "left"            # 왼쪽 정렬
        self.font_name = FONT
        self.font_size = dp(16)
        self.height = dp(30)            # 행 높이 소폭 축소
        self.background_normal = ""
        self.background_active = ""
        self.cursor_width = dp(2)
        self.padding = [dp(4), dp(4)]   # 내부 여백 축소(라벨-입력칸 사이 공백과 함께 체감 간격 줄이기)

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

# ---------- 앱 ----------
class SlabApp(App):
    prefix = "SG94"

    def build(self):
        Window.clearcolor = (0.93, 0.93, 0.93, 1)

        root = BoxLayout(orientation="vertical", padding=[dp(10), dp(6)], spacing=dp(6))

        # 상단: 우상단 설정 버튼 + 중앙 제목
        topbar = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(40))
        title = Label(text="후판 계산기", font_name=FONT, font_size=dp(28),
                      color=(0, 0, 0, 1), halign="center", valign="middle")
        title.bind(size=lambda *_: setattr(title, "text_size", title.size))
        # 오른쪽 설정
        btn_settings = RoundedButton(text="설정", size_hint=(None, 1), width=dp(68),
                                     bg_color=[0.27, 0.27, 0.27, 1],
                                     fg_color=[1, 1, 1, 1], radius=dp(10))
        # 설정 버튼만 반응하도록 collide 체크
        btn_settings.bind(on_touch_up=lambda w, t: self.open_settings() if w.collide_point(*t.pos) else None)

        # 좌-중앙-우 정렬을 위해 3분할
        topbar.add_widget(Label(size_hint=(.2, 1)))   # 좌측 빈 공간
        topbar.add_widget(title)                      # 중앙 제목
        right_box = BoxLayout(size_hint=(.2, 1))
        right_box.add_widget(Label())                 # 우측 여백
        right_box.add_widget(btn_settings)
        topbar.add_widget(right_box)
        root.add_widget(topbar)

        # -------- 입력부 (행 높이/간격/라벨폭 축소로 공백 최소화) --------
        row_h = dp(30)
        row_spacing = dp(4)
        label_w = dp(100)

        # 강번 입력
        row_code = BoxLayout(orientation="horizontal", size_hint=(1, None),
                             height=row_h, spacing=row_spacing)
        row_code.add_widget(Label(text="강번 입력:", font_name=FONT, color=(0,0,0,1),
                                  size_hint=(None,1), width=label_w, halign="right", valign="middle"))
        row_code.add_widget(Label(text=self.prefix, font_name=FONT, color=(0,0,0,1),
                                  size_hint=(None,1), width=dp(44), halign="center", valign="middle"))
        self.in_code_front = DigitInput(max_len=3, allow_float=False, size_hint=(None,1), width=dp(64))
        self.in_code_front.bind(text=self._auto_move_back)
        row_code.add_widget(self.in_code_front)
        row_code.add_widget(Label(text="-0", font_name=FONT, color=(0,0,0,1),
                                  size_hint=(None,1), width=dp(22), halign="center", valign="middle"))
        self.in_code_back = DigitInput(max_len=1, allow_float=False, size_hint=(None,1), width=dp(40))
        row_code.add_widget(self.in_code_back)
        root.add_widget(row_code)

        # Slab 길이 (5자리)
        row_total = BoxLayout(orientation="horizontal", size_hint=(1, None),
                              height=row_h, spacing=row_spacing)
        row_total.add_widget(Label(text="실제 Slab 길이:", font_name=FONT, color=(0,0,0,1),
                                   size_hint=(None,1), width=label_w, halign="right", valign="middle"))
        self.in_total = DigitInput(max_len=5, allow_float=True, size_hint=(None,1), width=dp(130))
        row_total.add_widget(self.in_total)
        row_total.add_widget(Label(size_hint=(1,1)))  # 오른쪽 여백
        root.add_widget(row_total)

        # 지시길이 (4자리) + 복사 버튼
        grid = GridLayout(cols=4, size_hint=(1, None), height=row_h*3 + row_spacing*2,
                          row_default_height=row_h, row_force_default=True, spacing=dp(6))

        self.in_p1 = DigitInput(max_len=4, allow_float=True, size_hint=(None,1), width=dp(110))
        self.in_p2 = DigitInput(max_len=4, allow_float=True, size_hint=(None,1), width=dp(110))
        self.in_p3 = DigitInput(max_len=4, allow_float=True, size_hint=(None,1), width=dp(110))

        # 1번
        grid.add_widget(Label(text="1번 지시길이:", font_name=FONT, color=(0,0,0,1),
                              size_hint=(None,1), width=label_w, halign="right", valign="middle"))
        grid.add_widget(self.in_p1); grid.add_widget(Label()); grid.add_widget(Label())
        # 2번
        grid.add_widget(Label(text="2번 지시길이:", font_name=FONT, color=(0,0,0,1),
                              size_hint=(None,1), width=label_w, halign="right", valign="middle"))
        grid.add_widget(self.in_p2)
        b21 = RoundedButton(text="← 1번", bg_color=[0.86,0.86,0.86,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(64), radius=dp(10))
        b21.bind(on_touch_up=lambda w, t: self._copy(self.in_p1, self.in_p2) if w.collide_point(*t.pos) else None)
        grid.add_widget(b21)
        grid.add_widget(Label())  # 간격 고정
        # 3번
        grid.add_widget(Label(text="3번 지시길이:", font_name=FONT, color=(0,0,0,1),
                              size_hint=(None,1), width=label_w, halign="right", valign="middle"))
        grid.add_widget(self.in_p3)
        b31 = RoundedButton(text="← 1번", bg_color=[0.86,0.86,0.86,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(64), radius=dp(10))
        b31.bind(on_touch_up=lambda w, t: self._copy(self.in_p1, self.in_p3) if w.collide_point(*t.pos) else None)
        grid.add_widget(b31)
        b32 = RoundedButton(text="← 2번", bg_color=[0.86,0.86,0.86,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(64), radius=dp(10))
        b32.bind(on_touch_up=lambda w, t: self._copy(self.in_p2, self.in_p3) if w.collide_point(*t.pos) else None)
        grid.add_widget(b32)
        root.add_widget(grid)

        # 계산 버튼
        btn_calc = RoundedButton(text="계산하기", bg_color=[0.23, 0.53, 0.23, 1],
                                 fg_color=[1,1,1,1], size_hint=(1, None),
                                 height=dp(44), radius=dp(10))
        btn_calc.bind(on_touch_up=lambda w, t: self.calculate() if w.collide_point(*t.pos) else None)
        root.add_widget(btn_calc)

        # -------- 결과 영역(스크롤) : 오류 메시지도 여기서 표시 --------
        self.result_sv = ScrollView(size_hint=(1, 1))
        self.result_container = BoxLayout(orientation="vertical", size_hint_y=None,
                                          padding=[dp(8), dp(8)], spacing=dp(6))
        self.result_container.bind(minimum_height=lambda c, h: setattr(c, "height", h))
        # 하얀 배경 + 둥근 모서리
        with self.result_container.canvas.before:
            Color(1,1,1,1)
            self._bg_rect = RoundedRectangle(pos=self.result_container.pos,
                                             size=self.result_container.size,
                                             radius=[(dp(6), dp(6))]*4)
        self.result_container.bind(pos=self._bg_follow, size=self._bg_follow)
        self.result_sv.add_widget(self.result_container)
        root.add_widget(self.result_sv)

        # 시그니처
        sig = Label(text="made by ft10350", font_name=FONT, color=(0.4,0.4,0.4,1),
                    halign="right", valign="middle", size_hint=(1, None), height=dp(22))
        sig.bind(size=lambda *_: setattr(sig, "text_size", sig.size))
        root.add_widget(sig)

        return root

    # ----- helpers -----
    def _auto_move_back(self, instance, value):
        if len(value) >= 3:
            self.in_code_back.focus = True

    def _copy(self, src, dst):
        dst.text = src.text

    def _bg_follow(self, *a):
        self._bg_rect.pos, self._bg_rect.size = self.result_container.pos, self.result_container.size

    def _set_result_text(self, text):
        """결과 컨테이너에 복사 가능한 라벨로 세팅"""
        self.result_container.clear_widgets()
        lbl = Label(text=text, font_name=FONT, color=(0,0,0,1),
                    size_hint=(1, None), halign="left", valign="top")
        # 복사/붙여넣기 가능(TextInput이 아니어도 길게 누르면 복사 가능하도록)
        # Kivy Label은 기본 복사 UI가 없으므로 TextInput(readonly)로 대체
        ti = TextInput(text=text, readonly=True, font_name=FONT, foreground_color=(0,0,0,1),
                       background_color=(0,0,0,0), size_hint=(1,None), multiline=True,
                       padding=[dp(4), dp(4)])
        # 높이 자동
        def _resize_ti(*_):
            ti.width = self.result_sv.width - dp(16)
            ti.text_size = (ti.width, None)
            ti.height = ti.minimum_height + dp(8)
        ti.bind(texture_size=_resize_ti, size=_resize_ti)
        self.result_sv.bind(size=_resize_ti)
        self.result_container.add_widget(ti)

    def _set_error_in_result(self, message):
        """에러를 결과 영역 내부에 (warning.png + 텍스트)로 표시"""
        self.result_container.clear_widgets()
        row = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(30), spacing=dp(6))
        if os.path.exists(WARN_ICON):
            row.add_widget(Image(source=WARN_ICON, size_hint=(None, None), size=(dp(18), dp(18))))
        else:
            # 아이콘이 없으면 대체문자
            row.add_widget(Label(text="⚠️", size_hint=(None,None), size=(dp(18), dp(18))))
        row.add_widget(Label(text=message, font_name=FONT, color=(0,0,0,1),
                             halign="left", valign="middle"))
        self.result_container.add_widget(row)

    # ----- 계산 -----
    def calculate(self, *_):
        slab = _num_or_none(self.in_total.text)
        p1 = _num_or_none(self.in_p1.text)
        p2 = _num_or_none(self.in_p2.text)
        p3 = _num_or_none(self.in_p3.text)

        if slab is None or slab <= 0:
            self._set_error_in_result("실제 Slab 길이를 올바르게 입력하세요.")
            return

        guides = [v for v in (p1, p2, p3) if v is not None and v > 0]
        if len(guides) < 2:
            self._set_error_in_result("최소 2개 이상의 지시길이를 입력하세요.")
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

        # 용어 개선: "각 Slab별 실제 절단 길이" -> "각 Slab별 절단 후 예상 길이"
        lines.append("▶ 각 Slab별 절단 후 예상 길이:")
        for i, r in enumerate(real, 1):
            lines.append(f"   {i}번: {r:,.1f}{mm}")

        lines.append("")
        # 절단센터 위치는 사용 안 함(요청에 따라 제외 가능) — 필요 시 주석 해제
        # lines.append(f"▶ 절단센터 위치(mm): {[round_half_up(c) for c in centers]}\n")

        # 시각화 제목 개선: "(실제 마킹 위치)" -> "(절단 마킹 포인트)"
        visual = "H"
        for i, r in enumerate(real, 1):
            mark = round_half_up(r + loss/2)
            visual += f"-{i}번({mark})-"
        visual += "T"
        lines.append("▶ 시각화 (절단 마킹 포인트):")
        lines.append(visual)

        self._set_result_text("\n".join(lines))

    # ----- 설정 -----
    def open_settings(self, *_):
        mv = ModalView(size_hint=(.9,.4))
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(8))
        box.add_widget(Label(text="설정은 추후 추가 예정입니다.", font_name=FONT,
                             color=(0,0,0,1)))
        close = RoundedButton(text="닫기", bg_color=[0.8,0.8,0.8,1], fg_color=[0,0,0,1],
                              size_hint=(1,None), height=dp(40), radius=dp(10))
        close.bind(on_touch_up=lambda w, t: mv.dismiss() if w.collide_point(*t.pos) else None)
        box.add_widget(close)
        mv.add_widget(box)
        mv.open()

if __name__ == "__main__":
    SlabApp().run()
