from __future__ import annotations

import pandas as pd

from src.starbucks_analyser.processing import compare, describe, top_n_by


def test_describe_basic():
    df = pd.DataFrame({"calories": [100, 200], "fat_g": [5, 10], "protein_g": [5, 5]})
    d = describe(df)
    assert d["count"] == 2
    assert "fat_to_protein_ratio" in d["means"]
    assert "medians" in d


def test_compare_has_key():
    d = pd.DataFrame({"calories": [100, 200]})
    f = pd.DataFrame({"calories": [300, 400]})
    out = compare(d, f)
    assert "comparisons" in out


def test_top_n_by_returns_sorted():
    df = pd.DataFrame({"item": ["a", "b", "c"], "calories": [100, 300, 200]})
    top = top_n_by(df, "calories", 2)
    assert list(top["item"]) == ["b", "c"]
