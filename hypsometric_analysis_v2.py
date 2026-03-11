#!/usr/bin/env python3
"""
Hypsometric Curve and Integral Analysis for Topographic Features
Processes CSV files from QGIS Hypsometric Curves tool for any landform analysis

Applicable to:
- Drainage basins and watersheds
- Volcanic features and circular landforms
- Mountain ranges and valleys
- Erosional landforms
- Any topographic polygon with elevation variation

Usage:
    python hypsometric_analysis_v2.py file1.csv file2.csv file3.csv
    python hypsometric_analysis_v2.py folder/*.csv
    python hypsometric_analysis_v2.py -p "pattern*.csv"
    python hypsometric_analysis_v2.py  # Uses default pattern histogram_*.csv
    python hypsometric_analysis_v2.py --absolute  # Plot with absolute elevation values
    python hypsometric_analysis_v2.py --explain  # Create explanatory diagrams

Examples:
    python hypsometric_analysis_v2.py watershed_analysis/*.csv
    python hypsometric_analysis_v2.py basin_1.csv basin_2.csv valley_3.csv
    python hypsometric_analysis_v2.py -p "landform_analysis_*.csv"
    python hypsometric_analysis_v2.py --absolute landform_*.csv  # Absolute elevation mode
    python hypsometric_analysis_v2.py --explain --absolute  # Both features combined
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
import os
import sys
import argparse
from pathlib import Path

def get_unique_filename(filename):
    """
    Generate a unique filename by adding (n) if file already exists
    Similar to browser download behavior
    """
    path = Path(filename)
    if not path.exists():
        return filename

    stem = path.stem
    suffix = path.suffix
    counter = 1

    while True:
        new_filename = f"{stem}({counter}){suffix}"
        if not Path(new_filename).exists():
            return new_filename
        counter += 1

def calculate_hypsometric_data(csv_file):
    """
    Calculate relative area and relative elevation from hypsometric CSV
    Returns relative values and hypsometric integral
    """
    # Read the CSV file
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        print(f"Error reading {csv_file}: {e}")
        return None, None, None, None, None, None, None

    # Extract feature ID from filename (remove path and extension)
    feature_id = Path(csv_file).stem

    # Clean up feature ID if it follows common QGIS patterns
    if feature_id.startswith('histogram_'):
        # Remove common histogram prefix patterns
        feature_id = feature_id.replace('histogram_', 'Feature_')

    # Validate required columns
    if 'Area' not in df.columns or 'Elevation' not in df.columns:
        print(f"Error: {csv_file} must contain 'Area' and 'Elevation' columns")
        return None, None, None, None, None, None, None

    # Get min and max values
    min_elevation = df['Elevation'].min()
    max_elevation = df['Elevation'].max()
    max_area = df['Area'].max()

    if max_elevation == min_elevation:
        print(f"Warning: No elevation variation in {csv_file}")
        return None, None, None, feature_id, min_elevation, max_elevation, max_area

    # Calculate relative values
    # Relative elevation (h/H): 0 at lowest point, 1 at highest
    df['rel_elevation'] = (df['Elevation'] - min_elevation) / (max_elevation - min_elevation)

    # Relative area (a/A): normalized cumulative area from 1 to 0
    df['rel_area'] = 1 - (df['Area'] / max_area)

    # Calculate hypsometric integral using trapezoidal rule
    # HI = area under the curve of rel_area vs rel_elevation
    hi = np.trapezoid(df['rel_area'], df['rel_elevation'])

    # Calculate HI using the elevation formula as well
    mean_elevation = np.average(df['Elevation'], weights=np.diff(np.append([0], df['Area'])))
    hi_formula = (mean_elevation - min_elevation) / (max_elevation - min_elevation)

    return df, hi, hi_formula, feature_id, min_elevation, max_elevation, max_area

def plot_hypsometric_curves(csv_files, output_prefix="hypsometric_analysis", absolute_mode=False):
    """
    Plot all hypsometric curves and calculate integrals

    Parameters:
    csv_files: list of CSV files to process
    output_prefix: prefix for output files
    absolute_mode: if True, use absolute elevation values and create separate plots
    """
    if not csv_files:
        print("No CSV files found!")
        return None

    results = []
    successful_plots = 0

    if absolute_mode and len(csv_files) > 1:
        # In absolute mode with multiple files, create separate plots for each
        print(f"Absolute mode with {len(csv_files)} files - creating separate plots for each feature")

        for i, csv_file in enumerate(csv_files):
            print(f"Processing: {csv_file}")

            result = calculate_hypsometric_data(csv_file)
            df, hi, hi_formula, feature_id, min_elev, max_elev, max_area = result

            if df is None:
                continue

            # Create individual plot for this feature
            plt.figure(figsize=(10, 8))

            plt.plot(df['rel_area'], df['Elevation'],
                    'b-', linewidth=3, label=f'{feature_id} (HI={hi:.3f})')

            # Fill under curve to show integral
            plt.fill_between(df['rel_area'], min_elev, df['Elevation'],
                            alpha=0.3, color='blue')

            # Format individual plot
            plt.xlabel('Relative Area (a/A)\n[a = cumulative area, A = total area]', fontsize=12)
            plt.ylabel('Elevation (m)', fontsize=12)
            plt.title(f'Hypsometric Curve: {feature_id}\nAbsolute Elevation', fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.xlim(0, 1)
            plt.ylim(min_elev, max_elev)

            # Add explanatory text
            explanation_text = (
                f"Feature: {feature_id}\n"
                f"Elevation range: {min_elev:.1f} - {max_elev:.1f} m ({max_elev-min_elev:.1f} m)\n"
                f"Area: {max_area:.1f} m²\n"
                f"Hypsometric Integral: {hi:.3f} ({interpret_hi(hi)})"
            )
            plt.figtext(0.5, -0.02, explanation_text, fontsize=10, style='italic',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.8),
                        horizontalalignment='center', verticalalignment='top')

            plt.tight_layout()

            # Save individual plot
            individual_plot_filename = f'{output_prefix}_{feature_id}_absolute.png'
            individual_plot_filename = get_unique_filename(individual_plot_filename)
            plt.savefig(individual_plot_filename, dpi=300, bbox_inches='tight')
            plt.close()

            print(f"Individual plot saved: {individual_plot_filename}")

            # Store results
            results.append({
                'feature_id': feature_id,
                'file_path': csv_file,
                'hypsometric_integral_curve': hi,
                'hypsometric_integral_formula': hi_formula,
                'min_elevation': min_elev,
                'max_elevation': max_elev,
                'elevation_range': max_elev - min_elev,
                'max_area': max_area,
                'interpretation': interpret_hi(hi)
            })

            print(f"{feature_id}:")
            print(f"  File: {csv_file}")
            print(f"  Elevation range: {min_elev:.1f} - {max_elev:.1f} m ({max_elev-min_elev:.1f} m)")
            print(f"  Area: {max_area:.1f} m²")
            print(f"  HI (curve): {hi:.3f}")
            print(f"  HI (formula): {hi_formula:.3f}")
            print(f"  Interpretation: {interpret_hi(hi)}")
            print()

            successful_plots += 1

    else:
        # Standard combined plot (for relative mode or single file in absolute mode)
        plt.figure(figsize=(12, 8))
        colors = plt.cm.tab10(np.linspace(0, 1, len(csv_files)))

        for i, csv_file in enumerate(csv_files):
            print(f"Processing: {csv_file}")

            result = calculate_hypsometric_data(csv_file)
            df, hi, hi_formula, feature_id, min_elev, max_elev, max_area = result

            if df is None:
                continue

            # Plot the curve
            if absolute_mode:
                plt.plot(df['rel_area'], df['Elevation'],
                        label=f'{feature_id} (HI={hi:.3f})',
                        color=colors[i % len(colors)], linewidth=2)

                # Fill under curve to show integral
                plt.fill_between(df['rel_area'], min_elev, df['Elevation'],
                                alpha=0.3, color=colors[i % len(colors)])
            else:
                plt.plot(df['rel_area'], df['rel_elevation'],
                        label=f'{feature_id} (HI={hi:.3f})',
                        color=colors[i % len(colors)], linewidth=2)

                # Fill under curve to show integral
                plt.fill_between(df['rel_area'], 0, df['rel_elevation'],
                                alpha=0.3, color=colors[i % len(colors)])

            # Store results
            results.append({
                'feature_id': feature_id,
                'file_path': csv_file,
                'hypsometric_integral_curve': hi,
                'hypsometric_integral_formula': hi_formula,
                'min_elevation': min_elev,
                'max_elevation': max_elev,
                'elevation_range': max_elev - min_elev,
                'max_area': max_area,
                'interpretation': interpret_hi(hi)
            })

            print(f"{feature_id}:")
            print(f"  File: {csv_file}")
            print(f"  Elevation range: {min_elev:.1f} - {max_elev:.1f} m ({max_elev-min_elev:.1f} m)")
            print(f"  Area: {max_area:.1f} m²")
            print(f"  HI (curve): {hi:.3f}")
            print(f"  HI (formula): {hi_formula:.3f}")
            print(f"  Interpretation: {interpret_hi(hi)}")
            print()

            successful_plots += 1

        if successful_plots == 0:
            print("No valid data to plot!")
            return None

        # Format combined plot
        plt.xlabel('Relative Area (a/A)\n[a = cumulative area, A = total area]', fontsize=12)

        if absolute_mode:
            plt.ylabel('Elevation (m)', fontsize=12)
            plt.title(f'Hypsometric Curves Analysis - Absolute Elevation ({successful_plots} features)', fontsize=14, fontweight='bold')
            # Set y-axis limits for absolute mode
            all_min = min([result['min_elevation'] for result in results])
            all_max = max([result['max_elevation'] for result in results])
            plt.ylim(all_min, all_max)
        else:
            plt.ylabel('Relative Elevation (h/H)\n[h = height above minimum, H = total height range]', fontsize=12)
            plt.title(f'Hypsometric Curves Analysis ({successful_plots} features)', fontsize=14, fontweight='bold')
            plt.ylim(0, 1)

        plt.grid(True, alpha=0.3)
        legend = plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.xlim(0, 1)

        # Add explanatory text below the legend
        if absolute_mode:
            explanation_text = (
                "Relative Area (a/A): Normalized cumulative area from total (A) to zero\n"
                "Absolute Elevation: Actual elevation values in meters\n"
                "where: a = cumulative area, A = total area\n"
                "Hypsometric Integral (HI) = area under the relative curve (shows landform maturity)"
            )
        else:
            explanation_text = (
                "Relative Area (a/A): Normalized cumulative area from total (A) to zero\n"
                "Relative Elevation (h/H): Normalized elevation from minimum (0) to maximum (1)\n"
                "where: a = cumulative area, A = total area, h = elevation above minimum, H = total elevation range\n"
                "Hypsometric Integral (HI) = area under the curve (shows landform maturity)"
            )

        # Position explanatory text below the graph
        plt.figtext(0.5, -0.02, explanation_text, fontsize=9, style='italic',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.8),
                    horizontalalignment='center', verticalalignment='top')

        plt.tight_layout()

        # Save combined plot
        plot_filename = f'{output_prefix}_curves.png'
        plot_filename = get_unique_filename(plot_filename)
        plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"Combined plot saved: {plot_filename}")

    # Create results DataFrame and save
    if successful_plots > 0:
        results_df = pd.DataFrame(results)
        results_filename = f'{output_prefix}_results.csv'
        results_filename = get_unique_filename(results_filename)
        results_df.to_csv(results_filename, index=False)
        print(f"Results saved: {results_filename}")
        return results_df
    else:
        print("No valid data to plot!")
        return None

def interpret_hi(hi):
    """
    Interpret hypsometric integral value
    """
    if hi > 0.6:
        return "Youthful - Convex profile, steep slopes"
    elif hi > 0.35:
        return "Mature - S-shaped profile, balanced erosion"
    else:
        return "Old - Concave profile, advanced erosion"

def create_explanatory_diagram(output_prefix="hypsometric_analysis"):
    """
    Create additional explanatory diagrams for better understanding
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    # 1. Theoretical hypsometric curve types
    x = np.linspace(0, 1, 100)

    # Youthful (convex) - exponential
    y_young = np.power(x, 0.3)
    # Mature (S-shaped) - sine-based
    y_mature = 0.5 + 0.5 * np.sin((x - 0.5) * np.pi)
    # Old (concave) - power
    y_old = np.power(x, 2)

    ax1.plot(x, y_young, 'r-', linewidth=3, label='Youthful (HI > 0.6)')
    ax1.plot(x, y_mature, 'orange', linewidth=3, label='Mature (0.35 < HI < 0.6)')
    ax1.plot(x, y_old, 'blue', linewidth=3, label='Old (HI < 0.35)')
    ax1.fill_between(x, 0, y_young, alpha=0.3, color='red')
    ax1.fill_between(x, 0, y_mature, alpha=0.3, color='orange')
    ax1.fill_between(x, 0, y_old, alpha=0.3, color='blue')

    ax1.set_xlabel('Relative Area (a/A)')
    ax1.set_ylabel('Relative Elevation (h/H)')
    ax1.set_title('Theoretical Hypsometric Curve Types')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)

    # 2. What the axes mean - conceptual diagram
    ax2.text(0.5, 0.9, 'Understanding the Axes', ha='center', fontsize=14, fontweight='bold')
    ax2.text(0.1, 0.7, 'Relative Area (a/A):', fontsize=12, fontweight='bold')
    ax2.text(0.1, 0.6, '• a = cumulative area from lowest elevation', fontsize=10)
    ax2.text(0.1, 0.55, '• A = total feature area', fontsize=10)
    ax2.text(0.1, 0.5, '• Range: 0 (no area) to 1 (total area)', fontsize=10)

    ax2.text(0.1, 0.35, 'Relative Elevation (h/H):', fontsize=12, fontweight='bold')
    ax2.text(0.1, 0.25, '• h = height above minimum elevation', fontsize=10)
    ax2.text(0.1, 0.2, '• H = total elevation range', fontsize=10)
    ax2.text(0.1, 0.15, '• Range: 0 (minimum) to 1 (maximum)', fontsize=10)

    ax2.text(0.1, 0.05, 'Hypsometric Integral = Area under the curve', fontsize=12,
             fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))

    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.axis('off')

    # 3. Landform evolution stages
    stages_x = [0.2, 0.5, 0.8]
    stages_y = [0.8, 0.5, 0.2]
    stages_labels = ['YOUTHFUL\nSteep slopes\nLittle erosion',
                     'MATURE\nBalanced\nModerate erosion',
                     'OLD\nGentle slopes\nHeavy erosion']

    colors = ['red', 'orange', 'blue']

    for i, (x_pos, y_pos, label, color) in enumerate(zip(stages_x, stages_y, stages_labels, colors)):
        circle = plt.Circle((x_pos, y_pos), 0.08, color=color, alpha=0.6)
        ax3.add_patch(circle)
        ax3.text(x_pos, y_pos-0.15, label, ha='center', va='top', fontsize=10, fontweight='bold')

    # Add arrows
    ax3.annotate('', xy=(0.45, 0.5), xytext=(0.25, 0.8),
                arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    ax3.annotate('', xy=(0.75, 0.2), xytext=(0.55, 0.5),
                arrowprops=dict(arrowstyle='->', lw=2, color='black'))

    ax3.text(0.5, 0.95, 'Landform Evolution Over Time', ha='center', fontsize=14, fontweight='bold')
    ax3.text(0.3, 0.65, 'Erosion', ha='center', fontsize=10, style='italic')
    ax3.text(0.65, 0.35, 'Erosion', ha='center', fontsize=10, style='italic')

    ax3.set_xlim(0, 1)
    ax3.set_ylim(0, 1)
    ax3.axis('off')

    # 4. Real-world applications
    ax4.text(0.5, 0.95, 'Applications of Hypsometric Analysis', ha='center', fontsize=14, fontweight='bold')

    applications = [
        '🏔️ Mountain Ranges: Assess tectonic vs. erosional control',
        '🌊 Watersheds: Evaluate drainage basin maturity',
        '💥 Circular Features: Determine preservation state',
        '🌋 Volcanic Features: Analyze degradation patterns',
        '🏞️ Coastal Cliffs: Study retreat processes',
        '❄️ Glacial Valleys: Examine erosional history'
    ]

    for i, app in enumerate(applications):
        ax4.text(0.05, 0.8 - i*0.12, app, fontsize=11, va='center')

    ax4.set_xlim(0, 1)
    ax4.set_ylim(0, 1)
    ax4.axis('off')

    plt.tight_layout()

    # Save explanatory diagram
    explanation_filename = f'{output_prefix}_explanation.png'
    explanation_filename = get_unique_filename(explanation_filename)
    plt.savefig(explanation_filename, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Explanatory diagram saved: {explanation_filename}")

    return explanation_filename

def main():
    parser = argparse.ArgumentParser(
        description='Hypsometric curve and integral analysis for topographic features',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s file1.csv file2.csv file3.csv
  %(prog)s analysis_v2/*.csv
  %(prog)s -p "new_analysis_*.csv"
  %(prog)s -o my_analysis landform_*.csv
        """
    )

    parser.add_argument('csv_files', nargs='*',
                       help='CSV files to analyze (default: histogram_*.csv)')
    parser.add_argument('-p', '--pattern',
                       help='File pattern to match (e.g., "analysis_*.csv")')
    parser.add_argument('-o', '--output', default='hypsometric_analysis',
                       help='Output filename prefix (default: hypsometric_analysis)')
    parser.add_argument('--absolute', action='store_true',
                       help='Plot absolute elevation values instead of relative elevation')
    parser.add_argument('--explain', action='store_true',
                       help='Create additional explanatory diagrams for better understanding')

    args = parser.parse_args()

    print("Hypsometric Curve and Integral Analysis")
    print("=" * 60)

    # Determine which files to process
    csv_files = []

    if args.pattern:
        # Use pattern matching
        csv_files = glob.glob(args.pattern)
        if not csv_files:
            print(f"No files found matching pattern: {args.pattern}")
            sys.exit(1)
        print(f"Found {len(csv_files)} files matching pattern: {args.pattern}")
    elif args.csv_files:
        # Use provided file list
        csv_files = args.csv_files
        # Check if files exist
        for file in csv_files:
            if not os.path.exists(file):
                print(f"Warning: File not found: {file}")
        csv_files = [f for f in csv_files if os.path.exists(f)]
        if not csv_files:
            print("No valid files found!")
            sys.exit(1)
    else:
        # Use default pattern
        csv_files = glob.glob('histogram_*.csv')
        if not csv_files:
            print("No files found with default pattern 'histogram_*.csv'")
            print("Please specify CSV files or use -p flag with a pattern")
            sys.exit(1)
        print(f"Using default pattern, found {len(csv_files)} files")

    csv_files.sort()
    print(f"Processing {len(csv_files)} files:")
    for file in csv_files:
        print(f"  - {file}")
    print()

    # Process the files
    results = plot_hypsometric_curves(csv_files, args.output, args.absolute)

    # Create explanatory diagrams if requested
    if args.explain:
        print("\nCreating explanatory diagrams...")
        create_explanatory_diagram(args.output)

    if results is not None:
        print("\nSummary of Results:")
        print("=" * 60)
        print(results[['feature_id', 'hypsometric_integral_curve', 'interpretation']].to_string(index=False))
    else:
        print("Analysis failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()