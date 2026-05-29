import pandas as pd
import numpy as np
from hplc.quant import Chromatogram


def analyze_chromatogram(
    csv_file: str,
    prominence_threshold: float = 0.01,
    output_csv: str = "peaks_summary.csv"
) -> dict:
    """
    分析色谱数据，返回峰统计信息并导出峰摘要 CSV。

    Parameters
    ----------
    csv_file : str
        输入色谱数据的 CSV 文件路径。
    prominence_threshold : float
        归一化峰高阈值，默认 0.01。
    output_csv : str
        导出峰摘要 CSV 的文件名，默认 'peaks_summary.csv'。

    Returns
    -------
    dict with keys:
        peak_count          : int   — 检测到的峰数量
        last_retention_time : float — 最后一个峰的保留时间
        min_resolution      : float — 所有相邻峰中最小的分离度
    """

    # ── 1. 加载数据 ──────────────────────────────────────────────────
    df = pd.read_csv(csv_file)
    time_col   = df.columns[0]
    signal_col = df.columns[1]
    print(f"自动识别列名: 时间列='{time_col}', 信号列='{signal_col}'")

    chrom = Chromatogram(df, cols={'time': time_col, 'signal': signal_col})

    # ── 2. 基线校正与峰拟合 ──────────────────────────────────────────
    print(f"正在进行基线校正与峰拟合 (prominence = {prominence_threshold})...")
    peaks_df = chrom.fit_peaks(prominence=prominence_threshold)

    # ── 3. 基础峰参数 ────────────────────────────────────────────────
    peak_count      = len(peaks_df)
    retention_times = peaks_df['retention_time'].values
    widths          = 4 * peaks_df['scale'].values  # W ≈ 4σ

    last_rt = float(retention_times[-1]) if peak_count > 0 else float('nan')

    # ── 4. 计算分离度（每个峰与下一个峰之间，挂在前一个峰后面）───────
    #   resolution[i] = Rs between peak i and peak i+1，存在峰 i 行
    #   最后一个峰无后继峰，填 NaN
    resolution_values = []
    print("\n" + "=" * 45)
    print(f"  积分分析报告 (共检测到 {peak_count} 个色谱峰)")
    print("=" * 45)

    for i in range(peak_count):
        area   = peaks_df['area'].values[i]
        height = peaks_df['amplitude'].values[i]

        if i < peak_count - 1:
            rt1, rt2 = retention_times[i], retention_times[i + 1]
            w1,  w2  = widths[i],          widths[i + 1]
            rs = 2 * (rt2 - rt1) / (w1 + w2)
            resolution_values.append(round(float(rs), 4))
            status = "完全分离" if rs >= 1.5 else "未完全分离"
            print(
                f"峰 {i+1}: RT = {retention_times[i]:.3f} min | "
                f"面积 = {area:.2f} | 峰高 = {height:.2f} | "
                f"Rs(峰{i+1}→峰{i+2}) = {rs:.3f} ({status})"
            )
        else:
            resolution_values.append(float('nan'))
            print(
                f"峰 {i+1}: RT = {retention_times[i]:.3f} min | "
                f"面积 = {area:.2f} | 峰高 = {height:.2f} | "
                f"Rs = —（最后一个峰）"
            )

    print("=" * 45)

    # ── 5. 最小分离度（忽略 NaN）────────────────────────────────────
    valid_rs = [r for r in resolution_values if not np.isnan(r)]
    min_resolution = float(min(valid_rs)) if valid_rs else 0.0
    print(f"\n最小分离度 Rs_min = {min_resolution:.3f}")

    # ── 6. 导出 CSV ──────────────────────────────────────────────────
    summary_df = pd.DataFrame({
        'peak_index'      : range(1, peak_count + 1),
        'retention_time'  : retention_times,
        'area'            : peaks_df['area'].values,
        'height'          : peaks_df['amplitude'].values,
        'resolution' : resolution_values,
    })
    summary_df.to_csv(output_csv, index=False)
    print(f"峰摘要已保存至: {output_csv}")

    # ── 7. 返回结果 ──────────────────────────────────────────────────
    return {
        'peak_count'          : peak_count,
        'last_retention_time' : last_rt,
        'min_resolution'      : min_resolution,
    }


# ── 调用示例 ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    result = analyze_chromatogram(
    csv_file             = 'phenyl_LHS5.csv',
    prominence_threshold = 0.01,
    output_csv           = 'peaks_summary.csv',
)


    print("\n── 返回值摘要 ──")
    print(f"峰数量             : {result['peak_count']}")
    print(f"最后一个峰保留时间 : {result['last_retention_time']:.3f} min")
    print(f"最小分离度         : {result['min_resolution']:.3f}")