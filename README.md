# Hypsometric Analysis Toolkit

A comprehensive toolkit for hypsometric curve and integral analysis of topographic features including watersheds, valleys, circular features, and other landforms.

## Overview

This toolkit processes CSV files from QGIS Hypsometric Curves tool to calculate hypsometric integrals and generate publication-ready plots for morphological analysis.

## Features

- **Hypsometric Curve Analysis**: Calculate relative area vs. relative elevation relationships
- **Hypsometric Integral Calculation**: Quantify landform maturity and erosional state
- **Multiple Plot Modes**:
  - Relative elevation (normalized 0-1)
  - Absolute elevation (actual elevation values)
  - Individual plots for multiple features
- **Auto-increment Filenames**: Prevents overwriting previous analysis results
- **Educational Diagrams**: Optional explanatory visualizations for presentations
- **Morphological Classification**: Automatic interpretation (youthful, mature, old)

## Installation

### Requirements

```bash
pip install pandas numpy matplotlib
```

## Quick Start

```bash
# Basic analysis with sample data
python hypso_v2/hypsometric_analysis_v2.py hypso_v2/sample_data.csv

# Analyze multiple files
python hypso_v2/hypsometric_analysis_v2.py file1.csv file2.csv

# Use pattern matching
python hypsometric_analysis_v2.py -p "landform_*.csv"

# Absolute elevation mode
python hypso_v2/hypsometric_analysis_v2.py --absolute data.csv

# Create educational diagrams
python hypso_v2/hypsometric_analysis_v2.py --explain
```

## Output

Both scripts generate:
1. **PNG plot** - Hypsometric curves visualization with interpretation zones
2. **CSV results** - Detailed numerical results including:
   - Hypsometric Integral (HI) values
   - Elevation ranges and areas
   - Morphological interpretation

## Hypsometric Integral Interpretation

| HI Value | Interpretation | Characteristics |
|----------|----------------|-----------------|
| HI > 0.6 | Youthful | Convex profile, steep slopes |
| 0.35 < HI < 0.6 | Mature | S-shaped profile, balanced erosion |
| HI < 0.35 | Old | Concave profile, advanced erosion |

## Requirements

```bash
pip install pandas numpy matplotlib
```

Or using conda:
```bash
conda install pandas numpy matplotlib
```

## CSV Data Format

Input CSV files must contain:
- `Area` column - Cumulative area values (m²)
- `Elevation` column - Elevation values (m)

Generated from QGIS Hypsometric Curves tool.

## License

MIT License