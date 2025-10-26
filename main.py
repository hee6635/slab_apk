# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import math, json, os

SETTINGS_FILE = "settings.json"

# ---------------------------
# 반올림 함수
# ---------------------------
def round_half_up(n):
    return int(n + 0.5)

# ---------------------------
# 설정 불러오기 / 저장
# ---------------------------
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
        "result_font_size": 16,   # 모바일 가독성 향상 (기본 16)
        "hide_mm": False,
        "loss": 15,
        "auto_font": True        # 창 크기에 따라 자동 폰트 조절
    }

def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------------------------
# 메인 프로그램 (UI만 모바일 친화로 개선)
# ---------------------------
class SlabCutCalculator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("후판 절단 계산기")

        # 화면 크기/스케일링 (모바일풍: 세로형, 큰 터치영역)
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        # 기본 윈도우 크기: 세로형 480x800 근사
        w, h = min(520, sw), min(860, sh)
        self.root.geometry(f"{w}x{h}")
        self.root.configure(bg="white")

        # 설정 불러오기
        self.settings = load_settings()
        self.prefix = self.settings.get("prefix", "SG94")
        self.round_result = self.settings.get("round_result", False)
        self.result_font_size = self.settings.get("result_font_size", 16)
        self.hide_mm = self.settings.get("hide_mm", False)
        self.loss_per_cut = self.settings.get("loss", 15)
        self.auto_font = self.settings.get("auto_font", True)

        # 전역 폰트(모바일 크게)
        self.font_title = tkfont.Font(family="NanumGothic", size=18, weight="bold")
        self.font_label = tkfont.Font(family="NanumGothic", size=14)
        self.font_label_b = tkfont.Font(family="NanumGothic", size=14, weight="bold")
        self.font_entry = tkfont.Font(family="NanumGothic", size=14)
        self.font_btn = tkfont.Font(family="NanumGothic", size=14, weight="bold")
        self.font_result = tkfont.Font(family="NanumGothic", size=self.result_font_size)

        # Tk 전체 스케일 (터치 영역 확대 효과)
        try:
            # 1.0(기본)→1.4~1.6 정도가 손가락 터치에 적당
            self.root.call('tk', 'scaling', 1.4)
        except Exception:
            pass

        # ttk 스타일 (버튼/엔트리 높이 증가)
        style = ttk.Style(self.root)
        try:
            style.theme_use("default")
        except Exception:
            pass
        style.configure("TButton", font=self.font_btn, padding=8)
        style.configure("TLabel", font=self.font_label)
        style.configure("TEntry", padding=8)

        # 숫자 입력 검증
        vcmd = (self.root.register(self.validate_number), '%P')

        # ===== 상단 타이틀/버튼 =====
        top = tk.Frame(self.root, bg="white")
        top.pack(fill="x", pady=8, padx=10)

        title_label = tk.Label(top, text="후판 절단 계산기", font=self.font_title, bg="white")
        title_label.pack(side="left", anchor="w")

        settings_btn = tk.Button(top, text="설정", font=self.font_btn,
                                 bg="#E0E0E0", fg="black", activebackground="#C8C8C8",
                                 relief="flat", padx=12, pady=8, command=self.open_settings)
        settings_btn.pack(side="right")

        # ===== 입력 영역 (세로 단일 컬럼, 큰 여백) =====
        form = tk.Frame(self.root, bg="white")
        form.pack(fill="x", padx=12, pady=6)

        # 강번
        row_code = tk.Frame(form, bg="white")
        row_code.pack(fill="x", pady=6)
        self.prefix_label = tk.Label(row_code, text=f"강번 입력 (접두어 {self.prefix})", font=self.font_label_b, bg="white")
        self.prefix_label.pack(anchor="w")

        code_line = tk.Frame(form, bg="white")
        code_line.pack(fill="x")
        self.code_front = tk.Entry(code_line, font=self.font_entry, width=6, justify="center",
                                   bg="white", relief="solid", validate="key", validatecommand=vcmd)
        self.code_front.pack(side="left", padx=(0,6), ipady=6)
        tk.Label(code_line, text="-0", font=self.font_label, bg="white").pack(side="left", padx=4)
        self.code_back = tk.Entry(code_line, font=self.font_entry, width=4, justify="center",
                                  bg="white", relief="solid", validate="key", validatecommand=vcmd)
        self.code_back.pack(side="left", padx=(6,0), ipady=6)
        self.code_front.bind("<KeyRelease>", self.auto_move_next)
        self.code_back.bind("<KeyRelease>", self.update_code_result)

        # Slab 길이
        row_total = tk.Frame(form, bg="white")
        row_total.pack(fill="x", pady=10)
        tk.Label(row_total, text="실제 Slab 길이", font=self.font_label_b, bg="white").pack(anchor="w")
        self.total_entry = tk.Entry(row_total, font=self.font_entry, width=12, bg="white",
                                    relief="solid", validate="key", validatecommand=vcmd, justify="center")
        self.total_entry.pack(fill="x", ipady=6)

        # 지시길이 1~3 (큰 버튼으로 복사)
        row_pieces = tk.Frame(form, bg="white")
        row_pieces.pack(fill="x", pady=6)
        self.piece_entries = []
        for i in range(3):
            block = tk.Frame(row_pieces, bg="white")
            block.pack(fill="x", pady=6)
            tk.Label(block, text=f"{i+1}번 지시길이", font=self.font_label_b, bg="white").pack(anchor="w")
            e = tk.Entry(block, font=self.font_entry, width=12, bg="white",
                         relief="solid", validate="key", validatecommand=vcmd, justify="center")
            e.pack(fill="x", ipady=6)
            self.piece_entries.append(e)

            btns = tk.Frame(block, bg="white")
            btns.pack(fill="x", pady=4)
            if i == 1:
                tk.Button(btns, text="← 1번 복사", font=self.font_btn,
                          bg="#777777", fg="white", activebackground="#5f5f5f",
                          relief="flat", padx=10, pady=8,
                          command=lambda: self.copy_value(0, 1)).pack(side="left")
            elif i == 2:
                tk.Button(btns, text="← 1번 복사", font=self.font_btn,
                          bg="#777777", fg="white", activebackground="#5f5f5f",
                          relief="flat", padx=10, pady=8,
                          command=lambda: self.copy_value(0, 2)).pack(side="left", padx=(0,8))
                tk.Button(btns, text="← 2번 복사", font=self.font_btn,
                          bg="#777777", fg="white", activebackground="#5f5f5f",
                          relief="flat", padx=10, pady=8,
                          command=lambda: self.copy_value(1, 2)).pack(side="left")

        # ===== 계산 버튼 (가로 전체, 큰 터치 영역) =====
        self.calc_btn = tk.Button(self.root, text="계산하기", command=self.calculate,
                                  bg="#4CAF50", fg="white", font=self.font_btn,
                                  relief="flat", height=2, padx=12, pady=14, activebackground="#45A049")
        self.calc_btn.pack(pady=10, fill="x", padx=12)

        # ===== 결과창 (큰 글씨, 스크롤되도록 라벨+캔버스) =====
        result_wrap = tk.Frame(self.root, bg="white")
        result_wrap.pack(padx=12, pady=10, fill="both", expand=True)

        frame_bg = tk.Frame(result_wrap, bg="#F5F5F5", bd=0, highlightthickness=0)
        frame_bg.pack(fill="both", expand=True)

        # 스크롤 가능한 캔버스
        canvas = tk.Canvas(frame_bg, bg="#F5F5F5", highlightthickness=0)
        scrollbar = tk.Scrollbar(frame_bg, orient="vertical", command=canvas.yview)
        self.result_holder = tk.Frame(canvas, bg="#F5F5F5")

        self.result_holder.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0,0), window=self.result_holder, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.result_label = tk.Label(self.result_holder,
                                     font=self.font_result,
                                     bg="#F5F5F5", justify="left", anchor="nw")
        self.result_label.pack(padx=10, pady=10, fill="both", expand=True)

        # 자동 폰트 조절
        if self.auto_font:
            self.root.bind("<Configure>", self.adjust_font_size)

        # 접근성: 탭 순서
        self.code_front.focus_set()

    # 숫자 입력 검증
    def validate_number(self, new_value):
        if new_value == "":
            return True
        try:
            float(new_value)
            return True
        except ValueError:
            return False

    # 강번 자동 이동 (앞 3자리 → 뒤칸)
    def auto_move_next(self, event):
        if len(self.code_front.get()) >= 3:
            self.code_back.focus()
        self.update_code_result()

    def update_code_result(self, event=None):
        front = self.code_front.get().strip()
        back = self.code_back.get().strip()
        if front and back:
            self.generated_code = f"{self.prefix}{front}-0{back}"
        else:
            self.generated_code = ""

    # 복사함수
    def copy_value(self, from_index, to_index):
        val = self.piece_entries[from_index].get()
        if val.strip():
            self.piece_entries[to_index].delete(0, tk.END)
            self.piece_entries[to_index].insert(0, val)

    # 계산 로직 (원본 그대로)
    def calculate(self):
        try:
            slab_len = float(self.total_entry.get())
            guides = [float(e.get()) for e in self.piece_entries if e.get()]
            if len(guides) < 2:
                self.result_label.config(text="⚠️ 최소 2개 이상의 Slab 길이를 입력하세요.")
                return

            cut_loss = self.loss_per_cut
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

            front = self.code_front.get().strip()
            back = self.code_back.get().strip()
            code_result = f"▶ 강번: {self.prefix}{front}-0{back}\n\n" if (front and back) else ""

            mm = "" if self.hide_mm else " mm"

            result_text = code_result
            result_text += f"▶ Slab 실길이: {slab_len:,.1f}{mm}\n"
            for i, g in enumerate(guides):
                result_text += f"▶ {i+1}번 지시길이: {g:,.1f}{mm}\n"
            result_text += f"▶ 절단 손실: {cut_loss}{mm} × {num} = {total_loss}{mm}\n"
            result_text += f"▶ 전체 여유길이: {remain:,.1f}{mm} → 각 +{add_each:,.1f}{mm}\n\n"

            if self.round_result:
                real_lengths_display = [round_half_up(r) for r in real_lengths]
                centers_display = [round_half_up(c) for c in centers]
            else:
                real_lengths_display = [round(r, 1) for r in real_lengths]
                centers_display = [round(c, 1) for c in centers]

            result_text += "▶ 각 Slab별 실제 절단 길이:\n"
            for i, r in enumerate(real_lengths_display):
                if isinstance(r, int):
                    result_text += f"   {i+1}번: {r:,}{mm}\n"
                else:
                    result_text += f"   {i+1}번: {r:,.1f}{mm}\n"

            result_text += f"\n▶ 절단센터 위치:{'' if self.hide_mm else '(mm)'} {centers_display}\n\n"

            visual = "H"
            for i, l in enumerate(real_lengths_display):
                if isinstance(l, int):
                    mark_val = l + round_half_up(cut_loss / 2)
                else:
                    mark_val = round_half_up(l + (cut_loss / 2))
                visual += f"-{i+1}번({mark_val})-"
            visual += "T"
            result_text += f"▶ 시각화 (실제 마킹 위치):\n{visual}\n"

            # 폰트 크기 반영
            self.result_label.config(font=("NanumGothic", self.result_font_size))
            self.result_label.config(text=result_text)

        except Exception as e:
            self.result_label.config(text=f"⚠️ 오류: {e}")

    # 창 크기에 따라 폰트 자동 조절 (모바일풍)
    def adjust_font_size(self, event):
        if not self.auto_font:
            return
        width = max(self.root.winfo_width(), 1)
        # 화면 폭 기준 간단 스케일
        if width < 420:
            s_lbl, s_ent, s_btn, s_res = 12, 12, 12, 14
        elif width < 520:
            s_lbl, s_ent, s_btn, s_res = 13, 13, 13, 15
        elif width < 700:
            s_lbl, s_ent, s_btn, s_res = 14, 14, 14, 16
        else:
            s_lbl, s_ent, s_btn, s_res = 15, 15, 15, 18

        self.font_label.configure(size=s_lbl)
        self.font_label_b.configure(size=s_lbl)
        self.font_entry.configure(size=s_ent)
        self.font_btn.configure(size=s_btn)
        self.font_result.configure(size=s_res)
        self.result_font_size = s_res

    def open_settings(self):
        SettingsWindow(self.root, self)

    def run(self):
        self.root.mainloop()

