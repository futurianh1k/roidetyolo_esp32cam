import os
import shutil
from SCons.Script import Import

Import("env")

def before_build(source, target, env):
    """
    빌드 전에 sdkconfig.h를 생성합니다
    """
    build_dir = env.subst("$BUILD_DIR")
    config_dir = os.path.join(build_dir, "config")

    # config 디렉토리 생성
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    # include/sdkconfig.h를 config/sdkconfig.h로 복사
    src_config = os.path.join(env.subst("$PROJECT_DIR"), "include", "sdkconfig.h")
    dst_config = os.path.join(config_dir, "sdkconfig.h")

    if os.path.exists(src_config):
        shutil.copy(src_config, dst_config)
        print(f"✅ Copied sdkconfig.h to {config_dir}")
    else:
        print(f"⚠️ Warning: {src_config} not found")

env.AddPreAction("$BUILD_DIR/${PROGNAME}.elf", before_build)
