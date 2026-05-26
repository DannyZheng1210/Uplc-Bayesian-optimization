import os
import csv

# ==============================================================================
#  1. 核心控制变量（保留作为脚本直接运行或导入时的全局默认参考）
# ==============================================================================
flow_rate = 0.300                     # mL/min: 全局流速
initial_organic_concentration = 30.0  # %B: 初始等度阶段的有机相浓度
max_organic_concentration = 100.0     # %B: 爬坡结束达到的最大有机相浓度

isocratic_time = 3.0                  # min: 初始等度保持时间
gradient_time = 7.0                   # min: 从初始浓度线性运行到最大浓度的时间
iteration_n = 16                      # 输出文件统一编号（用于批量生成时命名）

hold_at_max_time = 1.0    # min: 到达最大有机相后的保持时间
ramp_down_time = 0.5      # min: 从最大有机相回冲到初始浓度的时间
re_equil_time = 1.0       # min: 再平衡保持时间


# ==============================================================================
#  2. 辅助格式化函数
# ==============================================================================
def format_qsm_row(time_val, flow, a, b, c, d, curve):
    """生成单行标准原模板缩进的 XML 文本"""
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
#  3. 各文件独立生成函数
# ==============================================================================
def generate_qsm(base_name, run_time_str, flow, init_a, init_b, max_a, max_b,
                 post_a, post_b, t1, t2, t3, t4, t5, qsm_rows):
    """生成液相梯度方法文件 (.qsm)"""
    all_blocks = [format_qsm_row(*r) for r in qsm_rows]
    front_block = "\n".join(all_blocks[:-1])
    last_block = all_blocks[-1]

    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<AcquityQSMMethod xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="AcquityQSM-Method-r100.xsd" version="4" modified="true">
    <RunTime>{run_time_str}</RunTime>
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

    with open(f"{base_name}.qsm", "w", encoding="utf-8") as f:
        f.write(content)


