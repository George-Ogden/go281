from pybtex.textutils import abbreviate
from pybtex.database import parse_file
from bs4 import BeautifulSoup
from glob import glob

from typing import List, Optional

import argparse
import os
import re

IGNORED = {"calls"}
def parse_args():
    # parse input and output directories
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-dir", required=True)
    parser.add_argument("-o", "--output-dir", required=True)
    parser.add_argument("-u", "--url", default="https://go281.user.srcf.net")
    return parser.parse_args()


def complete_citations(template: str, directory: str) -> str:
    # check if citations.bib exists
    bibtex_file = os.path.join(directory, "citations.bib")
    if not os.path.exists(bibtex_file):
        return template

    # parse bibtex file
    references = parse_file(bibtex_file)

    # convert all placeholders in the document to citations
    citations = []
    for match in re.finditer(r"\[\[(.*?)\]\]", template):
        citation = match.group(1)
        # ignore bibliography placeholder
        if citation == "bibliography":
            continue

        # only fill in each citation once
        if not citation in citations:
            reference = references.entries[citation]
            # convert authors to readable format
            authors = reference.persons["author"]
            author = " ".join(
                name.render_as("html") for name in authors[0].rich_last_names
            )
            if len(authors) > 1:
                author += " et al."

            year = reference.fields["year"]
            # add citation to main text
            template = template.replace(
                match.group(0),
                f" (<a onclick=\"document.getElementById('bib-{citation}').scrollIntoView()\" class=\"text-decoration-none\">{author}, {year}</a>)",
            )

            citations.append(citation)

    # generate bibliography
    bibliography = ""
    for citation in citations + sorted(
        list(set(references.entries.keys()).difference(citations))
    ):
        # fill out fields
        reference = references.entries[citation]
        authors = reference.persons["author"]
        # convert authors to readable format
        author = ", ".join(
            [
                abbreviate(
                    " ".join(name.render_as("html") for name in author.rich_first_names)
                )
                + " ".join(name.render_as("html") for name in author.rich_last_names)
                for author in authors
            ][:10]
        )
        if len(authors) > 10:
            author += " et al."
        year = reference.fields["year"]
        title = reference.fields["title"]
        if (
            "eprinttype" in reference.fields
            and reference.fields["eprinttype"] == "arXiv"
        ):
            # add link to arXiv
            journal = "arXiv preprint arXiv:{eprint}".format(**reference.fields)
        elif "journal" in reference.fields:
            journal = reference.fields["journal"]
        elif "booktitle" in reference.fields:
            journal = reference.fields["booktitle"]
        else:
            raise ValueError(f"Unknown journal type for {citation}")
        # add line to bibliography
        bibliography += f"<p id =\"bib-{citation}\">{author}. {title}. <i>{journal}</i>, {year}."

    # add bibliography to template
    template = template.replace("[[bibliography]]", bibliography)

    # delete references
    del references
    return template


def complete_figures(template: str) -> str:
    soup = BeautifulSoup(template, "html.parser")
    figures = []
    if not soup.find("figure"):
        return template
    for figure in soup.find_all("figure"):
        id = figure["id"]
        figures.append(id)
        # add figure to caption
        caption = figure.find("figcaption")
        caption.string = f"Figure {len(figures)} | " + caption.get_text()
    html = str(soup)
    for i, figure in enumerate(figures):
        prefix, figure = figure.split("-", 1)
        # add figure to main text
        html = html.replace(
            f"[({figure})]",
            f"(<a onclick=\"document.getElementById('{prefix}-{figure}').scrollIntoView()\" class=\"text-decoration-none\">Figure {i+1}</a>)"
        )
    return html


def get_template(directory: str, file=None) -> str:
    if file is None:
        file = "template.html"
    os.path.relpath(directory, start=INPUT_DIR)
    # recursively search for template file
    try:
        with open(os.path.join(directory, file), "r") as f:
            template = f.read()
    except FileNotFoundError:
        return get_template(os.path.split(directory)[0], file)
    template = complete_figures(template)
    template = complete_citations(template, directory)
    return template


def build_template(directory: str, file: Optional[str] = None) -> str:
    template = get_template(directory, file)
    for match in re.finditer(r"{{(.*?)}}", template):
        # recursively build template
        template = template.replace(
            match.group(0), build_template(directory, match.group(1) + ".html")
        )
    return template


def generate_directory(directory: str) -> List[str]:
    pages = []
    # recursively generate files in directory
    for root, dirs, files in os.walk(directory):
        if not glob(os.path.join(root, "*.html")):
            continue
        relative_path = os.path.relpath(root, start=INPUT_DIR)
        target_dir = os.path.join(OUTPUT_DIR, relative_path)
        os.makedirs(target_dir, exist_ok=True)
        file = build_template(root)
        with open(
            os.path.join(target_dir, "index.html"),
            "w",
        ) as f:
            f.write(file)
        pages.append(relative_path)
        for dir in dirs:
            pages.extend(generate_directory(dir))
    return pages


def main(args: argparse.Namespace):
    pages = generate_directory(args.input_dir)
    with open(os.path.join(OUTPUT_DIR, "sitemap.txt"), "w") as f:
        # first page is the root (".")
        f.write(f"{args.url}\n")
        for page in pages[1:]:
            if page not in IGNORED:
                f.write(f"{args.url}/{page}/\n")


if __name__ == "__main__":
    args = parse_args()
    INPUT_DIR = args.input_dir
    OUTPUT_DIR = args.output_dir
    main(args)
