# ==============================================================================
#  1. 核心控制变量（修改这里即可）
# ==============================================================================
flow_rate = 0.500                     # mL/min: 全局流速
initial_organic_concentration = 40.0   # %B: 初始等度阶段的有机相浓度
max_organic_concentration = 100.0     # %B: 爬坡结束达到的最大有机相浓度

isocratic_time = 2.0                  # min: 初始等度保持时间
gradient_time = 3.0                   # min: 从初始浓度线性运行到最大浓度的时间
iteration_n = 15                       # 输出文件编号


# ==============================================================================
#  2. 辅助格式化函数（原模板 12/16 空格缩进）
# ==============================================================================
def format_row(time_val, flow, a, b, c, d, curve):
    """生成单行标准原模板缩进（Row占12格，内部子项占16格）的XML文本"""
    time_str = "Initial" if time_val == "Initial" else f"{float(time_val):.2f}"
    return (
        f"            <GradientRow>\n"
        f"                <Time>{time_str}</Time>\n"
        f"                <Flow>{flow:.3f}</Flow>\n"
        f"                <CompositionA>{a:.1f}</CompositionA>\n"
        f"                <CompositionB>{b:.1f}</CompositionB>\n"
        f"                <CompositionC>{c:.1f}</CompositionC>\n"
        f"                <CompositionD>{d:.1f}</CompositionD>\n"
        f"                <Curve>{curve}</Curve>\n"
        f"            </GradientRow>"
    )


