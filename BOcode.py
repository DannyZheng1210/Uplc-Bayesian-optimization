import pandas as pd
import torch
from botorch.models import SingleTaskGP
from botorch.models.transforms.input import Normalize
from botorch.models.transforms.outcome import Standardize
from botorch.fit import fit_gpytorch_mll
from botorch.optim import optimize_acqf
from botorch.acquisition.multi_objective.logei import qLogNoisyExpectedHypervolumeImprovement
from gpytorch.mlls import ExactMarginalLogLikelihood


def run_bo_suggest(
    csv_file       : str,
    num_experiments: int = 1,
    output_csv     : str = "bo_suggested.csv",
) -> pd.DataFrame:
    """
    读取历史实验数据，用 qLogNEHVI 多目标贝叶斯优化推荐下一个实验点。

    目标：
        number_of_peak      → 最大化
        critical_resolution → 最大化
        last_peak_elutes    → 最小化（取负数转为最大化）

    Parameters
    ----------
    csv_file        : 历史数据 CSV（experiment_master.csv）
    num_experiments : 推荐点数量，默认 1
    output_csv      : 推荐结果保存路径

    Returns
    -------
    pd.DataFrame，列为 organic_concentration / isocratic_time / gradient_time
    """

    # ── 1. 变量范围 ───────────────────────────────────────────────
    BOUNDS = torch.tensor([
        [5.0,  0.0, 0.0],   # 下界: organic_concentration, isocratic_time, gradient_time
        [60.0, 5.0, 5.0],   # 上界
    ], dtype=torch.double)

    # ── 2. 读取历史数据 ───────────────────────────────────────────
    df = pd.read_csv(csv_file)

    # 兼容列名有空格的旧版本
    df = df.rename(columns={
        'critical resolution': 'critical_resolution',
        'last peak elutes'   : 'last_peak_elutes',
    })

    required = [
        'organic_concentration', 'isocratic_time', 'gradient_time',
        'number_of_peak', 'critical_resolution', 'last_peak_elutes'
    ]
    df = df[required].dropna()
    print(f"读取到 {len(df)} 条有效历史数据。")

    # ── 3. 准备训练数据 ───────────────────────────────────────────
    train_X = torch.tensor(
        df[['organic_concentration', 'isocratic_time', 'gradient_time']].values,
        dtype=torch.double
    )

    # last_peak_elutes 取负数，统一为最大化方向
    Y_peak       = torch.tensor(df[['number_of_peak']].values,      dtype=torch.double)
    Y_resolution = torch.tensor(df[['critical_resolution']].values, dtype=torch.double)
    Y_last_peak  = torch.tensor(df[['last_peak_elutes']].values,    dtype=torch.double) * -1.0

    train_Y = torch.cat([Y_peak, Y_resolution, Y_last_peak], dim=1)  # shape: (n, 3)

    # ── 4. 参考点（比历史最差值再低一点，qLogNEHVI 必需）─────────
    ref_point = train_Y.min(dim=0).values - 0.1

    # ── 5. 训练 GP 模型 ───────────────────────────────────────────
    print("正在训练 GP 模型...")
    model = SingleTaskGP(
        train_X,
        train_Y,
        input_transform   = Normalize(d=train_X.shape[-1]),
        outcome_transform = Standardize(m=train_Y.shape[-1]),
    )
    mll = ExactMarginalLogLikelihood(model.likelihood, model)
    fit_gpytorch_mll(mll)

    # ── 6. 构建 qLogNEHVI 采集函数 ───────────────────────────────
    print("正在优化采集函数，推荐实验条件...")
    acq = qLogNoisyExpectedHypervolumeImprovement(
        model          = model,
        ref_point      = ref_point,
        X_baseline     = train_X,
        prune_baseline = True,
    )

    # ── 7. 优化采集函数，得到推荐点 ──────────────────────────────
    candidates, _ = optimize_acqf(
        acq_function = acq,
        bounds       = BOUNDS,
        q            = num_experiments,
        num_restarts = 10,
        raw_samples  = 128,
    )

    # ── 8. 整理输出 ───────────────────────────────────────────────
    result_df = pd.DataFrame(
        candidates.detach().numpy(),
        columns=['organic_concentration', 'isocratic_time', 'gradient_time']
    )
    result_df.index = result_df.index + 1

    print("\n── 推荐实验条件 ──────────────────────────────────────")
    print(result_df.to_string())
    print("─────────────────────────────────────────────────────")

    result_df.to_csv(output_csv, index_label='experiment_index')
    print(f"推荐结果已保存至: {output_csv}")

    return result_df


# ── 调用示例 ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    result = run_bo_suggest(
        csv_file        = 'experiment_master.csv',
        num_experiments = 1,
        output_csv      = 'bo_suggested.csv',
    )
    print(result)