# front matter-to-google-sheet.py
## This script is designed to read all of the .md files in a directory tree, 
## and populate a specified Google Sheet with the contents/status of all the frontmatter found 
## in those Markdown files.

import os
import glob
import pathlib
from datetime import datetime

from queue import Empty
from typing import Dict
import frontmatter
import gspread

fields = {
  "md-path": "Markdown Path",
  "md-file": "Markdown Filename",
  "dev-link": "Live DEV Link",
  "title": "title",
  "articleIndex": "articleIndex",
  "index": "index",
  "description": "description",
  "date": "date",
  "draft": "draft",
  "contributors": "contributors",
  "role": "contributor.role",
  "name": "contributor.name",
  "headshot": "contributor.headshot",
  "caption": "contributor.caption",
  "bio": "contributor.bio",
  "articletype": "articletype",
  "azure_dir": "azure_dir",
  "header_image": "header_image",
  "filename": "header_image.filename",
  "alt_text": "header_image.alt_text",
  "tags": "tags",
  "byline": "byline",
  "subtitle": "subtitle",
  "no_leaf_bug": "no_leaf_bug",
  "obsolete": "Obsolete Front Matter"
}

obsolete = ["sidebar", "pid", "issueIndex", "azure_headerimage", "author", "azure_headshot", "authorbio", "headerimage"]

contributor_fields = ["role", "name", "headshot", "caption", "bio"]

header_image_fields = ["filename", "alt_text"]


def truncate(text):
  if type(text) is str:
    if len(text) > 20:
      return text[:17] + "..."
  return text  

def process_contributors(contributors, contributor_fields):
  c_filtered = dict()
  for f in contributor_fields:
    if f in contributors[0].keys():
      c_filtered[f] = contributors[0][f]
    else:
      c_filtered[f] = ""
  return len(contributors), c_filtered 

def build_link(path):
  base_url = "https://icy-tree-020380010.azurestaticapps.net/"
  filename = path.name
  parent = path.parent.name
  grandma = path.parent.parent.name
  if "past" in grandma:
    url = f"{base_url}{grandma}/{parent}/{filename}".rstrip(" .md")
  else:
    url = f"{base_url}{parent}/{filename}".rstrip(" .md")
  return f"{url} "    # blank after the address is required to get a proper link!               

######################################################################

# Main...
if __name__ == '__main__':
  
  # Open the Google service account and sheet
  try:
    sa = gspread.service_account()
  except Exception as e:
    print(e)

  try:  
    sh = sa.open("Rootstalk Articles Front Matter")
  except Exception as e:
    print(e)  

  # Make a datestamp to name the new worksheet, and open the new sheet
  sheet_name = datetime.now().strftime("%Y-%b-%d-%H%M")
  try:
    worksheet = sh.add_worksheet(title=sheet_name, rows=1, cols=len(fields))
  except Exception as e:
    print(e)
  
  # Write `fields` values as heading row 1
  headings = list(fields.values())
  try:
    worksheet.append_row(headings)
  except Exception as e:
    print(e)

  # Specify the path to be processed...
  filepath = str(pathlib.Path.home()) + "/GitHub/rootstalk/content/**/volume*/*.md"
  
  # Iterate over the working directory tree + subdirectories for all {issue}/{article}.md files
  # Using '*.md' pattern recursively
  for file in glob.glob(filepath, recursive=True):

    path = pathlib.PurePath(file)
    article = frontmatter.load(file)
    obsolete = []
    filtered = dict.fromkeys(fields.keys(), "")   # must be sure to initialize this to empty here!

    # Loop on each top-level element of the article's front matter 
    for key in article.metadata:

      # Found a key that we didn't expect... warning
      if key not in fields.keys():
        assert key not in obsolete, "Error: Front matter key '{key}' does not exist in ANY list!"

        print(f"Warning: Front matter key '{key}' is obselete. This article needs to be updated!")
        obsolete.append(key)
        
      # We have an expected top-level key and value
      else:
        value = article.metadata[key]

        # If we have a list...
        if type(value) is list:
          if key == "contributors":
            c = value[0]
            for f in contributor_fields:
              if f in c.keys():
                filtered[fields[f]] = truncate(c[f])
              else:
                filtered[fields[f]] = ""
            value = len(value)

          # Just a list, nothing special  
          else:  
            value = ",".join(value)

        # If we have a dict...
        if type(value) is dict:
          if key == "header_image":
            for f in header_image_fields:
              if f in value.keys():
                filtered[fields[f]] = truncate(value[f])
              else:
                filtered[fields[f]] = ""
            value = True
          else:
            print(f"Warning: Unexpected front matter dict {key} found!")

        filtered[fields[key]] = truncate(value)
    
    # Seed the row with path and filename
    filtered[fields['md-file']] = path.name
    filtered[fields['md-path']] = path.parent.name

    # Build a live link and seed the row with it
    filtered[fields['dev-link']] = build_link(path)

    # Note any obsolete front matter
    filtered[fields['obsolete']] = obsolete

    # Break the filtered dict into a list of values
    row = list(filtered.values())

    # Append the worksheet row
    try:
      worksheet.append_row(row)
    except Exception as e:
      print(e)

