# -*- coding: utf-8 -*-
# 버전 17 — 기본 Kivy 위젯만 사용(커스텀 제거) / 설정 화면 재구성 / 입력폭 고정 비율 / 명칭 및 경고문 수정
# - 설정 항목(1~7): 고정부 변경, 정수 반올림, 출력부 폰트, mm표시 제거, 절단 손실 길이, 자동 폰트, 출력값 위치 이동
# - 메인: "Slab 실길이"로 라벨 교체, 입력 폭 비율 적용(강번 앞칸=3자리, 뒷칸=1자리·살짝 확장 / 실길이 5칸 / 지시길이 4칸)
# - 절단 손실(mm)=settings.loss_mm 기본 15 사용
# - mm 숨김/정수 반올림/시각화-예상길이 순서 교체 옵션 반영
# - settings.json 영구 저장/로드

import os, sys, json, traceback
from kivy.app import App
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.switch import Switch
from kivy.uix.widget import Widget

FONT = "NanumGothic"
SETTINGS_FILE = "settings.json"

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

def load_settings():
    defaults = {
        "prefix": "SG94",          # 1 입력값
        "fix_prefix": False,       # 1 토글: 강번 맨앞 영문+숫자 고정부 변경
        "round_int": False,        # 2 정수 결과 반올림
        "out_font": 15,            # 3 출력부 폰트 크기(px)
        "mm_hide": False,          # 4 결과값 mm 표시 제거
        "loss_mm": 15.0,           # 5 절단 손실 길이(mm)
        "auto_font": False,        # 6 모바일 대응 자동 폰트 조절(향후 확장)
        "swap_sections": False     # 7 출력값 위치 이동(시각화 ↔ 예상 길이)
    }
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
            defaults.update(data)
    except Exception:
        pass
    return defaults

