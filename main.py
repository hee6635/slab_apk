# -*- coding: utf-8 -*-
import os, json, traceback
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
        text: "후판 절단 계산기 (디버그)"
        size_hint_y: None
        height: dp(36)
    TextInput:
        id: total_entry
        hint_text: "실제 Slab 길이 입력"
        multiline: False
        input_filter: 'float'
    Button:
        text: "계산하기"
        size_hint_y: None
        height: dp(48)
        on_release: app.calculate(total_entry.text)
    ScrollView:
        do_scroll_x: False
        Label:
            id: result_label
            text: app.result_text
            size_hint_y: None
            height: self.texture_size[1] + dp(16)
            text_size: self.width, None
"""

def safe_write(path, text):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception as e:
        Logger.warning(f"WRITE_FAIL: {e}")

class SlabApp(App):
    prefix = StringProperty("SG94")
    round_result = BooleanProperty(False)
    result_font_size = NumericProperty(16)
    hide_mm = BooleanProperty(False)
    loss_per_cut = NumericProperty(15.0)
    result_text = StringProperty("")

    def build(self):
        try:
            self._settings_file = os.path.join(self.user_data_dir, "settings.json")
            self._load_settings()
            ui = Builder.load_string(KV)
            safe_write(os.path.join(self.user_data_dir, "startup_ok.txt"), "ok")
            return ui
        except Exception:
            tb = traceback.format_exc()
            Logger.exception("STARTUP_CRASH")
            safe_write(os.path.join(self.user_data_dir, "startup_error.txt"), tb)
            from kivy.uix.label import Label
            return Label(text="시작 오류 발생\nstartup_error.txt 확인")

    def _load_settings(self):
        try:
            if os.path.exists(self._settings_file):
                with open(self._settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.prefix = data.get("prefix", "SG94")
                self.round_result = data.get("round_result", False)
                self.result_font_size = int(data.get("result_font_size", 16))
                self.hide_mm = data.get("hide_mm", False)
                self.loss_per_cut = float(data.get("loss", 15))
        except Exception:
            Logger.warning("LOAD_SETTINGS_FAIL")

    def calculate(self, slab_len_text):
        try:
            slab_len = float(slab_len_text)
        except Exception:
            self.result_text = "⚠️ Slab 실길이를 올바르게 입력하세요."
            return
        self.result_text = f"입력값 확인: {slab_len:,.1f}{'' if self.hide_mm else ' mm'}"

if __name__ == "__main__":
    SlabApp().run()
