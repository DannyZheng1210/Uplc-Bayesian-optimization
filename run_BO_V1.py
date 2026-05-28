import os
import time
import pandas as pd

from uplc_conf import generate_all_methods, generate_csv_conf
from rawdata2csv import read_chromatogram
from LHS import LHS_initial_experiments
from objectives_extract import analyze_chromatogram
from BOcode import run_bo_suggest

# ======================================================================
# 全局配置参数（根据实验需要修改这里）
# ======================================================================

# ── 实验变量 ───────────────────────────────────────────────────────────
VARIABLE_NAMES = ["organic_concentration", "isocratic_time", "gradient_time"]
LOWER_BOUNDS   = [5,  0, 0]
UPPER_BOUNDS   = [60, 5, 5]

# ── 实验轮次 ───────────────────────────────────────────────────────────
N_INITIAL       = 5     # LHS 初始实验数量
N_BO_ITERATIONS = 10    # 贝叶斯优化迭代次数

# ── UPLC 硬件参数 ──────────────────────────────────────────────────────
SAMPLE_LOCATION = "2:48"
WAVELENGTH      = 254

# ── 文件夹路径（按实际情况修改）───────────────────────────────────────
CONF_OUTPUT_DIR  = "./"              # UPLC 4个配置文件输出目录
CSV_CONTROL_DIR  = "./"              # 控制 CSV 生成目录（UPLC 会从这里读取并删除）
PROCESSED_DIR    = "D:/Processed"    # UPLC 完成后控制 CSV 移入的目录（完成标志）
RAW_DATA_DIR     = "D:/RawData"      # UPLC raw 数据文件所在目录
CHROM_CSV_DIR    = "./"              # 色谱 CSV 输出目录
PEAKS_CSV_DIR    = "./"              # 峰分析 CSV 输出目录

# ── 总实验记录表 ───────────────────────────────────────────────────────
MASTER_CSV = "experiment_master.csv"

# ── 色谱分析参数 ───────────────────────────────────────────────────────
PROMINENCE_THRESHOLD = 0.01

# ── 轮询间隔 ───────────────────────────────────────────────────────────
POLL_INTERVAL = 30   # 每隔多少秒检查一次（秒）


# ======================================================================
# 工具函数
# ======================================================================

def init_master_csv(master_csv: str) -> pd.DataFrame:
    """初始化总实验记录 CSV，列名全部使用下划线。"""
    cols = [
        'iteration', 'algorithm',
        'organic_concentration', 'isocratic_time', 'gradient_time',
        'number_of_peak', 'critical_resolution', 'last_peak_elutes'
    ]
    if not os.path.exists(master_csv):
        df = pd.DataFrame(columns=cols)
        df.to_csv(master_csv, index=False)
        print(f"[初始化] 创建总实验记录表: {master_csv}")
    else:
        print(f"[初始化] 读取已有实验记录表: {master_csv}")
    return pd.read_csv(master_csv)


def append_result_to_master(master_csv: str, row: dict):
    """将单次实验结果追加写入总 CSV。"""
    df = pd.read_csv(master_csv)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(master_csv, index=False)
    print(f"[记录] 实验结果已写入: {master_csv}")


def wait_for_uplc(
    processed_dir   : str,
    conf_files_name : str,
    poll_interval   : int = 30,
) -> None:
    """
    轮询等待 UPLC 完成。
    判断标准：processed_dir 里出现 {conf_files_name}.csv。
    AutoLynx 运行结束后会删除源控制 CSV，并在 Processed 目录生成同名 CSV。
    """
    processed_csv = os.path.join(processed_dir, f"{conf_files_name}.csv")
    print(f"[等待] 监控 UPLC 完成，目标: {processed_csv}")
    while not os.path.exists(processed_csv):
        print(f"  ... 未检测到，{poll_interval}s 后重试")
        time.sleep(poll_interval)
    print(f"[完成] UPLC 运行结束")