def generate_tuv(base_name, run_time_str):
    """生成紫外检测器方法文件 (.v2487)"""
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<AcquityTUVMethod xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="AcquityTUV-Method-r100.xsd" version="1" modified="true">
\t<RunTime>{run_time_str}</RunTime>
\t<WavelengthMode>2</WavelengthMode>
\t<Lamp>true</Lamp>
\t<ChannelA>
\t\t<Description/>
\t\t<Wavelength>254</Wavelength>
\t\t<DataRate>DualDataRate_1B</DataRate>
\t\t<DataMode>DualModeA_1B</DataMode>
\t\t<FilterType>Filter_2</FilterType>
\t\t<TimeConstant>2.0000</TimeConstant>
\t\t<RatioMinimum>0.0001</RatioMinimum>
\t\t<AutoZeroWavelength>Az_3</AutoZeroWavelength>
\t\t<AutoZeroInjectStart>true</AutoZeroInjectStart>
\t\t<AutoZeroEventOrKey>true</AutoZeroEventOrKey>
\t</ChannelA>
\t<ChannelB>
\t\t<Description/>
\t\t<Wavelength>270</Wavelength>
\t\t<DataRate>DualDataRate_1B</DataRate>
\t\t<DataMode>DualModeB_2C</DataMode>
\t\t<FilterType>Filter_2</FilterType>
\t\t<TimeConstant>2.0000</TimeConstant>
\t\t<RatioMinimum>0.0001</RatioMinimum>
\t\t<AutoZeroWavelength>Az_3</AutoZeroWavelength>
\t\t<AutoZeroInjectStart>true</AutoZeroInjectStart>
\t\t<AutoZeroEventOrKey>true</AutoZeroEventOrKey>
\t</ChannelB>
\t<AnalogA>
\t\t<Sensitivity>2.0000</Sensitivity>
\t\t<Polarity>NormalPolarity_1</Polarity>
\t\t<AbsorbanceOffset>0.000</AbsorbanceOffset>
\t\t<VoltageOffset>0</VoltageOffset>
\t\t<RatioMinimum>0.0</RatioMinimum>
\t\t<RatioMaximum>2.0</RatioMaximum>
\t\t<ChartMarkEnable>true</ChartMarkEnable>
\t</AnalogA>
\t<AnalogB>
\t\t<Sensitivity>2.0000</Sensitivity>
\t\t<Polarity>NormalPolarity_1</Polarity>
\t\t<AbsorbanceOffset>0.000</AbsorbanceOffset>
\t\t<VoltageOffset>0</VoltageOffset>
\t\t<RatioMinimum>0.0</RatioMinimum>
\t\t<RatioMaximum>2.0</RatioMaximum>
\t\t<ChartMarkEnable>true</ChartMarkEnable>
\t</AnalogB>
\t<RunEvents>true</RunEvents>
\t<EventTable/>
\t<ThresholdA>
\t\t<Enable>false</Enable>
\t\t<Threshold>1.0000</Threshold>
\t\t<Event>ThresholdEvent_8</Event>
\t\t<Action>ThresholdAction_1</Action>
\t</ThresholdA>
\t<ThresholdB>
\t\t<Enable>false</Enable>
\t\t<Threshold>1.0000</Threshold>
\t\t<Event>ThresholdEvent_9</Event>
\t\t<Action>ThresholdAction_1</Action>
\t</ThresholdB>
\t<PulseWidth>1.0</PulseWidth>
\t<RectWavePeriod>0.2</RectWavePeriod>
</AcquityTUVMethod>"""

    with open(f"{base_name}.v2487", "w", encoding="utf-8") as f:
        f.write(content)


def generate_ftn(base_name, run_time_str):
    """生成样品管理器方法文件 (.ftn)"""
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<AcquitySMDIMethod language="English" version="2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="AcquityFTN-Method-R100.xsd" modified="true">
\t<RunTime>{run_time_str}</RunTime>
\t<Comment/>
\t<LoadAhead>ModeSequential_0</LoadAhead>
\t<LoopOfflineEnabled>false</LoopOfflineEnabled>
\t<LoopOffline>LoopOfflineAutomatic_-1</LoopOffline>
\t<WashSolvent>Water</WashSolvent>
\t<WashSolventXml>&lt;Solvent version="1" permanent="true" context="all" enabled="true" date="5/1/2010 12:00:00 AM"&gt;&lt;Id&gt;144FE7DA-582C-436f-BEED-9B9B3A6EE0D0&lt;/Id&gt;&lt;Type&gt;Aqueous&lt;/Type&gt;&lt;NameId&gt;PermanentSolventWater&lt;/NameId&gt;&lt;Name&gt;Water&lt;/Name&gt;&lt;Comment /&gt;&lt;Concentration&gt;0&lt;/Concentration&gt;&lt;Viscosity&gt;1.000&lt;/Viscosity&gt;&lt;/Solvent&gt;</WashSolventXml>
\t<WashSolventType>SolventType_2</WashSolventType>
\t<InsertionWashTime>0</InsertionWashTime>
\t<WashTime>6</WashTime>
\t<PurgeSolvent>Water</PurgeSolvent>
\t<PurgeSolventXml>&lt;Solvent version="1" permanent="true" context="all" enabled="true" date="5/1/2010 12:00:00 AM"&gt;&lt;Id&gt;144FE7DA-582C-436f-BEED-9B9B3A6EE0D0&lt;/Id&gt;&lt;Type&gt;Aqueous&lt;/Type&gt;&lt;NameId&gt;PermanentSolventWater&lt;/NameId&gt;&lt;Name&gt;Water&lt;/Name&gt;&lt;Comment /&gt;&lt;Concentration&gt;0&lt;/Concentration&gt;&lt;Viscosity&gt;1.000&lt;/Viscosity&gt;&lt;/Solvent&gt;</PurgeSolventXml>
\t<PurgeSolventType>SolventType_2</PurgeSolventType>
\t<ValveCycles>CustomDisable_-1</ValveCycles>
\t<DoDilution>false</DoDilution>
\t<DilutionVolume>0</DilutionVolume>
\t<DelayTime>0</DelayTime>
\t<NeedlePosition>4</NeedlePosition>
\t<ColumnTemperature>35.0</ColumnTemperature>
\t<ColumnTemperatureLimit>5.0</ColumnTemperatureLimit>
\t<SampleTemperature>HeaterOff_-1</SampleTemperature>
\t<SampleTemperatureLimit>5</SampleTemperatureLimit>
\t<CustomRate>CustomDisable_-1</CustomRate>
\t<NeedleDepth>CustomDisable_-1</NeedleDepth>
\t<PreAspirateAir>CustomDisable_-1</PreAspirateAir>
\t<PostAspirateAir>CustomDisable_-1</PostAspirateAir>
\t<ColumnTemperatureDataEnable>false</ColumnTemperatureDataEnable>
\t<AmbientTemperatureDataEnable>false</AmbientTemperatureDataEnable>
\t<SampleTemperatureDataEnable>false</SampleTemperatureDataEnable>
\t<ElevatorTemperatureDataEnable>false</ElevatorTemperatureDataEnable>
\t<SamplePressureDataEnable>false</SamplePressureDataEnable>
\t<PreheaterTemperatureDataEnable>false</PreheaterTemperatureDataEnable>
\t<SealForceDataEnable>false</SealForceDataEnable>
\t<SampleTempAlarmEnable>false</SampleTempAlarmEnable>
\t<ColumnTempAlarmEnable>false</ColumnTempAlarmEnable>
\t<NoInject>false</NoInject>
\t<AutoAddMixStrokeCycles>CustomDisable_-1</AutoAddMixStrokeCycles>
\t<AutoAddMixStokeVolUl>CustomDisable_-1</AutoAddMixStokeVolUl>
\t<PreHeaterMode>MethodPreHeaterMode_1</PreHeaterMode>
\t<RunEvents>false</RunEvents>
\t<EventTable/>
</AcquitySMDIMethod>"""

    with open(f"{base_name}.ftn", "w", encoding="utf-8") as f:
        f.write(content)


