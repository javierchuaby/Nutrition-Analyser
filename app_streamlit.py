import os
import re
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.starbucks_analyser.data_loader import load_drinks, load_food
from src.starbucks_analyser.filters import apply_filters, get_sugar_or_carb_column
from src.starbucks_analyser.llm.summarize import summarize_metrics
from src.starbucks_analyser.processing import compare as compare_metrics
from src.starbucks_analyser.processing import describe, load_metrics, save_metrics, top_n_by
from src.starbucks_analyser.viz.charts import (
    direct_comparisons,
    extremes_comparison,
    overall_average_comparisons,
)


@st.cache_data(ttl=3600)  # Cache for 1 hour
def cached_summarize_metrics(payload: dict, api_key_hash: str) -> str:
    """Cached version of summarize_metrics to avoid rate limits.
    
    api_key_hash is included in cache key to invalidate cache when API key changes.
    """
    return summarize_metrics(payload)

# Load environment variables from .env file (after imports to avoid circular deps)
# Use override=True to reload .env if it changes (though Streamlit restart is still needed)
load_dotenv(override=True)  # noqa: E402

st.set_page_config(page_title="Starbucks Nutrition Analyser", layout="wide")
st.title("Starbucks Nutrition Analyser")

with st.sidebar:
    st.header("Data")
    drinks_file = st.file_uploader("Drinks CSV", type=["csv"])
    food_file = st.file_uploader("Food CSV", type=["csv"])
    st.header("Filters")
    calories_le = st.number_input("Max calories", min_value=0, value=0, step=10)
    sugar_le = st.number_input("Max sugar_g (uses carbs if missing)", min_value=0, value=0, step=1)
    protein_ge = st.number_input("Min protein_g", min_value=0, value=0, step=1)
    sodium_le = st.number_input("Max sodium_mg", min_value=0, value=0, step=10)
    name_contains = st.text_input("Name contains")
    run_button = st.button("Process")

