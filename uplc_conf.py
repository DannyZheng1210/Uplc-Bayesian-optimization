import os
import csv

# ==============================================================================
#  1. Core control variables
#     (kept as global defaults for direct script execution or importing)
# ==============================================================================
flow_rate = 0.300                      # mL/min: global flow rate
initial_organic_concentration = 30.0  # %B: initial organic solvent concentration
max_organic_concentration = 100.0     # %B: maximum organic solvent concentration

isocratic_time = 1.0                  # min: initial isocratic hold time
gradient_time = 1.0                   # min: gradient ramp time to maximum concentration
iteration_n = 16                      # unified output numbering for batch generation

hold_at_max_time = 1.0    # min: hold time at maximum organic concentration
ramp_down_time = 0.5      # min: ramp back to initial concentration
re_equil_time = 1.0       # min: re-equilibration time


# ==============================================================================
#  2. Helper formatting function
# ==============================================================================
def format_qsm_row(time_val, flow, a, b, c, d, curve):
    """Generate a single XML GradientRow with standard template indentation."""

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
#  3. Generate QSM file
# ==============================================================================
def generate_qsm(
    base_name,
    run_time_str,
    flow,
    init_a,
    init_b,
    max_a,
    max_b,
    post_a,
    post_b,
    t1,
    t2,
    t3,
    t4,
    t5,
    qsm_rows,
):
    """Generate LC gradient method file (.qsm)."""

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
{last_block}
    </GradientTable>

    <Comment/>

    <FlowRampRate>0.45</FlowRampRate>

    <PreInjectorVolume>0</PreInjectorVolume>

    <StrokeVolume>50 uL   (flow &lt;= 2.000 mL/min)</StrokeVolume>

    <SystemReequilibrationVolume>0</SystemReequilibrationVolume>

    <SystemReequilibrationVentPoint>
        SystemReequilibrationVentPointSolventManager_0
    </SystemReequilibrationVentPoint>

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

    <AcidName/>
    <AcidConcentration>0</AcidConcentration>
    <AcidXml/>

    <BaseName/>
    <BaseConcentration>0</BaseConcentration>
    <BaseXml/>

    <SaltName/>
    <SaltConcentration>0</SaltConcentration>
    <SaltXml/>

    <AqueousName/>
    <AqueousXml/>

    <BufferSystemName/>
    <BufferSystemConcentration>0</BufferSystemConcentration>

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

</AcquityQSMMethod>
"""

    with open(f"{base_name}.qsm", "w", encoding="utf-8") as f:
        f.write(content)


# ==============================================================================
#  4. Generate TUV file
# ==============================================================================
def generate_tuv(base_name, run_time_str):
    """Generate UV detector method file (.v2487)."""

    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<AcquityTUVMethod xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="AcquityTUV-Method-r100.xsd" version="1" modified="true">

    <RunTime>{run_time_str}</RunTime>

    <WavelengthMode>2</WavelengthMode>

    <Lamp>true</Lamp>

    <ChannelA>

        <Description/>

        <Wavelength>254</Wavelength>

        <DataRate>DualDataRate_1B</DataRate>

        <DataMode>DualModeA_1B</DataMode>

        <FilterType>Filter_2</FilterType>

        <TimeConstant>2.0000</TimeConstant>

        <RatioMinimum>0.0001</RatioMinimum>

        <AutoZeroWavelength>Az_3</AutoZeroWavelength>

        <AutoZeroInjectStart>true</AutoZeroInjectStart>

        <AutoZeroEventOrKey>true</AutoZeroEventOrKey>

    </ChannelA>

    <ChannelB>

        <Description/>

        <Wavelength>270</Wavelength>

        <DataRate>DualDataRate_1B</DataRate>

        <DataMode>DualModeB_2C</DataMode>

        <FilterType>Filter_2</FilterType>

        <TimeConstant>2.0000</TimeConstant>

        <RatioMinimum>0.0001</RatioMinimum>

        <AutoZeroWavelength>Az_3</AutoZeroWavelength>

        <AutoZeroInjectStart>true</AutoZeroInjectStart>

        <AutoZeroEventOrKey>true</AutoZeroEventOrKey>

    </ChannelB>

</AcquityTUVMethod>
"""

    with open(f"{base_name}.v2487", "w", encoding="utf-8") as f:
        f.write(content)


