BASE_DIR=$(shell pwd)
BUILD_DIR?=$(BASE_DIR)/build
SCRATCH_DIR?=$(BASE_DIR)/scratch
SRC_DIR=$(BASE_DIR)/src

$(shell mkdir -p $(BUILD_DIR))
$(shell mkdir -p $(SCRATCH_DIR))

.PHONY: all
all: $(BUILD_DIR)/buildit_queue.py $(BUILD_DIR)/server.py $(BUILD_DIR)/protect

$(BUILD_DIR)/buildit_queue.py: $(SRC_DIR)/buildit_queue.py
	sed -e s?$$\{BASE_DIR_PLACEHOLDER\}?$(BASE_DIR)?g $< > $@

$(BUILD_DIR)/server.py: $(SRC_DIR)/server.py
	sed -e s?$$\{BASE_DIR_PLACEHOLDER\}?$(BASE_DIR)?g $< > $@


$(BUILD_DIR)/protect: $(SRC_DIR)/protect.c
	gcc $< -o $@ -lseccomp

clean:
	rm -rf build
