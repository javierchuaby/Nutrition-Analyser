# Starbucks Nutrition Analyser

A modular LLM-powered nutrition analysis tool for Starbucks menu data with processing, comparisons, visualizations, Groq summaries, CLI, tests, and optional Streamlit UI.

## Features

- **Robust CSV Loading**: Automatic encoding detection (UTF-8, UTF-16), column normalization, and deduplication
- **Descriptive Statistics**: Comprehensive statistics (mean, median, min, max, totals) for all nutrients
- **Cross-Dataset Comparisons**: Compare drinks vs food across multiple metrics
- **Visualizations**: Multiple chart types (top items, means comparison, direct comparisons, extremes)
- **LLM Summarization**: Groq-powered summaries with deterministic output
- **Advanced Filtering**: Multi-criteria filtering (calories, sugar, fat, protein, sodium, caffeine, name search)
- **Streamlit UI**: Optional web interface with file uploads, filtering, and interactive visualizations
- **Type Safety**: Full type hints with Mypy strict mode
- **Quality Gates**: Black formatting, Ruff linting, Mypy type checking, and comprehensive tests

## Setup

### Prerequisites

- **Python 3.10 or higher** (Python 3.11+ recommended)
- **pip** (Python package manager, usually comes with Python)
- **CSV files** with Starbucks menu nutrition data

### Step 1: Verify Python Installation

First, check if Python is installed and which version:

```bash
python --version
# or
python3 --version
```

