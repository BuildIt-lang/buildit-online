BASE_DIR=$(shell pwd)
BUILD_DIR?=$(BASE_DIR)/build
SCRATCH_DIR?=$(BASE_DIR)/scratch
SCRATCH_DIR_VNAMES?=$(BASE_DIR)/scratch_var_names

SRC_DIR=$(BASE_DIR)/src
SUPPORT_DIR=$(BASE_DIR)/support

$(shell mkdir -p $(BUILD_DIR))
$(shell mkdir -p $(SCRATCH_DIR))
$(shell mkdir -p $(SCRATCH_DIR_VNAMES))

.PHONY: all
all: $(BUILD_DIR)/buildit_queue.py $(BUILD_DIR)/server.py $(BUILD_DIR)/protect $(BUILD_DIR)/open.o $(BUILD_DIR)/dladdr.o

$(BUILD_DIR)/buildit_queue.py: $(SRC_DIR)/buildit_queue.py
	sed -e s?$$\{BASE_DIR_PLACEHOLDER\}?$(BASE_DIR)?g $< > $@

$(BUILD_DIR)/server.py: $(SRC_DIR)/server.py
	sed -e s?$$\{BASE_DIR_PLACEHOLDER\}?$(BASE_DIR)?g $< > $@


$(BUILD_DIR)/protect: $(SRC_DIR)/protect.c
	gcc $< -o $@ -lseccomp

$(BUILD_DIR)/open.o: $(SUPPORT_DIR)/open.c
	gcc $< -o $@ -c

$(BUILD_DIR)/dladdr.o: $(SUPPORT_DIR)/dladdr.c
	gcc $< -o $@ -c

clean:
	rm -rf build