# ==============================================================================
#  5. Generate FTN file
# ==============================================================================
def generate_ftn(base_name, run_time_str):
    """Generate sample manager method file (.ftn)."""

    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<AcquitySMDIMethod language="English" version="2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="AcquityFTN-Method-R100.xsd" modified="true">

    <RunTime>{run_time_str}</RunTime>

    <Comment/>

    <LoadAhead>ModeSequential_0</LoadAhead>

    <LoopOfflineEnabled>false</LoopOfflineEnabled>

    <ColumnTemperature>35.0</ColumnTemperature>

    <ColumnTemperatureLimit>5.0</ColumnTemperatureLimit>

    <SampleTemperature>HeaterOff_-1</SampleTemperature>

    <SampleTemperatureLimit>5</SampleTemperatureLimit>

</AcquitySMDIMethod>
"""

    with open(f"{base_name}.ftn", "w", encoding="utf-8") as f:
        f.write(content)


# ==============================================================================
# #  6. Generate EXP file
# ==============================================================================
def generate_exp(base_name, run_time_str, flow):
    """Generate MS acquisition method file (.exp)."""

    # Safe raw strings to prevent Windows path 'unicodeescape' errors (\U, \u, etc.)
    cal_path = r"C:\MassLynx\IntelliStart\Results\Unit Mass Resolution\Calibration_20240719_1.cal"
    inst_path = r"c:\masslynx\default.pro\acqudb\default.ipr"

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
ExperimentCalibrationFilename,{cal_path},Enabled
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
FunctionInstrumentConditions,{inst_path}
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
RequiredPointsPerPeak,12
"""

    with open(f"{base_name}.exp", "w", encoding="utf-8", newline="\r\n") as f:
        f.write(content)


# ==============================================================================
#  7. Main coordination function
# ==============================================================================
def generate_all_methods(
    isocratic_time,
    gradient_time,
    initial_org,
    output_dir,
    conf_files_name,
    max_org=100.0,
    flow=0.500,
    hold_at_max=1.0,
    ramp_down=0.5,
    re_equil=1.0,
):
    """
    Main coordination function.

    Required parameters:
        isocratic_time
        gradient_time
        initial_org

    All other parameters use default values.
    """

    # --------------------------------------------------------------------------
    # 7.1 Calculate composition values
    # --------------------------------------------------------------------------
    init_a = round(100.0 - initial_org, 1)
    init_b = round(float(initial_org), 1)

    max_a = round(100.0 - max_org, 1)
    max_b = round(float(max_org), 1)

    post_b = min(5.0, max_org)
    post_a = round(100.0 - post_b, 1)

    # --------------------------------------------------------------------------
    # 7.2 Calculate time points
    # --------------------------------------------------------------------------
    t1 = isocratic_time
    t2 = t1 + gradient_time
    t3 = t2 + hold_at_max
    t4 = t3 + ramp_down
    t5 = t4 + re_equil

    run_time_str = f"{t5:.2f}"

    # --------------------------------------------------------------------------
    # 7.3 Create output directory
    # --------------------------------------------------------------------------
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.join(output_dir, conf_files_name)

    # --------------------------------------------------------------------------
    # 7.4 Build gradient table
    # --------------------------------------------------------------------------
    qsm_rows = [
        ("Initial", flow, init_a, init_b, 0.0, 0.0, "Initial"),
        (t1, flow, init_a, init_b, 0.0, 0.0, "6"),
        (t2, flow, max_a, max_b, 0.0, 0.0, "6"),
        (t3, flow, max_a, max_b, 0.0, 0.0, "6"),
        (t4, flow, post_a, post_b, 0.0, 0.0, "6"),
        (t5, flow, post_a, post_b, 0.0, 0.0, "6"),
    ]

    # --------------------------------------------------------------------------
    # 7.5 Generate all method files
    # --------------------------------------------------------------------------
    generate_qsm(
        base_name,
        run_time_str,
        flow,
        init_a,
        init_b,
        max_a,
        max_b,
        post_a,
        post_b,
        t1,
        t2,
        t3,
        t4,
        t5,
        qsm_rows,
    )

    generate_tuv(base_name, run_time_str)

    generate_ftn(base_name, run_time_str)

    generate_exp(base_name, run_time_str, flow)

    # --------------------------------------------------------------------------
    # 7.6 Terminal summary
    # --------------------------------------------------------------------------
    print("=" * 70)

    print(f"[Successfully generated 4 configuration files]")
    print(f"Base file name: {base_name}")

    print("-" * 70)

    print(f"1. {base_name}.qsm")
    print(f"2. {base_name}.v2487")
    print(f"3. {base_name}.ftn")
    print(f"4. {base_name}.exp")

    print("-" * 70)

    print("Gradient table preview:")

    print(
        f"{'Time':>10} {'Flow':>8} {'%A':>8} {'%B':>8} {'%C':>8} {'%D':>8} Curve"
    )

    for r in qsm_rows:

        t = r[0] if r[0] == "Initial" else f"{float(r[0]):.2f}"

        print(
            f"{t:>10} "
            f"{r[1]:>8.3f} "
            f"{r[2]:>8.1f} "
            f"{r[3]:>8.1f} "
            f"{r[4]:>8.1f} "
            f"{r[5]:>8.1f} "
            f"{r[6]}"
        )

    print("=" * 70)


