cd buildit
make -C deps/libelfin

make BUILD_DIR=$(pwd)/build -j$(nproc)
make BUILD_DIR=$(pwd)/build_var_names LIBUNWIND_PATH=/libunwind/install/usr/local RECOVER_VAR_NAMES=1 -j$(nproc) TRACER_USE_LIBUNWIND=1

