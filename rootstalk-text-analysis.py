# rootstalk-text-analysis.py
##
## This script, evolved from rootstalk-front-matter-to-google-sheet.py, is designed to read all of the ROOTSTALK .md files in 
## a directory tree, parse the body text (everything after the front matter) and produce a CSV file with the word count for 
## each individual term encountered.

import os
import glob
import pathlib
import re
import snowballstemmer

from datetime import datetime
from collections import Counter
from stop_words import get_stop_words

from queue import Empty
from typing import Dict
import frontmatter
import csv
import gspread as gs
import gspread_formatting as gsf


fields = ["term", "count", "num_files"]
stops = get_stop_words('en')

# def truncate(text):
#   if type(text) is str:
#     if len(text) > 132:
#       return text[:129] + "..."
#   return text  

# def build_link(k, path):
#   base_urls = { "develop":"https://yellow-wave-0e513e510.3.azurestaticapps.net/", "main":"https://yellow-wave-0e513e510.3.azurestaticapps.net/", "production":"https://rootstalk.grinnell.edu/" }
#   filename = path.name
#   parent = path.parent.name
#   grandma = path.parent.parent.name
#   if (filename == "_index.md"):
#     filename = ""
#   else:
#     filename = filename[:-3]    # remove .md  
#   if "past" in grandma:
#     url = f"{base_urls[k]}{grandma}/{parent}/{filename}"
#   else:
#     url = f"{base_urls[k]}{parent}/{filename}"
#   return f"{url} "   # blank at the end is necessary for links to work properly

# def parent_path(path):
#   parent = path.parent.name
#   grandma = path.parent.parent.name
#   if "past" in grandma:
#     return f"{grandma}/{parent}"
#   else:
#     return f"{parent}"

# # Lifted from https://stackoverflow.com/a/54231563
# #  csv_file - path to csv file to upload
# #  sheet - a gspread.Spreadsheet object
# #  cell - string giving starting cell, optionally including sheet/tab name
# #    example: 'A1', 'MySheet!C3', etc.
# def paste_csv(csv_file, sheet, cell):
#   if '!' in cell:
#     (tab_name, cell) = cell.split('!')
#     wks = sheet.worksheet(tab_name)
#   else:
#     wks = sheet.sheet1
#   (first_row, first_column) = gs.utils.a1_to_rowcol(cell)

#   with open(csv_file, 'r') as f:
#     csv_contents = f.read()
#   body = {
#     'requests': [{
#       'pasteData': {
#         "coordinate": {
#           "sheetId": wks.id,
#           "rowIndex": first_row-1,
#           "columnIndex": first_column-1,
#         },
#         "data": csv_contents,
#         "type": 'PASTE_NORMAL',
#         "delimiter": ',',
#       }
#     }]
#   }
#   return sheet.batch_update(body)
    
# # From an example at https://pypi.org/project/gspread-formatting/
# def format_google_sheet(sheet, tab_name):
#   bold = gsf.cellFormat(
#     backgroundColor=gsf.color(0.9, 0.9, 0.9),
#     textFormat=gsf.textFormat(bold=True, foregroundColor=gsf.color(0, 0, 0)),
#     )
#   wks = sheet.worksheet(tab_name)
#   batch = gsf.batch_updater(sheet)
#   batch.set_frozen(wks, rows=1)
#   batch.format_cell_ranges(wks, [('A1:Z1', bold)])
#   return batch.execute()

# # From a blog post at https://stackoverflow.com/questions/50938274/sort-a-spread-sheet-via-gspread
# def sort_google_sheet(sheet, tab_name):
#   wks = sheet.worksheet(tab_name)
#   wks.sort((9, 'asc'))   # sort first by articleIndex
#   wks.sort((1, 'asc'))   # now sort by Content Path
#   return

# # From an example at https://pypi.org/project/gspread-formatting/
# def highlight_todo_cells(sheet, tab_name):
#   wks = sheet.worksheet(tab_name)
#   rule = gsf.ConditionalFormatRule(
#     ranges=[gsf.GridRange.from_a1_range('H2:H2000', wks)],
#     booleanRule=gsf.BooleanRule(
#         condition=gsf.BooleanCondition('NOT_BLANK'),
#         format=gsf.cellFormat(textFormat=gsf.textFormat(bold=True), backgroundColor=gsf.Color(1,1,0))
#     )
#   )

## The following functions from https://www.geeksforgeeks.org/text-analysis-in-python-3/ 

# Counts word frequency
def count_words(text):				
	skips = [".", ",", ":", ";", "'", '"', "”", "“", "‘"]
	for ch in skips:
		text = text.replace(ch, "")
	word_counts = {}
	for word in text.split(" "):
		if word in word_counts:
			word_counts[word]+= 1
		else:
			word_counts[word]= 1
	return word_counts

# Count snowball-stemmed word frequency
def snowball_count_words(the_ball):				
	word_counts = {}
	for word in the_ball:
		if word in word_counts:
			word_counts[word] += 1
		else:
			word_counts[word] = 1
	return word_counts

