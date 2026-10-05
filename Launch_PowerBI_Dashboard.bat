@echo off
title Crime Data Analytics - Power BI Integration Launcher
color 0b
cls
echo ==============================================================================
echo    CRIME DATA ANALYTICS ^& VISUALIZATION SYSTEM - POWER BI LAUNCHER
echo    Connected to SQLite Database: database\crime_analytics.db
echo    Coverage: 28 States ^| 743 Districts ^| 252,240 Records (2021-2025)
echo ==============================================================================
echo.
echo [1/3] Refreshing Power BI datasets from live database...
python scripts\prepare_powerbi_dataset.py
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Python dataset refresh encountered an issue, proceeding with existing dataset.
) else (
    echo [SUCCESS] Power BI datasets successfully refreshed!
)
echo.
echo [2/3] Opening Dataset folder...
explorer /select,"%~dp0data\powerbi_crime_dataset.xlsx"
echo.
echo [3/3] Launching Microsoft Power BI Desktop...
if exist "C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe" (
    start "" "C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe"
    echo [SUCCESS] Microsoft Power BI Desktop launched!
) else (
    echo [NOTICE] PBIDesktop.exe not found at standard path. Please launch Power BI Desktop from Start Menu.
)
echo.
echo ==============================================================================
echo  QUICK STEPS TO BUILD DASHBOARD IN POWER BI DESKTOP:
echo ==============================================================================
echo  1. In Power BI Desktop, click: 'Get Data' -^> 'Excel workbook'
echo  2. Select: data\powerbi_crime_dataset.xlsx (already highlighted in Explorer)
echo  3. Check: 'State_Analytics', 'Crime_Type_Analytics', 'Yearly_Trends'
echo  4. Click: 'Load'
echo  5. Create Visuals:
echo     - Donut Chart: Drag Crime_Type_Analytics[crime_type] ^& [total_cases]
echo     - Bar Chart  : Drag State_Analytics[state] ^& [total_cases]
echo     - Line Chart : Drag Yearly_Trends[year] ^& [total_cases]
echo     - Card Visual: Drag Total Cases, Chargesheeted, Convictions
echo ==============================================================================
echo.
pause
