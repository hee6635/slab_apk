# -*- coding: utf-8 -*-
import os, json
from kivy.app import App
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.core.window import Window

# ===== 1) 폰트 등록 (파일이 있으면 자동 적용) =====
FONT_NAME = ""
_here = os.path.dirname(__file__)
_nanum = os.path.join(_here, "NanumGothic.ttf")
if os.path.exists(_nanum):
    LabelBase.register(name="NanumGothic", fn_regular=_nanum)
    FONT_NAME = "NanumGothic"

KV = r"""
#:import dp kivy.metrics.dp

<Slim@Label>:
    size_hint_y: None
    height: self.texture_size[1] + dp(6)
    text_size: self.width, None
    font_name: app.font_name if app.font_name else None

<MyEntry@TextInput>:
    multiline: False
    write_tab: False
    input_filter: 'float'
    halign: 'center'
    size_hint_y: None
    height: dp(40)
    font_size: dp(16)
    font_name: app.font_name if app.font_name else None

<Root@BoxLayout>:
    orientation: 'vertical'
    padding: dp(12)
    spacing: dp(10)

    # 타이틀 바
    BoxLayout:
        size_hint_y: None
        height: dp(44)
        Label:
            text: "후판 절단 계산기"
            bold: True
            font_size: dp(20)
            font_name: app.font_name if app.font_name else None

    # Slab 총 길이
    BoxLayout:
        size_hint_y: None
        height: dp(56)
        spacing: dp(8)
        Slim:
            text: "실제 Slab 길이"
        MyEntry:
            id: total_len
            hint_text: "예) 12000"

    # 지시길이 1~3
    GridLayout:
        cols: 2
        size_hint_y: None
        height: self.minimum_height
        row_default_height: dp(44)
        row_force_default: True
        spacing: dp(8)

        Slim: text: "1번 지시길이"
        MyEntry: id: p1; hint_text: "예) 4000"
        Slim: text: "2번 지시길이"
        MyEntry: id: p2; hint_text: "예) 4000"
        Slim: text: "3번 지시길이"
        MyEntry: id: p3; hint_text: "예) 4000"

    # 계산 버튼
    Button:
        text: "계산하기"
        size_hint_y: None
        height: dp(56)
        font_size: dp(18)
        font_name: app.font_name if app.font_name else None
        on_release: app.calculate(total_len.text, [p1.text, p2.text, p3.text])

    # 결과 영역
    BoxLayout:
        orientation: 'vertical'
        size_hint_y: 1
        Slim:
            text: "결과"
            font_size: dp(16)
        ScrollView:
            do_scroll_x: False
            bar_width: dp(6)
            GridLayout:
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                Label:
                    id: result
                    text: app.result_text
                    size_hint_y: None
                    height: self.texture_size[1] + dp(16)
                    halign: 'left'
                    valign: 'top'
                    text_size: self.width, None
                    font_size: dp(app.result_font_size)
                    font_name: app.font_name if app.font_name else None
"""

def round_half_up(n):
    return int(float(n) + 0.5)

def _parse_float(s: str):
    """빈문자/잘못된 값은 None 반환 (앱이 절대 죽지 않게)"""
    try:
        s = (s or "").strip()
        if not s:
            return None
        return float(s)
    except Exception:
        return None

class SlabApp(App):
    # 설정값(간단 버전)
    result_font_size = NumericProperty(16)
    hide_mm = BooleanProperty(False)
    round_result = BooleanProperty(False)
    loss_per_cut = NumericProperty(15.0)
    prefix = StringProperty("SG94")

    # 폰트 경로
    font_name = StringProperty(FONT_NAME)

    # 출력
    result_text = StringProperty("")

    def build(self):
        # 세로 고정 느낌(가로여도 UI가 세로로 보이도록)
        try:
            if Window.width > Window.height:
                Window.size = (Window.height*0.6, Window.height)  # 미세 보정
        except Exception:
            pass
        return Builder.load_string(KV)

    def calculate(self, slab_len_text, pieces_text_list):
        slab = _parse_float(slab_len_text)
        if slab is None or slab <= 0:
            self.result_text = "⚠️ Slab 실길이를 올바르게 입력하세요."
            return

        guides = []
        for s in pieces_text_list:
            v = _parse_float(s)
            if v is not None and v > 0:
                guides.append(v)

        if len(guides) < 2:
            self.result_text = "⚠️ 최소 2개 이상의 지시길이를 입력하세요."
            return

        cut = float(self.loss_per_cut)
        num = len(guides) - 1
        total_loss = cut * num
        remain = slab - (sum(guides) + total_loss)
        add_each = remain / len(guides)

        real = [g + add_each for g in guides]

        # 센터 계산
        centers = []
        acc = 0
        for l in real[:-1]:
            acc += l + (cut / 2)
            centers.append(acc)
            acc += (cut / 2)

        mm = "" if self.hide_mm else " mm"

        header = []
        header.append(f"▶ Slab 실길이: {slab:,.1f}{mm}")
        for i, g in enumerate(guides, 1):
            header.append(f"▶ {i}번 지시길이: {g:,.1f}{mm}")
        header.append(f"▶ 절단 손실: {cut}{mm} × {num} = {total_loss}{mm}")
        header.append(f"▶ 전체 여유길이: {remain:,.1f}{mm} → 각 +{add_each:,.1f}{mm}\n")

        if self.round_result:
            real_disp = [round_half_up(r) for r in real]
            centers_disp = [round_half_up(c) for c in centers]
        else:
            real_disp = [round(r, 1) for r in real]
            centers_disp = [round(c, 1) for c in centers]

        body = ["▶ 각 Slab별 실제 절단 길이:"]
        for i, r in enumerate(real_disp, 1):
            if isinstance(r, int):
                body.append(f"   {i}번: {r:,}{mm}")
            else:
                body.append(f"   {i}번: {r:,.1f}{mm}")

        body.append("")
        body.append(f"▶ 절단센터 위치:{'' if self.hide_mm else '(mm)'} {centers_disp}\n")

        visual = "H"
        for i, r in enumerate(real_disp, 1):
            # 마킹은 정수 표기
            rv = float(r) if not isinstance(r, (int, float)) else r
            mark = round_half_up(rv + cut/2)
            visual += f"-{i}번({mark})-"
        visual += "T"
        body.append("▶ 시각화 (실제 마킹 위치):")
        body.append(visual)

        self.result_text = "\n".join(header + body)

if __name__ == "__main__":
    SlabApp().run()
