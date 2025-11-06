from __future__ import annotations

import os

from groq import Groq


def get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY missing")
    return Groq(api_key=api_key)
