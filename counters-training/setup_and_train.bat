@echo off
REM Windows Batch Script to Set Up and Train YOLOv11n
REM This script automates the entire setup process

echo ================================================
echo YOLOv11n Counter Detection Training Setup
echo ================================================
echo.

REM Step 1: Create virtual environment
echo [Step 1/4] Creating Python virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    echo Make sure Python is installed and in your PATH
    pause
    exit /b 1
)
echo Virtual environment created successfully!
echo.

REM Step 2: Activate virtual environment and install dependencies
echo [Step 2/4] Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully!
echo.

REM Step 3: Check if images are labeled
echo [Step 3/4] Checking dataset...
if not exist "dataset\images\train\*.jpg" (
    echo.
    echo ================================================
    echo IMPORTANT: You need to label your images first!
    echo ================================================
    echo.
    echo Please follow these steps:
    echo 1. Run: pip install labelImg
    echo 2. Run: labelImg
    echo 3. Label all images in counter_dataset folder
    echo 4. Split images: 80%% to dataset/images/train
    echo                  20%% to dataset/images/val
    echo 5. Split labels: 80%% to dataset/labels/train
    echo                  20%% to dataset/labels/val
    echo.
    echo Then run this script again or run: python train_yolov11n.py
    echo.
    pause
    exit /b 0
)

REM Step 4: Start training
echo [Step 4/4] Starting training...
echo.
echo This will take a while. You can monitor progress in the terminal.
echo Training results will be saved to: runs/detect/counter_train/
echo.
python train_yolov11n.py

echo.
echo ================================================
echo Setup and training completed!
echo ================================================
echo.
echo Next steps:
echo 1. Check training results in runs/detect/counter_train/
echo 2. Test your model: python test_model.py
echo 3. Use the best.pt file in your Electron app
echo.
pause

