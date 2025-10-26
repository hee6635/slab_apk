[app]
title = 후판 계산기
package.name = slabcalc
package.domain = org.local

source.dir = .
source.include_exts = py,kv,png,jpg,ttf,txt
version = 0.1
requirements = python3,kivy
icon.filename = icon.png

orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1

[android]
android.api = 34
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a
