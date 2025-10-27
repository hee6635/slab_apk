# -*- coding: utf-8 -*-
import sys, os, traceback
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.window import Window


# ===================== 전역 크래시 로그 후크 =====================
def _install_global_crash_hook(user_data_dir: str):
    """앱이 죽더라도 로그를 남기는 전역 후크"""
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

        # 앱 전용 폴더
        if user_data_dir:
            _write(os.path.join(user_data_dir, "last_crash.txt"), txt)

        # .kivy 폴더
        _write("/storage/emulated/0/.kivy/last_crash.txt", txt)

        # 원래 예외 출력도 유지
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _hook


# ===================== 본체 UI =====================
class SlabApp(App):
    def build(self):
        # 전역 예외 후크 설치
        _install_global_crash_hook(self.user_data_dir)

        Window.clearcolor = (0, 0, 0, 1)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.label_title = Label(
            text="후판 절단 계산기",
            font_name="NanumGothic",
            font_size='20sp',
            color=(1, 1, 1, 1),
            size_hint=(1, 0.1)
        )
        layout.add_widget(self.label_title)

        # Slab 총 길이 입력
        self.input_total = TextInput(
            hint_text="Slab 총 길이 입력",
            font_name="NanumGothic",
            multiline=False,
            input_filter='float',
            size_hint=(1, 0.1)
        )
        layout.add_widget(self.input_total)

        # 결과 표시창
        self.label_result = Label(
            text="",
            font_name="NanumGothic",
            color=(1, 1, 1, 1),
            size_hint=(1, 0.6)
        )
        layout.add_widget(self.label_result)

        # 계산 버튼
        self.btn_calc = Button(
            text="계산하기",
            font_name="NanumGothic",
            background_color=(0, 0.3, 0, 1),
            size_hint=(1, 0.1)
        )
        self.btn_calc.bind(on_press=self.calculate)
        layout.add_widget(self.btn_calc)

        return layout

    def calculate(self, instance):
        try:
            val = self.input_total.text.strip()
            if not val:
                raise ValueError("길이를 입력해주세요.")
            total = float(val)
            self.label_result.text = f"계산 결과: {total * 2:.1f} mm"
        except Exception as e:
            self.label_result.text = f"⚠ 오류: {e}"
            raise  # 강제 종료 시 로그에 남기기 위함


# ===================== 실행부 =====================
if __name__ == "__main__":
    SlabApp().run()