# ==============================================================================
#  3. 主生成函数
# ==============================================================================
def generate_qsm(isocratic_time, gradient_time, initial_org, max_org, flow, output_path="method.qsm"):
    # 动态计算浓度比例
    init_a = round(100.0 - initial_org, 1)
    init_b = round(float(initial_org), 1)
    max_a = round(100.0 - max_org, 1)
    max_b = round(float(max_org), 1)
    post_b = 5.0 if max_org >= 5.0 else max_org
    post_a = round(100.0 - post_b, 1)

    # 计算时间轴节点
    t1 = isocratic_time       
    t2 = t1 + gradient_time   
    t3 = t2 + 1.0             
    t4 = t3 + 0.5             
    t5 = t4 + 1.0             
    run_time = t5

    # 梯度表数据定义
    rows = [
        ("Initial", flow, init_a, init_b, 0.0, 0.0, "Initial"),
        (t1,        flow, init_a, init_b, 0.0, 0.0, "6"),        
        (t2,        flow, max_a,  max_b,  0.0, 0.0, "6"),        
        (t3,        flow, max_a,  max_b,  0.0, 0.0, "6"),        
        (t4,        flow, post_a, post_b, 0.0, 0.0, "6"),        
        (t5,        flow, post_a, post_b, 0.0, 0.0, "6"),        
    ]

    # 分开处理：前5行正常带换行，第6行尾部不带换行，紧贴 </GradientTable>
    all_blocks = [format_row(*r) for r in rows]
    front_block = "\n".join(all_blocks[:-1])  
    last_block = all_blocks[-1]               

    # 全局使用纯空格替换原先的 \t，确保在任何编辑器中排版一致
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<AcquityQSMMethod xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="AcquityQSM-Method-r100.xsd" version="4" modified="true">
    <RunTime>{run_time:.2f}</RunTime>
    <SolventNameA></SolventNameA>
    <SolventNameB></SolventNameB>
    <SolventNameC></SolventNameC>
    <SolventNameD></SolventNameD>
    <SolventTypeA>1</SolventTypeA>
    <SolventTypeB>1</SolventTypeB>
    <SolventTypeC>1</SolventTypeC>
    <SolventTypeD>1</SolventTypeD>
    <SolventXmlA></SolventXmlA>
    <SolventXmlB></SolventXmlB>
    <SolventXmlC></SolventXmlC>
    <SolventXmlD></SolventXmlD>
    <LowPressureLimit>0</LowPressureLimit>
    <HighPressureLimit>15000</HighPressureLimit>
    <SealWashPeriod>5.00</SealWashPeriod>
    <VentValvePosition>VentValvePositionSystem_1</VentValvePosition>
    <GradientTable>
{front_block}
{last_block}</GradientTable>
    <Comment/>
    <FlowRampRate>0.45</FlowRampRate>
    <PreInjectorVolume>0</PreInjectorVolume>
    <StrokeVolume>50 uL   (flow &lt;= 2.000 mL/min)</StrokeVolume>
    <SystemReequilibrationVolume>0</SystemReequilibrationVolume>
    <SystemReequilibrationVentPoint>SystemReequilibrationVentPointSolventManager_0</SystemReequilibrationVentPoint>
    <SystemReequilibrationFlowRate>2.000</SystemReequilibrationFlowRate>
    <ColumnReequilibrationVolume>0</ColumnReequilibrationVolume>
    <SolventSelectionValveAPosition>0</SolventSelectionValveAPosition>
    <SolventSelectionValveBPosition>0</SolventSelectionValveBPosition>
    <SolventSelectionValveCPosition>0</SolventSelectionValveCPosition>
    <SolventSelectionValveDPosition>0</SolventSelectionValveDPosition>
    <IsICSInExclusiveMode>false</IsICSInExclusiveMode>
    <SystemPressureDataEnable>false</SystemPressureDataEnable>
    <FlowRateDataEnable>false</FlowRateDataEnable>
    <PercentADataEnable>false</PercentADataEnable>
    <PercentBDataEnable>false</PercentBDataEnable>
    <PercentCDataEnable>false</PercentCDataEnable>
    <PercentDDataEnable>false</PercentDDataEnable>
    <PrimaryDataEnable>false</PrimaryDataEnable>
    <AccumulatorDataEnable>false</AccumulatorDataEnable>
    <DegasserDataEnable>false</DegasserDataEnable>
    <UseCompositionGradientTable>true</UseCompositionGradientTable>
    <AcidName/><AcidConcentration>0</AcidConcentration><AcidXml/>
    <BaseName/><BaseConcentration>0</BaseConcentration><BaseXml/>
    <SaltName/><SaltConcentration>0</SaltConcentration><SaltXml/>
    <AqueousName/><AqueousXml/>
    <BufferSystemName/><BufferSystemConcentration>0</BufferSystemConcentration>
    <BufferSystemUsePka>true</BufferSystemUsePka>
    <BufferSystemPka>7.00</BufferSystemPka>
    <BufferSystemMinimumPh>6.00</BufferSystemMinimumPh>
    <BufferSystemMaximumPh>7.00</BufferSystemMaximumPh>
    <BufferSystemXml/>
    <PhSaltGradientTable>
        <PhSaltGradientTableRow>
            <Time>Initial_0</Time>
            <Flow>{flow:.3f}</Flow>
            <Ph>7.00</Ph>
            <PhCurve>Initial_0</PhCurve>
            <SaltConcentration>0</SaltConcentration>
            <SaltCurve>Initial_0</SaltCurve>
        </PhSaltGradientTableRow>
    </PhSaltGradientTable>
    <ALineSolventType>0</ALineSolventType>
    <BLineSolventType>1</BLineSolventType>
    <CLineSolventType>2</CLineSolventType>
    <DLineSolventType>3</DLineSolventType>
    <GradientStartTime>GradientStartTimeAtInjection_0</GradientStartTime>
    <GradientStartUl>0</GradientStartUl>
    <GradientStartMin>0.00</GradientStartMin>
    <PreanalysisModeEnabled>false</PreanalysisModeEnabled>
</AcquityQSMMethod>"""

    # 4. 写入输出文件
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xml_content)

    # 5. 控制台终端打印图表功能（用于肉眼快速核对）
    print("=" * 65)
    print(f"成功生成方法文件: {output_path}")
    print(f"液相总运行时间 (RunTime) : {run_time:.2f} min")
    print("-" * 65)
    header = f"  {'Time':>8}  {'Flow':>6}  {'%A':>6}  {'%B':>6}  {'%C':>4}  {'%D':>4}  Curve"
    print(header)
    for r in rows:
        t = r[0] if r[0] == "Initial" else f"{float(r[0]):.2f}"
        print(f"  {t:>8}  {r[1]:>6.3f}  {r[2]:>6.1f}  {r[3]:>6.1f}  {r[4]:>4.1f}  {r[5]:>4.1f}  {r[6]}")
    print("=" * 65)

    return xml_content


# ==============================================================================
#  4. 运行入口
# ==============================================================================
if __name__ == "__main__":
    generate_qsm(
        isocratic_time=isocratic_time,
        gradient_time=gradient_time,
        initial_org=initial_organic_concentration,
        max_org=max_organic_concentration,
        flow=flow_rate,
        output_path=f"iteration_{iteration_n:02d}.qsm",
    )