# Screen Censor — Windows Installer Build Kit

This folder is prepared to build a Windows installer (`ScreenCensor_Setup.exe`) using GitHub Actions.
The current session is not a Windows build machine, so it cannot compile and verify a native Windows `.exe` here.

## Build the installer (one-time setup)
1. Create or sign in to a GitHub account.
2. Create a new repository, e.g. `screen-censor`.
3. Upload the **contents** of this folder to the repository (including the hidden `.github` folder).
4. Open the repository's **Actions** tab.
5. Select **Build Windows Installer** and click **Run workflow** (or wait for the first push build).
6. When the workflow is green, open its run, scroll to **Artifacts**, and download `ScreenCensor-Windows-Installer`.
7. Extract the artifact. It contains `ScreenCensor_Setup.exe`. Run it on Windows 10/11 64-bit.

## Important
- This creates a native Windows installer on a Windows GitHub runner; Python is bundled into the app by PyInstaller. The target PC does not need Python installed.
- The first launch may need internet access because NudeNet may fetch its detection model if it is not already present. This build kit does not bundle the model file.
- Detection is probabilistic and periodic, not instantaneous. Content may be visible briefly; false positives and missed detections are possible. Do not rely on it as the only safety control.
- Windows SmartScreen may show an unknown-publisher warning because the installer is not code-signed.
- Scan the downloaded installer with Microsoft Defender before running it.
- This is an unsigned community-style build workflow; review the source and GitHub Actions log before installing.
