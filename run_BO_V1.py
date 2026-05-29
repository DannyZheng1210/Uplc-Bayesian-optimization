import os
import time
import logging
import pandas as pd

from uplc_conf import generate_all_confs, generate_csv_conf
from rawdata2csv import read_chromatogram
from LHS import LHS_initial_experiments
from objectives_extract import analyze_chromatogram
from BOcode import run_bo_suggest

# ======================================================================
# 日志配置
# ======================================================================

logging.basicConfig(
    level    = logging.INFO,
    format   = "%(asctime)s [%(levelname)s] %(message)s",
    handlers = [
        logging.FileHandler("experiment.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ======================================================================
# 全局配置参数（根据实验需要修改这里）
# ======================================================================

# ── 实验变量 ───────────────────────────────────────────────────────────
VARIABLE_NAMES = ["organic_concentration", "isocratic_time", "gradient_time"]
LOWER_BOUNDS   = [5,  0, 0]
UPPER_BOUNDS   = [60, 1, 1]

# ── 实验轮次 ───────────────────────────────────────────────────────────
N_INITIAL       = 5     # LHS 初始实验数量
N_BO_ITERATIONS = 2    # 贝叶斯优化迭代次数

# ── UPLC 硬件参数 ──────────────────────────────────────────────────────
SAMPLE_LOCATION = "2:48"
WAVELENGTH      = 254

# ── 文件夹路径（按实际情况修改）───────────────────────────────────────
CONF_OUTPUT_DIR  = r"D:\automation_test.PRO\ACQUDB"              # UPLC 4个配置文件输出目录
CSV_CONTROL_DIR  = r"D:\autolynx"              # 控制 CSV 生成目录
PROCESSED_DIR    = r"D:\autolynx\Processed"    # UPLC 完成标志目录
RAW_DATA_DIR     = r"D:\automation_test.PRO\Data"      # UPLC raw 数据文件目录
CHROM_CSV_DIR    = "./chromatogram_data"     # 色谱 CSV 输出目录
PEAKS_CSV_DIR    = "./peaks_analysis"        # 峰分析 CSV 输出目录

# ── 总实验记录表 ───────────────────────────────────────────────────────
MASTER_CSV = "experiment_master.csv"

# ── 色谱分析参数 ───────────────────────────────────────────────────────
PROMINENCE_THRESHOLD = 0.01

# ── 延时参数 ───────────────────────────────────────────────────────────
POLL_INTERVAL        = 30   # UPLC 轮询间隔（秒）
UPLC_DONE_DELAY      = 5    # UPLC 完成后等待文件写稳定（秒）
RAW_READ_DELAY       = 3    # raw 文件读取前延时（秒）


# ======================================================================
# 工具函数
# ======================================================================

def init_master_csv(master_csv: str) -> pd.DataFrame:
    """初始化总实验记录 CSV。"""
    cols = [
        'iteration', 'algorithm',
        'organic_concentration', 'isocratic_time', 'gradient_time',
        'number_of_peak', 'critical_resolution', 'last_peak_elutes'
    ]
    if not os.path.exists(master_csv):
        df = pd.DataFrame(columns=cols)
        df.to_csv(master_csv, index=False)
        logger.info(f"[初始化] 创建总实验记录表: {master_csv}")
    else:
        logger.info(f"[初始化] 读取已有实验记录表: {master_csv}")
    return pd.read_csv(master_csv)


def init_output_dirs():
    """初始化输出文件夹。"""
    for dir_path in [CHROM_CSV_DIR, PEAKS_CSV_DIR]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            logger.info(f"[初始化] 创建输出文件夹: {dir_path}")
        else:
            logger.info(f"[初始化] 文件夹已存在: {dir_path}")


def append_variables_to_master(master_csv: str, row: dict):
    """写入 variables，objectives 列留空。"""
    df = pd.read_csv(master_csv)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(master_csv, index=False)
    logger.info(f"[记录] Variables 已写入: iteration={row['iteration']}")


def update_objectives_in_master(master_csv: str, iteration: int, result: dict):
    """根据 iteration 找到对应行，补全 objectives。"""
    df  = pd.read_csv(master_csv)
    idx = df[df['iteration'] == iteration].index
    df.loc[idx, 'number_of_peak']      = result['peak_count']
    df.loc[idx, 'critical_resolution'] = result['min_resolution']
    df.loc[idx, 'last_peak_elutes']    = result['last_retention_time']
    df.to_csv(master_csv, index=False)
    logger.info(f"[记录] Objectives 已补全: iteration={iteration} | "
                f"peaks={result['peak_count']}  "
                f"resolution={result['min_resolution']}  "
                f"last_rt={result['last_retention_time']}")


def get_valid_master_csv(master_csv: str) -> str:
    """
    过滤掉 objectives 为空的行，返回临时 CSV 路径供 BO 使用。
    避免 None 行导致 BO 算法报错。
    """
    df       = pd.read_csv(master_csv)
    df_valid = df.dropna(subset=['number_of_peak', 'critical_resolution', 'last_peak_elutes'])
    tmp_path = "bo_input_tmp.csv"
    df_valid.to_csv(tmp_path, index=False)
    logger.info(f"[BO] 有效实验数: {len(df_valid)}/{len(df)}")
    return tmp_path


def wait_for_uplc(
    processed_dir   : str,
    conf_files_name : str,
    poll_interval   : int = 30,
    done_delay      : int = 5,
) -> None:
    """
    轮询等待 UPLC 完成。
    检测到完成标志文件后，额外等待 done_delay 秒确保文件写稳定。
    """
    processed_csv = os.path.join(processed_dir, f"{conf_files_name}.csv")
    logger.info(f"[等待] 监控 UPLC 完成，目标: {processed_csv}")
    while not os.path.exists(processed_csv):
        logger.info(f"  ... 未检测到，{poll_interval}s 后重试")
        time.sleep(poll_interval)
    logger.info(f"[完成] 检测到完成标志，等待 {done_delay}s 确保文件写稳定...")
    time.sleep(done_delay)
    logger.info(f"[完成] UPLC 运行结束: {conf_files_name}")


def run_uplc_and_get_objectives(
    iteration      : int,
    conf_files_name: str,
    master_csv     : str,
) -> dict | None:
    """
    等待 UPLC 完成 → raw 转色谱 CSV → 分析 → 补全 objectives。
    分析失败时记录错误日志，objectives 保持 None，不中断主流程。
    """
    wait_for_uplc(
        processed_dir   = PROCESSED_DIR,
        conf_files_name = conf_files_name,
        poll_interval   = POLL_INTERVAL,
        done_delay      = UPLC_DONE_DELAY,
    )

    try:
        # ── raw 文件存在性检查 ─────────────────────────────────────
        raw_file = os.path.join(RAW_DATA_DIR, f"{conf_files_name}.raw")
        if not os.path.exists(raw_file):
            raise FileNotFoundError(f"raw 文件不存在: {raw_file}")

        # ── raw 转色谱 CSV ─────────────────────────────────────────
        logger.info(f"[分析] 等待 {RAW_READ_DELAY}s 后读取 raw 文件...")
        time.sleep(RAW_READ_DELAY)
        chrom_csv = read_chromatogram(raw_file, chromatogram_csv=CHROM_CSV_DIR, wavelength=WAVELENGTH)
        logger.info(f"[分析] 色谱 CSV 已生成: {chrom_csv}")

        # ── 分析色谱图提取 objectives ──────────────────────────────
        peaks_csv = os.path.join(PEAKS_CSV_DIR, f"{conf_files_name}_peaks.csv")
        result    = analyze_chromatogram(
            csv_file             = chrom_csv,
            prominence_threshold = PROMINENCE_THRESHOLD,
            output_csv           = peaks_csv,
        )

        # ── 补全 objectives ────────────────────────────────────────
        update_objectives_in_master(master_csv, iteration, result)
        return result

    except Exception as e:
        logger.error(f"[错误] iteration={iteration} ({conf_files_name}) 分析失败: {e}")
        logger.warning(f"[警告] iteration={iteration} objectives 保持 None，继续下一个实验")
        return None


# ======================================================================
# 主流程
# ======================================================================

def run_closed_loop():

    init_output_dirs()
    init_master_csv(MASTER_CSV)

    # ══════════════════════════════════════════════════════════════
    # 阶段一：LHS 初始实验
    # ══════════════════════════════════════════════════════════════
    logger.info("\n" + "█"*60)
    logger.info("  阶段一：LHS 初始实验")
    logger.info("█"*60)

    lhs_df = LHS_initial_experiments(
        variable_names = VARIABLE_NAMES,
        n_initial      = N_INITIAL,
        lower_bounds   = LOWER_BOUNDS,
        upper_bounds   = UPPER_BOUNDS,
    )

    # ── LHS 所有 variables 一次性全部写入 ─────────────────────────
    logger.info("[LHS] 一次性写入全部 variables...")
    for i, row in enumerate(lhs_df.itertuples(index=False), start=1):
        var_row = {
            'iteration'            : i,
            'algorithm'            : f"LHS{i}",
            'organic_concentration': round(row.organic_concentration, 2),
            'isocratic_time'       : round(row.isocratic_time,        2),
            'gradient_time'        : round(row.gradient_time,         2),
            'number_of_peak'       : None,
            'critical_resolution'  : None,
            'last_peak_elutes'     : None,
        }
        append_variables_to_master(MASTER_CSV, var_row)

    # ── 逐个提交 UPLC 并补全 objectives ───────────────────────────
    logger.info("[LHS] 开始逐个运行实验...")
    for i, row in enumerate(lhs_df.itertuples(index=False), start=1):
        conf_name = f"LHS{i}"

        logger.info("="*60)
        logger.info(f"  LHS 实验 {i}/{N_INITIAL} | {conf_name}")
        logger.info(f"  organic={row.organic_concentration:.2f}%  "
                    f"iso_time={row.isocratic_time:.2f}min  "
                    f"grad_time={row.gradient_time:.2f}min")
        logger.info("="*60)

        # 生成配置文件并提交 UPLC
        generate_all_confs(
            isocratic_time  = row.isocratic_time,
            gradient_time   = row.gradient_time,
            initial_org     = row.organic_concentration,
            output_dir      = CONF_OUTPUT_DIR,
            conf_files_name = conf_name,
        )
        generate_csv_conf(
            file_name       = conf_name,
            sample_location = SAMPLE_LOCATION,
            conf_names      = conf_name,
            output_dir      = CSV_CONTROL_DIR,
        )

        # 等待完成并补全 objectives
        run_uplc_and_get_objectives(
            iteration       = i,
            conf_files_name = conf_name,
            master_csv      = MASTER_CSV,
        )

    # ══════════════════════════════════════════════════════════════
    # 阶段二：贝叶斯优化迭代
    # ══════════════════════════════════════════════════════════════
    logger.info("\n" + "█"*60)
    logger.info("  阶段二：贝叶斯优化迭代")
    logger.info("█"*60)

    for bo_iter in range(1, N_BO_ITERATIONS + 1):
        iteration = N_INITIAL + bo_iter
        conf_name = f"BO{bo_iter}"

        logger.info("="*60)
        logger.info(f"  BO 第 {bo_iter}/{N_BO_ITERATIONS} 轮 | {conf_name}")
        logger.info("="*60)

        # ── BO 推荐参数 ────────────────────────────────────────────
        logger.info("[BO] 正在推荐实验条件...")
        try:
            suggested = run_bo_suggest(
                csv_file        = get_valid_master_csv(MASTER_CSV),
                num_experiments = 1,
                output_csv      = f"bo_suggested_{bo_iter}.csv",
            )
            org_conc  = float(suggested['organic_concentration'].iloc[0])
            iso_time  = float(suggested['isocratic_time'].iloc[0])
            grad_time = float(suggested['gradient_time'].iloc[0])
            logger.info(f"[BO 推荐] organic={org_conc:.2f}  "
                        f"iso={iso_time:.2f}  "
                        f"grad={grad_time:.2f}")

        except Exception as e:
            logger.error(f"[错误] BO 第 {bo_iter} 轮推荐失败: {e}")
            logger.warning(f"[警告] 跳过 BO 第 {bo_iter} 轮，继续下一轮")
            continue

        # ── 写入 variables ─────────────────────────────────────────
        var_row = {
            'iteration'            : iteration,
            'algorithm'            : conf_name,
            'organic_concentration': round(org_conc,  2),
            'isocratic_time'       : round(iso_time,  2),
            'gradient_time'        : round(grad_time, 2),
            'number_of_peak'       : None,
            'critical_resolution'  : None,
            'last_peak_elutes'     : None,
        }
        append_variables_to_master(MASTER_CSV, var_row)

        # ── 生成配置文件并提交 UPLC ────────────────────────────────
        generate_all_confs(
            isocratic_time  = iso_time,
            gradient_time   = grad_time,
            initial_org     = org_conc,
            output_dir      = CONF_OUTPUT_DIR,
            conf_files_name = conf_name,
        )
        generate_csv_conf(
            file_name       = conf_name,
            sample_location = SAMPLE_LOCATION,
            conf_names      = conf_name,
            output_dir      = CSV_CONTROL_DIR,
        )

        # ── 等待完成并补全 objectives ──────────────────────────────
        run_uplc_and_get_objectives(
            iteration       = iteration,
            conf_files_name = conf_name,
            master_csv      = MASTER_CSV,
        )

    # ── 最终输出 ───────────────────────────────────────────────────
    logger.info("\n" + "█"*60)
    logger.info("  Close-loop 优化全部完成！")
    logger.info(f"  完整实验记录: {MASTER_CSV}")
    logger.info("█"*60)

    final_df = pd.read_csv(MASTER_CSV)
    logger.info(f"\n{final_df.to_string(index=False)}")


# ======================================================================
# 入口
# ======================================================================
if __name__ == "__main__":
    run_closed_loop()