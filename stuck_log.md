#ConsultBae AI Automation — Stuck Log

This document records the major implementation issues encountered during development and how they were resolved.

#Issue 1 — SQLite Query Interface

Problem

The SQLite database could be opened in VS Code using a SQLite Viewer, but there was no visible SQL query editor. The viewer allowed tables to be inspected but did not provide the query interface needed for validation.

What I tried

I looked for a query or SQL editor inside the database viewer.

Solution

Instead of depending on a GUI SQL editor, I created:

src/inspect_database.py

This script uses Python's SQLite interface to connect to the database and inspect tables and records.

What I learned

A database viewer is useful for visual inspection, but a small repeatable inspection script is more reliable for validating a take-home project.

#Issue 2 — n8n LLM Model Selection

Problem

While building the n8n skill-categorization workflow, the required LLM model was not available in the model-selection list.

What I tried

I checked the available model options in the n8n LLM node instead of assuming that a model name from an example would be available in the current environment.

Solution

I adapted the workflow to use an available model/provider while keeping the required output categories unchanged:

web dev
data
automation-heavy

The LLM output was then passed through a JavaScript categorization/validation step so that only the allowed categories were accepted.

What I learned

Workflow configurations depend on the models and credentials available in the actual environment. The important part is to preserve the required input/output contract rather than hard-code an unavailable model.

#Issue 3 — Browser Audio Recording and WAV Format

Problem

The browser's MediaRecorder API produced a browser recording format such as WebM, while the backend audio-processing pipeline expected WAV input.

Simply changing the filename from .webm to .wav would not actually convert the audio format.

What I tried

Initially, the recording was wrapped in a Blob and then given a .wav filename. This did not represent a genuine WAV conversion.

Solution

The frontend was changed so that the recorded audio is converted into an actual PCM WAV representation before it is submitted to the backend.

The backend can then extract the required audio properties.

What I learned

Changing a file extension does not convert its underlying encoding. File-format compatibility needs to be handled explicitly between browser and backend.

#Issue 4 — Audio Player Showing 0:00 / 0:00

Problem

After audio submission was working, the frontend audio player showed:

0:00 / 0:00

even though the backend had successfully extracted duration, sample rate, bitrate, and loudness.

What I tried

I checked the FastAPI audio-file endpoint and verified that the uploaded WAV files existed.

I then checked the server logs and found requests such as:

GET /api/audio/file/recording.wav 404
GET /api/audio/file/test_audio.wav 404

Root Cause

The actual generated files were stored in:

audio/submissions/

with generated filenames such as:

a4ed28d35bb84197a67b3920ae8aa970.wav
0354185618114ed49b7ac5735538abc.wav

The frontend was still requesting old/hard-coded filenames such as recording.wav and test_audio.wav.

Solution

The frontend was changed to use the audio_url / actual audio_filename returned by the backend instead of hard-coded test filenames.

After the fix, the browser successfully loaded the real recordings and displayed their actual durations, for example:

0:02 / 0:02
0:04 / 0:04

What I learned

When a frontend resource returns a 404, checking backend access logs and then verifying the actual filesystem contents quickly distinguishes a backend storage problem from a frontend URL-generation problem.

Key Debugging Lessons

The most useful debugging pattern throughout the project was:

Observe the error
      ↓
Check the server/terminal output
      ↓
Inspect the actual files/data
      ↓
Identify the mismatch
      ↓
Make the smallest targeted change
      ↓
Retest end-to-end

I also avoided committing generated audio recordings, local databases, virtual environments, and environment secrets to GitHub by updating .gitignore.#