# -*- coding: utf-8 -*-
import os, json, traceback
from kivy.app import App
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.core.window import Window

KV = r"""
#:import dp kivy.metrics.dp

<SlimLabel@Label>:
    size_hint_y: None
    height: self.texture_size[1] + dp(6)
    text_size: self.width, None

<MyTextInput@TextInput>:
    multiline: False
    write_tab: False
    input_filter: 'float'
    halign: 'center'
    font_size: app.font_entry
    font_name: app.font_name if app.font_name else None

<SettingsPopup@ModalView>:
    size_hint: .92, .9
    auto_dismiss: False
    background_color: 0,0,0,.5
    BoxLayout:
        orientation: 'vertical'
        padding: dp(14)
        spacing: dp(10)

        Label:
            text: "환경설정"
            bold: True
            font_size: app.font_title
            font_name: app.font_name if app.font_name else None
            size_hint_y: None
            height: dp(30)

        GridLayout:
            cols: 2
            spacing: dp(8)
            size_hint_y: None
            height: self.minimum_height

            SlimLabel:
                text: "1. 강번 접두어"
                font_name: app.font_name if app.font_name else None
            MyTextInput:
                id: in_prefix
                text: app.prefix or "SG94"

            SlimLabel:
                text: "2. 결과 반올림(정수)"
                font_name: app.font_name if app.font_name else None
            CheckBox:
                id: in_round
                active: app.round_result
                size_hint_x: None
                width: dp(30)

            SlimLabel:
                text: "3. 출력 폰트 크기"
                font_name: app.font_name if app.font_name else None
            MyTextInput:
                id: in_font
                input_filter: 'int'
                text: str(app.result_font_size)

            SlimLabel:
                text: "4. mm 표시 숨기기"
                font_name: app.font_name if app.font_name else None
            CheckBox:
                id: in_hide_mm
                active: app.hide_mm
                size_hint_x: None
                width: dp(30)

            SlimLabel:
                text: "5. 절단 손실(mm)"
                font_name: app.font_name if app.font_name else None
            MyTextInput:
                id: in_loss
                text: str(app.loss_per_cut)

        Widget: size_hint_y: 0.02

        BoxLayout:
            size_hint_y: None
            height: dp(48)
            spacing: dp(8)
            Button:
                text: "저장"
                font_name: app.font_name if app.font_name else None
                on_release: app.save_settings_kv(
                    in_prefix.text, in_round.active, in_font.text, in_hide_mm.active, in_loss.text
                ); root.dismiss()
            Button:
                text: "취소"
                font_name: app.font_name if app.font_name else None
                on_release: root.dismiss()

<RootUI@BoxLayout>:
    orientation: 'vertical'
    padding: dp(12)
    spacing: dp(10)

    # 상단 바
    BoxLayout:
        size_hint_y: None
        height: dp(44)
        Label:
            text: "후판 절단 계산기"
            halign: 'left'; valign: 'middle'; text_size: self.size
            bold: True
            font_size: app.font_title
            font_name: app.font_name if app.font_name else None
        Button:
            size_hint_x: None
            width: dp(90)
            text: "설정"
            font_name: app.font_name if app.font_name else None
            on_release: app.open_settings()

    # 강번
    BoxLayout:
        orientation: 'vertical'
        spacing: dp(4)
        SlimLabel:
            text: "강번 입력 (접두어 %s)" % (app.prefix or "SG94")
            bold: True
            font_name: app.font_name if app.font_name else None
        BoxLayout:
            spacing: dp(6)
            MyTextInput:
                id: code_front
                hint_text: "앞 3자리"
                input_filter: 'int'
                on_text: app._update_generated_code(code_front.text, code_back.text)
            Label:
                text: "-0"
                size_hint_x: None
                width: dp(28)
                halign: 'center'; valign: 'middle'; text_size: self.size
                font_name: app.font_name if app.font_name else None
            MyTextInput:
                id: code_back
                hint_text: "뒤 1~2자리"
                input_filter: 'int'
                on_text: app._update_generated_code(code_front.text, code_back.text)

    # Slab 실길이
    BoxLayout:
        orientation: 'vertical'
        spacing: dp(4)
        SlimLabel:
            text: "실제 Slab 길이"
            bold: True
            font_name: app.font_name if app.font_name else None
        MyTextInput:
            id: total_entry
            hint_text: "예) 12000"
            input_filter: 'float'

    # 지시길이 1~3 + 복사 버튼
    GridLayout:
        cols: 1
        spacing: dp(6)

        BoxLayout:
            orientation: 'vertical'
            SlimLabel:
                text: "1번 지시길이"; bold: True
                font_name: app.font_name if app.font_name else None
            MyTextInput: id: p1; hint_text: "예) 4000"
        BoxLayout:
            orientation: 'vertical'
            SlimLabel:
                text: "2번 지시길이"; bold: True
                font_name: app.font_name if app.font_name else None
            MyTextInput: id: p2; hint_text: "예) 4000"
            BoxLayout:
                size_hint_y: None; height: dp(42); spacing: dp(8)
                Button:
                    text: "← 1번 복사"
                    font_name: app.font_name if app.font_name else None
                    on_release: p2.text = p1.text
        BoxLayout:
            orientation: 'vertical'
            SlimLabel:
                text: "3번 지시길이"; bold: True
                font_name: app.font_name if app.font_name else None
            MyTextInput: id: p3; hint_text: "예) 4000"
            BoxLayout:
                size_hint_y: None; height: dp(42); spacing: dp(8)
                Button:
                    text: "← 1번 복사"
                    font_name: app.font_name if app.font_name else None
                    on_release: p3.text = p1.text
                Button:
                    text: "← 2번 복사"
                    font_name: app.font_name if app.font_name else None
                    on_release: p3.text = p2.text

    # 계산 버튼
    Button:
        size_hint_y: None
        height: dp(56)
        text: "계산하기"
        font_name: app.font_name if app.font_name else None
        on_release: app.calculate(total_entry.text, [p1.text, p2.text, p3.text], code_front.text, code_back.text)

    # 결과 영역(스크롤)
    BoxLayout:
        orientation: 'vertical'
        size_hint_y: 1
        Label:
            text: "결과"
            size_hint_y: None
            height: dp(24)
            halign: 'left'; valign: 'middle'; text_size: self.size
            font_name: app.font_name if app.font_name else None
        ScrollView:
            do_scroll_x: False
            bar_width: dp(6)
            GridLayout:
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                Label:
                    id: result_label
                    text: app.result_text
                    size_hint_y: None
                    height: self.texture_size[1] + dp(16)
                    halign: 'left'; valign: 'top'
                    text_size: self.width, None
                    font_size: app.font_result
                    font_name: app.font_name if app.font_name else None
"""

