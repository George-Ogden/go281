SOURCE_DIR=src
TARGET_DIR=build

all: build
build: $(SOURCE_DIR)/**/*
	python build_html.py -i $(SOURCE_DIR) -o $(TARGET_DIR)
	cp $(SOURCE_DIR)/images $(TARGET_DIR)/images -r

clean:
	rm -rf $(TARGET_DIR)
	rm __pycache__

.PHONY: all build clean