def generate_exp(base_name, run_time_str, flow):
    """生成质谱采集方法文件 (.exp)"""
    content = f"""GENERAL INFORMATION
ExperimentName,Default Experiment
ExperimentCreationTime,Thu 23 Apr 2026 13:54:39
VersionNumber,1.0
ExperimentDuration,{run_time_str}
AnalogChannelDescription1,Channel 1,Disabled
AnalogChannelDescription2,Channel 2,Disabled
AnalogChannelDescription3,Channel 3,Disabled
AnalogChannelDescription4,Channel 4,Disabled
AnalogChannelDescription5,Channel 5,Disabled
AnalogChannelDescription6,Channel 6,Disabled
AnalogChannelDescription7,Channel 7,Disabled
AnalogChannelDescription8,Channel 8,Disabled
MUXAnalogOffset1,0.0000
MUXAnalogOffset2,0.0000
MUXAnalogOffset3,0.0000
MUXAnalogOffset4,0.0000
MUXAnalogOffset5,0.0000
MUXAnalogOffset6,0.0000
MUXAnalogOffset7,0.0000
MUXAnalogOffset8,0.0000
ExperimentCalibrationFilename,C:\\MassLynx\\IntelliStart\\Results\\Unit Mass Resolution\\Calibration_20240719_1.cal,Enabled
ExperimentNegCalibrationFilename,,Disabled,Disabled,Disabled,Disabled,Disabled,Disabled,Disabled,Disabled,Disabled,Disabled,Disabled,Disabled,Disabled,Disabled,Disabled,Disabled,Disabled,Disabl ,Disabled
SolventDelayStart1,0.0000
SolventDelayEnd1,0.0000
SolventDelayTemp1,0.0000
SolventDelayStart2,0.0000
SolventDelayEnd2,0.0000
SolventDelayTemp2,0.0000
SolventDelayStart3,0.0000
SolventDelayEnd3,0.0000
SolventDelayTemp3,0.0000
SolventDelayStart4,0.0000
SolventDelayEnd4,0.0000
SolventDelayTemp4,0.0000
SolventDelayDivertValveEnabled,0
ReferenceFrequency,0
ReferenceConeVoltage,35
ReferenceScanTime,0
ReferenceCentroidAverage,1
ReferenceSetMass,0
ReferenceCollisionEnergy,0
PositivePolarity,1
WMode,0
DREExtended,0
ExperimentExtension,TIMED_EVENTS_EXTENSION
ExperimentExtensionData,No Change,No Change,No Change,No Change,No Change,LC,5,No Action,No Action,20,1,0
NumberOfFunctions,1
FunctionTypes,MS Scan

FUNCTION 1
FunctionType,MS Scan
FunctionDataFormat,Centroid
FunctionIonMode,ES Mode
FunctionPolarity,Positive
FunctionInstrumentConditions,c:\\masslynx\\default.pro\\acqudb\\default.ipr
FunctionStartMass,100
FunctionEndMass,500
FunctionStartTime(min),0
FunctionEndTime(min),{run_time_str}
FunctionScanTime(sec),1
FunctionInterScanTime(sec),-1
Scans To Sum,16960
NumFunctions,1
Resolution,1000
PrimaryScanLock,2
SecondaryScanLock,2
ThresholdLock,100
StepLock,0.02
FunctionOnOffState,1
PeakDisplayTuneMode,0
SIRMode,Peak Top
NumSIRMasses,0
FastLockOn,1
UseWMode,0
ConeVoltage,30
UseTunePageConeVoltage,0
UseCVRamp,0
CVRampStart,20
CVRampEnd,70
CVRampStartMass,100
CVRampEndMass,1000
UseTuneProbeTemp,0
ProbeTemp,20
Gain,1
PointsPerAMU,32
StoreZeros,false
EnableMRMSmooth,0
MRMSmoothWidth,3
MRMSmoothRepeats,2
FractionLowMassIndex,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
FractionHighMassIndex,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
FractionMultiplier,1
FractionMode,0
PointsPerPeakWidth,4.0000
RequiredPointsPerPeak,12"""

    with open(f"{base_name}.exp", "w", encoding="utf-8", newline="\r\n") as f:
        f.write(content)