You should see `Python 3.10.x` or higher. If Python is not installed:
- **macOS**: Install via [python.org](https://www.python.org/downloads/) or using Homebrew: `brew install python3`
- **Windows**: Download from [python.org](https://www.python.org/downloads/)
- **Linux**: Use your package manager, e.g., `sudo apt install python3 python3-pip` (Ubuntu/Debian)

### Step 2: Create Virtual Environment

Navigate to the project directory and create a virtual environment:

```bash
# Navigate to project directory
cd "path/to/Starbucks Analyser"

# Create virtual environment
python -m venv .venv
# or on some systems:
python3 -m venv .venv
```

### Step 3: Activate Virtual Environment

**On macOS/Linux:**
```bash
source .venv/bin/activate
```

**On Windows (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

**On Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

If you see `(.venv)` at the start of your command prompt, the virtual environment is active.

### Step 4: Install Dependencies

**Option A: Using requirements.txt (Recommended)**
```bash
pip install -r requirements.txt
```

**Option B: Manual installation**
```bash
pip install pandas numpy matplotlib streamlit typer python-dotenv groq
```

**For development (optional):**
```bash
pip install black ruff mypy pytest types-python-dotenv
```

### Step 5: Verify Installation

Test that the installation worked:

```bash
# Check if packages are installed
python -c "import pandas, numpy, matplotlib, streamlit, typer; print('All packages installed successfully!')"
```

If you see "All packages installed successfully!", you're ready to proceed.

### Step 6: Configure Environment (Optional for LLM Features)

The LLM summarization feature requires a Groq API key. The app works without it, but some features will be unavailable.

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file** and add your Groq API key:
   ```
   GROQ_API_KEY=your_actual_groq_api_key_here
   ```
   
   To get a Groq API key:
   - Visit https://console.groq.com/
   - Sign up or log in
   - Create an API key
   - Copy the key and paste it in `.env` (replace `your_actual_groq_api_key_here`)

**Note:** The `.env` file is already in `.gitignore`, so your API key won't be committed to version control.

### Step 7: Prepare Data Files

Place your Starbucks menu CSV files in the `data/raw/` directory:

```bash
# Make sure the directory exists
mkdir -p data/raw

# Copy your CSV files to:
# - data/raw/starbucks-menu-nutrition-drinks.csv
# - data/raw/starbucks-menu-nutrition-food.csv
```

The CSV files should have columns like:
- `item_name` (or `item`)
- `Calories` (or `calories`)
- `Fat (g)` (or `fat_g`)
- `Carb. (g)` (or `carbs_g`)
- `Fiber (g)` (or `fiber_g`)
- `Protein` or `Protein (g)` (or `protein_g`)
- `Sodium` (or `sodium`) - optional

### Step 8: Verify Setup

Run a quick test to make sure everything works:

```bash
# Test CLI (should show help without errors)
python -m src.starbucks_analyser.cli --help

# Test Streamlit (will open in browser)
streamlit run app_streamlit.py
```

If both commands work, your setup is complete!

## Quick Start

### Run the Streamlit UI (Recommended for First-Time Users)

```bash
# Make sure virtual environment is activated
streamlit run app_streamlit.py
```

This will:
- Open your web browser automatically
- Allow you to upload CSV files through the interface
- Generate visualizations and summaries interactively

### Run CLI Commands

All CLI commands follow this pattern:
```bash
python -m src.starbucks_analyser.cli <command> [options]
```

Get help for any command:
```bash
python -m src.starbucks_analyser.cli --help
python -m src.starbucks_analyser.cli <command> --help
```

## Quality Commands

These commands are optional but recommended for development:

```bash
# Format code (ensures consistent style)
black .

# Lint code (finds potential issues)
ruff check .

# Type check (validates type hints)
mypy src

# Run tests (verifies functionality)
pytest -q

# Run tests with verbose output
pytest -v
```

## CLI Commands

### Generate Metrics

Generate comprehensive statistics and comparisons, saved to JSON:

```bash
python -m src.starbucks_analyser.cli stats \
  data/raw/starbucks-menu-nutrition-drinks.csv \
  data/raw/starbucks-menu-nutrition-food.csv \
  --out outputs/metrics/metrics.json
```

### Compare Datasets

Compare drinks vs food and print JSON output:

```bash
python -m src.starbucks_analyser.cli compare \
  data/raw/starbucks-menu-nutrition-drinks.csv \
  data/raw/starbucks-menu-nutrition-food.csv
```

### Visualizations

Create top-N items chart (drinks):

```bash
python -m src.starbucks_analyser.cli viz-top \
  data/raw/starbucks-menu-nutrition-drinks.csv \
  --column calories --top-n 10 \
  --out outputs/plots/top_drinks.png
```

Create top-N items chart (food):

```bash
python -m src.starbucks_analyser.cli viz-top-food \
  data/raw/starbucks-menu-nutrition-food.csv \
  --column calories --top-n 10 \
  --out outputs/plots/top_food.png
```

Create grouped means comparison chart:

```bash
python -m src.starbucks_analyser.cli viz-means \
  data/raw/starbucks-menu-nutrition-drinks.csv \
  data/raw/starbucks-menu-nutrition-food.csv \
  --out outputs/plots/means_comparison.png
```

### LLM Summarization

Generate LLM summary (prints to stdout). Requires `GROQ_API_KEY` in environment or `.env`:

```bash
python -m src.starbucks_analyser.cli summarize \
  --metrics-path outputs/metrics/metrics.json
```

Save summary to file:

```bash
python -m src.starbucks_analyser.cli summarize \
  --metrics-path outputs/metrics/metrics.json \
  --out outputs/summaries/summary.txt
```

### Filtering

Filter food items under calorie threshold (prints CSV):

```bash
python -m src.starbucks_analyser.cli filter-food-under \
  data/raw/starbucks-menu-nutrition-food.csv \
  --max-calories 500
```

Filter by any column threshold:

```bash
python -m src.starbucks_analyser.cli filter-column \
  data/raw/starbucks-menu-nutrition-drinks.csv \
  --column sugar_g --max-value 30 \
  --kind auto
```

Multi-criteria filtering:

```bash
python -m src.starbucks_analyser.cli filter-multi \
  data/raw/starbucks-menu-nutrition-drinks.csv \
  --calories-le 200 \
  --sugar-g-le 25 \
  --protein-ge 5 \
  --name-contains "latte"
```

## Streamlit UI

Launch the interactive web interface:

```bash
# Make sure virtual environment is activated first
streamlit run app_streamlit.py
```

**What happens:**
1. Streamlit starts a local web server
2. Your default web browser opens automatically (usually at `http://localhost:8501`)
3. If it doesn't open automatically, navigate to the URL shown in the terminal

**Features:**
- Upload CSV files through web interface (no need to place files in `data/raw/`)
- Apply multiple filters (calories, sugar, fat, protein, sodium, name search)
- View generated visualizations alongside LLM summaries
- Cached summaries to handle API rate limits gracefully
- All visualizations are displayed inline with the summary

**To stop the server:**
- Press `Ctrl+C` in the terminal where Streamlit is running

## Troubleshooting

### Common Issues

**Issue: "command not found: python" or "python: command not found"**
- **Solution**: Use `python3` instead of `python`, or ensure Python is in your PATH

**Issue: "No module named 'pandas'" or similar import errors**
- **Solution**: Make sure you've activated the virtual environment (you should see `(.venv)` in your prompt)
- Then run: `pip install -r requirements.txt`

**Issue: "streamlit: command not found"**
- **Solution**: Install Streamlit: `pip install streamlit`
- Make sure virtual environment is activated

**Issue: CSV files not loading**
- **Solution**: 
  - Check file paths are correct
  - Ensure CSV files are in `data/raw/` directory
  - Check file encoding (the app handles UTF-8 and UTF-16 automatically)
  - Verify CSV has required columns (see Step 7 in Setup)

**Issue: "GROQ_API_KEY missing" error**
- **Solution**: 
  - LLM features are optional - the app works without them
  - If you want LLM summarization, create `.env` file with your API key (see Step 6 in Setup)
  - The app will use cached summaries or skip LLM features if API key is missing

**Issue: Port 8501 already in use (Streamlit)**
- **Solution**: 
  - Streamlit will automatically try another port
  - Or specify a different port: `streamlit run app_streamlit.py --server.port 8502`
  - Or stop the other Streamlit instance using that port

**Issue: ModuleNotFoundError when running CLI**
- **Solution**: 
  - Make sure you're in the project root directory
  - Ensure virtual environment is activated
  - Run: `pip install -r requirements.txt`

**Issue: Permission denied errors (macOS/Linux)**
- **Solution**: 
  - Don't use `sudo` with pip when virtual environment is activated
  - If needed, fix permissions: `chmod +x .venv/bin/activate`

### Getting Help

If you encounter issues not covered here:
1. Check that all steps in Setup were completed correctly
2. Verify Python version: `python --version` (should be 3.10+)
3. Ensure virtual environment is activated
4. Try reinstalling dependencies: `pip install --upgrade -r requirements.txt`
5. Check the project structure matches what's shown in "Project Structure" section

## Project Structure

```
.
├── data/
│   ├── raw/                          # CSV files (UTF-8/UTF-16 supported)
│   │   ├── starbucks-menu-nutrition-drinks.csv
│   │   └── starbucks-menu-nutrition-food.csv
│   └── processed/                    # For future processed data
├── outputs/
│   ├── metrics/                      # Generated metrics JSON
│   └── plots/                        # Saved visualizations
├── src/starbucks_analyser/
│   ├── cli.py                        # Typer CLI commands
│   ├── data_loader.py                # CSV loading with encoding detection
│   ├── processing.py                 # Statistics and comparisons
│   ├── filters.py                    # Dietary filtering utilities
│   ├── llm/
│   │   ├── groq_client.py           # Groq API client
│   │   └── summarize.py             # LLM summarization
│   └── viz/
│       └── charts.py                 # Visualization functions
├── tests/                            # Unit tests with LLM mocking
├── app_streamlit.py                  # Optional Streamlit UI
├── pyproject.toml                    # Tool configurations
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment variable template (optional)
├── .gitignore                        # Git ignore rules
└── README.md                         # This file
```

## Notes

### Metrics and Proxies

- If an explicit `sugar_g` column is absent in the source datasets, `carbs_g` is used as a proxy for sugar in summaries. This assumption is noted in the LLM prompt to ensure transparency.

### CSV Encoding

- The data loader automatically handles UTF-8, UTF-16, and other common encodings
- Food CSV typically uses UTF-16 encoding, which is automatically detected

### Column Normalization

- Column names are normalized (e.g., "Fat (g)" → "fat_g", "Protein" → "protein_g")
- Missing columns are handled gracefully
- Duplicate items are deduplicated using first non-null value strategy

### LLM Integration

- Deterministic output for identical inputs (temperature 0.2)
- Graceful degradation when API key is missing
- Summary caching to handle rate limits
- Structured output with markdown tables and sections

## Acceptance Criteria

- ✅ Robust CSV ingestion with normalization and encoding detection
- ✅ Descriptive statistics (mean, median, min, max, totals)
- ✅ Cross-dataset comparisons (calories, sugar, fat, protein, sodium, fat-to-protein ratio)
- ✅ Multiple visualization types (top items, means, direct comparisons, extremes)
- ✅ Groq LLM summaries from deterministic metrics
- ✅ Advanced filtering utilities (single and multi-criteria)
- ✅ Optional Streamlit UI with file uploads
- ✅ Clean documentation and comprehensive tests
- ✅ Type safety with Mypy strict mode
- ✅ Quality gates (Black, Ruff, Mypy, Pytest)
