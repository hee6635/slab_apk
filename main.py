# -*- coding: utf-8 -*-
import os, json
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.core.window import Window
from kivy.logger import Logger

KV = r"""
#:import dp kivy.metrics.dp

BoxLayout:
    orientation: 'vertical'
    padding: dp(12)
    spacing: dp(10)

    Label:
        text: "후판 절단 계산기"
        font_size: app.font_title
        font_name: app.font_name
        size_hint_y: None
        height: dp(36)

    TextInput:
        id: total_entry
        hint_text: "실제 Slab 길이 입력"
        multiline: False
        input_filter: 'float'
        font_size: app.font_entry
        font_name: app.font_name

    Button:
        text: "계산하기"
        size_hint_y: None
        height: dp(48)
        font_name: app.font_name
        on_release: app.calculate(total_entry.text)

    ScrollView:
        do_scroll_x: False
        Label:
            id: result_label
            text: app.result_text
            size_hint_y: None
            height: self.texture_size[1] + dp(16)
            text_size: self.width, None
            font_size: app.font_result
            font_name: app.font_name
"""

def round_half_up(n):
    return int(float(n) + 0.5)

class SlabApp(App):
    prefix = StringProperty("SG94")
    round_result = BooleanProperty(False)
    result_font_size = NumericProperty(16)
    hide_mm = BooleanProperty(False)
    loss_per_cut = NumericProperty(15.0)

    font_title = NumericProperty(20)
    font_entry = NumericProperty(18)
    font_result = NumericProperty(16)
    font_name = StringProperty("NotoSansKR.ttf")  # 번들한 한글폰트 파일명

    result_text = StringProperty("")

    _settings_file = None

    def build(self):
        try:
            if min(Window.size) < 720:
                self.font_title = 18
                self.font_entry = 16
                self.font_result = 16
        except Exception:
            pass

        self._settings_file = os.path.join(self.user_data_dir, "settings.json")
        self._load_settings()
        self.font_result = int(self.result_font_size or 16)
        return Builder.load_string(KV)

    def _load_settings(self):
        if os.path.exists(self._settings_file):
            try:
                with open(self._settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.prefix = data.get("prefix", "SG94")
                self.round_result = data.get("round_result", False)
                self.result_font_size = int(data.get("result_font_size", 16))
                self.hide_mm = data.get("hide_mm", False)
                self.loss_per_cut = float(data.get("loss", 15))
            except Exception as e:
                Logger.warning(f"LOAD_SETTINGS_FAIL: {e}")
        else:
            self.save_settings()

    def save_settings(self):
        data = dict(
            prefix=self.prefix,
            round_result=self.round_result,
            result_font_size=int(self.result_font_size or 16),
            hide_mm=self.hide_mm,
            loss=float(self.loss_per_cut or 15),
        )
        os.makedirs(self.user_data_dir, exist_ok=True)
        with open(self._settings_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_settings_kv(self, prefix, round_result, font_size_text, hide_mm, loss_text):
        try:
            self.prefix = (prefix or "SG94").strip()
            self.round_result = bool(round_result)
            self.result_font_size = int(font_size_text or 16)
            self.hide_mm = bool(hide_mm)
            self.loss_per_cut = float(loss_text or 15)
        except Exception:
            self.result_font_size = 16
            self.loss_per_cut = 15.0
        self.font_result = self.result_font_size
        self.save_settings()

    def open_settings(self):
        from kivy.factory import Factory
        Factory.SettingsPopup().open()

    def calculate(self, slab_len_text):
        try:
            slab_len = float((slab_len_text or "").strip())
        except Exception:
            self.result_text = "⚠️ Slab 실길이를 올바르게 입력하세요."
            return

        result_lines = [f"▶ Slab 실길이: {slab_len:,.1f}{'' if self.hide_mm else ' mm'}"]
        # 간단화: 지시길이 기능은 뺀 버전
        self.result_text = "\n".join(result_lines)

if __name__ == "__main__":
    SlabApp().run()
