"""Converts [[roamlinks]] to become relative [Markdown](../Links)

Code adapted from https://github.com/Jackiexiao/mkdocs-roamlinks-plugin
    NOTE: not using any of the MKDocs functionality, just the roamlink mods

Notes on path conversions (for github):
* Relative paths work, absolute from repo root do not
* Spaces in file names need to be converted to `%20`
* Capitalization matching is required

TODOs:
- [ ] Skip Template files

"""

import re
import os
from pathlib import Path
import urllib.parse
from functools import partial

# For Regex, match groups are:
#       0: Whole roamlike link e.g. [[filename#title|alias]]
#       1: Whole roamlike link e.g. filename#title|alias
#       2: filename
#       3: #title
#       4: |alias
ROAMLINK_RE = r'\[\[(([^\]#\|]*)(#[^\|\]]+)*(\|[^\]]*)*)\]\]'

BASE_PATH = Path(__file__).parent / 'Gygax75'
PATH_BLACKLIST = [BASE_PATH / 'templates']

def simplify(filename):
    """ ignore - _ and space different, replace .md to '' so it will match .md file,
    if you want to link to png, make sure you filename contain suffix .png, same for other files
    but if you want to link to markdown, you don't need suffix .md """
    return re.sub(r"[\-_ ]", "", filename.lower()).replace(".md", "")


def gfm_anchor(title):
    """Convert to gfw title / anchor
    see: https://gist.github.com/asabaylus/3071099#gistcomment-1593627"""
    if title:
        title = title.strip().lower()
        title = re.sub(r'[^\w\u4e00-\u9fff\- ]', "", title)
        title = re.sub(r' +', "-", title)
        return title

    return ""


def convert_roamlinks(match, root_path, orig_path, all_paths):
    """


    Args:
        match: re `match` object
        file_path:
        all_paths:
    """
    # Name of the markdown file
    whole_link = match.group(0)
    filename = match.group(2).strip() if match.group(2) else ""
    title = match.group(3).strip() if match.group(3) else ""
    format_title = gfm_anchor(title)
    alias = match.group(4).strip('|') if match.group(4) else ""

    # Walk through all files in docs directory to find a matching file
    rel_link_url = ''
    if filename:
        for path in all_paths:
            # If we have a match, create the relative path from linker to the link
            if simplify(path.name) == simplify(filename):

                # Constructing relative path from the root to the desired file
                rel_link_url = (Path(os.path.relpath(root_path,
                                                     orig_path.parent)) /
                                '..' /
                                path)
                if title:
                    rel_link_url = rel_link_url + '#' + format_title
                continue

        if rel_link_url == '':
            #print(filename)
            return whole_link.replace('[', '*').replace(']', '*')
    else:
        rel_link_url = '#' + format_title

    rel_link_url = str(rel_link_url)

    # Construct the return link
    # Windows escapes "\" unintentionally, and it creates incorrect links, so need to replace with "/"
    rel_link_url = rel_link_url.replace("\\", "/")

    # Handle "bad" URL characters (e.g., " " --> "%20")
    rel_link_url = urllib.parse.quote(rel_link_url)

    if filename:
        if alias:
            link = f'[{alias}]({rel_link_url})'
        else:
            link = f'[{filename+title}]({rel_link_url})'
    else:
        if alias:
            link = f'[{alias}]({rel_link_url})'
        else:
            link = f'[{title}]({rel_link_url})'

    return link


def main(root_path=BASE_PATH):
    # Get list of all files
    all_paths = []
    for root, _, files in os.walk(root_path):
        root = Path(root)
        if root.name == '.obsidian':
            continue
        for name in files:
            all_paths.append(root / name)

    print(all_paths)

    # root_path = Path(__file__).parent
    # #target_file = root_path / 'adventure-p' / 'Adventure Overview.md'
    #target_file = root_path / 'Session reports' / 'Session 1.md'
    #print(target_file, root_path)
    for target_file in all_paths:
        if (not target_file.name.endswith('.md') or
            target_file.parent in PATH_BLACKLIST):
            continue

    # Read in file contents
        with open(target_file) as fh:
            contents = fh.read()

        # Update content
        new_contents = re.sub(ROAMLINK_RE,
                              partial(convert_roamlinks,
                                      root_path=root_path,
                                      orig_path=target_file,
                                      all_paths=all_paths),
                              contents)

        print(new_contents)

        # Write to temp file, then write temp_file over original file
        temp_file = target_file.parent / ('updated_links-' + target_file.name)
        temp_file.write_text(new_contents)
        temp_file.replace(target_file)

if __name__ == '__main__':
    main()
