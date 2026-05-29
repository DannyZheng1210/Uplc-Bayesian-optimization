import rainbow as rb
import os

def read_chromatogram(chromatogram_rawdata, chromatogram_csv="./", wavelength=254):
    """
    将 .raw 文件转换为色谱 CSV。
    
    Parameters
    ----------
    chromatogram_rawdata : str
        输入的 .raw 文件路径
    chromatogram_csv : str
        输出 CSV 目录（默认当前目录）
    wavelength : int or list
        检测波长（默认 254nm）
    
    Returns
    -------
    str
        生成的 CSV 文件路径
    
    Raises
    ------
    FileNotFoundError
        如果输入文件不存在
    ValueError
        如果找不到 UV 检测器
    """
    # ── 检查输入文件 ───────────────────────────────────────────
    if not os.path.exists(chromatogram_rawdata):
        raise FileNotFoundError(f"raw 文件不存在: {chromatogram_rawdata}")
    
    # ── 读取 raw 文件 ──────────────────────────────────────────
    datadir = rb.read(chromatogram_rawdata)
    
    # ── 构造输出路径 ───────────────────────────────────────────
    base_name = os.path.splitext(os.path.basename(chromatogram_rawdata))[0]
    output_path = os.path.join(chromatogram_csv, f"{base_name}.csv")
    
    # ── 查找 UV 检测器并导出 ────────────────────────────────────
    uv_found = False
    for f in datadir.datafiles:
        if f.detector == "UV":
            f.export_csv(output_path, labels=wavelength)
            uv_found = True
            print(f"[成功] 色谱 CSV 已生成: {output_path}")
            break
    
    if not uv_found:
        raise ValueError(f"找不到 UV 检测器 在 {chromatogram_rawdata}")
    
    return output_path


# ── 调用示例 ────────────────────────────────────────────────
if __name__ == "__main__":
    result = read_chromatogram("phenyl_LHS5.raw", wavelength=254)
    print(f"输出文件: {result}")