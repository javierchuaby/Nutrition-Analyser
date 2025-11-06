# Starbucks Nutrition Analyser - Project Handoff

## ✅ Project Status: COMPLETE

All core functionality has been implemented and validated. The project is production-ready with robust error handling, type safety, and comprehensive testing.

## 🎯 Acceptance Criteria Status

- ✅ **Robust CSV ingestion**: Both drinks and food CSVs load correctly with UTF-8/UTF-16 encoding detection and schema normalization
- ✅ **Descriptive statistics**: Generated and saved to `outputs/metrics/metrics.json`
- ✅ **Cross-dataset comparisons**: Calorie comparison between drinks and food implemented
- ✅ **Visualization**: Bar chart of top drinks by calories saved to `outputs/plots/top_drinks.png`
- ✅ **Groq summarization**: LLM integration ready (requires `.env` with `GROQ_API_KEY`)
- ✅ **Filtering utilities**: `filter-food-under` command working correctly
- ✅ **Streamlit UI**: Optional web interface implemented
- ✅ **Quality gates**: Black, Ruff, Mypy, and Pytest all passing

## 📁 Project Structure

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
│   ├── __init__.py
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
└── README.md                         # Project documentation

```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher (Python 3.11+ recommended)
- pip (Python package manager)
- Starbucks menu CSV files

### Step 1: Verify Python Installation

Check if Python is installed:

```bash
python --version
# or
python3 --version
```

Should show Python 3.10.x or higher. If not installed:
- **macOS**: `brew install python3` or download from [python.org](https://www.python.org/downloads/)
- **Windows**: Download from [python.org](https://www.python.org/downloads/)
- **Linux**: `sudo apt install python3 python3-pip` (Ubuntu/Debian)

### Step 2: Create Virtual Environment

```bash
# Navigate to project directory
cd "path/to/Starbucks Analyser"

# Create virtual environment
python -m venv .venv
# or
python3 -m venv .venv
```

### Step 3: Activate Virtual Environment

**macOS/Linux:**
```bash
source .venv/bin/activate
```

**Windows (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

You should see `(.venv)` at the start of your prompt when activated.

### Step 4: Install Dependencies

**Recommended (using requirements.txt):**
```bash
pip install -r requirements.txt
```

**Alternative (manual installation):**
```bash
pip install pandas numpy matplotlib streamlit typer python-dotenv groq
```

**For development tools (optional):**
```bash
pip install black ruff mypy pytest types-python-dotenv
```

### Step 5: Verify Installation

Test that packages are installed correctly:

```bash
python -c "import pandas, numpy, matplotlib, streamlit, typer; print('Installation successful!')"
```

### Step 6: Configure Environment (Optional)

LLM summarization requires a Groq API key. The app works without it, but some features will be unavailable.

1. **Create `.env` file:**
   ```bash
   # Copy the example (if it exists)
   cp .env.example .env
   
   # Or create manually
   echo "GROQ_API_KEY=your_actual_groq_api_key_here" > .env
   ```

2. **Edit `.env`** and add your Groq API key:
   ```
   GROQ_API_KEY=your_actual_groq_api_key_here
   ```
   
   Get your API key from: https://console.groq.com/

### Step 7: Prepare Data Files

Place CSV files in `data/raw/`:

```bash
mkdir -p data/raw
# Copy your CSV files:
# - data/raw/starbucks-menu-nutrition-drinks.csv
# - data/raw/starbucks-menu-nutrition-food.csv
```

### Step 8: Verify Setup

Test that everything works:

```bash
# Test CLI
python -m src.starbucks_analyser.cli --help

# Test Streamlit
streamlit run app_streamlit.py
```

If both commands work, setup is complete!

## 📋 Usage Examples

### CLI Commands

```bash
# Generate statistics and metrics
python -m src.starbucks_analyser.cli stats \
    data/raw/starbucks-menu-nutrition-drinks.csv \
    data/raw/starbucks-menu-nutrition-food.csv \
    --out outputs/metrics/metrics.json

# Compare drinks vs food (prints JSON)
python -m src.starbucks_analyser.cli compare \
    data/raw/starbucks-menu-nutrition-drinks.csv \
    data/raw/starbucks-menu-nutrition-food.csv

