; NSIS Modern User Interface Installer Script
; For Live Object Detection & Auto-Labeling Suite

!include "MUI2.nsh"
!include "FileFunc.nsh"

; General Definitions
!define PRODUCT_NAME "Live Object Detection"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "LiveObjectDetection"
!define PRODUCT_WEB_SITE "https://github.com/VicRoger27/LiveObjectDetection"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\LiveAnyLabeling.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKCU"

; Installer file settings
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "..\..\dist\LiveAnyLabeling_Setup.exe"
InstallDir "$LOCALAPPDATA\LiveAnyLabeling"
InstallDirRegKey HKCU "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show
RequestExecutionLevel user

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "..\..\anylabeling\resources\images\icon.ico"
!define MUI_UNICON "..\..\anylabeling\resources\images\icon.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\..\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\LiveAnyLabeling.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch Live Object Detection Suite"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\help_en.html"
!define MUI_FINISHPAGE_SHOWREADME_TEXT "Open Visual HTML User Guide"
!insertmacro MUI_PAGE_FINISH

; Uninstaller Pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite try

  ; Copy all built files from PyInstaller dist/LiveAnyLabeling directory
  File /r "..\..\dist\LiveAnyLabeling\*.*"

  ; Create Shortcuts
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  CreateShortcut "$SMPROGRAMS\${PRODUCT_NAME}\Live AnyLabeling.lnk" "$INSTDIR\LiveAnyLabeling.exe" "" "$INSTDIR\LiveAnyLabeling.exe" 0
  CreateShortcut "$SMPROGRAMS\${PRODUCT_NAME}\Visual User Guide.lnk" "$INSTDIR\help_en.html"
  CreateShortcut "$SMPROGRAMS\${PRODUCT_NAME}\Camera Tutorial.lnk" "$INSTDIR\help_camera.html"
  CreateShortcut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk" "$INSTDIR\uninst.exe"
  CreateShortcut "$DESKTOP\Live Object Detection Suite.lnk" "$INSTDIR\LiveAnyLabeling.exe" "" "$INSTDIR\LiveAnyLabeling.exe" 0

  ; Write registry keys for uninstaller
  WriteRegStr HKCU "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\LiveAnyLabeling.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\LiveAnyLabeling.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"

  WriteUninstaller "$INSTDIR\uninst.exe"
SectionEnd

Section Uninstall
  RMDir /r "$INSTDIR"
  RMDir /r "$SMPROGRAMS\${PRODUCT_NAME}"
  Delete "$DESKTOP\Live Object Detection Suite.lnk"

  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKCU "${PRODUCT_DIR_REGKEY}"
  SetAutoClose true
SectionEnd
