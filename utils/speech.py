from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path

from gtts import gTTS

from utils.config import AUDIO_DIR, AUDIO_FILE


def phat_am(
    word: str,
    language: str = "en",
) -> str:
    """
    Tạo file MP3 phát âm từ tiếng Anh bằng gTTS.

    Trả về đường dẫn file âm thanh.
    """
    normalized_word = word.strip()

    if not normalized_word:
        raise ValueError(
            "Từ cần phát âm không được để trống."
        )

    audio_directory = Path(AUDIO_DIR)

    audio_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    audio_path = Path(AUDIO_FILE)

    try:
        tts = gTTS(
            text=normalized_word,
            lang=language,
        )

        tts.save(
            str(audio_path)
        )

    except Exception as error:
        raise RuntimeError(
            f"Không thể tạo âm thanh cho "
            f"'{normalized_word}': {error}"
        ) from error

    return str(audio_path)


def open_audio_file(
    audio_path: str | Path,
) -> None:
    """
    Mở file âm thanh bằng chương trình mặc định
    của hệ điều hành.
    """
    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file âm thanh: "
            f"{audio_path}"
        )

    operating_system = platform.system()

    if operating_system == "Windows":
        os.startfile(
            str(audio_path)
        )

    elif operating_system == "Darwin":
        subprocess.run(
            [
                "open",
                str(audio_path),
            ],
            check=False,
        )

    else:
        subprocess.run(
            [
                "xdg-open",
                str(audio_path),
            ],
            check=False,
        )


def speak(
    word: str,
) -> str:
    """
    Tạo file âm thanh và mở phát âm.
    """
    audio_path = phat_am(word)

    open_audio_file(audio_path)

    return audio_path