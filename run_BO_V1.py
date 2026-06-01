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
# Project Name Configuration (modify here to create new project)
# ======================================================================
PROJECT_NAME = "test_001"  # Modify here for your project name

# ======================================================================
# Logging Configuration
# ======================================================================

logging.basicConfig(
    level    = logging.INFO,
    format   = "%(asctime)s [%(levelname)s] %(message)s",
    handlers = [
        logging.FileHandler(f"{PROJECT_NAME}_experiment.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ======================================================================
# Global Configuration Parameters (modify here according to experiment needs)
# ======================================================================

# ── Experiment Variables ───────────────────────────────────────────────
VARIABLE_NAMES = ["organic_concentration", "isocratic_time", "gradient_time"]
LOWER_BOUNDS   = [5,  0, 0]
UPPER_BOUNDS   = [60, 1, 3]

# ── Experiment Iterations ───────────────────────────────────────────────
N_INITIAL       = 2     # Number of initial LHS experiments
N_BO_ITERATIONS = 2    # Number of Bayesian optimization iterations

# ── UPLC Hardware Parameters ────────────────────────────────────────────
SAMPLE_LOCATION = "2:48"
WAVELENGTH      = 254

# ── Folder Paths (modify according to actual situation) ─────────────────
CONF_OUTPUT_DIR  = r"D:\automation_test.PRO\ACQUDB"              # UPLC configuration files output directory
CSV_CONTROL_DIR  = r"D:\autolynx"              # CSV control generation directory
PROCESSED_DIR    = r"D:\autolynx\Processed"    # UPLC completion flag directory
RAW_DATA_DIR     = r"D:\automation_test.PRO\Data"      # UPLC raw data file directory
CHROM_CSV_DIR    = f"./{PROJECT_NAME}_chromatogram_data"     # Chromatogram CSV output directory
PEAKS_CSV_DIR    = f"./{PROJECT_NAME}_peaks_analysis"        # Peak analysis CSV output directory

# ── Master Experiment Record Table ───────────────────────────────────────
MASTER_CSV = f"{PROJECT_NAME}_experiment_master.csv"

# ── Chromatogram Analysis Parameters ────────────────────────────────────
PROMINENCE_THRESHOLD = 0.01

# ── Delay Parameters ────────────────────────────────────────────────────
POLL_INTERVAL        = 15   # UPLC polling interval (seconds)
UPLC_DONE_DELAY      = 5    # Wait time after UPLC completion for file stability (seconds)
RAW_READ_DELAY       = 3    # Delay before reading raw file (seconds)


# ======================================================================
# Utility Functions
# ======================================================================

def init_master_csv(master_csv: str) -> pd.DataFrame:
    """Initialize the master experiment record CSV."""
    cols = [
        'iteration', 'algorithm',
        'organic_concentration', 'isocratic_time', 'gradient_time',
        'number_of_peak', 'critical_resolution', 'last_peak_elutes'
    ]
    if not os.path.exists(master_csv):
        df = pd.DataFrame(columns=cols)
        df.to_csv(master_csv, index=False)
        logger.info(f"[Initialize] Create master experiment record: {master_csv}")
    else:
        logger.info(f"[Initialize] Load existing experiment record: {master_csv}")
    return pd.read_csv(master_csv)


def init_output_dirs():
    """Initialize output directories."""
    for dir_path in [CHROM_CSV_DIR, PEAKS_CSV_DIR]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            logger.info(f"[Initialize] Create output directory: {dir_path}")
        else:
            logger.info(f"[Initialize] Directory already exists: {dir_path}")


def append_variables_to_master(master_csv: str, row: dict):
    """Write variables to master CSV, leave objectives columns empty."""
    df = pd.read_csv(master_csv)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(master_csv, index=False)
    logger.info(f"[Record] Variables written: iteration={row['iteration']}")


def update_objectives_in_master(master_csv: str, iteration: int, result: dict):
    """Find row by iteration and complete objectives columns."""
    df  = pd.read_csv(master_csv)
    idx = df[df['iteration'] == iteration].index
    df.loc[idx, 'number_of_peak']      = result['peak_count']
    df.loc[idx, 'critical_resolution'] = result['min_resolution']
    df.loc[idx, 'last_peak_elutes']    = result['last_retention_time']
    df.to_csv(master_csv, index=False)
    logger.info(f"[Record] Objectives completed: iteration={iteration} | "
                f"peaks={result['peak_count']}  "
                f"resolution={result['min_resolution']}  "
                f"last_rt={result['last_retention_time']}")


def get_valid_master_csv(master_csv: str) -> str:
    """
    Filter out rows with empty objectives and return temporary CSV path for BO.
    Avoid None rows causing BO algorithm errors.
    """
    df       = pd.read_csv(master_csv)
    df_valid = df.dropna(subset=['number_of_peak', 'critical_resolution', 'last_peak_elutes'])
    tmp_path = f"{PROJECT_NAME}_bo_input_tmp.csv"
    df_valid.to_csv(tmp_path, index=False)
    logger.info(f"[BO] Valid experiments: {len(df_valid)}/{len(df)}")
    return tmp_path


def wait_for_uplc(
    processed_dir   : str,
    conf_files_name : str,
    poll_interval   : int = 30,
    done_delay      : int = 5,
) -> None:
    """
    Poll and wait for UPLC completion.
    After detecting the completion flag file, wait additional done_delay seconds to ensure file stability.
    """
    processed_csv = os.path.join(processed_dir, f"{conf_files_name}.csv")
    logger.info(f"[Wait] Monitoring UPLC completion, target: {processed_csv}")
    while not os.path.exists(processed_csv):
        logger.info(f"  ... Not detected, retry after {poll_interval}s")
        time.sleep(poll_interval)
    logger.info(f"[Done] Completion flag detected, waiting {done_delay}s to ensure file stability...")
    time.sleep(done_delay)
    logger.info(f"[Done] UPLC run completed: {conf_files_name}")


def run_uplc_and_get_objectives(
    iteration      : int,
    conf_files_name: str,
    master_csv     : str,
) -> dict | None:
    """
    Wait for UPLC completion → convert raw to chromatogram CSV → analyze → complete objectives.
    On analysis failure, log error and keep objectives as None, do not interrupt main workflow.
    """
    wait_for_uplc(
        processed_dir   = PROCESSED_DIR,
        conf_files_name = conf_files_name,
        poll_interval   = POLL_INTERVAL,
        done_delay      = UPLC_DONE_DELAY,
    )

    try:
        # ── Check raw file existence ────────────────────────────────
        raw_file = os.path.join(RAW_DATA_DIR, f"{conf_files_name}.raw")
        if not os.path.exists(raw_file):
            raise FileNotFoundError(f"Raw file does not exist: {raw_file}")

        # ── Convert raw to chromatogram CSV ─────────────────────────
        logger.info(f"[Analysis] Waiting {RAW_READ_DELAY}s before reading raw file...")
        time.sleep(RAW_READ_DELAY)
        chrom_csv = read_chromatogram(raw_file, chromatogram_csv=CHROM_CSV_DIR, wavelength=WAVELENGTH)
        logger.info(f"[Analysis] Chromatogram CSV generated: {chrom_csv}")

        # ── Analyze chromatogram and extract objectives ──────────────
        peaks_csv = os.path.join(PEAKS_CSV_DIR, f"{conf_files_name}_peaks.csv")
        result    = analyze_chromatogram(
            csv_file             = chrom_csv,
            prominence_threshold = PROMINENCE_THRESHOLD,
            output_csv           = peaks_csv,
        )

        # ── Complete objectives ────────────────────────────────────
        update_objectives_in_master(master_csv, iteration, result)
        return result

    except Exception as e:
        logger.error(f"[Error] iteration={iteration} ({conf_files_name}) analysis failed: {e}")
        logger.warning(f"[Warning] iteration={iteration} objectives remain None, continue to next experiment")
        return None


# ======================================================================
# Main Workflow
# ======================================================================

def run_closed_loop():

    init_output_dirs()
    init_master_csv(MASTER_CSV)

    # ══════════════════════════════════════════════════════════════
    # Phase 1: LHS Initial Experiments
    # ══════════════════════════════════════════════════════════════
    logger.info("\n" + "█"*60)
    logger.info("  Phase 1: LHS Initial Experiments")
    logger.info("█"*60)

    lhs_df = LHS_initial_experiments(
        variable_names = VARIABLE_NAMES,
        n_initial      = N_INITIAL,
        lower_bounds   = LOWER_BOUNDS,
        upper_bounds   = UPPER_BOUNDS,
    )

    # ── Write all LHS variables at once ────────────────────────────
    logger.info("[LHS] Write all variables at once...")
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

    # ── Submit to UPLC one by one and complete objectives ─────────
    logger.info("[LHS] Starting experiments one by one...")
    for i, row in enumerate(lhs_df.itertuples(index=False), start=1):
        conf_name = f"LHS{i}"

        logger.info("="*60)
        logger.info(f"  LHS Experiment {i}/{N_INITIAL} | {conf_name}")
        logger.info(f"  organic={row.organic_concentration:.2f}%  "
                    f"iso_time={row.isocratic_time:.2f}min  "
                    f"grad_time={row.gradient_time:.2f}min")
        logger.info("="*60)

        # Generate configuration files and submit to UPLC
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

        # Wait for completion and complete objectives
        run_uplc_and_get_objectives(
            iteration       = i,
            conf_files_name = conf_name,
            master_csv      = MASTER_CSV,
        )

    # ══════════════════════════════════════════════════════════════
    # Phase 2: Bayesian Optimization Iterations
    # ══════════════════════════════════════════════════════════════
    logger.info("\n" + "█"*60)
    logger.info("  Phase 2: Bayesian Optimization Iterations")
    logger.info("█"*60)

    for bo_iter in range(1, N_BO_ITERATIONS + 1):
        iteration = N_INITIAL + bo_iter
        conf_name = f"BO{bo_iter}"

        logger.info("="*60)
        logger.info(f"  BO Iteration {bo_iter}/{N_BO_ITERATIONS} | {conf_name}")
        logger.info("="*60)

        # ── BO recommends parameters ────────────────────────────────
        logger.info("[BO] Recommending experiment conditions...")
        try:
            suggested = run_bo_suggest(
                csv_file        = get_valid_master_csv(MASTER_CSV),
                num_experiments = 1,
                output_csv      = f"{PROJECT_NAME}_bo_suggested_{bo_iter}.csv",
            )
            org_conc  = float(suggested['organic_concentration'].iloc[0])
            iso_time  = float(suggested['isocratic_time'].iloc[0])
            grad_time = float(suggested['gradient_time'].iloc[0])
            logger.info(f"[BO Recommended] organic={org_conc:.2f}  "
                        f"iso={iso_time:.2f}  "
                        f"grad={grad_time:.2f}")

        except Exception as e:
            logger.error(f"[Error] BO iteration {bo_iter} recommendation failed: {e}")
            logger.warning(f"[Warning] Skip BO iteration {bo_iter}, continue next")
            continue

        # ── Write variables ────────────────────────────────────────
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

        # ── Generate configuration files and submit to UPLC ────────
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

        # ── Wait for completion and complete objectives ───────────
        run_uplc_and_get_objectives(
            iteration       = iteration,
            conf_files_name = conf_name,
            master_csv      = MASTER_CSV,
        )

    # ── Final output ──────────────────────────────────────────────
    logger.info("\n" + "█"*60)
    logger.info("  Close-loop optimization completed!")
    logger.info(f"  Complete experiment record: {MASTER_CSV}")
    logger.info("█"*60)

    final_df = pd.read_csv(MASTER_CSV)
    logger.info(f"\n{final_df.to_string(index=False)}")


# ======================================================================
# Entry Point
# ======================================================================
if __name__ == "__main__":
    run_closed_loop()