# ==============================================================================
#  4. 主协调函数（调整参数顺序，必填在前，带默认值的在后）
# ==============================================================================
def generate_all_methods(isocratic_time, 
                         gradient_time, 
                         initial_org, 
                         max_org=100.0, 
                         flow=0.300, 
                         iteration=16, 
                         output_dir=".",
                         hold_at_max=1.0, 
                         ramp_down=0.5, 
                         re_equil=1.0):
    """
    主协调函数。
    前三个参数 (isocratic_time, gradient_time, initial_org) 为必填项。
    其余参数在未指定时自动使用默认值。
    """
    # -------- 4.1 计算浓度参数 --------
    init_a = round(100.0 - initial_org, 1)
    init_b = round(float(initial_org), 1)
    max_a  = round(100.0 - max_org, 1)
    max_b  = round(float(max_org), 1)
    post_b = min(5.0, max_org)          # 再平衡有机相浓度，不超过最大浓度
    post_a = round(100.0 - post_b, 1)

    # -------- 4.2 计算时间轴节点 --------
    t1 = isocratic_time
    t2 = t1 + gradient_time
    t3 = t2 + hold_at_max
    t4 = t3 + ramp_down
    t5 = t4 + re_equil
    run_time_str = f"{t5:.2f}"

    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.join(output_dir, f"iteration_{iteration:02d}")

    # -------- 4.3 构造梯度表行数据 --------
    qsm_rows = [
        ("Initial", flow, init_a, init_b, 0.0, 0.0, "Initial"),
        (t1,        flow, init_a, init_b, 0.0, 0.0, "6"),
        (t2,        flow, max_a,  max_b,  0.0, 0.0, "6"),
        (t3,        flow, max_a,  max_b,  0.0, 0.0, "6"),
        (t4,        flow, post_a, post_b, 0.0, 0.0, "6"),
        (t5,        flow, post_a, post_b, 0.0, 0.0, "6"),
    ]

    # -------- 4.4 调用各文件生成函数 --------
    generate_qsm(base_name, run_time_str, flow, init_a, init_b, max_a, max_b,
                 post_a, post_b, t1, t2, t3, t4, t5, qsm_rows)
    generate_tuv(base_name, run_time_str)
    generate_ftn(base_name, run_time_str)
    generate_exp(base_name, run_time_str, flow)

    # -------- 4.5 终端核对输出 --------
    print("=" * 65)
    print(f"【成功联动生成 4 个配置文件】 基础文件名: {base_name}")
    print(f" 1. {base_name}.qsm    (液相系统 Runtime: {run_time_str} min)")
    print(f" 2. {base_name}.v2487  (紫外检测器 Runtime: {run_time_str} min)")
    print(f" 3. {base_name}.ftn    (样品管理器 Runtime: {run_time_str} min)")
    print(f" 4. {base_name}.exp    (质谱采集时间: {run_time_str} min)")
    print("-" * 65)
    print(" 终端核对液相梯度表格:")
    print(f"  {'Time':>8}  {'Flow':>6}  {'%A':>6}  {'%B':>6}  {'%C':>4}  {'%D':>4}  Curve")
    for r in qsm_rows:
        t = r[0] if r[0] == "Initial" else f"{float(r[0]):.2f}"
        print(f"  {t:>8}  {r[1]:>6.3f}  {r[2]:>6.1f}  {r[3]:>6.1f}  {r[4]:>4.1f}  {r[5]:>4.1f}  {r[6]}")
    print("=" * 65)


