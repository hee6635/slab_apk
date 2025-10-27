# -*- coding: utf-8 -*-
import sys, os, traceback

# ---------- 아주 이른 전역 후크 (임포트/KV 파싱 단계도 캡쳐) ----------
def _install_early_hook():
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
        # 1) 숨김 폴더
        _write("/storage/emulated/0/.kivy/early_crash.txt", txt)
        # 2) 혹시 앱 데이터 폴더를 나중에 알게 되면 거기도 남길 수 있도록 유지
        try:
            from kivy.app import App
            ud = getattr(App.get_running_app(), "user_data_dir", None)
            if ud:
                _write(os.path.join(ud, "early_crash.txt"), txt)
        except Exception:
            pass
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _hook

_install_early_hook()
# --------------------------------------------------------------------

# 여기서부터 Kivy 로드
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.core.window import Window

KV = r"""
#:import dp kivy.metrics.dp

<Slim@Label>:
    size_hint_y: None
    height: self.texture_size[1] + dp(6)
    text_size: self.width, None
    color: 1,1,1,1

<MyEntry@TextInput>:
    multiline: False
    write_tab: False
    input_filter: 'float'
    halign: 'center'
    background_color: (1,1,1,1)
    foreground_color: (0,0,0,1)
    size_hint_y: None
    height: dp(44)
    font_size: dp(16)

<Root@BoxLayout>:
    orientation: 'vertical'
    padding: dp(14)
    spacing: dp(10)

    BoxLayout:
        size_hint_y: None
        height: dp(52)
        Label:
            text: "후판 절단 계산기"
            bold: True
            font_size: dp(22)
            color: 1,1,1,1

    BoxLayout:
        orientation: 'vertical'
        spacing: dp(6)
        Slim: text: "실제 Slab 길이"
        MyEntry:
            id: total_len
            hint_text: "예) 12000"

    GridLayout:
        cols: 2
        size_hint_y: None
        height: self.minimum_height
        row_default_height: dp(44)
        row_force_default: True
        spacing: dp(10)

        Slim: text: "1번 지시길이"
        MyEntry: id: p1; hint_text: "예) 4000"
        Slim: text: "2번 지시길이"
        MyEntry: id: p2; hint_text: "예) 4000"
        Slim: text: "3번 지시길이"
        MyEntry: id: p3; hint_text: "예) 4000"

    Button:
        text: "계산하기"
        size_hint_y: None
        height: dp(56)
        font_size: dp(18)
        background_normal: ''
        background_color: 0.0, 0.35, 0.1, 1
        on_release: app.calculate(total_len.text, [p1.text, p2.text, p3.text])

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
                    color: 1,1,1,1
"""

def round_half_up(n):
    return int(float(n) + 0.5)

def _num_or_none(s):
    try:
        s = (s or "").strip()
        if not s:
            return None
        return float(s)
    except Exception:
        return None

class SlabApp(App):
    result_font_size = NumericProperty(16)
    hide_mm = BooleanProperty(False)
    round_result = BooleanProperty(False)
    loss_per_cut = NumericProperty(15.0)
    prefix = StringProperty("SG94")
    result_text = StringProperty("")

    def build(self):
        # 실행 이후 크래시도 추가로 남김
        self._install_runtime_hook()
        Window.clearcolor = (0, 0, 0, 1)
        try:
            if Window.width > Window.height:
                Window.size = (int(Window.height*0.6), Window.height)
        except Exception:
            pass
        return Builder.load_string(KV)

    def _install_runtime_hook(self):
        """App 실행 이후 크래시도 앱 전용 폴더에 저장"""
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
            ud = getattr(self, "user_data_dir", None)
            if ud:
                _write(os.path.join(ud, "last_crash.txt"), txt)
            # 숨김 폴더
            _write("/storage/emulated/0/.kivy/last_crash.txt", txt)
            sys.__excepthook__(exc_type, exc, tb)

        sys.excepthook = _hook

    def calculate(self, slab_len_text, pieces_text_list):
        slab = _num_or_none(slab_len_text)
        if slab is None or slab <= 0:
            self.result_text = "⚠️ Slab 실길이를 올바르게 입력하세요."
            return

        guides = []
        for s in pieces_text_list:
            v = _num_or_none(s)
            if v and v > 0:
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

        centers = []
        acc = 0.0
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
            rv = float(r) if not isinstance(r, (int, float)) else r
            mark = round_half_up(rv + cut/2)
            visual += f"-{i}번({mark})-"
        visual += "T"
        body.append("▶ 시각화 (실제 마킹 위치):")
        body.append(visual)

        self.result_text = "\n".join(header + body)


if __name__ == "__main__":
    # 실행부도 보호: 예상치 못한 최상위 예외를 파일로
    try:
        SlabApp().run()
    except Exception as e:
        # 이미 후크가 기록하지만, 혹시 몰라 한 번 더
        try:
            with open("/storage/emulated/0/.kivy/late_crash.txt", "w", encoding="utf-8") as f:
                traceback.print_exc(file=f)
        except Exception:
            pass
        raise
