"""
Streaming Narration Generator for Quilltale TRPG.
Provides token-by-token and typewriter-style streaming yields for UI responsiveness.
"""
import time
from typing import Generator


class NarrationStreamer:
    """Streams narration text character-by-character or chunk-by-chunk."""

    @staticmethod
    def stream_text(full_narration: str, chunk_delay: float = 0.015) -> Generator[str, None, None]:
        current_text = ""
        for char in full_narration:
            current_text += char
            yield current_text
            if char in [".", "\n", "!", "?"]:
                time.sleep(chunk_delay * 2)
            else:
                time.sleep(chunk_delay)
