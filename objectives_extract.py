import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from hplc.quant import Chromatogram


def analyze_chromatogram(
    csv_file: str,
    prominence_threshold: float = 0.01,
    output_csv: str = "peaks_summary.csv",
    output_plot: str = None
) -> dict:
    """
    Analyze chromatogram data, return peak statistics and export peak summary CSV.

    Parameters
    ----------
    csv_file : str
        Input chromatogram CSV file path.
    prominence_threshold : float
        Normalized peak height threshold, default 0.01.
    output_csv : str
        Output peak summary CSV filename, default 'peaks_summary.csv'.
    output_plot : str, optional
        Output chromatogram plot image path (.png). If None, no plot will be saved.

    Returns
    -------
    dict with keys:
        peak_count          : int   — Number of detected peaks
        last_retention_time : float — Retention time of last peak
        min_resolution      : float — Minimum resolution among adjacent peaks
    """

    # ── 1. Load data ────────────────────────────────────────────────────
    df = pd.read_csv(csv_file)
    time_col   = df.columns[0]
    signal_col = df.columns[1]
    print(f"Auto-detected column names: time_col='{time_col}', signal_col='{signal_col}'")

    chrom = Chromatogram(df, cols={'time': time_col, 'signal': signal_col})

    # ── 2. Baseline correction and peak fitting ─────────────────────────
    print(f"Performing baseline correction and peak fitting (prominence = {prominence_threshold})...")
    peaks_df = chrom.fit_peaks(prominence=prominence_threshold)

    # ── 3. Basic peak parameters ────────────────────────────────────────
    peak_count      = len(peaks_df)
    retention_times = peaks_df['retention_time'].values
    widths          = 4 * peaks_df['scale'].values  # W ≈ 4σ

    last_rt = float(retention_times[-1]) if peak_count > 0 else float('nan')

    # ── 4. Calculate resolution (between each peak and next peak)────────
    #   resolution[i] = Rs between peak i and peak i+1, stored in peak i row
    #   Last peak has no successor, filled with NaN
    resolution_values = []
    print("\n" + "=" * 45)
    print(f"  Integration Analysis Report (Total {peak_count} peaks detected)")
    print("=" * 45)

    for i in range(peak_count):
        area   = peaks_df['area'].values[i]
        height = peaks_df['amplitude'].values[i]

        if i < peak_count - 1:
            rt1, rt2 = retention_times[i], retention_times[i + 1]
            w1,  w2  = widths[i],          widths[i + 1]
            rs = 2 * (rt2 - rt1) / (w1 + w2)
            resolution_values.append(round(float(rs), 4))
            status = "Fully Resolved" if rs >= 1.5 else "Partially Resolved"
            print(
                f"Peak {i+1}: RT = {retention_times[i]:.3f} min | "
                f"Area = {area:.2f} | Height = {height:.2f} | "
                f"Rs(Peak{i+1}→Peak{i+2}) = {rs:.3f} ({status})"
            )
        else:
            resolution_values.append(float('nan'))
            print(
                f"Peak {i+1}: RT = {retention_times[i]:.3f} min | "
                f"Area = {area:.2f} | Height = {height:.2f} | "
                f"Rs = —(Last peak)"
            )

    print("=" * 45)

    # ── 5. Minimum resolution (ignoring NaN) ────────────────────────────
    valid_rs = [r for r in resolution_values if not np.isnan(r)]
    min_resolution = float(min(valid_rs)) if valid_rs else 0.0
    print(f"\nMinimum resolution Rs_min = {min_resolution:.3f}")

    # ── 6. Export CSV ───────────────────────────────────────────────────
    summary_df = pd.DataFrame({
        'peak_index'      : range(1, peak_count + 1),
        'retention_time'  : retention_times,
        'area'            : peaks_df['area'].values,
        'height'          : peaks_df['amplitude'].values,
        'resolution' : resolution_values,
    })
    summary_df.to_csv(output_csv, index=False)
    print(f"Peak summary saved to: {output_csv}")

    # ── 7. Plot and save chromatogram ────────────────────────────────────
    if output_plot is not None:
        try:
            # Use hplc-py library's show() method to generate the plot with fitted peaks
            fig, ax = chrom.show()
            fig.suptitle(f'Chromatogram Analysis (Total Peaks: {peak_count})', fontsize=13, fontweight='bold')
            
            plt.tight_layout()
            plt.savefig(output_plot, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"Chromatogram plot saved to: {output_plot}")
        except Exception as e:
            print(f"Warning: Failed to save chromatogram plot: {e}")

    # ── 8. Return results ───────────────────────────────────────────────
    return {
        'peak_count'          : peak_count,
        'last_retention_time' : last_rt,
        'min_resolution'      : min_resolution,
    }


# ── Usage example ────────────────────────────────────────────────────────
if __name__ == "__main__":
    result = analyze_chromatogram(
    csv_file             = 'phenyl_LHS5.csv',
    prominence_threshold = 0.01,
    output_csv           = 'peaks_summary.csv',
    output_plot          = 'chromatogram_plot.png',
)
    output_csv           = 'peaks_summary.csv',
)


    print("\n── Return value summary ──")
    print(f"Peak count             : {result['peak_count']}")
    print(f"Last peak retention time : {result['last_retention_time']:.3f} min")
    print(f"Minimum resolution      : {result['min_resolution']:.3f}")