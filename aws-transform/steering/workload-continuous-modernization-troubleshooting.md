---
name: troubleshooting
description: Troubleshooting guide for issues that occur during setup and execution of AWS Transform continuous modernization.
---

# Common Errors

## Error writing files to the ~/.atxct folder

If attempting to read or write files to the user's ~/.atxct folder fails due to an error similar to "File access is restricted to the open workspace folders", write a script or find another way to read/write to this directory -- there is no substitute/alternative location for files in ~/.atxct so be sure to find a way to do it.

