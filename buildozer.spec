[app]
title = 후판 계산기
package.name = slabcalc
package.domain = org.test

# ✅ 누락된 항목 추가
source.dir = .
version = 0.1

# 파일/아이콘
source.include_exts = py,kv,json,png
icon.filename = %(source.dir)s/icon.png   # 아이콘 파일명이 다르면 여기 맞추세요

# 엔트리/의존성
entrypoint = main.py
requirements = python3,kivy

# 표시/화면
orientation = portrait
fullscreen = 0
android.permissions = 

[buildozer]
log_level = 2
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.debug = 1
