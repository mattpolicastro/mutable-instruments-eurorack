# Builds one Plaits Lab package into a VCV Rack 2 module for auditioning.
#
#   make RACK_DIR=<Rack-SDK> [PACKAGE=<package directory | catalog id>]
#   make RACK_DIR=<Rack-SDK> dist     # a .vcvplugin to drop into Rack
#   make RACK_DIR=<Rack-SDK> test     # Rack-free checks of the voice
RACK_DIR ?= ../Rack-SDK
PACKAGE ?= ../packages/community/phreak
PYTHON ?= python3

# The SDK resolves the package's sources, engine class and post-processing.
$(shell mkdir -p build && $(PYTHON) sources.py "$(PACKAGE)" > build/package.mk)
include build/package.mk
ifeq ($(PLAITS_LAB_SOURCES),)
$(error sources.py could not resolve PACKAGE=$(PACKAGE))
endif

FLAGS += -DTEST -D_USE_MATH_DEFINES $(PLAITS_LAB_FLAGS)
SOURCES += src/plugin.cpp src/lab_voice.cc $(PLAITS_LAB_SOURCES)
DISTRIBUTABLES += res LICENSE

include $(RACK_DIR)/plugin.mk

test: build/test_lab_voice
	build/test_lab_voice

build/test_lab_voice: tests/test_lab_voice.cc src/lab_voice.cc $(PLAITS_LAB_SOURCES)
	$(CXX) -std=c++11 -O2 -DTEST -D_USE_MATH_DEFINES $(PLAITS_LAB_FLAGS) -Isrc $^ -o $@

.PHONY: test