# ---------------------------
# 설정창 (UI만 정돈)
# ---------------------------
class SettingsWindow:
    def __init__(self, master, main_app):
        self.main_app = main_app
        self.top = tk.Toplevel(master)
        self.top.title("환경 설정")
        self.top.configure(bg="white")

        # 모바일풍 크기
        self.top.geometry("520x720")

        title = tk.Label(self.top, text="환경설정", font=("NanumGothic", 18, "bold"), bg="white")
        title.pack(pady=12)

        container = tk.Frame(self.top, bg="white")
        container.pack(fill="both", expand=True, padx=14, pady=10)

        # 1) 접두어
        block1 = tk.Frame(container, bg="white"); block1.pack(fill="x", pady=8)
        tk.Label(block1, text="1. 강번 접두어", font=("NanumGothic", 14, "bold"), bg="white").pack(anchor="w")
        row1 = tk.Frame(block1, bg="white"); row1.pack(fill="x", pady=4)
        tk.Label(row1, text="접두어", font=("NanumGothic", 13), bg="white").pack(side="left")
        self.entry_prefix = tk.Entry(row1, width=10, relief="solid", bg="white", justify="center",
                                     font=("NanumGothic", 13))
        self.entry_prefix.pack(side="left", padx=8, ipady=6)
        self.entry_prefix.insert(0, self.main_app.prefix)

        # 2) 반올림
        block2 = tk.Frame(container, bg="white"); block2.pack(fill="x", pady=8)
        tk.Label(block2, text="2. 결과값 반올림 (정수표시)", font=("NanumGothic", 14, "bold"), bg="white").pack(anchor="w")
        self.round_var = tk.BooleanVar(value=self.main_app.round_result)
        tk.Checkbutton(block2, text="소수점 없이 정수로 반올림", font=("NanumGothic", 13),
                       bg="white", activebackground="white",
                       variable=self.round_var, fg="#444444", padx=6).pack(anchor="w", pady=4)

        # 3) 출력 폰트 크기
        block3 = tk.Frame(container, bg="white"); block3.pack(fill="x", pady=8)
        tk.Label(block3, text="3. 출력값 폰트 크기", font=("NanumGothic", 14, "bold"), bg="white").pack(anchor="w")
        row3 = tk.Frame(block3, bg="white"); row3.pack(fill="x", pady=4)
        tk.Label(row3, text="폰트 크기", font=("NanumGothic", 13), bg="white").pack(side="left")
        self.entry_font_size = tk.Entry(row3, width=6, relief="solid", bg="white", justify="center",
                                        font=("NanumGothic", 13))
        self.entry_font_size.pack(side="left", padx=8, ipady=6)
        self.entry_font_size.insert(0, str(self.main_app.result_font_size or 16))

        # 4) mm 표시 제거
        block4 = tk.Frame(container, bg="white"); block4.pack(fill="x", pady=8)
        tk.Label(block4, text="4. mm 표시 선택", font=("NanumGothic", 14, "bold"), bg="white").pack(anchor="w")
        self.hide_mm_var = tk.BooleanVar(value=self.main_app.hide_mm)
        tk.Checkbutton(block4, text="체크 시 mm 표시 제거", font=("NanumGothic", 13),
                       bg="white", activebackground="white",
                       variable=self.hide_mm_var, fg="#666666", padx=6).pack(anchor="w", pady=4)

        # 5) 절단 손실
        block5 = tk.Frame(container, bg="white"); block5.pack(fill="x", pady=8)
        tk.Label(block5, text="5. 절단 손실 (mm)", font=("NanumGothic", 14, "bold"), bg="white").pack(anchor="w")
        row5 = tk.Frame(block5, bg="white"); row5.pack(fill="x", pady=4)
        tk.Label(row5, text="절단 손실", font=("NanumGothic", 13), bg="white").pack(side="left")
        self.entry_loss = tk.Entry(row5, width=6, relief="solid", bg="white", justify="center",
                                   font=("NanumGothic", 13))
        self.entry_loss.pack(side="left", padx=8, ipady=6)
        self.entry_loss.insert(0, str(self.main_app.loss_per_cut))

        # 6) 자동 폰트
        block6 = tk.Frame(container, bg="white"); block6.pack(fill="x", pady=8)
        tk.Label(block6, text="6. 자동 폰트 크기", font=("NanumGothic", 14, "bold"), bg="white").pack(anchor="w")
        self.auto_font_var = tk.BooleanVar(value=self.main_app.auto_font)
        tk.Checkbutton(block6, text="창 크기에 따라 자동 조절", font=("NanumGothic", 13),
                       bg="white", activebackground="white",
                       variable=self.auto_font_var, fg="#666666", padx=6).pack(anchor="w", pady=4)

        # 저장 버튼
        save_btn = tk.Button(self.top, text="저장 + 뒤로가기",
                             font=("NanumGothic", 14, "bold"),
                             bg="#4CAF50", fg="white", activebackground="#45A049",
                             relief="flat", height=2, padx=12, pady=12,
                             command=self.save_and_close)
        save_btn.pack(pady=12, fill="x", padx=14)

    def save_and_close(self):
        new_prefix = self.entry_prefix.get().strip() or "SG94"
        new_round = self.round_var.get()
        try:
            new_font_size = int(self.entry_font_size.get())
        except ValueError:
            new_font_size = 16
        new_hide_mm = self.hide_mm_var.get()
        try:
            new_loss = float(self.entry_loss.get())
        except ValueError:
            new_loss = 15
        new_auto_font = self.auto_font_var.get()

        settings = load_settings()
        settings["prefix"] = new_prefix
        settings["round_result"] = new_round
        settings["result_font_size"] = new_font_size
        settings["hide_mm"] = new_hide_mm
        settings["loss"] = new_loss
        settings["auto_font"] = new_auto_font
        save_settings(settings)

        # 메인 반영
        self.main_app.prefix = new_prefix
        self.main_app.round_result = new_round
        self.main_app.result_font_size = new_font_size
        self.main_app.hide_mm = new_hide_mm
        self.main_app.loss_per_cut = new_loss
        self.main_app.auto_font = new_auto_font

        self.main_app.prefix_label.config(text=f"강번 입력 (접두어 {new_prefix})")
        # auto_font 바인딩 갱신
        try:
            self.main_app.root.unbind("<Configure>")
        except Exception:
            pass
        if new_auto_font:
            self.main_app.root.bind("<Configure>", self.main_app.adjust_font_size)

        self.top.destroy()

if __name__ == "__main__":
    SlabCutCalculator().run()
