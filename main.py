# 버전 9 - 전체 설정화면 + 출력부 스크롤 제거 + 항목(1~3) 반영 2025-10-28
# - 설정창: 팝업 → 전체 화면, 입력부와 유사한 UI
# - 설정 항목: (1) 접두어(영문+숫자만), (2) 정수 반올림(회색 안내문), (3) 출력 폰트 크기(기본 11)
# - 저장 누르면 settings.json 저장 후 자동으로 메인 복귀 (뒤로 버튼 없음)
# - 출력부: 스크롤 제거(고정 라벨). 추후 복사 기능은 별도 추가 가능.

import os, sys, json, re, traceback
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.properties import NumericProperty, ListProperty, BooleanProperty, StringProperty
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget

SETTINGS_FILE = "settings.json"
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

def _install_global_crash_hook(user_data_dir: str):
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
        if user_data_dir:
            _write(os.path.join(user_data_dir, "last_crash.txt"), txt)
        _write("/storage/emulated/0/.kivy/last_crash.txt", txt)
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _hook

# 둥근 버튼(터치 가능한 Label)
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

# 숫자 입력(왼쪽정렬 + 자릿수 제한)
class DigitInput(TextInput):
    max_len = NumericProperty(3)
    allow_float = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multiline = False
        self.halign = "left"
        self.padding = (dp(6), dp(5))
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

# 영문+숫자만 허용하는 입력(접두어용)
class AlnumInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multiline = False
        self.halign = "left"
        self.padding = (dp(6), dp(5))
        self.font_name = FONT
        self.font_size = dp(16)
        self.height = dp(30)
        self.background_normal = ""
        self.background_active = ""
        self.cursor_width = dp(2)
        self.write_tab = False
        self.bind(text=self._filter_alnum)

    def _filter_alnum(self, *_):
        # 영문 대소문자 + 숫자만 유지
        t = self.text
        nt = re.sub(r'[^A-Za-z0-9]', '', t)
        if nt != t:
            self.text = nt

