# Hugo Frontmatter Tools

A collection of Python scripts desinged to help manage Hugo .md content frontmatter.

---

## Python

See [Proper Python](https://blog.summittdweller.com/posts/2022/09/proper-python/) for applicable guidance when enabling Python parts of this workflow.  

---

## frontmatter-to-csv.py

This script is designed to read all of the .md files in a directory tree, and populate a single .csv file with the contents/status of all the frontmatter found in those Markown files.  Inspired by [convert.py](https://git.kucharczyk.xyz/lukas/frontmatter-to-csv/src/branch/main/frontmatter_to_csv/convert.py) from the [lukas/frontmatter-to-csv](https://git.kucharczyk.xyz/lukas/frontmatter-to-csv) repo.  

---

### Link Generation

On October 25, 2022, a feature was added to this script for generation of links to corresponding "development" site pages.  So, for instance, the row of `.csv` data that previously contained this:

```csv
volume-viii-issue-1,trissell.md,Food Deserts in t...,9,trissell,,05/10/2022 15:22:00,False,1,author,Mikayla Trissell,Trissel-1-volume-...
```

...now contains this:

```csv
volume-viii-issue-1,trissell.md,https://icy-tree-020380010.azurestaticapps.net/volume-viii-issue-1/trissell ,Food Deserts in t...,9,trissell,,05/10/2022 15:22:00,False,1,author,Mikayla Trissell,Trissel-1-volume-...
```

A link to the article `trissell`, for our example, now appears in the 3rd column of the `.csv` data.  Clicking that link from any view of the `.csv` file should open the "icy-tree" development version of the current article.  Note that this version of the website is actively generated from the `main` branch of the _Rootstalk_ project code.

---

## Static Elements

Static elements of the script currently include the following.

### Expected Fields

```python
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
```

### Obsolete Fields

The following fields are considered "obsolete" and deprecated.  Articles that still posses these fields should be upgraded to use corresponding `fields` as soon as possible.

```python
obsolete = ["sidebar", "pid", "issueIndex", "azure_headerimage", "author", "azure_headshot", "authorbio", "headerimage"]
```

### Contributor `dict` Fields

```python
contributor_fields = ["role", "name", "headshot", "caption", "bio"]
```

### Header Image `dict` Fields

```python
header_image_fields = ["filename", "alt_text"]
```

### Input `glob` File Spec

```python
 filepath = "/Users/mark/GitHub/rootstalk/content/**/volume*/*.md"
```

### CSV Output Filename

```python
with open("frontmatter-status.csv", "w") as csvfile:
 ```

### Link Generation Base URL

```python
def build_link(path):
  base_url = "https://icy-tree-020380010.azurestaticapps.net/"
```
