@echo off
set WIX_PATH=c:\SOFTDEV\tools\wix
set PATH=%WIX_PATH%;%PATH%

echo [INFO] Compiling WiX sources...
candle Product.wxs CustomMaintenanceTypeDlg.wxs

echo [INFO] Linking MSI...
light Product.wixobj CustomMaintenanceTypeDlg.wixobj -ext WixUIExtension -ext WixUtilExtension -out SPYSCALP_v0.1.5_Setup.msi

if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Installer built: SPYSCALP_v0.1.5_Setup.msi
) else (
    echo [ERROR] Build failed.
)

pause