class SlabApp(App):
    # 런타임 설정값
    prefix = StringProperty("SG94")
    round_result = BooleanProperty(False)   # True면 정수로 표시
    result_font_size = NumericProperty(11)  # 출력부 폰트 크기

    def build(self):
        _install_global_crash_hook(self.user_data_dir)
        Window.clearcolor = (0.93, 0.93, 0.93, 1)

        # ---- 설정 로드 ----
        self._load_settings()

        # 두 화면을 필요시 전환 (메인 / 설정)
        self.root_box = BoxLayout(orientation="vertical", padding=[dp(12), dp(8)], spacing=dp(8))
        self._build_main_view()  # 처음엔 메인 화면
        return self.root_box

    # ========== 메인 화면 ==========
    def _build_main_view(self):
        self.root_box.clear_widgets()

        # 상단바(우측 설정)
        topbar = BoxLayout(size_hint=(1, None), height=dp(40))
        topbar.add_widget(Widget())
        btn_settings = RoundedButton(text="설정", size_hint=(None, 1), width=dp(66),
                                     bg_color=[0.27, 0.27, 0.27, 1], fg_color=[1, 1, 1, 1])
        btn_settings.bind(on_release=lambda *_: self._build_settings_view())
        topbar.add_widget(btn_settings)
        self.root_box.add_widget(topbar)

        # 제목(센터)
        title_row = BoxLayout(size_hint=(1, None), height=dp(44))
        title = Label(text="후판 계산기", font_name=FONT, font_size=dp(28),
                      color=(0, 0, 0, 1), halign="center", valign="middle")
        title.bind(size=lambda *_: setattr(title, "text_size", title.size))
        title_row.add_widget(title)
        self.root_box.add_widget(title_row)

        # 강번 입력(버전9 스타일 유지)
        row_code = BoxLayout(orientation="horizontal", size_hint=(1, None),
                             height=dp(30), spacing=dp(4))
        lab_code = Label(text="강번 입력:", font_name=FONT, color=(0,0,0,1),
                         size_hint=(None,1), width=dp(74), halign="right", valign="middle")
        lab_code.bind(size=lambda *_: setattr(lab_code, "text_size", lab_code.size))
        row_code.add_widget(lab_code)

        lab_prefix = Label(text=self.prefix, font_name=FONT, color=(0,0,0,1),
                           size_hint=(None,1), width=dp(44), halign="center", valign="middle")
        lab_prefix.bind(size=lambda *_: setattr(lab_prefix, "text_size", lab_prefix.size))
        row_code.add_widget(lab_prefix)

        self.in_code_front = DigitInput(max_len=3, allow_float=False, size_hint=(None,1), width=dp(60))
        self.in_code_front.bind(text=self._auto_move_back)
        row_code.add_widget(self.in_code_front)

        lab_dash = Label(text="-0", font_name=FONT, color=(0,0,0,1),
                         size_hint=(None,1), width=dp(22), halign="center", valign="middle")
        lab_dash.bind(size=lambda *_: setattr(lab_dash, "text_size", lab_dash.size))
        row_code.add_widget(lab_dash)

        self.in_code_back = DigitInput(max_len=1, allow_float=False, size_hint=(None,1), width=dp(40))
        row_code.add_widget(self.in_code_back)
        self.root_box.add_widget(row_code)

        # 실제 Slab 길이
        row_total = BoxLayout(orientation="horizontal", size_hint=(1, None),
                              height=dp(30), spacing=dp(4))
        lab_total = Label(text="실제 Slab 길이:", font_name=FONT, color=(0,0,0,1),
                          size_hint=(None,1), width=dp(104), halign="right", valign="middle")
        lab_total.bind(size=lambda *_: setattr(lab_total, "text_size", lab_total.size))
        row_total.add_widget(lab_total)

        self.in_total = DigitInput(max_len=5, allow_float=True, size_hint=(None,1), width=dp(124))
        row_total.add_widget(self.in_total)
        row_total.add_widget(Widget())
        self.root_box.add_widget(row_total)

        # 지시길이
        grid = GridLayout(cols=4, size_hint=(1, None), height=dp(30*3+8*2),
                          row_default_height=dp(30), row_force_default=True, spacing=dp(8))
        def _lab(text, w):
            lb = Label(text=text, font_name=FONT, color=(0,0,0,1),
                       size_hint=(None,1), width=w, halign="right", valign="middle")
            lb.bind(size=lambda *_: setattr(lb, "text_size", lb.size))
            return lb

        self.in_p1 = DigitInput(max_len=4, allow_float=True, size_hint=(None,1), width=dp(100))
        self.in_p2 = DigitInput(max_len=4, allow_float=True, size_hint=(None,1), width=dp(100))
        self.in_p3 = DigitInput(max_len=4, allow_float=True, size_hint=(None,1), width=dp(100))

        grid.add_widget(_lab("1번 지시길이:", dp(104))); grid.add_widget(self.in_p1); grid.add_widget(Label()); grid.add_widget(Label())
        grid.add_widget(_lab("2번 지시길이:", dp(104))); grid.add_widget(self.in_p2)
        b21 = RoundedButton(text="← 1번", bg_color=[0.8,0.8,0.8,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(58))
        b21.bind(on_release=lambda *_: self._copy(self.in_p1, self.in_p2))
        grid.add_widget(b21); grid.add_widget(Label())
        grid.add_widget(_lab("3번 지시길이:", dp(104))); grid.add_widget(self.in_p3)
        btn_row = BoxLayout(orientation="horizontal", spacing=dp(8),
                            size_hint=(None,1), width=dp(58*2 + 8))
        b31 = RoundedButton(text="← 1번", bg_color=[0.8,0.8,0.8,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(58))
        b32 = RoundedButton(text="← 2번", bg_color=[0.8,0.8,0.8,1], fg_color=[0,0,0,1],
                            size_hint=(None,1), width=dp(58))
        b31.bind(on_release=lambda *_: self._copy(self.in_p1, self.in_p3))
        b32.bind(on_release=lambda *_: self._copy(self.in_p2, self.in_p3))
        btn_row.add_widget(b31); btn_row.add_widget(b32)
        grid.add_widget(btn_row); grid.add_widget(Label())
        self.root_box.add_widget(grid)

        # 계산 버튼
        btn_calc = RoundedButton(text="계산하기", bg_color=[0.23, 0.53, 0.23, 1],
                                 fg_color=[1,1,1,1], size_hint=(1, None),
                                 height=dp(44), radius=dp(10))
        btn_calc.bind(on_release=lambda *_: self.calculate())
        self.root_box.add_widget(btn_calc)

        # 경고 바 (필요 시 노출)
        self.warn_bar = BoxLayout(orientation="horizontal", spacing=dp(6),
                                  size_hint=(1, None), height=0, opacity=0)
        self.warn_icon = Label(text="⚠", font_name=FONT, color=(1,0.2,0.2,1),
                               size_hint=(None, None), size=(dp(18), dp(18)))
        self.warn_msg = Label(text="", font_name=FONT, color=(0,0,0,1),
                              halign="left", valign="middle")
        self.warn_msg.bind(size=lambda *_: setattr(self.warn_msg, "text_size", self.warn_msg.size))
        self.warn_bar.add_widget(self.warn_icon); self.warn_bar.add_widget(self.warn_msg)
        self.root_box.add_widget(self.warn_bar)

        # 결과(스크롤 제거, 고정 라벨)
        self.result_label = Label(text="", font_name=FONT, color=(0,0,0,1),
                                  size_hint=(1, None), halign="left", valign="top")
        self.result_label.font_size = dp(self.result_font_size)
        self.result_label.bind(texture_size=lambda *_: self._resize_result())
        # 하얀 배경
        with self.result_label.canvas.before:
            Color(1,1,1,1)
            self._bg_rect = RoundedRectangle(size=self.result_label.size, pos=self.result_label.pos,
                                             radius=[(dp(6), dp(6))]*4)
        self.result_label.bind(size=self._bg_follow, pos=self._bg_follow)
        self.root_box.add_widget(self.result_label)

        # 하단 버전 표기
        sig = Label(text="버전 9", font_name=FONT, color=(0.4,0.4,0.4,1),
                    halign="right", valign="middle", size_hint=(1, None), height=dp(22))
        sig.bind(size=lambda *_: setattr(sig, "text_size", sig.size))
        self.root_box.add_widget(sig)

    # ========== 설정 화면 ==========
    def _build_settings_view(self):
        self.root_box.clear_widgets()

        # 상단바(좌측 ‘메인으로’)
        topbar = BoxLayout(size_hint=(1, None), height=dp(40))
        btn_back = RoundedButton(text="저장", size_hint=(None, 1), width=dp(66),
                                 bg_color=[0.23,0.53,0.23,1], fg_color=[1, 1, 1, 1])
        btn_back.bind(on_release=lambda *_: self._save_settings_and_back())
        topbar.add_widget(btn_back)
        topbar.add_widget(Widget())  # 가운데/오른쪽 여백
        self.root_box.add_widget(topbar)

        # 제목
        title_row = BoxLayout(size_hint=(1, None), height=dp(44))
        title = Label(text="환경설정", font_name=FONT, font_size=dp(28),
                      color=(0, 0, 0, 1), halign="center", valign="middle")
        title.bind(size=lambda *_: setattr(title, "text_size", title.size))
        title_row.add_widget(title)
        self.root_box.add_widget(title_row)

        # 줄바꿈 3칸 간격
        spacer = Label(text="\n\n\n", font_name=FONT, color=(0,0,0,0), size_hint=(1,None), height=dp(24))
        self.root_box.add_widget(spacer)

        # 공통: 한 줄 레이아웃 생성기 (라벨-입력/체크)
        def _row(h=30, spacing=6): return BoxLayout(size_hint=(1,None), height=dp(h), spacing=dp(spacing))
        def _lab(text, w):
            lb = Label(text=text, font_name=FONT, color=(0,0,0,1),
                       size_hint=(None,1), width=w, halign="right", valign="middle")
            lb.bind(size=lambda *_: setattr(lb, "text_size", lb.size))
            return lb

        # (1) 접두어
        row1_title = _row()
        row1_title.add_widget(Label(text="1. 접두어", font_name=FONT, color=(0,0,0,1),
                                    halign="left", valign="middle"))
        self.root_box.add_widget(row1_title)

        row1 = _row()
        row1.add_widget(_lab("값:", dp(60)))
        self.set_prefix = AlnumInput(size_hint=(None,1), width=dp(120))
        self.set_prefix.text = self.prefix
        row1.add_widget(self.set_prefix)
        row1.add_widget(Widget())
        self.root_box.add_widget(row1)

        # (2) 정수 결과 반올림
        row2_title = _row()
        row2_title.add_widget(Label(text="2. 정수 결과 반올림", font_name=FONT, color=(0,0,0,1),
                                    halign="left", valign="middle"))
        self.root_box.add_widget(row2_title)

        row2 = _row()
        # 간단 체크박스: 토글 버튼 스타일(라운드 회색)
        self.set_round = RoundedButton(
            text=("ON" if self.round_result else "OFF"),
            size_hint=(None,1), width=dp(64),
            bg_color=[0.8,0.8,0.8,1] if not self.round_result else [0.23,0.53,0.23,1],
            fg_color=[0,0,0,1] if not self.round_result else [1,1,1,1]
        )
        self.set_round.bind(on_release=self._toggle_round)
        row2.add_widget(self.set_round)
        help2 = Label(text="출력부 소수점 값을 정수로 표시", font_name=FONT,
                      color=(0.5,0.5,0.5,1), halign="left", valign="middle")
        help2.bind(size=lambda *_: setattr(help2, "text_size", help2.size))
        row2.add_widget(help2)
        row2.add_widget(Widget())
        self.root_box.add_widget(row2)

        # (3) 출력부 폰트 크기 (기본 11)
        row3_title = _row()
        row3_title.add_widget(Label(text="3. 출력부 폰트 크기", font_name=FONT, color=(0,0,0,1),
                                    halign="left", valign="middle"))
        self.root_box.add_widget(row3_title)

        row3 = _row()
        row3.add_widget(_lab("크기:", dp(60)))
        self.set_result_font = DigitInput(max_len=3, allow_float=False, size_hint=(None,1), width=dp(70))
        self.set_result_font.text = str(self.result_font_size or 11)  # 기본 11
        row3.add_widget(self.set_result_font)
        row3.add_widget(Widget())
        self.root_box.add_widget(row3)

        # 하단 안내
        foot = Label(text="저장 버튼을 누르면 설정이 저장되고 메인 화면으로 돌아갑니다.",
                     font_name=FONT, color=(0.4,0.4,0.4,1),
                     size_hint=(1,None), height=dp(24), halign="center", valign="middle")
        foot.bind(size=lambda *_: setattr(foot, "text_size", foot.size))
        self.root_box.add_widget(foot)

    # ========== 유틸 공통 ==========
    def _show_warn(self, msg):
        self.warn_msg.text = msg
        self.warn_bar.height = dp(28)
        self.warn_bar.opacity = 1

    def _hide_warn(self):
        self.warn_msg.text = ""
        self.warn_bar.height = 0
        self.warn_bar.opacity = 0

    def _auto_move_back(self, instance, value):
        if len(value) >= 3:
            self.in_code_back.focus = True

    def _copy(self, src, dst):
        dst.text = src.text

    def _bg_follow(self, *_):
        if hasattr(self, "_bg_rect"):
            self._bg_rect.pos, self._bg_rect.size = self.result_label.pos, self.result_label.size

    def _resize_result(self, *_):
        self.result_label.text_size = (self.result_label.width - dp(12), None)
        self.result_label.height = self.result_label.texture_size[1] + dp(12)

    # ========== 계산 ==========
    def calculate(self, *_):
        try:
            slab = _num_or_none(self.in_total.text)
            p1, p2, p3 = map(_num_or_none, [self.in_p1.text, self.in_p2.text, self.in_p3.text])

            if slab is None or slab <= 0:
                self.result_label.text = ""
                self._show_warn("실제 Slab 길이를 올바르게 입력하세요.")
                return

            guides = [v for v in (p1, p2, p3) if v is not None and v > 0]
            if len(guides) < 2:
                self.result_label.text = ""
                self._show_warn("최소 2개 이상의 지시길이를 입력하세요.")
                return

            self._hide_warn()

            loss = 15.0
            total_loss = loss * (len(guides) - 1)
            remain = slab - (sum(guides) + total_loss)
            add_each = remain / len(guides) if len(guides) else 0.0
            real = [g + add_each for g in guides]

            mm = " mm"
            cf = (self.in_code_front.text or "").strip()
            cb = (self.in_code_back.text or "").strip()

            # 반올림 설정 반영
            def fmt(x):
                if self.round_result:
                    return f"{round_half_up(x)}"
                return f"{x:,.1f}"

            lines = []
            if cf and cb:
                lines.append(f"▶ 강번: {self.prefix}{cf}-0{cb}\n")

            lines.append(f"▶ Slab 실길이: {fmt(slab)}{'' if self.round_result else mm}")
            for i, g in enumerate(guides, 1):
                lines.append(f"▶ {i}번 지시길이: {fmt(g)}{'' if self.round_result else mm}")
            lines.append(f"▶ 절단 손실: {fmt(loss)}{'' if self.round_result else mm} × {len(guides)-1} = {fmt(total_loss)}{'' if self.round_result else mm}")
            lines.append(f"▶ 전체 여유길이: {fmt(remain)}{'' if self.round_result else mm} → 각 +{fmt(add_each)}{'' if self.round_result else mm}\n")

            lines.append("▶ 절단 후 예상 길이:")
            for i, r in enumerate(real, 1):
                lines.append(f"   {i}번: {fmt(r)}{'' if self.round_result else mm}")

            lines.append("\n▶ 시각화 (절단 마킹 포인트):")
            visual = "H"
            for i, r in enumerate(real, 1):
                mark = round_half_up(r + loss/2) if self.round_result else f"{r + loss/2:,.1f}"
                visual += f"-{i}번({mark})-"
            visual += "T"
            lines.append(visual)

            self.result_label.font_size = dp(self.result_font_size or 11)
            self.result_label.text = "\n".join(lines)
        except Exception as e:
            self._show_warn(f"오류: {e}")
            raise

    # ========== 설정 저장/로드 ==========
    def _load_settings(self):
        # 기본값
        s = {"prefix": "SG94", "round": False, "font": 11}
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    s.update({
                        "prefix": data.get("prefix", s["prefix"]),
                        "round": bool(data.get("round", s["round"])),
                        "font": int(data.get("font", s["font"])),
                    })
        except Exception:
            pass
        self.prefix = s["prefix"]
        self.round_result = s["round"]
        self.result_font_size = s["font"]

    def _save_settings_and_back(self):
        # 입력값 수집 및 검증
        try:
            new_prefix = (self.set_prefix.text or "SG94")
            new_prefix = re.sub(r'[^A-Za-z0-9]', '', new_prefix) or "SG94"
            new_font = int(self.set_result_font.text or "11")
            if new_font <= 0:
                new_font = 11
            data = {
                "prefix": new_prefix,
                "round": self.round_result,
                "font": new_font
            }
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # 앱 상태 반영
            self.prefix = new_prefix
            self.result_font_size = new_font

            # 메인 화면 재구성
            self._build_main_view()
        except Exception as e:
            # 저장 중 오류도 경고로 표시
            self._build_main_view()
            self._show_warn(f"설정 저장 오류: {e}")

    def _toggle_round(self, *_):
        self.round_result = not self.round_result
        # 토글 버튼 색/문구 갱신
        if self.round_result:
            self.set_round.text = "ON"
            self.set_round.bg_color = [0.23,0.53,0.23,1]
            self.set_round.fg_color = [1,1,1,1]
        else:
            self.set_round.text = "OFF"
            self.set_round.bg_color = [0.8,0.8,0.8,1]
            self.set_round.fg_color = [0,0,0,1]

if __name__ == "__main__":
    SlabApp().run()
