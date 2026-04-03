---
title: "Tags Index"
aliases: [tag index, all tags]
---

# Tags Index

## By Tag

```dataview
TABLE WITHOUT ID
  link(file.link, file.name) as "Page",
  category as "Category"
FROM "wiki"
WHERE contains(tags, this.current_tag)
SORT category ASC, title ASC
```

> Note: Browse tags via Obsidian's tag pane (left sidebar) for the best experience.

## Most Used Tags

```dataview
TABLE length(rows) as "Count", rows.file.link as "Pages"
FROM "wiki"
FLATTEN tags as tag
GROUP BY tag
SORT length(rows) DESC
```