def run_one_experiment(
    iteration      : int,
    algorithm      : str,
    org_conc       : float,
    iso_time       : float,
    grad_time      : float,
    conf_files_name: str,
    master_csv     : str,
):
    """
    执行一次完整的实验流程：
      1. 生成 UPLC 4个配置文件 + 控制 CSV
      2. 等待 UPLC 完成（两阶段监控）
      3. raw 数据转色谱 CSV
      4. 分析色谱图提取 objectives
      5. 将结果追加到总 CSV
    """
    print(f"\n{'='*60}")
    print(f"  迭代 {iteration:>3} | 算法: {algorithm}")
    print(f"  organic={org_conc:.2f}%  iso_time={iso_time:.2f}min  grad_time={grad_time:.2f}min")
    print(f"{'='*60}")

    # ── 1. 生成配置文件 + 控制 CSV ────────────────────────────────
    generate_all_methods(
        isocratic_time  = iso_time,
        gradient_time   = grad_time,
        initial_org     = org_conc,
        output_dir      = CONF_OUTPUT_DIR,
        conf_files_name = conf_files_name,
    )
    generate_csv_conf(
        file_name       = conf_files_name,
        sample_location = SAMPLE_LOCATION,
        conf_names      = conf_files_name,
        output_dir      = CSV_CONTROL_DIR,
    )

    # ── 2. 等待 UPLC 完成 ──────────────────────────────────────────
    wait_for_uplc(
        processed_dir   = PROCESSED_DIR,
        conf_files_name = conf_files_name,
        poll_interval   = POLL_INTERVAL,
    )

    # ── 3. raw 转色谱 CSV ──────────────────────────────────────────
    raw_file  = os.path.join(RAW_DATA_DIR, f"{conf_files_name}.raw")
    read_chromatogram(raw_file, chromatogram_csv=CHROM_CSV_DIR, wavelength=WAVELENGTH)
    chrom_csv = os.path.join(CHROM_CSV_DIR, f"{conf_files_name}.csv")

    # ── 4. 分析色谱图提取 objectives ──────────────────────────────
    peaks_csv = os.path.join(PEAKS_CSV_DIR, f"{conf_files_name}_peaks.csv")
    result = analyze_chromatogram(
        csv_file             = chrom_csv,
        prominence_threshold = PROMINENCE_THRESHOLD,
        output_csv           = peaks_csv,
    )

    # ── 5. 追加到总 CSV ────────────────────────────────────────────
    row = {
        'iteration'            : iteration,
        'algorithm'            : algorithm,
        'organic_concentration': round(org_conc,  2),
        'isocratic_time'       : round(iso_time,  2),
        'gradient_time'        : round(grad_time, 2),
        'number_of_peak'       : result['peak_count'],
        'critical_resolution'  : result['min_resolution'],
        'last_peak_elutes'     : result['last_retention_time'],
    }
    append_result_to_master(master_csv, row)
    return result


# ======================================================================
# 主流程
# ======================================================================

def run_closed_loop():

    init_master_csv(MASTER_CSV)

    # ══════════════════════════════════════════════════════════════
    # 阶段一：LHS 初始实验
    # ══════════════════════════════════════════════════════════════
    print("\n" + "█"*60)
    print("  阶段一：LHS 初始实验")
    print("█"*60)

    lhs_df = LHS_initial_experiments(
        variable_names = VARIABLE_NAMES,
        n_initial      = N_INITIAL,
        lower_bounds   = LOWER_BOUNDS,
        upper_bounds   = UPPER_BOUNDS,
    )

    for i, row in enumerate(lhs_df.itertuples(index=False), start=1):
        conf_name = f"LHS{i}"
        run_one_experiment(
            iteration       = i,
            algorithm       = conf_name,
            org_conc        = row.organic_concentration,
            iso_time        = row.isocratic_time,
            grad_time       = row.gradient_time,
            conf_files_name = conf_name,
            master_csv      = MASTER_CSV,
        )

    # ══════════════════════════════════════════════════════════════
    # 阶段二：贝叶斯优化迭代
    # ══════════════════════════════════════════════════════════════
    print("\n" + "█"*60)
    print("  阶段二：贝叶斯优化迭代")
    print("█"*60)

    for bo_iter in range(1, N_BO_ITERATIONS + 1):
        iteration = N_INITIAL + bo_iter
        conf_name = f"BO{bo_iter}"

        print(f"\n[BO 第 {bo_iter} 轮] 正在推荐实验条件...")
        suggested = run_bo_suggest(
            csv_file        = MASTER_CSV,
            num_experiments = 1,
            output_csv      = f"bo_suggested_{bo_iter}.csv",
        )

        org_conc  = float(suggested['organic_concentration'].iloc[0])
        iso_time  = float(suggested['isocratic_time'].iloc[0])
        grad_time = float(suggested['gradient_time'].iloc[0])
        print(f"[BO 推荐] organic={org_conc:.2f}  iso={iso_time:.2f}  grad={grad_time:.2f}")

        run_one_experiment(
            iteration       = iteration,
            algorithm       = conf_name,
            org_conc        = org_conc,
            iso_time        = iso_time,
            grad_time       = grad_time,
            conf_files_name = conf_name,
            master_csv      = MASTER_CSV,
        )

    print("\n" + "█"*60)
    print("  Close-loop 优化全部完成！")
    print(f"  完整实验记录: {MASTER_CSV}")
    print("█"*60)
    print(pd.read_csv(MASTER_CSV).to_string(index=False))


# ======================================================================
# 入口
# ======================================================================
if __name__ == "__main__":
    run_closed_loop()