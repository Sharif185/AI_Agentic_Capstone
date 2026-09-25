# Data Directory

## Purpose

Local storage for tool data (not committed to Git).

## Files

- courses.json - Course information (committed, synthetic)
- sample_students.json - Sample student data (committed, synthetic)
- tickets.db - SQLite database for tickets (NOT committed)

## Gitignore

tickets.db is in .gitignore - it's generated at runtime.
