from __future__ import annotations

import pandas as pd

from src.starbucks_analyser.filters import by_calories_under


def test_by_calories_under():
    df = pd.DataFrame({"calories": [100, 600]})
    res = by_calories_under(df, 500)
    assert res.shape[0] == 1