# ==============================================================================
#  8. Generate CSV sequence configuration
# ==============================================================================
def generate_csv_conf(
    file_name,
    sample_location,
    conf_names,
    output_dir,
    index=1,
    inj_vol=5,
    ms_tune_file="Instrument",
):
    """
    Generate a CSV sequence configuration file.
    """

    full_csv_path = os.path.join(output_dir, f"{file_name}.csv")

    headers = [
        "Index",
        "FILE_NAME",
        "MS_FILE",
        "MS_TUNE_FILE",
        "INLET_FILE",
        "SAMPLE_LOCATION",
        "INJ_VOL",
    ]

    row_data = [
        index,
        file_name,
        conf_names,
        ms_tune_file,
        conf_names,
        sample_location,
        inj_vol,
    ]

    with open(full_csv_path, "w", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)

        writer.writerow(headers)

        writer.writerow(row_data)

    print(f"Successfully created CSV file: {full_csv_path}")

    print(
        f"Sample name: {file_name} | "
        f"Sample location: {sample_location} | "
        f"Linked method: {conf_names}"
    )


# # ==============================================================================
# #  9. Script entry point
# # ==============================================================================
# if __name__ == "__main__":

#     confs_floder = r"D:\automation_test.PRO\ACQUDB" 
#     confs_name = "test_confs" 
    
#     generate_all_methods(
#         isocratic_time=isocratic_time,
#         gradient_time=gradient_time,
#         initial_org=initial_organic_concentration,
#         output_dir=confs_floder,
#         conf_files_name=confs_name,
#         max_org=max_organic_concentration,
#         flow=flow_rate,
#         hold_at_max=hold_at_max_time,
#         ramp_down=ramp_down_time,
#         re_equil=re_equil_time,
#     )
    
#     # ======= 修改这里 =======
#     file_name = confs_name  # 将文件名设为 "test_confs" 而不是整个文件夹路径
#     # =======================
    
#     sample_location = "2:48"
#     csv_control_folder = r"D:\autolynx"

#     generate_csv_conf(
#             file_name,
#             sample_location,
#             conf_names=confs_name,
#             output_dir = csv_control_folder,
#             index=1,
#             inj_vol=5,
#             ms_tune_file="Instrument",
#         )