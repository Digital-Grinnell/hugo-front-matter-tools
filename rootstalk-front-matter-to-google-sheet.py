# rootstalk-front-matter-to-google-sheet.py
##
## This script, evolved from front-matter-to-csv.py, is designed to read all of the ROOTSTALK .md files in 
## a directory tree and populate a specified .csv file (and dedicated Google Sheet) with the contents/status
## of all the frontmatter found in those Markdown files.

import os
import glob
import pathlib
from datetime import datetime

from queue import Empty
from typing import Dict
import frontmatter
import csv
import gspread
from gspread_formatting import *


branches = [ "develop", "main", "production" ]

fields = {
  "md-path": "Content Path",
  "md-file": "Filename",
  "develop-link": "develop Link",
  "main-link": "main Link",
  "production-link": "Production Link",
  "title": "title",
  "last_modified_at": "last_modified_at",
  "to-do": "to-do List",
  "articleIndex": "articleIndex",
  "description": "description",
  "azure_dir": "azure_dir",
  "obsolete": "Obsolete Front Matter",
  "contributors": "contributors",
  "role": "contributor.role",
  "name": "contributor.name",
  "headshot": "contributor.headshot",
  "caption": "contributor.caption",
  "bio": "contributor.bio",
  "articletype": "articletype",
  "header_image": "header_image",
  "filename": "header_image.filename",
  "alt_text": "header_image.alt_text",
  "tags": "tags",
  "byline": "byline",
  "byline2": "byline2",
  "subtitle": "subtitle",
  "no_leaf_bug": "no_leaf_bug",
  "index": "index",
  "date": "date",
  "draft": "draft"
}

obsolete = ["sidebar", "pid", "issueIndex", "azure_headerimage", "author", "azure_headshot", "authorbio", "headerimage"]

contributor_fields = ["role", "name", "headshot", "caption", "bio"]

header_image_fields = ["filename", "alt_text"]


def truncate(text):
  if type(text) is str:
    if len(text) > 128:
      return text[:125] + "..."
  return text  

def process_contributors(contributors, contributor_fields):
  c_filtered = dict()
  for f in contributor_fields:
    if f in contributors[0].keys():
      c_filtered[f] = contributors[0][f]
    else: 
      c_filtered[f] = ""
  return len(contributors), c_filtered 

def build_link(k, path):
  base_urls = { "develop":"https://thankful-flower-0a2308810.1.azurestaticapps.net/", "main":"https://icy-tree-020380010.azurestaticapps.net/", "production":"https://rootstalk.grinnell.edu/" }
  filename = path.name
  parent = path.parent.name
  grandma = path.parent.parent.name
  if "past" in grandma:
    url = f"{base_urls[k]}{grandma}/{parent}/{filename}".rstrip(" .md")
  else:
    url = f"{base_urls[k]}{parent}/{filename}".rstrip(" .md")
  return f"{url} "   # blank at the end is necessary for links to work properly

def parent_path(path):
  parent = path.parent.name
  grandma = path.parent.parent.name
  if "past" in grandma:
    return f"{grandma}/{parent}"
  else:
    return f"{parent}"

def paste_csv(csv_file, sheet, cell):
  # Lifted from https://stackoverflow.com/a/54231563
  #  csv_file - path to csv file to upload
  #  sheet - a gspread.Spreadsheet object
  #  cell - string giving starting cell, optionally including sheet/tab name
  #    example: 'A1', 'MySheet!C3', etc.
  if '!' in cell:
    (tab_name, cell) = cell.split('!')
    wks = sheet.worksheet(tab_name)
  else:
    wks = sheet.sheet1
  (first_row, first_column) = gspread.utils.a1_to_rowcol(cell)

  with open(csv_file, 'r') as f:
    csv_contents = f.read()
  body = {
    'requests': [{
      'pasteData': {
        "coordinate": {
          "sheetId": wks.id,
          "rowIndex": first_row-1,
          "columnIndex": first_column-1,
        },
        "data": csv_contents,
        "type": 'PASTE_NORMAL',
        "delimiter": ',',
      }
    }]
  }
  return sheet.batch_update(body)
    

# From an example at https://pypi.org/project/gspread-formatting/
def format_google_sheet(sheet, tab_name):
  bold = cellFormat(
    backgroundColor=color(0, 0, 0),
    textFormat=textFormat(bold=True, foregroundColor=color(1, 1, 1)),
    )
  wks = sheet.worksheet(tab_name)
  batch = batch_updater(sheet)
  batch.set_frozen(wks, rows=1)
  batch.format_cell_ranges(wks, [('A1:Z1', bold)])
  return batch.execute()


# From an example at https://pypi.org/project/gspread-formatting/
def highlight_todo_cells(sheet, tab_name):
  wks = sheet.worksheet(tab_name)
  rule = ConditionalFormatRule(
    ranges=[GridRange.from_a1_range('H2:H2000', wks)],
    booleanRule=BooleanRule(
        condition=BooleanCondition('NOT_BLANK'),
        format=CellFormat(textFormat=textFormat(bold=True), backgroundColor=Color(1,0,0))
    )
  )

  rules = get_conditional_format_rules(wks)
  rules.append(rule)
  rules.save()



######################################################################

# Main...
if __name__ == '__main__':
  csv_filename = "front-matter-status.csv"
  
  # Open the .csv file for output
  with open(csv_filename, "w") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fields.values())
    writer.writeheader()

    # Specify the path to be processed...
    filepath = str(pathlib.Path.home()) + "/GitHub/rootstalk/content/**/volume*/*.md"
  
    # Iterate over the working directory tree + subdirectories for all {issue}/{article}.md files
    # Using '*.md' pattern recursively
    for file in glob.glob(filepath, recursive=True):
    
      path = pathlib.PurePath(file)
      article = frontmatter.load(file)
      obsolete = []
      filtered = dict()  # must be sure to initialize this to empty here!

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
    
      # Seed the .csv row with path and filename
      filtered[fields['md-file']] = path.name[:-3]
      filtered[fields['md-path']] = parent_path(path)

      # Build one live link for each code branch and seed the .csv row with them
      for key in branches:
        key_name = f"{key}-link"
        filtered[fields[key_name]] = build_link(key, path)

      # Note any obsolete front matter
      filtered[fields['obsolete']] = obsolete

      writer.writerow(filtered)

  # Ok, done writing the .csv, now copy it to a new tab/worksheet in our Google Sheet
  # Open the Google service account and sheet
  try:
    sa = gspread.service_account()
  except Exception as e:
    print(e)

  try:  
    sh = sa.open("Rootstalk Articles Front Matter")
  except Exception as e:
    print(e)  

  # Make a datestamp to name the new worksheet
  sheet_name = datetime.now().strftime("%Y-%b-%d-%I:%M%p")
  
  # Create the new/empty worksheet
  try:
    worksheet = sh.add_worksheet(title=sheet_name, rows=1, cols=1)
  except Exception as e:
    print(e)  

  # Call our function to write the new Google Sheet worksheet
  try:
    paste_csv(csv_filename, sh, sheet_name + "!A1")
  except Exception as e:
    print(e)

  # Call our format function to set the format of the new sheet
  try:
    format_google_sheet(sh, sheet_name)
  except Exception as e:
    print(e)

  # Call our function to set conditional formatting
  try:
    highlight_todo_cells(sh, sheet_name)
  except Exception as e:
    print(e)