# Filter food items under 300 calories (prints CSV)
python -m src.starbucks_analyser.cli filter-food-under \
    data/raw/starbucks-menu-nutrition-food.csv \
    --max-calories 300

# Generate visualization (top 10 drinks by calories)
python -m src.starbucks_analyser.cli viz-top \
    data/raw/starbucks-menu-nutrition-drinks.csv \
    --column calories --top-n 10 \
    --out outputs/plots/top_drinks.png

# Generate visualization (top 10 food items)
python -m src.starbucks_analyser.cli viz-top-food \
    data/raw/starbucks-menu-nutrition-food.csv \
    --column calories --top-n 10 \
    --out outputs/plots/top_food.png

# Generate grouped means comparison chart
python -m src.starbucks_analyser.cli viz-means \
    data/raw/starbucks-menu-nutrition-drinks.csv \
    data/raw/starbucks-menu-nutrition-food.csv \
    --out outputs/plots/means_comparison.png

# Multi-criteria filtering
python -m src.starbucks_analyser.cli filter-multi \
    data/raw/starbucks-menu-nutrition-drinks.csv \
    --calories-le 200 \
    --sugar-g-le 25 \
    --protein-ge 5 \
    --name-contains "latte"

# Generate LLM summary (requires GROQ_API_KEY in .env)
python -m src.starbucks_analyser.cli summarize \
    --metrics-path outputs/metrics/metrics.json
```

### 4. Run Streamlit UI (Recommended)

```bash
# Make sure virtual environment is activated
streamlit run app_streamlit.py
```

**What happens:**
- Streamlit starts a local web server
- Browser opens automatically at `http://localhost:8501`
- Upload CSV files through the web interface
- View visualizations and summaries interactively

**To stop:** Press `Ctrl+C` in the terminal

## 🧪 Quality Assurance

All quality gates are passing:

```bash
# Format code
black .

# Lint code
ruff check .

# Type check
mypy src

# Run tests
pytest -q
```

## 📊 Sample Output

### Metrics (`outputs/metrics/metrics.json`)
- **Drinks**: Descriptive stats (count, means, medians, mins, maxs, totals) for all nutrients
- **Food**: Descriptive stats (count, means, medians, mins, maxs, totals) for all nutrients
- **Comparisons**: Direct comparisons between drinks and food including:
  - Average calories difference
  - Average sugar/carbs difference
  - Average fat, protein, sodium differences
  - Fat-to-protein ratio comparison
  - Largest difference metric identification
- **Top Items**: Top 10 items by calories and sugar for both drinks and food

### Visualizations
Multiple chart types are generated:
- `top_drinks.png` / `top_food.png`: Top N items bar charts
- `means_comparison.png`: Grouped bar chart comparing nutrient means
- `overall_average_comparisons.png`: Overall average comparison visualization
- `direct_comparisons.png`: Direct metric-by-metric comparisons
- `extremes_comparison.png`: Comparison of extreme values (min/max)

## 🔧 Technical Details

### CSV Loading
- Automatically handles UTF-8, UTF-16, and other common encodings
- Normalizes column names (handles variations like "Fat (g)" → "fat_g", "Protein" → "protein_g")
- Coerces numeric columns with proper NA handling
- Deduplicates items by name (case-insensitive) using first non-null value strategy
- Handles missing columns gracefully
- Validates schema and reports data quality issues

### Type Safety
- Full type hints on all public functions
- Mypy strict mode enabled and passing
- Pandas stubs installed for better type checking

### LLM Integration
- Groq API client with error handling
- Deterministic metrics-based prompts (temperature 0.2)
- Structured output with markdown tables and sections
- Summary caching to handle API rate limits
- Graceful degradation when API key is missing
- Cached summaries displayed when API fails

### Visualization Functions
- `bar_top_items`: Top N items bar chart (CLI command: `viz-top`, `viz-top-food`)
- `grouped_means_bar`: Grouped means comparison (CLI command: `viz-means`)
- `overall_average_comparisons`: Overall average comparison chart (Streamlit)
- `direct_comparisons`: Direct metric comparisons chart (Streamlit)
- `extremes_comparison`: Min/max extremes comparison (Streamlit)