# Counts word frequency using Counter from collections
def count_words_fast(text):	
	text = text.lower()
	skips = [".", ", ", ":", ";", "'", '"', "?", "!", "“"]
	for ch in skips:
		text = text.replace(ch, "")
	word_counts = Counter(text.split(" "))
	return word_counts

	# >>>count_words_fast(text) You can check the function


######################################################################

# Main...
if __name__ == '__main__':
  csv_filename = "text-analysis.csv"
  stemmer = snowballstemmer.stemmer('english');

  terms = dict( )
  
  # Specify the path to be processed...
  filepath = str(pathlib.Path.home()) + "/GitHub/npm-rootstalk/content/**/volume*/*.md"
  
  # Iterate over the working directory tree + subdirectories for all {issue}/{article}.md files
  # Using '*.md' pattern recursively
  for file in glob.glob(filepath, recursive=True):
    
    path = pathlib.PurePath(file)
    article = frontmatter.load(file)
    text = re.sub( r'{{%.+%}}', " ", article.content ).replace("\n", " ").replace("  ", " ").lower()   

    # counts = count_words(text)
    ball = stemmer.stemWords(text.split());
    counts = snowball_count_words(ball)
			
    for term in counts:
      if term not in stops and len(term) < 20:
        if term in terms.keys( ):
          terms[term] = terms[term] + counts[term] + 0.001  
        else:
          terms[term] = counts[term] + 0.001

  # Open the .csv file for output
  with open(csv_filename, "w", newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fields)
    writer.writeheader()    
    sorted_by_count = sorted(terms.items(), key=lambda x:x[1], reverse=True)
    dict_sorted = dict(sorted_by_count)
    for key, value in dict_sorted.items():
      count = int(value)
      frac = value - count
      n = frac * 1000.
      num_files = int(round(n))
      writer.writerow( {'term': key, 'count': count, 'num_files': num_files} )
    csvfile.close( )

					








  #     # Loop on each top-level element of the article's front matter 
  #     for key in article.body:

  #       # Found a key that we didn't expect... warning
  #       if key not in fields.keys():
  #         assert key not in obsolete, "Error: Front matter key '{key}' does not exist in ANY list!"

  #         print(f"Warning: Front matter key '{key}' is obselete. This article needs to be updated!")
  #         obsolete.append(key)
        
  #       # We have an expected top-level key and value
  #       else:
  #         value = article.metadata[key]

  #         # If we have a list...
  #         if type(value) is list:
  #           if key == "contributors":
  #             c = value[0]
  #             for f in contributor_fields:
  #               if f in c.keys():
  #                 filtered[fields[f]] = truncate(c[f])
  #               else:
  #                 filtered[fields[f]] = ""
  #             value = len(value)

  #           # Just a list, nothing special  
  #           else:  
  #             value = ",".join(value)

  #         # If we have a dict...
  #         if type(value) is dict:
  #           if key == "header_image":
  #             for f in header_image_fields:
  #               if f in value.keys():
  #                 filtered[fields[f]] = truncate(value[f])
  #               else:
  #                 filtered[fields[f]] = ""
  #             value = True
  #           else:
  #             print(f"Warning: Unexpected front matter dict {key} found!")

  #         filtered[fields[key]] = truncate(value)
    
  #     # Seed the .csv row with path and filename
  #     filtered[fields['md-file']] = path.name[:-3]
  #     filtered[fields['md-path']] = parent_path(path)

  #     # Build one live link for each code branch and seed the .csv row with them
  #     for key in branches:
  #       key_name = f"{key}-link"
  #       filtered[fields[key_name]] = build_link(key, path)

  #     # Note any obsolete front matter
  #     filtered[fields['obsolete']] = obsolete

  #     writer.writerow(filtered)

  # # Ok, done writing the .csv, now copy it to a new tab/worksheet in our Google Sheet
  # # Open the Google service account and sheet
  # try:
  #   sa = gs.service_account()
  # except Exception as e:
  #   print(e)

  # try:  
  #   sh = sa.open("Rootstalk Articles Front Matter")
  # except Exception as e:
  #   print(e)  

  # # Make a datestamp to name the new worksheet
  # sheet_name = datetime.now().strftime("%Y-%b-%d-%I:%M%p")
  
  # # Create the new/empty worksheet
  # try:
  #   worksheet = sh.add_worksheet(title=sheet_name, rows=1, cols=1)
  # except Exception as e:
  #   print(e)  

  # # Call our function to write the new Google Sheet worksheet
  # try:
  #   paste_csv(csv_filename, sh, sheet_name + "!A1")
  # except Exception as e:
  #   print(e)

  # # Call our format function to set the overall format of the new sheet
  # try:
  #   format_google_sheet(sh, sheet_name)
  # except Exception as e:
  #   print(e)

  # # Call our function to sort the new sheet
  # try:
  #   sort_google_sheet(sh, sheet_name)
  # except Exception as e:
  #   print(e)

  # # Call our function to set conditional formatting rules
  # try:
  #   highlight_todo_cells(sh, sheet_name)
  # except Exception as e:
  #   print(e)
