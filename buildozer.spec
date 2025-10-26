[app]
title = 후판 계산기
package.name = slabcalc
package.domain = org.local

# 프로젝트 루트에서 빌드
source.dir = .

# 포함 확장자 (이미지/폰트/텍스트 포함)
source.include_exts = py,kv,png,jpg,ttf,txt

# 앱 버전
version = 0.1

# 필수 의존성 (최소)
requirements = python3,kivy

# 아이콘 (레포 루트에 icon.png 있어야 함)
icon.filename = icon.png

[buildozer]
log_level = 2
warn_on_root = 1

[android]
# 당신이 성공했던 조합 유지
android.api = 34
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a
