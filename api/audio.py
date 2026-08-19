from pathlib import Path
import sqlite3
import wave
import math
import struct
import uuid
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_FILE = BASE_DIR / "consultbae.db"

AUDIO_DIR = BASE_DIR / "audio" / "submissions"

# Make sure the folder exists
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/audio",
    tags=["Audio"]
)


# ============================================================
# DATABASE
# ============================================================

def get_db():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_audio_table():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS audio_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            audio_filename TEXT NOT NULL,
            audio_path TEXT NOT NULL,
            duration_seconds REAL NOT NULL,
            sample_rate_khz REAL NOT NULL,
            bitrate_kbps REAL NOT NULL,
            loudness_db REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# LOUDNESS
# ============================================================

def calculate_loudness_db(frames, sample_width):

    if not frames:
        return -100.0

    if sample_width == 2:

        count = len(frames) // 2

        samples = struct.unpack(
            "<" + ("h" * count),
            frames
        )

        if not samples:
            return -100.0

        rms = math.sqrt(
            sum(sample * sample for sample in samples)
            / len(samples)
        )

        if rms <= 0:
            return -100.0

        return round(
            20 * math.log10(rms / 32768.0),
            2
        )

    return -100.0


# ============================================================
# STARTUP
# ============================================================

@router.on_event("startup")
def startup():

    init_audio_table()


# ============================================================
# UPLOAD AUDIO
# ============================================================

@router.post("/upload")
async def upload_audio(

    name: str = Form(...),

    phone: str = Form(...),

    person_id: int | None = Form(None),

    audio: UploadFile = File(...)
):

    # --------------------------------------------------------
    # Check file
    # --------------------------------------------------------

    if not audio.filename:

        raise HTTPException(
            status_code=400,
            detail="Audio file is required"
        )


    extension = Path(
        audio.filename
    ).suffix.lower()


    if extension != ".wav":

        raise HTTPException(
            status_code=400,
            detail=(
                "Please upload a WAV audio file. "
                "WAV is used so metadata can be extracted reliably."
            )
        )


    # --------------------------------------------------------
    # Generate unique filename
    # --------------------------------------------------------

    file_id = uuid.uuid4().hex

    filename = f"{file_id}.wav"

    file_path = AUDIO_DIR / filename


    # --------------------------------------------------------
    # Save uploaded file
    # --------------------------------------------------------

    contents = await audio.read()

    file_path.write_bytes(contents)


    # --------------------------------------------------------
    # Extract WAV metadata
    # --------------------------------------------------------

    try:

        with wave.open(str(file_path), "rb") as wav:

            channels = wav.getnchannels()

            sample_rate = wav.getframerate()

            sample_width = wav.getsampwidth()

            frame_count = wav.getnframes()


            duration = (
                frame_count / sample_rate
                if sample_rate
                else 0
            )


            bitrate = (
                sample_rate
                * sample_width
                * 8
                * channels
            ) / 1000


            frames = wav.readframes(frame_count)


            loudness = calculate_loudness_db(
                frames,
                sample_width
            )


    except Exception as exc:

        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=400,
            detail=f"Invalid WAV audio file: {exc}"
        )


    # ========================================================
    # SAVE DATABASE RECORD
    # ========================================================

    conn = get_db()


    cursor = conn.execute(
        """
        INSERT INTO audio_submissions (
            person_id,
            name,
            phone,
            audio_filename,
            audio_path,
            duration_seconds,
            sample_rate_khz,
            bitrate_kbps,
            loudness_db,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,

        (
            person_id,

            name,

            phone,

            # IMPORTANT:
            # Save the UUID filename, NOT the original filename
            filename,

            # Save relative path
            str(
                file_path.relative_to(BASE_DIR)
            ),

            round(duration, 3),

            round(
                sample_rate / 1000,
                3
            ),

            round(
                bitrate,
                2
            ),

            loudness,

            datetime.utcnow().isoformat()
        )
    )


    submission_id = cursor.lastrowid


    conn.commit()

    conn.close()


    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "success": True,

        "submission_id": submission_id,

        "name": name,

        "phone": phone,

        "duration_seconds": round(
            duration,
            3
        ),

        "sample_rate_khz": round(
            sample_rate / 1000,
            3
        ),

        "bitrate_kbps": round(
            bitrate,
            2
        ),

        "loudness_db": loudness,

        # IMPORTANT:
        # This is now the ACTUAL filename on disk
        "audio_filename": filename,

        "audio_url": (
            f"/api/audio/file/{filename}"
        )
    }


# ============================================================
# GET ALL SUBMISSIONS
# ============================================================

@router.get("/submissions")
def get_submissions():

    conn = get_db()


    rows = conn.execute(
        """
        SELECT *
        FROM audio_submissions
        ORDER BY id DESC
        """
    ).fetchall()


    conn.close()


    result = []


    for row in rows:

        item = dict(row)


        # ----------------------------------------------------
        # IMPORTANT FOR OLD DATABASE RECORDS
        # ----------------------------------------------------
        #
        # Your old records may contain:
        #
        # audio_filename = "recording.wav"
        #
        # while the actual file is:
        #
        # audio/submissions/UUID.wav
        #
        # We use audio_path to recover the actual filename.
        #

        if item.get("audio_path"):

            actual_filename = Path(
                item["audio_path"]
            ).name

            item["audio_filename"] = actual_filename

            item["audio_url"] = (
                f"/api/audio/file/{actual_filename}"
            )


        result.append(item)


    return result


# ============================================================
# SERVE AUDIO FILE
# ============================================================

@router.get("/file/{filename}")
def get_audio_file(filename: str):

    # IMPORTANT:
    #
    # AUDIO_DIR already points to:
    #
    # audio/submissions
    #
    # So DO NOT add another /submissions here.

    file_path = AUDIO_DIR / filename


    # Security check
    #
    # Prevent someone from requesting files outside
    # the audio directory.

    try:

        file_path.resolve().relative_to(
            AUDIO_DIR.resolve()
        )

    except ValueError:

        raise HTTPException(
            status_code=400,
            detail="Invalid audio filename"
        )


    # --------------------------------------------------------
    # Check file exists
    # --------------------------------------------------------

    if not file_path.exists():

        raise HTTPException(
            status_code=404,
            detail="Audio file not found"
        )


    # --------------------------------------------------------
    # Return WAV file
    # --------------------------------------------------------

    return FileResponse(

        path=file_path,

        media_type="audio/wav",

        filename=filename
    )