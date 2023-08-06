SOURCE_DIR=src
TARGET_DIR=build

all: build
build: $(SOURCE_DIR)/**/*
	python build_html.py -i $(SOURCE_DIR) -o $(TARGET_DIR)
	cp $(SOURCE_DIR)/images $(TARGET_DIR)/ -r
	cp $(SOURCE_DIR)/static $(TARGET_DIR)/ -r
	cp $(SOURCE_DIR)/favicon.ico $(TARGET_DIR)/
	cp $(SOURCE_DIR)/.htaccess $(TARGET_DIR)/

clean:
	rm -rf $(TARGET_DIR)
	rm __pycache__

.PHONY: all build clean