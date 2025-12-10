import os
import shutil
import glob
from SCons.Script import Import

Import("env")


def before_build(source, target, env):
    """
    빌드 전에 sdkconfig.h를 생성하고 M5GFX 라이브러리 패치를 적용합니다
    """
    build_dir = env.subst("$BUILD_DIR")
    config_dir = os.path.join(build_dir, "config")
    project_dir = env.subst("$PROJECT_DIR")

    # config 디렉토리 생성
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    # include/sdkconfig.h를 config/sdkconfig.h로 복사
    src_config = os.path.join(project_dir, "include", "sdkconfig.h")
    dst_config = os.path.join(config_dir, "sdkconfig.h")

    if os.path.exists(src_config):
        shutil.copy(src_config, dst_config)
        print(f"✅ Copied sdkconfig.h to {config_dir}")
    else:
        print(f"⚠️ Warning: {src_config} not found")

    # M5GFX 라이브러리에서 esp_log.h를 올바르게 include하도록 패치
    # ESP-IDF v5.x와 Arduino Core 간의 호환성 문제 해결
    lib_deps_dir = os.path.join(project_dir, ".pio", "libdeps", "m5stack-cores3")
    m5gfx_paths = glob.glob(os.path.join(lib_deps_dir, "M5GFX@*"))

    if m5gfx_paths:
        m5gfx_path = m5gfx_paths[0]
        print(f"📦 Found M5GFX library: {m5gfx_path}")

        # esp_log.h 관련 빌드 플래그 처리 안내
        print("✅ Applying ESP-IDF/Arduino log compatibility setup")

        # lgfx_qrcode.h bool 정의 패치 (C++ 전처리로 인한 충돌 방지)
        qrcode_header = os.path.join(
            m5gfx_path, "src", "lgfx", "utility", "lgfx_qrcode.h"
        )
        if os.path.exists(qrcode_header):
            with open(qrcode_header, "r", encoding="utf-8") as f:
                content = f.read()

            old_snippet = (
                "#ifndef __cplusplus\n"
                "typedef unsigned char bool;\n"
                "static const bool false = 0;\n"
                "static const bool true = 1;\n"
                "#endif\n"
            )
            new_snippet = (
                "#if !defined(__cplusplus) && !defined(__bool_true_false_are_defined)\n"
                "typedef unsigned char bool;\n"
                "static const bool false = 0;\n"
                "static const bool true = 1;\n"
                "#endif\n"
            )

            if old_snippet in content and new_snippet not in content:
                content = content.replace(old_snippet, new_snippet, 1)
                with open(qrcode_header, "w", encoding="utf-8") as f:
                    f.write(content)
                print("🩹 Patched lgfx_qrcode.h bool guard for C99 compatibility")
        else:
            print("⚠️ lgfx_qrcode.h not found; skipping bool guard patch")


env.AddPreAction("$BUILD_DIR/${PROGNAME}.elf", before_build)
