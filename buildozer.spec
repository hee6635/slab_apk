[app]
title = 후판 계산기
package.name = slabcalc
package.domain = org.local

source.dir = .
# 현재 레포에 있는 확장자들 모두 포함
source.include_exts = py,kv,png,jpg,ttf,txt,json

# 앱 버전
version = 0.1

# 재현성을 위해 Kivy 버전 고정 권장
requirements = python3, kivy==2.3.0

# 아이콘 파일 실제로 있으므로 사용
icon.filename = icon.png

orientation = portrait
fullscreen = 0

# Kivy 기본 폰트 대신 NanumGothic.ttf를 코드에서 직접 지정하셨으니 별도 설정 불필요

[buildozer]
log_level = 2
warn_on_root = 1

[android]
# SDK 34
android.api = 34
# 최소/NDK API 일치 (arm64에서 안정)
android.minapi = 24
android.ndk_api = 24

# 64비트 단일 타겟
android.archs = arm64-v8a

# API 33+에서는 외부저장소 권한이 사실상 폐지됨.
# 파일 접근 안 쓰면 비워두는 게 경고 줄이는 데 유리
android.permissions =
