# rootstalk-google-sheet-to-front-matter.py
##
## This script, evolved from rootstalk-front-matter-to-google-sheet.py, is designed to read all editable_fields
## gcells from an "Update" worksheet/tab of our dedicated Google Sheet to update the front matter of 
## corresponding ROOTSTALK .md files as identified in the required_fields.

import os
import glob
import pathlib
import sys
import csv
import tempfile
from datetime import datetime

from queue import Empty
from typing import Dict
import frontmatter
import gspread as gs

required_fields = {
  "md-path": "Content Path",
  "md-file": "Filename"
}

editable_fields = {
  "title": "title",
  "to-do": "to-do List",
  "articleIndex": "articleIndex",
  "description": "description",
  "articletype": "articletype",
  "tags": "tags",
  "byline": "byline",
  "byline2": "byline2",
  "subtitle": "subtitle",
  "no_leaf_bug": "no_leaf_bug"
}

def process_record(rec, path):
  try:
    post = frontmatter.load(path)
  except Exception as e:
    print(e)

  for key,value in rec.items():
    if key in editable_fields:
      post[key] = value

  # now dump the frontmatter post back into the file
  try:
    md = open(path, "w")
    md.write(frontmatter.dumps(post))
    md.close
  except Exception as e:
    print(e)
  return

######################################################################

# Main...
if __name__ == '__main__':

  # Open the Google service account and sheet
  try:
    sa = gs.service_account()
  except Exception as e:
    print(e)

  try:  
    sh = sa.open("Rootstalk Articles Front Matter")
  except Exception as e:
    print(e)  

  # Read all worksheets from the Google Sheet, and find the sheet named "Update"
  sheets = sh.worksheets()
  for ws in sheets:
    title = ws.title
    # Found the "Update" sheet
    if (title == "Update"):

      # Generate a temporary .csv of the worksheet 
      # per https://community.esri.com/t5/python-questions/how-to-convert-a-google-spreadsheet-to-a-csv-file/td-p/452722
      with open('temp.csv', 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerows(ws.get_all_values())

      # Read the temporary .csv into a dict
      with open('temp.csv', 'r') as data:
        for record in csv.DictReader(data):

          # worksheet record now in dict form, process it for updates
          md_path = str(pathlib.Path.home()) + "/GitHub/rootstalk/content/" + record['Content Path'] + "/" + record['Filename'] + ".md"
          if os.path.exists(md_path):
            process_record(record, md_path)
          else:
            print(f"Warning: File '{md_path}' does not exist so it's record has been skipped.")

  exit()