def save_settings(data: dict):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ---------------- 메인 화면 ----------------
class MainScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        Window.clearcolor = (0.93, 0.93, 0.93, 1)
        root = BoxLayout(orientation="vertical", padding=[dp(12), dp(8)], spacing=dp(8))
        self.add_widget(root)

        # 상단바
        bar = BoxLayout(size_hint=(1, None), height=dp(40))
        bar.add_widget(Widget())
        btn_settings = Button(text="설정", size_hint=(None, 1), width=dp(80))
        btn_settings.bind(on_release=lambda *_: self.app.open_settings())
        bar.add_widget(btn_settings)
        root.add_widget(bar)

        # 제목
        title_row = BoxLayout(size_hint=(1, None), height=dp(48))
        title = Label(text="후판 계산기", font_name=FONT, font_size=dp(32),
                      color=(0,0,0,1), halign="center", valign="middle")
        title.bind(size=lambda *_: setattr(title, "text_size", title.size))
        title_row.add_widget(title)
        root.add_widget(title_row)

        # ===== 입력부 폭 규격(비율 고정) =====
        # 설정 1번 입력칸 폭을 기준으로 잡는다: 두 자리 자연스럽게 보이는 정도
        W_UNIT = dp(53)  # 기준 박스(설정 1번과 동일 비율)
        # 강번: 앞칸(3자리) ~0.9*W_UNIT*1.2, 뒷칸(1자리) ~0.6*W_UNIT
        self.w_code_front = dp(60)
        self.w_code_back  = dp(36)
        # Slab 실길이: 5칸
        self.w_slab = dp(124)
        # 지시길이: 4칸
        self.w_guide = dp(100)

        # 강번 입력
        row_code = BoxLayout(size_hint=(1, None), height=dp(30), spacing=dp(6))
        lab = Label(text="강번 입력:", font_name=FONT, color=(0,0,0,1),
                    size_hint=(None,1), width=dp(96), halign="right", valign="middle")
        lab.bind(size=lambda *_: setattr(lab, "text_size", lab.size))
        row_code.add_widget(lab)

        self.lab_prefix = Label(text=self.app.settings.get("prefix","SG94"),
                                font_name=FONT, color=(0,0,0,1),
                                size_hint=(None,1), width=dp(48),
                                halign="center", valign="middle")
        self.lab_prefix.bind(size=lambda *_: setattr(self.lab_prefix, "text_size", self.lab_prefix.size))
        row_code.add_widget(self.lab_prefix)

        self.in_code_front = TextInput(multiline=False, font_name=FONT,
                                       size_hint=(None,1), width=self.w_code_front,
                                       padding=(dp(6), dp(5)))
        self.in_code_front.bind(text=self._auto_move_back)
        row_code.add_widget(self.in_code_front)

        dash = Label(text="-0", font_name=FONT, color=(0,0,0,1),
                     size_hint=(None,1), width=dp(24), halign="center", valign="middle")
        dash.bind(size=lambda *_: setattr(dash, "text_size", dash.size))
        row_code.add_widget(dash)

        self.in_code_back = TextInput(multiline=False, font_name=FONT,
                                      size_hint=(None,1), width=self.w_code_back,
                                      padding=(dp(6), dp(5)))
        row_code.add_widget(self.in_code_back)
        root.add_widget(row_code)

        # Slab 실길이
        row_total = BoxLayout(size_hint=(1, None), height=dp(30), spacing=dp(6))
        labt = Label(text="Slab 실길이:", font_name=FONT, color=(0,0,0,1),
                     size_hint=(None,1), width=dp(96), halign="right", valign="middle")
        labt.bind(size=lambda *_: setattr(labt, "text_size", labt.size))
        row_total.add_widget(labt)
        self.in_total = TextInput(multiline=False, font_name=FONT,
                                  size_hint=(None,1), width=self.w_slab,
                                  padding=(dp(6), dp(5)))
        row_total.add_widget(self.in_total)
        row_total.add_widget(Widget())
        root.add_widget(row_total)

        # 지시길이 Grid
        grid = GridLayout(cols=4, size_hint=(1, None), height=dp(30*3+8*2),
                          row_default_height=dp(30), row_force_default=True, spacing=dp(8))

        def lab_r(text):
            L = Label(text=text, font_name=FONT, color=(0,0,0,1),
                      size_hint=(None,1), width=dp(96), halign="right", valign="middle")
            L.bind(size=lambda *_: setattr(L, "text_size", L.size))
            return L

        self.in_p1 = TextInput(multiline=False, font_name=FONT, size_hint=(None,1),
                               width=self.w_guide, padding=(dp(6), dp(5)))
        self.in_p2 = TextInput(multiline=False, font_name=FONT, size_hint=(None,1),
                               width=self.w_guide, padding=(dp(6), dp(5)))
        self.in_p3 = TextInput(multiline=False, font_name=FONT, size_hint=(None,1),
                               width=self.w_guide, padding=(dp(6), dp(5)))

        grid.add_widget(lab_r("1번 지시길이:")); grid.add_widget(self.in_p1)
        btn_void1 = Widget(); btn_void2 = Widget()
        grid.add_widget(btn_void1); grid.add_widget(btn_void2)

        grid.add_widget(lab_r("2번 지시길이:")); grid.add_widget(self.in_p2)
        b21 = Button(text="← 1번", size_hint=(None,1), width=dp(68))
        b21.bind(on_release=lambda *_: self._copy(self.in_p1, self.in_p2))
        grid.add_widget(b21); grid.add_widget(Widget())

        grid.add_widget(lab_r("3번 지시길이:")); grid.add_widget(self.in_p3)
        b31 = Button(text="← 1번", size_hint=(None,1), width=dp(68))
        b32 = Button(text="← 2번", size_hint=(None,1), width=dp(68))
        b31.bind(on_release=lambda *_: self._copy(self.in_p1, self.in_p3))
        b32.bind(on_release=lambda *_: self._copy(self.in_p2, self.in_p3))
        row_btns = BoxLayout(size_hint=(None,1), width=dp(68*2+8), spacing=dp(8))
        row_btns.add_widget(b31); row_btns.add_widget(b32)
        grid.add_widget(row_btns); grid.add_widget(Widget())
        root.add_widget(grid)

        # 계산 버튼
        btn_calc = Button(text="계산하기", size_hint=(1,None), height=dp(44))
        btn_calc.bind(on_release=lambda *_: self.calculate())
        root.add_widget(btn_calc)

        # 경고바
        warn = BoxLayout(orientation="horizontal", spacing=dp(6),
                         size_hint=(1,None), height=0, opacity=0)
        if os.path.exists("warning.png"):
            try:
                icon = Image(source="warning.png", size_hint=(None,None), size=(dp(18),dp(18)))
            except Exception:
                icon = Label(text="⚠", font_name=FONT, color=(1,0.2,0.2,1),
                             size_hint=(None,None), size=(dp(18),dp(18)))
        else:
            icon = Label(text="⚠", font_name=FONT, color=(1,0.2,0.2,1),
                         size_hint=(None,None), size=(dp(18),dp(18)))
        self.warn_msg = Label(text="", font_name=FONT, color=(0,0,0,1), halign="left", valign="middle")
        self.warn_msg.bind(size=lambda *_: setattr(self.warn_msg, "text_size", self.warn_msg.size))
        warn.add_widget(icon); warn.add_widget(self.warn_msg)
        self.warn_bar = warn
        root.add_widget(self.warn_bar)

        # 출력 라벨(고정 라벨)
        self.out = Label(text="", font_name=FONT, color=(0,0,0,1),
                         size_hint=(1,1), halign="left", valign="top")
        self.out.bind(size=lambda *_: setattr(self.out, "text_size", (self.out.width-dp(12), None)))
        root.add_widget(self.out)

        # 하단 서명
        sig = Label(text="made by ft10350", font_name=FONT, color=(0.4,0.4,0.4,1),
                    size_hint=(1,None), height=dp(22), halign="right", valign="middle")
        sig.bind(size=lambda *_: setattr(sig, "text_size", sig.size))
        root.add_widget(sig)

        self.apply_settings(self.app.settings)

    # helpers
    def _copy(self, src, dst):
        dst.text = src.text

    def _auto_move_back(self, instance, value):
        if len(value or "") >= 3:
            self.in_code_back.focus = True

    def _show_warn(self, msg):
        self.warn_msg.text = msg
        self.warn_bar.height = dp(28)
        self.warn_bar.opacity = 1

    def _hide_warn(self):
        self.warn_msg.text = ""
        self.warn_bar.height = 0
        self.warn_bar.opacity = 0

    def _fmt(self, x, as_int=False, mm=False):
        if as_int:
            s = f"{round_half_up(x):,d}"
        else:
            s = f"{x:,.1f}"
        return s if not mm else f"{s} mm"

    def calculate(self):
        try:
            st = self.app.settings
            slab = _num_or_none(self.in_total.text)
            p1, p2, p3 = map(_num_or_none, [self.in_p1.text, self.in_p2.text, self.in_p3.text])

            if slab is None or slab <= 0:
                self.out.text = ""
                self._show_warn("Slab 실길이를 올바르게 입력하세요.")
                return

            guides = [v for v in (p1,p2,p3) if v is not None and v > 0]
            if len(guides) < 2:
                self.out.text = ""
                self._show_warn("최소 2개 이상의 지시길이를 입력하세요.")
                return
            self._hide_warn()

            loss = float(st.get("loss_mm", 15.0))
            total_loss = loss * (len(guides)-1)
            remain = slab - (sum(guides) + total_loss)
            add_each = remain / len(guides) if len(guides) else 0.0
            real = [g + add_each for g in guides]

            as_int = bool(st.get("round_int", False))
            show_mm = not bool(st.get("mm_hide", False))

            cf = (self.in_code_front.text or "").strip()
            cb = (self.in_code_back.text or "").strip()
            lines_top = []
            if cf and cb:
                prefix = st.get("prefix","SG94")
                lines_top.append(f"▶ 강번: {prefix}{cf}-0{cb}\n")

            lines_info = []
            lines_info.append(f"▶ Slab 실길이: {self._fmt(slab, as_int, show_mm)}")
            for i,g in enumerate(guides,1):
                lines_info.append(f"▶ {i}번 지시길이: {self._fmt(g, as_int, show_mm)}")
            lines_info.append(f"▶ 절단 손실: {self._fmt(loss, as_int, show_mm)} × {len(guides)-1} = {self._fmt(total_loss, as_int, show_mm)}")
            lines_info.append(f"▶ 전체 여유길이: {self._fmt(remain, as_int, show_mm)} → 각 +{self._fmt(add_each, as_int, show_mm)}\n")

            lines_est = ["▶ 절단 후 예상 길이:"]
            for i, r in enumerate(real, 1):
                lines_est.append(f"   {i}번: {self._fmt(r, as_int, show_mm)}")

            visual = "H"
            for i, r in enumerate(real, 1):
                mark = r + loss/2.0
                mark_s = f"{round_half_up(mark)}" if as_int else f"{mark:,.1f}"
                visual += f"-{i}번({mark_s})-"
            visual += "T"
            lines_vis = ["\n▶ 시각화 (절단 마킹 포인트):", visual]

            if st.get("swap_sections", False):
                body = lines_top + lines_info + lines_vis + [""] + lines_est
            else:
                body = lines_top + lines_info + lines_est + [""] + lines_vis

            self.out.font_size = dp(self._auto_output_font())
            self.out.text = "\n".join(body)

        except Exception as e:
            self._show_warn(f"오류: {e}")
            raise

    def _auto_output_font(self):
        st = self.app.settings
        if st.get("auto_font", False):
            # 매우 단순한 스케일: 폭 기준
            w = max(Window.width, 320)
            base = 15
            return int(base * (w/360.0))
        return int(st.get("out_font", 15))

    def apply_settings(self, st: dict):
        # 접두어 라벨
        self.lab_prefix.text = st.get("prefix","SG94")
        # 출력 라벨 폰트
        self.out.font_size = dp(self._auto_output_font())

