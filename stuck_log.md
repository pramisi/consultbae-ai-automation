# ConsultBae AI Automation — Stuck Log

This document records the major implementation issues encountered during development and how they were resolved.

---

## Issue 1 — SQLite Query Interface

### Problem

The SQLite database could be opened in VS Code using a SQLite Viewer, but there was no visible SQL query editor.

### What I tried

I looked for a query or SQL editor inside the database viewer.

The viewer allowed the tables to be inspected but did not provide the query interface needed for validation.

### Solution

Instead of depending on a GUI SQL editor, I created:

```text
src/inspect_database.py
