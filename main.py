# -*- coding: utf-8 -*-
import json, os, traceback, sys
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.gridlayout import GridLayout

Window.clearcolor = (0.95, 0.95, 0.95, 1)


class SlabApp(App):
    def build(self):
        layout = BoxLayout(orientation="vertical", padding=10, spacing=5)

        # 상단 제목
        title = Label(
            text="후판 절단 계산기",
            font_name="NanumGothic",
            font_size="24sp",
            color=(0, 0, 0, 1),
            size_hint=(1, 0.12)
        )
        layout.add_widget(title)

        # 강번 입력 영역
        box_code = BoxLayout(size_hint=(1, 0.1), spacing=5)
        box_code.add_widget(Label(text="강번 입력:", font_name="NanumGothic", color=(0, 0, 0, 1), size_hint_x=0.3))
        box_code.add_widget(Label(text="SG94", font_name="NanumGothic", color=(0, 0, 0, 1), size_hint_x=0.2))
        self.input_front = TextInput(size_hint_x=0.2, multiline=False, input_filter="int")
        box_code.add_widget(self.input_front)
        box_code.add_widget(Label(text="-0", font_name="NanumGothic", color=(0, 0, 0, 1), size_hint_x=0.1))
        self.input_back = TextInput(size_hint_x=0.2, multiline=False, input_filter="int")
        box_code.add_widget(self.input_back)
        layout.add_widget(box_code)

        # 설정 버튼 (진한 회색)
        btn_setting = Button(
            text="설정",
            font_name="NanumGothic",
            size_hint=(None, None),
            size=(70, 40),
            pos_hint={"right": 1, "top": 1},
            background_color=(0.33, 0.33, 0.33, 1),
            color=(1, 1, 1, 1)
        )
        layout.add_widget(btn_setting)

        # 실제 Slab 길이 입력
        box_total = BoxLayout(size_hint=(1, 0.1), spacing=5)
        box_total.add_widget(Label(text="실제 Slab 길이:", font_name="NanumGothic", color=(0, 0, 0, 1), size_hint_x=0.4))
        self.input_total = TextInput(multiline=False, input_filter="float")
        box_total.add_widget(self.input_total)
        layout.add_widget(box_total)

        # 지시길이 입력
        grid = GridLayout(cols=4, size_hint=(1, 0.4), spacing=5)
        self.inputs = []
        for i in range(3):
            grid.add_widget(Label(text=f"{i+1}번 지시길이:", font_name="NanumGothic", color=(0, 0, 0, 1)))
            inp = TextInput(multiline=False, input_filter="float")
            grid.add_widget(inp)
            self.inputs.append(inp)

            # 복사 버튼 크기 축소
            if i == 1:
                b1 = Button(text="← 1번", font_name="NanumGothic", size_hint_x=0.18, background_color=(0.5, 0.5, 0.5, 1), color=(1,1,1,1))
                b1.bind(on_press=lambda x: self.copy_value(0, 1))
                grid.add_widget(b1)
                grid.add_widget(Label())  # 빈칸
            elif i == 2:
                b2 = Button(text="← 1번", font_name="NanumGothic", size_hint_x=0.18, background_color=(0.5, 0.5, 0.5, 1), color=(1,1,1,1))
                b2.bind(on_press=lambda x: self.copy_value(0, 2))
                b3 = Button(text="← 2번", font_name="NanumGothic", size_hint_x=0.18, background_color=(0.5, 0.5, 0.5, 1), color=(1,1,1,1))
                b3.bind(on_press=lambda x: self.copy_value(1, 2))
                grid.add_widget(b2)
                grid.add_widget(b3)
            else:
                grid.add_widget(Label())
                grid.add_widget(Label())
        layout.add_widget(grid)

        # 계산 버튼
        btn_calc = Button(
            text="계산하기",
            font_name="NanumGothic",
            background_color=(0.2, 0.5, 0.2, 1),
            color=(1, 1, 1, 1),
            size_hint=(1, 0.1)
        )
        btn_calc.bind(on_press=self.calculate)
        layout.add_widget(btn_calc)

        # 결과 표시
        self.label_result = Label(
            text="",
            font_name="NanumGothic",
            color=(0, 0, 0, 1),
            halign="left",
            valign="top",
            size_hint=(1, 0.3)
        )
        layout.add_widget(self.label_result)

        # 하단 시그니처 (오른쪽 정렬)
        footer = Label(
            text="made by ft10350",
            font_name="NanumGothic",
            color=(0.4, 0.4, 0.4, 1),
            halign="right",
            size_hint=(1, 0.05)
        )
        layout.add_widget(footer)

        return layout

    def copy_value(self, src, dest):
        self.inputs[dest].text = self.inputs[src].text

    def calculate(self, instance):
        try:
            total = float(self.input_total.text)
            guides = [float(i.text) for i in self.inputs if i.text]
            if not guides:
                raise ValueError("지시길이를 입력하세요.")
            result = sum(guides)
            self.label_result.text = f"총합: {result:.1f} / 잔여: {total - result:.1f}"
        except Exception as e:
            self.label_result.text = f"⚠ 오류: {e}"


if __name__ == "__main__":
    SlabApp().run()