# ---------------- 설정 화면(기본 위젯만) ----------------
class SettingsScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        Window.clearcolor = (0.93, 0.93, 0.93, 1)
        root = BoxLayout(orientation="vertical", padding=[dp(12), dp(8)], spacing=dp(10))
        self.add_widget(root)

        # 상단바 (여백 최소화)
        bar = BoxLayout(size_hint=(1,None), height=dp(40))
        title = Label(text="환경설정", font_name=FONT, font_size=dp(28),
                      color=(0,0,0,1), halign="center", valign="middle")
        title.bind(size=lambda *_: setattr(title, "text_size", title.size))
        bar.add_widget(title)
        btn_save = Button(text="저장", size_hint=(None,1), width=dp(80))
        btn_save.bind(on_release=lambda *_: self._save_and_back())
        bar.add_widget(btn_save)
        root.add_widget(bar)

        # (1) 강번 고정부 변경
        root.add_widget(self._section_title("1. 강번 고정부 변경"))
        row1 = BoxLayout(size_hint=(1,None), height=dp(30), spacing=dp(8))
        self.in_prefix = TextInput(text=self.app.settings.get("prefix","SG94"),
                                   multiline=False, font_name=FONT,
                                   size_hint=(None,1), width=dp(53),
                                   padding=(dp(6), dp(5)))
        row1.add_widget(self.in_prefix)
        desc1 = Label(text="강번 맨앞 영문+숫자 고정부 변경", font_name=FONT, color=(0,0,0,1),
                      halign="left", valign="middle")
        desc1.bind(size=lambda *_: setattr(desc1, "text_size", desc1.size))
        row1.add_widget(desc1)
        sw1 = Switch(active=bool(self.app.settings.get("fix_prefix", False)),
                     size_hint=(None,None), size=(dp(48), dp(24)))
        # 오른쪽 정렬
        row1.add_widget(Widget())
        row1.add_widget(sw1)
        self.sw_fix_prefix = sw1
        root.addWidget = root.add_widget
        root.add_widget(row1)

        # (2) 정수 결과 반올림
        root.add_widget(self._section_title("2. 정수 결과 반올림"))
        row2 = BoxLayout(size_hint=(1,None), height=dp(30))
        row2.add_widget(Label(text="출력부 소수값을 정수로 표시", font_name=FONT,
                              color=(0,0,0,1), halign="left", valign="middle"))
        self.sw_round = Switch(active=bool(self.app.settings.get("round_int", False)),
                               size_hint=(None,None), size=(dp(48), dp(24)))
        row2.add_widget(Widget()); row2.add_widget(self.sw_round)
        root.add_widget(row2)

        # (3) 출력부 폰트 크기
        root.add_widget(self._section_title("3. 출력부 폰트 크기"))
        row3 = BoxLayout(size_hint=(1,None), height=dp(30), spacing=dp(8))
        self.in_out_font = TextInput(text=str(int(self.app.settings.get("out_font",15))),
                                     multiline=False, font_name=FONT,
                                     size_hint=(None,1), width=dp(53),
                                     padding=(dp(6), dp(5)))
        row3.add_widget(self.in_out_font)
        row3.add_widget(Label(text="px  결과표시 라벨 폰트 크기", font_name=FONT,
                              color=(0,0,0,1), halign="left", valign="middle"))
        root.add_widget(row3)

        # (4) 결과값 mm 표시 제거
        root.add_widget(self._section_title("4. 결과값 mm 표시 제거"))
        row4 = BoxLayout(size_hint=(1,None), height=dp(30))
        row4.add_widget(Label(text="체크 시 단위(mm) 문구 숨김 (숫자만 표시)",
                              font_name=FONT, color=(0,0,0,1)))
        self.sw_mmhide = Switch(active=bool(self.app.settings.get("mm_hide", False)),
                                size_hint=(None,None), size=(dp(48), dp(24)))
        row4.add_widget(Widget()); row4.add_widget(self.sw_mmhide)
        root.add_widget(row4)

        # (5) 절단 손실 길이 조정
        root.add_widget(self._section_title("5. 절단 손실 길이 조정"))
        row5 = BoxLayout(size_hint=(1,None), height=dp(30), spacing=dp(8))
        self.in_loss = TextInput(text=f"{float(self.app.settings.get('loss_mm',15.0)):.0f}",
                                 multiline=False, font_name=FONT,
                                 size_hint=(None,1), width=dp(53),
                                 padding=(dp(6), dp(5)))
        row5.add_widget(self.in_loss)
        row5.add_widget(Label(text="절단시 손실 보정 길이 (mm)", font_name=FONT, color=(0,0,0,1)))
        root.add_widget(row5)

        # (6) 모바일 대응 자동 폰트 크기 조절
        root.add_widget(self._section_title("6. 모바일 대응 자동 폰트 크기 조절"))
        row6 = BoxLayout(size_hint=(1,None), height=dp(30))
        row6.add_widget(Label(text="화면 해상도에 맞게 입력부 폰트 자동 스케일",
                              font_name=FONT, color=(0,0,0,1)))
        self.sw_autofont = Switch(active=bool(self.app.settings.get("auto_font", False)),
                                  size_hint=(None,None), size=(dp(48), dp(24)))
        row6.add_widget(Widget()); row6.add_widget(self.sw_autofont)
        root.add_widget(row6)

        # (7) 출력값 위치 이동
        root.add_widget(self._section_title("7. 출력값 위치 이동"))
        row7 = BoxLayout(size_hint=(1,None), height=dp(30))
        row7.add_widget(Label(text="ON 시 '시각화'가 먼저, 그 다음 '절단 후 예상 길이'",
                              font_name=FONT, color=(0,0,0,1)))
        self.sw_swap = Switch(active=bool(self.app.settings.get("swap_sections", False)),
                              size_hint=(None,None), size=(dp(48), dp(24)))
        row7.add_widget(Widget()); row7.add_widget(self.sw_swap)
        root.add_widget(row7)

        # 하단 버전 표기
        foot = Label(text="버전 1.0(설정)", font_name=FONT, color=(0.4,0.4,0.4,1),
                     size_hint=(1,None), height=dp(22), halign="right", valign="middle")
        foot.bind(size=lambda *_: setattr(foot, "text_size", foot.size))
        root.add_widget(foot)

    def _section_title(self, text):
        L = Label(text=text, font_name=FONT, color=(0,0,0,1),
                  size_hint=(1,None), height=dp(20), halign="left", valign="middle")
        L.bind(size=lambda *_: setattr(L, "text_size", L.size))
        return L

    def _save_and_back(self):
        st = dict(self.app.settings)
        st["prefix"] = (self.in_prefix.text or "SG94").strip()
        st["fix_prefix"] = bool(self.sw_fix_prefix.active)
        st["round_int"] = bool(self.sw_round.active)
        try:
            st["out_font"] = max(8, min(40, int(self.in_out_font.text or "15")))
        except Exception:
            st["out_font"] = 15
        st["mm_hide"] = bool(self.sw_mmhide.active)
        try:
            st["loss_mm"] = float(self.in_loss.text or "15")
        except Exception:
            st["loss_mm"] = 15.0
        st["auto_font"] = bool(self.sw_autofont.active)
        st["swap_sections"] = bool(self.sw_swap.active)

        save_settings(st)
        self.app.settings = st
        self.app.main.apply_settings(st)
        self.app.sm.current = "main"

# ---------------- 앱 ----------------
class SlabApp(App):
    def build(self):
        _install_global_crash_hook(self.user_data_dir)
        self.settings = load_settings()
        self.sm = ScreenManager(transition=NoTransition())
        self.main = MainScreen(self, name="main")
        self.settings_screen = SettingsScreen(self, name="settings")
        self.sm.add_widget(self.main)
        self.sm.add_widget(self.settings_screen)
        self.sm.current = "main"
        return self.sm

    def open_settings(self):
        self.sm.current = "settings"

if __name__ == "__main__":
    SlabApp().run()