def generate_csv_conf(
    file_name,
    sample_location,
    conf_names,
    output_dir,  # 传入已经建好的文件夹路径
    index=1,
    inj_vol=5,
    ms_tune_file="Instrument",
):

    # 1. 直接拼接完整的 CSV 文件路径
    full_csv_path = os.path.join(output_dir, f"{file_name}.csv")

    # 2. 准备标准的表头
    headers = [
        "Index",
        "FILE_NAME",
        "MS_FILE",
        "MS_TUNE_FILE",
        "INLET_FILE",
        "SAMPLE_LOCATION",
        "INJ_VOL",
    ]

    # 3. 组装单行数据（根据 conf_names 联动 MS_FILE 和 INLET_FILE）
    row_data = [
        index,
        file_name,
        conf_names,  # MS_FILE
        ms_tune_file,
        conf_names,  # INLET_FILE
        sample_location,
        inj_vol,
    ]

    # 4. 使用 'w' 模式直接全新创建文件并写入表头与数据
    with open(full_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)  # 写入第一行表头
        writer.writerow(row_data)  # 写入第二行数据

    print(f"成功在【{output_dir}】下全新创建了配置文件：{file_name}")
    print(
        f" 数据名: {file_name} | 位置: {sample_location} | 联动方法名: {conf_names}"
    )

# ==============================================================================
#  5. 运行入口（保持脚本直接运行时仍可用旧控制变量）
# ==============================================================================
if __name__ == "__main__":
    generate_all_methods(
        isocratic_time=isocratic_time,
        gradient_time=gradient_time,
        initial_org=initial_organic_concentration,
        max_org=max_organic_concentration,
        flow=flow_rate,
        iteration=iteration_n,
        hold_at_max=hold_at_max_time,
        ramp_down=ramp_down_time,
        re_equil=re_equil_time
    )