CC ?= cc
BASE = -std=c11 -Wall -Wextra -Werror -Ibuild -Isrc -Itests -ffp-contract=off
SRC = src/plugin.c src/repeat.c
WRAPS = malloc calloc realloc free pthread_mutex_lock pthread_mutex_trylock pthread_mutex_unlock pthread_join open fopen read write
WRAPFLAGS = $(foreach f,$(WRAPS),-Wl,--wrap=$(f))
SAN = -fsanitize=address,undefined -fno-omit-frame-pointer -fno-pie -no-pie
.PHONY: all native test sanitize skin arm package clean
all: native skin
build/params.h: ui/params.json tools/gen_params.py
	python3 tools/gen_params.py
build/beatrepeat-native.so: $(SRC) src/repeat.h src/vst2_abi.h build/params.h
	$(CC) $(BASE) -O2 -fPIC -fvisibility=hidden -shared $(SRC) -lm -pthread -Wl,--no-undefined -o $@
native: build/beatrepeat-native.so
build/shadow_art: vendor/mpc/tools/shadow_art.c vendor/mpc/tools/vendor/force-shadow/tools/render_conf_preview.c vendor/mpc/tools/vendor/force-shadow/tools/stb_truetype.h vendor/mpc/tools/vendor/force-shadow/src/font8x8.h
	mkdir -p build
	$(CC) -O2 -Ivendor/mpc/tools/vendor/force-shadow/tools $< -lm -o $@
skin: native build/shadow_art
	python3 tools/build_skin.py
	python3 tests/test_skin.py
build/test: $(SRC) src/repeat.h src/vst2_abi.h tests/test.c tests/oracle.h tests/crossfade4_128.h vendor/core/beatrepeat.h build/params.h
	$(CC) $(BASE) -O2 -g $(SRC) tests/test.c $(WRAPFLAGS) -lm -pthread -o $@
test: native build/test
	./build/test
	python3 tests/test_shared.py
sanitize: build/params.h
	$(CC) $(BASE) -O1 -g $(SAN) $(SRC) tests/test.c $(WRAPFLAGS) -lm -pthread -o build/test-sanitize
	ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 ./build/test-sanitize
arm: build/params.h
	tools/build_arm.sh
package: all arm
	python3 tools/package.py
	python3 tests/test_package.py
clean:
	rm -rf build