if run_button and drinks_file and food_file:
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".csv") as tmp_drinks:
        tmp_drinks.write(drinks_file.getvalue())
        tmp_drinks_path = tmp_drinks.name
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".csv") as tmp_food:
        tmp_food.write(food_file.getvalue())
        tmp_food_path = tmp_food.name
    try:
        d = load_drinks(tmp_drinks_path)
        f = load_food(tmp_food_path)
    finally:
        os.unlink(tmp_drinks_path)
        os.unlink(tmp_food_path)
    # Apply filters when any control is non-zero/non-empty
    filt_kwargs = {
        "calories_le": float(calories_le) if calories_le else None,
        "sugar_g_le": float(sugar_le) if sugar_le else None,
        "protein_g_ge": float(protein_ge) if protein_ge else None,
        "sodium_mg_le": float(sodium_le) if sodium_le else None,
        "name_contains": name_contains or None,
    }
    df_drinks = apply_filters(d, **filt_kwargs)
    df_food = apply_filters(f, **filt_kwargs)

    # st.subheader("Descriptive Stats (filtered)")
    d_desc, f_desc = describe(df_drinks), describe(df_food)

    # st.subheader("Comparisons")
    cmp = compare_metrics(df_drinks, df_food)
    
    # Prepare top items data for visualizations and summary
    drinks_sugar_col = get_sugar_or_carb_column(df_drinks) or "carbs_g"
    food_sugar_col = get_sugar_or_carb_column(df_food) or "carbs_g"
    tops = {
        "drinks_top_calories": top_n_by(df_drinks, "calories", 10).to_dict(orient="records"),
        "drinks_top_sugar": top_n_by(df_drinks, drinks_sugar_col, 10).to_dict(orient="records"),
        "drinks_top_fat": top_n_by(df_drinks, "fat_g", 10).to_dict(orient="records"),
        "food_top_calories": top_n_by(df_food, "calories", 10).to_dict(orient="records"),
        "food_top_sugar": top_n_by(df_food, food_sugar_col, 10).to_dict(orient="records"),
        "food_top_fat": top_n_by(df_food, "fat_g", 10).to_dict(orient="records"),
    }

    # Generate charts for sections that have corresponding tables
    path_avg = overall_average_comparisons(
        d_desc, f_desc, "outputs/plots/overall_average_comparisons.png"
    )
    path_direct = direct_comparisons(
        d_desc,
        f_desc,
        cmp.get("comparisons", {}),
        "outputs/plots/direct_comparisons.png"
    )
    path_extremes = extremes_comparison(df_drinks, df_food, "outputs/plots/extremes_comparison.png")
    
    # Add CSS for larger spacing before h2 headers only
    st.markdown(
        """
        <style>
        /* Larger spacing before h2 headers (## in markdown) */
        h2 {
            margin-top: 3rem !important;
        }
        /* First h2 header shouldn't have top margin */
        .stMarkdown h2:first-of-type {
            margin-top: 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    payload = {
        "drinks": d_desc,
        "food": f_desc,
        "comparisons": cmp.get("comparisons", {}),
        "tops": tops,
    }
    save_metrics(payload, "outputs/metrics/metrics.json")
    
    # Try to load previously saved summary if API fails
    summary_cache_path = "outputs/metrics/summary_cache.txt"
    
    try:
        # Get API key hash to invalidate cache when API key changes
        api_key = os.getenv("GROQ_API_KEY", "")
        import hashlib
        api_key_hash = hashlib.md5(api_key.encode() if api_key else b"").hexdigest()
        
        # Use cached version to avoid rate limits for identical data
        # Include API key hash in cache key so cache invalidates when key changes
        text = cached_summarize_metrics(payload, api_key_hash)
        
        # Save successful summary to cache for future use when API fails
        Path(summary_cache_path).parent.mkdir(parents=True, exist_ok=True)
        with open(summary_cache_path, "w") as f:
            f.write(text)
        
        # Split summary into sections and display charts alongside corresponding sections
        # Split by ## headers (main sections only, not ### subsections)
        parts = re.split(r'(^## .+)', text, flags=re.MULTILINE)
        
        i = 0
        while i < len(parts):
            part = parts[i].strip()
            if not part:
                i += 1
                continue
            
            # Check if this is a header
            if part.startswith('## '):
                # Get content after this header (until next ## or end)
                content = ""
                if i + 1 < len(parts):
                    # Collect all non-header content
                    j = i + 1
                    while j < len(parts) and not parts[j].strip().startswith('## '):
                        if parts[j].strip():
                            content += parts[j] + "\n"
                        j += 1
                    content = content.strip()
                
                # Display charts alongside corresponding sections
                # Map section names to their chart paths and captions
                section_charts = {
                    'Overall Average Comparisons': (path_avg, "Overall Average Comparisons Chart"),
                    'Direct Comparisons': (path_direct, "Direct Comparisons Chart"),
                    'Extremes Comparisons': (path_extremes, "Extremes Comparison Chart"),
                }
                
                # Check if this section has a chart
                chart_info = None
                for section_name, (chart_path, caption) in section_charts.items():
                    if section_name in part:
                        chart_info = (chart_path, caption)
                        break
                
                if chart_info:
                    # Display header as markdown first (so it renders properly)
                    st.markdown(part)
                    # Then display content and chart side by side
                    chart_path, caption = chart_info
                    col1, col2 = st.columns(2)
                    with col1:
                        if content:
                            st.markdown(content)
                    with col2:
                        st.image(chart_path, caption=caption)
                    # Skip to after the content
                    i = j
                else:
                    # Regular section without chart
                    st.markdown(part)
                    if content:
                        st.markdown(content)
                    i = j
            else:
                # Content before first header
                st.markdown(part)
                i += 1
                
    except Exception as e:
        error_msg = str(e)
        st.warning(f"Error generating summary: {error_msg}")
        
        # Try to load cached summary from previous successful run
        if os.path.exists(summary_cache_path):
            try:
                with open(summary_cache_path, "r") as f:
                    cached_text = f.read()
                st.info("📋 Displaying previously saved summary (API rate limit reached)")
                
                # Split and display cached summary
                parts = re.split(r'(^## .+)', cached_text, flags=re.MULTILINE)
                
                i = 0
                while i < len(parts):
                    part = parts[i].strip()
                    if not part:
                        i += 1
                        continue
                    
                    # Check if this is a header
                    if part.startswith('## '):
                        # Get content after this header (until next ## or end)
                        content = ""
                        if i + 1 < len(parts):
                            j = i + 1
                            while j < len(parts) and not parts[j].strip().startswith('## '):
                                if parts[j].strip():
                                    content += parts[j] + "\n"
                                j += 1
                            content = content.strip()
                        
                        # Display charts alongside corresponding sections
                        section_charts = {
                            'Overall Average Comparisons': (path_avg, "Overall Average Comparisons Chart"),
                            'Direct Comparisons': (path_direct, "Direct Comparisons Chart"),
                            'Extremes Comparisons': (path_extremes, "Extremes Comparison Chart"),
                        }
                        
                        chart_info = None
                        for section_name, (chart_path, caption) in section_charts.items():
                            if section_name in part:
                                chart_info = (chart_path, caption)
                                break
                        
                        if chart_info:
                            st.markdown(part)
                            chart_path, caption = chart_info
                            col1, col2 = st.columns(2)
                            with col1:
                                if content:
                                    st.markdown(content)
                            with col2:
                                st.image(chart_path, caption=caption)
                            i = j
                        else:
                            st.markdown(part)
                            if content:
                                st.markdown(content)
                            i = j
                    else:
                        st.markdown(part)
                        i += 1
            except Exception as cache_error:
                st.error(f"Could not load cached summary: {cache_error}")
        else:
            st.info("💡 Tip: Wait ~9 minutes for rate limit reset, or upgrade your Groq plan for more tokens.")
