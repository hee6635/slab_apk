# sanity_main.py 내용 (main.py에 그대로 붙여넣어 빌드)
from kivy.app import App
from kivy.uix.label import Label
from kivy.utils import platform
import os, time

class SanityApp(App):
    def build(self):
        # 시작 로그 파일 남기기
        try:
            p = os.path.join(self.user_data_dir, "sanity_ok.txt")
            with open(p, "w", encoding="utf-8") as f:
                f.write("started at %s" % time.time())
        except Exception as e:
            pass
        return Label(text="HELLO KIVY")

if __name__ == "__main__":
    SanityApp().run()
