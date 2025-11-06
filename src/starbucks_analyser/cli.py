from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv

from .data_loader import load_drinks, load_food
from .filters import apply_filters, by_calories_under, with_column_threshold
from .llm.summarize import summarize_metrics
from .processing import compare as compare_metrics
from .processing import describe, save_metrics, top_n_by
from .viz.charts import bar_top_items, grouped_means_bar

# Load environment variables from .env file (after imports to avoid circular deps)
load_dotenv()  # noqa: E402

app = typer.Typer()


@app.command()
def stats(drinks: str, food: str, out: str = "outputs/metrics/metrics.json") -> None:
    d = load_drinks(drinks)
    f = load_food(food)
    drinks_desc = describe(d)
    food_desc = describe(f)
    cmp = compare_metrics(d, f)
    tops = {
        "drinks_top_calories": top_n_by(d, "calories", 10).to_dict(orient="records"),
        "drinks_top_sugar": top_n_by(d, "sugar_g", 10).to_dict(orient="records")
        if "sugar_g" in d.columns
        else top_n_by(d, "carbs_g", 10).to_dict(orient="records"),
        "food_top_calories": top_n_by(f, "calories", 10).to_dict(orient="records"),
        "food_top_sugar": top_n_by(f, "sugar_g", 10).to_dict(orient="records")
        if "sugar_g" in f.columns
        else top_n_by(f, "carbs_g", 10).to_dict(orient="records"),
    }
    payload = {"drinks": drinks_desc, "food": food_desc, "comparisons": cmp.get("comparisons", {}), "tops": tops}
    save_metrics(payload, out)
    typer.echo(f"Saved metrics to {out}")


@app.command()
def compare(drinks: str, food: str) -> None:
    d = load_drinks(drinks)
    f = load_food(food)
    cmp = compare_metrics(d, f)
    typer.echo(json.dumps(cmp, indent=2))


@app.command()
def filter_food_under(food: str, max_calories: float = 500.0) -> None:
    f = load_food(food)
    res = by_calories_under(f, max_calories)
    typer.echo(res.to_csv(index=False))


@app.command()
def viz_top(
    drinks: str,
    column: str = "calories",
    top_n: int = 10,
    out: str = "outputs/plots/top_drinks.png",
) -> None:
    d = load_drinks(drinks)
    path = bar_top_items(d, column=column, top_n=top_n, out_path=out)
    typer.echo(f"Saved plot to {path}")


@app.command()
def viz_top_food(
    food: str,
    column: str = "calories",
    top_n: int = 10,
    out: str = "outputs/plots/top_food.png",
) -> None:
    f = load_food(food)
    path = bar_top_items(f, column=column, top_n=top_n, out_path=out)
    typer.echo(f"Saved plot to {path}")


@app.command()
def viz_means(
    drinks: str,
    food: str,
    out: str = "outputs/plots/means_comparison.png",
) -> None:
    d = load_drinks(drinks)
    f = load_food(food)
    path = grouped_means_bar(d, f, ["calories", "sugar_g", "fat_g", "protein_g", "sodium"], out)
    typer.echo(f"Saved plot to {path}")


@app.command()
def summarize(
    metrics_path: str = "outputs/metrics/metrics.json",
    out: Optional[str] = None,
) -> None:
    with open(metrics_path) as f:
        payload = json.load(f)
    try:
        text = summarize_metrics(payload)
    except Exception as e:
        # Graceful failure if GROQ_API_KEY is missing or client errors
        typer.echo(f"LLM summarization unavailable: {e}")
        return

    if out:
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text)
        typer.echo(f"Saved summary to {out}")
    else:
        typer.echo(text)


@app.command()
def filter_column(
    dataset: str,
    column: str,
    max_value: float,
    kind: str = "auto",
) -> None:
    """Filter a dataset by numeric column threshold and print CSV.

    kind: one of 'drinks', 'food', or 'auto' to infer based on path.
    """
    if kind == "drinks" or (kind == "auto" and "drink" in dataset.lower()):
        df = load_drinks(dataset)
    elif kind == "food" or (kind == "auto" and "food" in dataset.lower()):
        df = load_food(dataset)
    else:
        # default to drinks loader to ensure normalization; if it fails, user can set kind
        df = load_drinks(dataset)
    res = with_column_threshold(df, column=column, max_value=max_value)
    typer.echo(res.to_csv(index=False))


@app.command()
def filter_multi(
    dataset: str,
    kind: str = "auto",
    calories_le: float | None = None,
    sugar_g_le: float | None = None,
    fat_g_le: float | None = None,
    protein_g_ge: float | None = None,
    sodium_mg_le: float | None = None,
    caffeine_mg_gt: float | None = None,
    name_contains: str | None = None,
) -> None:
    if kind == "drinks" or (kind == "auto" and "drink" in dataset.lower()):
        df = load_drinks(dataset)
    elif kind == "food" or (kind == "auto" and "food" in dataset.lower()):
        df = load_food(dataset)
    else:
        df = load_drinks(dataset)
    res = apply_filters(
        df,
        calories_le=calories_le,
        sugar_g_le=sugar_g_le,
        fat_g_le=fat_g_le,
        protein_g_ge=protein_g_ge,
        sodium_mg_le=sodium_mg_le,
        caffeine_mg_gt=caffeine_mg_gt,
        name_contains=name_contains,
    )
    typer.echo(res.to_csv(index=False))


if __name__ == "__main__":
    app()
