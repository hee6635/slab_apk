[app]
title = 후판 계산기
package.name = slabcalc
package.domain = org.test

# 포함할 파일
source.include_exts = py,kv,json,png

# 아이콘
icon.filename = %(source.dir)s/icon.png

# 실행 파일
entrypoint = main.py

# 파이썬 패키지 (표준라이브러리는 불필요)
requirements = python3,kivy

# 화면/표시
orientation = portrait
fullscreen = 0

# 권한 (필요 없음)
android.permissions = 

[buildozer]
log_level = 2

# Android 빌드 설정 (GitHub Actions에서 docker 이미지가 알아서 맞춰줌)
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.debug = 1
