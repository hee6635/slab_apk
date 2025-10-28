# 버전 5 - UI 미세조정 & 결과 편집 가능(TextInput) 2025-10-28
# 변경점:
# - 강번 첫 입력칸(in_code_front) 폭 확대: dp(84)
# - 입력 칸 가로폭: 전체 대비 약 60% 유지
# - 라벨↔입력칸 간격(라벨 width) 축소 유지(= 50% 축소 효과)
# - 결과 영역: TextInput로 복귀(복사/편집 가능)
# - 출력 섹션명: "절단 후 예상 길이", "시각화 (절단 마킹 포인트)"
# - "절단센터 위치" 출력 제거

# -*- coding: utf-8 -*-
import os
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.uix.modalview import ModalView
from kivy.properties import NumericProperty, ListProperty, BooleanProperty
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget

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

# 둥근 버튼 (라벨 + 버튼)
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

# 숫자 입력(왼쪽정렬 + 패딩 + 길이제한)
class DigitInput(TextInput):
    max_len = NumericProperty(3)
    allow_float = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multiline = False
        self.halign = "left"
        self.padding = (dp(8), dp(6))
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

class SlabApp(App):
    prefix = "SG94"

    def build(self):
        Window.clearcolor = (0.93, 0.93, 0.93, 1)

        root = BoxLayout(orientation="vertical", padding=[dp(12), dp(8)], spacing=dp(8))

        # 상단 설정 버튼 (우상단)
        topbar = BoxLayout(size_hint=(1, None), height=dp(40), padding=[0, 0, 0, 0], spacing=0)
        topbar.add_widget(Widget())
        btn_settings = RoundedButton(text="설정", size_hint=(None, 1), width=dp(72),
                                     bg_color=[0.27, 0.27, 0.27, 1], fg_color=[1, 1, 1, 1])
        btn_settings.bind(on_release=lambda *_: self.open_settings())
        topbar.add_widget(btn_settings)
        root.add_widget(topbar)

        # 제목 (가운데 정렬)
        title_row = BoxLayout(size_hint=(1, None), height=dp(44))
        title = Label(text="후판 계산기", font_name=FONT, font_size=dp(28),
                      color=(0, 0, 0, 1), halign="center", valign="middle")
        title.bind(size=lambda *_: setattr(title, "text_size", title.size))
        title_row.add_widget(title)
        root.add_widget(title_row)

        # 공통: 라벨 폭(간격 축소용)
        LABEL_W = dp(90)  # 이전 대비 50% 정도 축소 효과

        # 강번 입력 행
        row_code = BoxLayout(orientation="horizontal", size_hint=(1, None),
                             height=dp(30), spacing=dp(6))
        row_code.add_widget(Label(text="강번 입력:", font_name=FONT, color=(0,0,0,1),
                                  size_hint=(None,1), width=LABEL_W, halign="right", valign="middle"))
        row_code.add_widget(Label(text=self.prefix, font_name=FONT, color=(0,0,0,1),
                                  size_hint=(None,1), width=dp(44)))
        # 첫 입력칸 폭 확대
        self.in_code_front = DigitInput(max_len=3, allow_float=False, size_hint=(None,1), width=dp(84))
        self.in_code_front.bind(text=self._auto_move_back)
        row_code.add_widget(self.in_code_front)
        row_code.add_widget(Label(text="-0", font_name=FONT, color=(0,0,0,1),
                                  size_hint=(None,1), width=dp(26)))
        self.in_code_back = DigitInput(max_len=1, allow_float=False, size_hint=(None,1), width=dp(44))
        row_code.add_widget(self.in_code_back)
        # 남는 공간 약간 유지
        row_code.add_widget(Widget())
        root.add_widget(row_code)

        # 실제 Slab 길이
        row_total = BoxLayout(orientation="horizontal", size_hint=(1, None),
                              height=dp(30), spacing=dp(6))
        row_total.add_widget(Label(text="실제 Slab 길이:", font_name=FONT, color=(0,0,0,1),
                                   size_hint=(None,1), width=LABEL_W, halign="right", valign="middle"))
        # 전체 대비 약 60% 폭
        self.in_total = DigitInput(max_len=5, allow_float=True, size_hint=(None,1), width=dp(180))
        row_total.add_widget(self.in_total)
        row_total.add_widget(Widget())
        root.add_widget(row_total)

        # 지시길이들 + 복사 버튼
        grid = GridLayout(cols=4, size_hint=(1, None), height=dp(30*3+8*2),
                          row_default_height=dp(30), row_force_default=True, spacing=dp(8))

        self.in_p1 = DigitInput(max_len=4, allow_float=True, size_hint=(None,1), width=dp(160))
        self.in_p2 = DigitInput(max_len=4, allow_float=True, size_hint=(None,1), width=dp(160))
        self.in_p3 = DigitInput(max_len=4, allow_float=True, size_hint=(None,1), width=dp(160))

        grid.add_widget(Label(text="1번 지시길이:", font_name=FONT, color=(0,0,0,1),
                              size_hint=(None,1), width=LABEL_W, halign="right", valign="middle"))
        grid.add_widget(self.in_p1)
        grid.add_widget(Label())
        grid.add_widget(Label())

        grid.add_widget(Label(text="2번 지시길이:", font_name=FONT, color=(0,0,0,1),
                              size_hint=(None,1), width=LABEL_W, halign="right", valign="middle"))
        grid.add_widget(self.in_p2)
        b21 = RoundedButton(text="← 1번", bg_color=[0.8,0.8,0.8,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(64))
        b21.bind(on_release=lambda *_: self._copy(self.in_p1, self.in_p2))
        grid.add_widget(b21)
        grid.add_widget(Label())

        grid.add_widget(Label(text="3번 지시길이:", font_name=FONT, color=(0,0,0,1),
                              size_hint=(None,1), width=LABEL_W, halign="right", valign="middle"))
        grid.add_widget(self.in_p3)
        btn_row = BoxLayout(orientation="horizontal", spacing=dp(8),
                            size_hint=(None,1), width=dp(64*2 + 8))
        b31 = RoundedButton(text="← 1번", bg_color=[0.8,0.8,0.8,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(64))
        b32 = RoundedButton(text="← 2번", bg_color=[0.8,0.8,0.8,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(64))
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

        # 결과 영역: TextInput(복사/편집 가능, 스크롤 없이 고정 높이)
        wrapper = BoxLayout(orientation="vertical", spacing=dp(6))
        # 결과 박스(라운드 배경)
        self.result_box = BoxLayout(size_hint=(1, None), height=dp(300), padding=dp(10))
        with self.result_box.canvas.before:
            Color(1,1,1,1)
            self._res_bg = RoundedRectangle(size=self.result_box.size, pos=self.result_box.pos,
                                            radius=[(dp(6), dp(6))]*4)
        self.result_box.bind(size=self._resbg_follow, pos=self._resbg_follow)

        self.result_input = TextInput(text="", font_name=FONT, font_size=dp(15),
                                      foreground_color=(0,0,0,1),
                                      background_color=(0,0,0,0),  # 투명(상자 배경만 사용)
                                      cursor_width=dp(2),
                                      readonly=False,  # 편집 가능(복사/붙여넣기 편리)
                                      multiline=True, size_hint=(1,1))
        # 좌측 정렬 느낌을 위해 padding 유지
        self.result_input.padding = (dp(6), dp(6))
        self.result_box.add_widget(self.result_input)
        wrapper.add_widget(self.result_box)

        # 하단 버전 태그
        version = Label(text="버전 5", font_name=FONT, color=(0.4,0.4,0.4,1),
                        halign="right", valign="middle", size_hint=(1, None), height=dp(20))
        version.bind(size=lambda *_: setattr(version, "text_size", version.size))
        wrapper.add_widget(version)

        root.add_widget(wrapper)

        return root

    # helpers
    def _resbg_follow(self, *_):
        self._res_bg.pos, self._res_bg.size = self.result_box.pos, self.result_box.size

    def _auto_move_back(self, instance, value):
        if len(value) >= 3:
            self.in_code_back.focus = True

    def _copy(self, src, dst):
        dst.text = src.text

    # 계산
    def calculate(self, *_):
        try:
            slab = _num_or_none(self.in_total.text)
            p1, p2, p3 = map(_num_or_none, [self.in_p1.text, self.in_p2.text, self.in_p3.text])

            if slab is None or slab <= 0:
                # TextInput은 이미지 아이콘을 못 그리므로 텍스트 경고로 대체
                self.result_input.text = "⚠️ 실제 Slab 길이를 올바르게 입력하세요."
                return

            guides = [v for v in (p1, p2, p3) if v is not None and v > 0]
            if len(guides) < 2:
                self.result_input.text = "⚠️ 최소 2개 이상의 지시길이를 입력하세요."
                return

            loss = 15.0
            total_loss = loss * (len(guides) - 1)
            remain = slab - (sum(guides) + total_loss)
            add_each = remain / len(guides)
            real = [g + add_each for g in guides]

            mm = " mm"
            cf = (self.in_code_front.text or "").strip()
            cb = (self.in_code_back.text or "").strip()
            lines = []
            if cf and cb:
                lines.append(f"▶ 강번: {self.prefix}{cf}-0{cb}\n")
            lines.append(f"▶ Slab 실길이: {slab:,.1f}{mm}")
            for i, g in enumerate(guides, 1):
                lines.append(f"▶ {i}번 지시길이: {g:,.1f}{mm}")
            lines.append(f"▶ 절단 손실: {loss}{mm} × {len(guides)-1} = {total_loss}{mm}")
            lines.append(f"▶ 전체 여유길이: {remain:,.1f}{mm} → 각 +{add_each:,.1f}{mm}\n")

            # 절단 후 예상 길이
            lines.append("▶ 절단 후 예상 길이:")
            for i, r in enumerate(real, 1):
                lines.append(f"   {i}번: {r:,.1f}{mm}")

            # 시각화 (절단 마킹 포인트) — 절단센터 위치는 출력하지 않음
            visual = "H"
            for i, r in enumerate(real, 1):
                mark = round_half_up(r + loss/2)
                visual += f"-{i}번({mark})-"
            visual += "T"
            lines.append("\n▶ 시각화 (절단 마킹 포인트):")
            lines.append(visual)

            self.result_input.text = "\n".join(lines)

        except Exception as e:
            self.result_input.text = f"⚠️ 오류: {e}"

    # 설정
    def open_settings(self, *_):
        mv = ModalView(size_hint=(.9, .4))
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(8))
        box.add_widget(Label(text="설정은 추후 추가 예정입니다.", font_name=FONT,
                             color=(0, 0, 0, 1)))
        close = RoundedButton(text="닫기", bg_color=[0.8, 0.8, 0.8, 1], fg_color=[0, 0, 0, 1],
                              size_hint=(1, None), height=dp(40))
        close.bind(on_release=lambda *_: mv.dismiss())
        box.add_widget(close)
        mv.add_widget(box)
        mv.open()

if __name__ == "__main__":
    SlabApp().run()
