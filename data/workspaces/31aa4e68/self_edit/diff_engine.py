"""Diff helpers for upgrade plans and promotion summaries."""

from __future__ import annotations

import difflib


def unified_diff(old_text: str, new_text: str, fromfile: str, tofile: str) -> str:
    return "".join(
        difflib.unified_diff(
            old_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile=fromfile,
            tofile=tofile,
        )
    )

