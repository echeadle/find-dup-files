#!/bin/bash

# Script to remove all __pycache__ directories recursively without affecting other files or folders.

find . -type d -name "__pycache__" -print0 | while IFS= read -r -d $'\0' dir; do
  echo "Removing directory: $dir"
  rm -rf "$dir"
done

echo "Finished removing __pycache__ directories."