### Filtering Capabilities
- Single column filtering: `filter-food-under`, `filter-column`
- Multi-criteria filtering: `filter-multi` with support for:
  - Calories (≤)
  - Sugar/Carbs (≤)
  - Fat (≤)
  - Protein (≥)
  - Sodium (≤)
  - Caffeine (>)
  - Name contains (substring search, case-insensitive)

## 🔧 Troubleshooting

### Common Installation Issues

**"command not found: python" or "python: command not found"**
- Use `python3` instead of `python`
- Ensure Python is installed and in your PATH
- On Windows, you may need to add Python to PATH during installation

**"No module named 'pandas'" or similar import errors**
- Ensure virtual environment is activated (you should see `(.venv)` in prompt)
- Run: `pip install -r requirements.txt`
- Check you're using the correct Python interpreter

**"streamlit: command not found"**
- Install Streamlit: `pip install streamlit`
- Ensure virtual environment is activated

**"Permission denied" errors (macOS/Linux)**
- Don't use `sudo` with pip when virtual environment is activated
- Fix permissions: `chmod +x .venv/bin/activate`

**Port 8501 already in use (Streamlit)**
- Streamlit will automatically try another port
- Or specify: `streamlit run app_streamlit.py --server.port 8502`
- Or stop the other Streamlit instance

### Runtime Issues

**CSV files not loading**
- Check file paths are correct
- Ensure CSV files are in `data/raw/` directory (or use Streamlit upload)
- Verify CSV has required columns (see README)
- Check file encoding (app handles UTF-8 and UTF-16 automatically)

**"GROQ_API_KEY missing" error**
- LLM features are optional - app works without them
- Create `.env` file with API key (see Step 6)
- App will use cached summaries or skip LLM features if API key is missing

**ModuleNotFoundError when running CLI**
- Ensure you're in the project root directory
- Virtual environment must be activated
- Run: `pip install -r requirements.txt`

**Visualization errors**
- Ensure matplotlib is installed: `pip install matplotlib`
- Check that output directory exists: `mkdir -p outputs/plots`

### Getting Help

If issues persist:
1. Verify all setup steps were completed correctly
2. Check Python version: `python --version` (should be 3.10+)
3. Ensure virtual environment is activated
4. Try reinstalling: `pip install --upgrade -r requirements.txt`
5. Check project structure matches documentation

## 📝 Notes

1. **CSV Encoding**: The food CSV typically uses UTF-16 encoding, which is automatically detected and handled. The loader tries multiple encodings (UTF-8, UTF-16, Latin-1, etc.) until one succeeds.

2. **Missing Columns**: Some CSVs may not have all nutrition columns (e.g., food CSV doesn't have sodium). The code handles missing columns gracefully by filling with NaN.

3. **Sugar Proxy**: If `sugar_g` column is absent, `carbs_g` is used as a proxy in summaries. This is noted in the LLM prompt for transparency.

4. **Deduplication**: Items with duplicate names (case-insensitive) are merged using a "first non-null value" strategy, then the first row is kept as tie-breaker.

5. **Streamlit File Uploads**: The Streamlit app uses temporary files to handle uploaded CSV files since pandas expects file paths. Files are cleaned up after processing.

6. **Environment Variables**: The `.env` file is gitignored. Create it manually or copy from `.env.example` if it exists.

7. **LLM Rate Limits**: The Streamlit app caches successful summaries and displays cached versions when API rate limits are hit. Cache is invalidated when API key changes.

8. **Column Name Support**: The code supports both new normalized names (`item_name`, `sodium`) and legacy names (`item`, `sodium_mg`) for backward compatibility.

## 🎓 Future Enhancements

Potential improvements:
- Add more advanced comparison metrics (percentiles, distributions)
- Implement interactive visualizations (Plotly, Bokeh)
- Add export functionality (PDF reports, Excel)
- Create requirements.txt file for easier dependency management
- Add GitHub Actions CI/CD pipeline
- Expand test coverage for edge cases
- Add data validation rules and warnings
- Implement data quality scoring
- Add support for custom nutrition goals/targets
- Create comparison templates for different use cases

## 📧 Support

For issues or questions:
- Check the README.md for detailed documentation
- Review test files for usage examples
- All code follows PEP 8 and type hints standards

---

**Project completed**: November 2024  
**Python version**: 3.10+ (tested on 3.14)  
**All acceptance criteria met** ✅
