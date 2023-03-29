from glob import glob
import argparse
import os
import re


def parse_args():
    # parse input and output directories
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-dir", required=True)
    parser.add_argument("-o", "--output-dir", required=True)
    return parser.parse_args()


def get_template(directory, file=None) -> str:
    if file is None:
        file = "template.html"
    os.path.relpath(directory, start=INPUT_DIR)
    # recursively search for template file
    try:
        with open(os.path.join(directory, file), "r") as f:
            template = f.read()
    except FileNotFoundError:
        return get_template(os.path.split(directory)[0], file)
    return template


def build_template(directory, file=None) -> str:
    template = get_template(directory, file)
    for match in re.finditer(r"{{(.*?)}}", template):
        # recursively build template
        template = template.replace(
            match.group(0), build_template(directory, match.group(1) + ".html")
        )
    return template


def generate_directory(directory):
    # recursively generate files in directory
    for root, dirs, files in os.walk(directory):
        if not glob(os.path.join(root, "*.html")):
            continue
        target_dir = os.path.join(OUTPUT_DIR, os.path.relpath(root, start=INPUT_DIR))
        os.makedirs(target_dir, exist_ok=True)
        file = build_template(root)
        with open(
            os.path.join(
                OUTPUT_DIR, os.path.relpath(root, start=INPUT_DIR), "index.html"
            ),
            "w",
        ) as f:
            f.write(file)
        for dir in dirs:
            generate_directory(dir)


def main(args):
    generate_directory(args.input_dir)


if __name__ == "__main__":
    args = parse_args()
    INPUT_DIR = args.input_dir
    OUTPUT_DIR = args.output_dir
    main(args)