def round_half_up(n): return int(float(n) + 0.5)

class SlabApp(App):
    prefix = StringProperty("SG94")
    round_result = BooleanProperty(False)
    result_font_size = NumericProperty(16)
    hide_mm = BooleanProperty(False)
    loss_per_cut = NumericProperty(15.0)

    font_title = NumericProperty(18)
    font_entry = NumericProperty(16)
    font_result = NumericProperty(16)
    font_name = StringProperty("")

    result_text = StringProperty("")
    _settings_file = None

    def build(self):
        try:
            if min(Window.size) < 720:
                self.font_title = 18; self.font_entry = 16; self.font_result = 16
            else:
                self.font_title = 20; self.font_entry = 18; self.font_result = 18
        except Exception:
            pass

        for cand in ("NanumGothic.ttf", "./NanumGothic.ttf"):
            if os.path.exists(cand):
                self.font_name = cand
                break

        self._settings_file = os.path.join(self.user_data_dir, "settings.json")
        self._load_settings()
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
                self.font_result = self.result_font_size
            except Exception:
                pass
        else:
            self.save_settings()

    def save_settings(self):
        data = dict(
            prefix=self.prefix,
            round_result=bool(self.round_result),
            result_font_size=int(self.result_font_size or 16),
            hide_mm=bool(self.hide_mm),
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

    def _update_generated_code(self, front, back):
        pass

    def calculate(self, slab_len_text, pieces_text_list, code_front, code_back):
        try:
            slab_len = float((slab_len_text or "").strip())
        except Exception:
            self.result_text = "⚠️ Slab 실길이를 올바르게 입력하세요."
            return

        guides = []
        for t in pieces_text_list:
            s = (t or "").strip()
            if s:
                try:
                    guides.append(float(s))
                except Exception:
                    pass

        if len(guides) < 2:
            self.result_text = "⚠️ 최소 2개 이상의 지시길이를 입력하세요."
            return

        cut_loss = float(self.loss_per_cut)
        num = len(guides) - 1
        total_loss = cut_loss * num
        remain = slab_len - (sum(guides) + total_loss)
        add_each = remain / len(guides)
        real_lengths = [g + add_each for g in guides]

        centers = []
        accum = 0
        for l in real_lengths[:-1]:
            accum += l + (cut_loss / 2)
            centers.append(accum)
            accum += (cut_loss / 2)

        front = (code_front or "").strip()
        back = (code_back or "").strip()
        code_result = f"▶ 강번: {self.prefix}{front}-0{back}\n\n" if (front and back) else ""
        mm = "" if self.hide_mm else " mm"

        header = []
        header.append(f"▶ Slab 실길이: {slab_len:,.1f}{mm}")
        for i, g in enumerate(guides):
            header.append(f"▶ {i+1}번 지시길이: {g:,.1f}{mm}")
        header.append(f"▶ 절단 손실: {cut_loss}{mm} × {num} = {total_loss}{mm}")
        header.append(f"▶ 전체 여유길이: {remain:,.1f}{mm} → 각 +{add_each:,.1f}{mm}\n")

        if self.round_result:
            real_lengths_display = [round_half_up(r) for r in real_lengths]
            centers_display = [round_half_up(c) for c in centers]
        else:
            real_lengths_display = [round(r, 1) for r in real_lengths]
            centers_display = [round(c, 1) for c in centers]

        body = ["▶ 각 Slab별 실제 절단 길이:"]
        for i, r in enumerate(real_lengths_display):
            if isinstance(r, int):
                body.append(f"   {i+1}번: {r:,}{mm}")
            else:
                body.append(f"   {i+1}번: {r:,.1f}{mm}")

        body.append("")
        body.append(f"▶ 절단센터 위치:{'' if self.hide_mm else '(mm)'} {centers_display}\n")

        visual = "H"
        for i, l in enumerate(real_lengths_display):
            mark_val = round_half_up((l if isinstance(l, (int, float)) else float(l)) + (cut_loss / 2))
            visual += f"-{i+1}번({mark_val})-"
        visual += "T"
        body.append("▶ 시각화 (실제 마킹 위치):")
        body.append(visual)

        self.result_text = code_result + "\n".join(header + body)


# --------- 여기부터: 크래시 로그를 /storage/emulated/0/1/startup_error.txt 로 저장 ---------
def _save_crash_to_fixed_path(exc_text: str):
    target_dir = "/storage/emulated/0/1"
    target_path = os.path.join(target_dir, "startup_error.txt")
    try:
        os.makedirs(target_dir, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(exc_text)
    except Exception:
        # 최후 보루: 앱 전용 폴더에도 한 번 더 남겨둔다(보이지 않으면 무시해도 됨)
        try:
            app = App.get_running_app()
            if app and hasattr(app, "user_data_dir"):
                upath = os.path.join(app.user_data_dir, "startup_error.txt")
                os.makedirs(os.path.dirname(upath), exist_ok=True)
                with open(upath, "w", encoding="utf-8") as f:
                    f.write(exc_text)
        except Exception:
            pass
# -------------------------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        SlabApp().run()
    except Exception:
        msg = traceback.format_exc()
        _save_crash_to_fixed_path(msg)
        raise
