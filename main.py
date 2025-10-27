# -*- coding: utf-8 -*-
import os, sys
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window

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

class SlabApp(App):
    def build(self):
        Window.clearcolor = (0, 0, 0, 1)  # 검정 배경(가독)
        root = BoxLayout(orientation='vertical', padding=12, spacing=10)

        # 타이틀
        root.add_widget(Label(text="후판 절단 계산기", font_size='20sp',
                              color=(1,1,1,1), size_hint=(1, 0.12)))

        # Slab 총 길이
        row_total = BoxLayout(orientation='horizontal', size_hint=(1, 0.12), spacing=8)
        row_total.add_widget(Label(text="실제 Slab 길이", color=(1,1,1,1), size_hint=(0.5, 1)))
        self.in_total = TextInput(hint_text="예) 12000", multiline=False,
                                  input_filter='float', size_hint=(0.5, 1))
        row_total.add_widget(self.in_total)
        root.add_widget(row_total)

        # 지시길이 1~3
        grid = GridLayout(cols=2, size_hint=(1, 0.36), row_default_height=48, row_force_default=True, spacing=8)
        grid.add_widget(Label(text="1번 지시길이", color=(1,1,1,1)))
        self.in_p1 = TextInput(hint_text="예) 4000", multiline=False, input_filter='float')
        grid.add_widget(self.in_p1)

        grid.add_widget(Label(text="2번 지시길이", color=(1,1,1,1)))
        self.in_p2 = TextInput(hint_text="예) 4000", multiline=False, input_filter='float')
        grid.add_widget(self.in_p2)

        grid.add_widget(Label(text="3번 지시길이", color=(1,1,1,1)))
        self.in_p3 = TextInput(hint_text="예) 4000", multiline=False, input_filter='float')
        grid.add_widget(self.in_p3)
        root.add_widget(grid)

        # 복사 버튼 줄(선택)
        row_copy = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=8)
        btn_copy_2 = Button(text="2번 ← 1번", on_press=lambda *_: self._copy(self.in_p1, self.in_p2))
        btn_copy_3a = Button(text="3번 ← 1번", on_press=lambda *_: self._copy(self.in_p1, self.in_p3))
        btn_copy_3b = Button(text="3번 ← 2번", on_press=lambda *_: self._copy(self.in_p2, self.in_p3))
        row_copy.add_widget(btn_copy_2); row_copy.add_widget(btn_copy_3a); row_copy.add_widget(btn_copy_3b)
        root.add_widget(row_copy)

        # 절단 손실
        row_loss = BoxLayout(orientation='horizontal', size_hint=(1, 0.12), spacing=8)
        row_loss.add_widget(Label(text="절단 손실(mm)", color=(1,1,1,1), size_hint=(0.5, 1)))
        self.in_loss = TextInput(text="15", multiline=False, input_filter='float', size_hint=(0.5, 1))
        row_loss.add_widget(self.in_loss)
        root.add_widget(row_loss)

        # 계산 버튼
        btn_calc = Button(text="계산하기", background_normal='', background_color=(0.0, 0.35, 0.1, 1),
                          size_hint=(1, 0.12))
        btn_calc.bind(on_press=self.calculate)
        root.add_widget(btn_calc)

        # 결과 영역 (스크롤)
        root.add_widget(Label(text="결과", color=(1,1,1,1), size_hint=(1, 0.08)))
        self.result_label = Label(text="", color=(1,1,1,1), size_hint=(1, None), halign='left', valign='top')
        self.result_label.bind(texture_size=lambda *_: self._resize_result())
        sv = ScrollView(size_hint=(1, 0.4))
        sv.add_widget(self.result_label)
        root.add_widget(sv)

        return root

    def _copy(self, src, dst):
        dst.text = src.text

    def _resize_result(self):
        # 텍스트 높이에 맞춰 자동 확장
        self.result_label.text_size = (self.result_label.width, None)
        self.result_label.height = self.result_label.texture_size[1] + 12

    def calculate(self, *_):
        # 안전 파싱 (크래시 방지)
        slab = _num_or_none(self.in_total.text)
        p1 = _num_or_none(self.in_p1.text)
        p2 = _num_or_none(self.in_p2.text)
        p3 = _num_or_none(self.in_p3.text)
        loss = _num_or_none(self.in_loss.text)

        if slab is None or slab <= 0:
            self.result_label.text = "⚠️ Slab 실길이를 올바르게 입력하세요."
            return

        guides = [v for v in (p1, p2, p3) if v is not None and v > 0]
        if len(guides) < 2:
            self.result_label.text = "⚠️ 최소 2개 이상의 지시길이를 입력하세요."
            return

        if loss is None or loss < 0:
            loss = 15.0  # 기본값

        # 계산
        num = len(guides) - 1
        total_loss = loss * num
        remain = slab - (sum(guides) + total_loss)
        add_each = remain / len(guides)
        real = [g + add_each for g in guides]

        # 센터
        centers = []
        acc = 0.0
        for l in real[:-1]:
            acc += l + (loss/2)
            centers.append(acc)
            acc += (loss/2)

        # 출력
        mm = " mm"
        lines = []
        lines.append(f"▶ Slab 실길이: {slab:,.1f}{mm}")
        for i, g in enumerate(guides, 1):
            lines.append(f"▶ {i}번 지시길이: {g:,.1f}{mm}")
        lines.append(f"▶ 절단 손실: {loss}{mm} × {num} = {total_loss}{mm}")
        lines.append(f"▶ 전체 여유길이: {remain:,.1f}{mm} → 각 +{add_each:,.1f}{mm}\n")

        lines.append("▶ 각 Slab별 실제 절단 길이:")
        for i, r in enumerate(real, 1):
            lines.append(f"   {i}번: {r:,.1f}{mm}")

        lines.append("")
        lines.append(f"▶ 절단센터 위치(mm): { [round_half_up(c) for c in centers] }\n")

        visual = "H"
        for i, r in enumerate(real, 1):
            mark = round_half_up(r + loss/2)
            visual += f"-{i}번({mark})-"
        visual += "T"
        lines.append("▶ 시각화 (실제 마킹 위치):")
        lines.append(visual)

        self.result_label.text = "\n".join(lines)

if __name__ == "__main__":
    SlabApp().run()
