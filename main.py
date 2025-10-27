# -*- coding: utf-8 -*-
import os, json, math, traceback
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

SETTINGS_FILE = "settings.json"


def round_half_up(n):
    return int(n + 0.5)


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "prefix": "SG94",
        "round_result": False,
        "result_font_size": 11,
        "hide_mm": False,
        "loss": 15,
    }


def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class SlabLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.settings = load_settings()
        self.prefix = self.settings.get("prefix", "SG94")
        self.round_result = self.settings.get("round_result", False)
        self.hide_mm = self.settings.get("hide_mm", False)
        self.loss_per_cut = self.settings.get("loss", 15)

        self.add_widget(Label(text="후판 절단 계산기", font_size="22sp", size_hint_y=None, height=60))

        self.input_total = TextInput(hint_text="Slab 실길이", multiline=False, size_hint_y=None, height=50)
        self.add_widget(self.input_total)

        self.pieces = []
        for i in range(3):
            ti = TextInput(hint_text=f"{i+1}번 지시길이", multiline=False, size_hint_y=None, height=50)
            self.add_widget(ti)
            self.pieces.append(ti)

        self.btn = Button(text="계산하기", background_color=(0, 0.6, 0, 1), size_hint_y=None, height=60)
        self.btn.bind(on_press=self.calculate)
        self.add_widget(self.btn)

        self.result_box = ScrollView(size_hint=(1, 1))
        self.result_label = Label(text="", font_size="16sp", size_hint_y=None, halign="left", valign="top")
        self.result_label.bind(texture_size=self._update_height)
        self.result_box.add_widget(self.result_label)
        self.add_widget(self.result_box)

    def _update_height(self, *_):
        self.result_label.height = self.result_label.texture_size[1]
        self.result_label.text_size = (self.result_box.width - 20, None)

    def calculate(self, instance):
        try:
            slab_len = float(self.input_total.text)
            guides = [float(t.text) for t in self.pieces if t.text.strip()]
            if len(guides) < 2:
                self.result_label.text = "⚠️ 최소 2개 이상의 지시길이를 입력하세요."
                return

            cut_loss = self.loss_per_cut
            num = len(guides) - 1
            total_loss = cut_loss * num
            remain = slab_len - (sum(guides) + total_loss)
            add_each = remain / len(guides)
            real_lengths = [g + add_each for g in guides]

            result = f"▶ Slab 실길이: {slab_len}\n"
            result += f"▶ 절단 손실: {cut_loss} × {num} = {total_loss}\n"
            result += f"▶ 전체 여유길이: {remain:.1f} → 각 +{add_each:.1f}\n\n"

            result += "▶ 실제 절단 길이:\n"
            for i, r in enumerate(real_lengths):
                val = round_half_up(r) if self.round_result else round(r, 1)
                result += f"{i+1}번: {val}\n"

            self.result_label.text = result
        except Exception as e:
            self.result_label.text = f"⚠️ 오류: {e}"


class SlabApp(App):
    def build(self):
        return SlabLayout()


if __name__ == "__main__":
    try:
        SlabApp().run()
    except Exception:
        path = "/storage/emulated/0/startup_error.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        raise
