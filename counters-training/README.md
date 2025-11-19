# YOLOv11n Counter Detection Training

This folder contains everything you need to train a YOLOv11 nano model to detect counters.

## 📁 Folder Structure

```
counters-training/
├── counter_dataset/          # Your original counter images
├── dataset/                  # Organized dataset for YOLO
│   ├── images/
│   │   ├── train/           # Training images (80%)
│   │   └── val/             # Validation images (20%)
│   └── labels/
│       ├── train/           # Training labels
│       └── val/             # Validation labels
├── counter-data.yaml         # Dataset configuration
├── train_yolov11n.py         # Training script
├── test_model.py             # Testing script
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🚀 Quick Start Guide

### Step 1: Set Up Python Environment

Open a terminal/command prompt in this folder and run:

```bash
# Create a virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Label Your Images

Before training, you need to label your images. This means drawing boxes around counters and telling YOLO where they are.

**Option 1: Use LabelImg (Recommended for Beginners)**

1. Install LabelImg:
   ```bash
   pip install labelImg
   ```

2. Run LabelImg:
   ```bash
   labelImg
   ```

3. In LabelImg:
   - Click "Open Dir" and select `counter_dataset` folder
   - Click "Change Save Dir" and select `dataset/labels/train` folder
   - Make sure "YOLO" format is selected (not PascalVOC)
   - For each image:
     - Press 'W' to draw a box around each counter
     - Type "counter" as the label
     - Press 'Ctrl+S' to save
     - Press 'D' to go to next image

4. After labeling all images:
   - Move about 80% of images from `counter_dataset` to `dataset/images/train`
   - Move about 20% of images from `counter_dataset` to `dataset/images/val`
   - Move the corresponding label files:
     - 80% of `.txt` files stay in `dataset/labels/train`
     - 20% of `.txt` files go to `dataset/labels/val`

**Important:** Each image must have a matching label file with the same name.
- Example: `counter_0000.jpg` → `counter_0000.txt`

### Step 3: Train the Model

Once your images are labeled and organized:

```bash
python train_yolov11n.py
```

This will:
- Download the YOLOv11n pre-trained model (first time only)
- Train on your counter images for 100 epochs
- Save the best model to `runs/detect/counter_train/weights/best.pt`
- Create training charts and metrics

**Training will take time** depending on your computer:
- With GPU: 10-30 minutes
- With CPU only: 1-3 hours

### Step 4: Test Your Model

After training completes:

```bash
python test_model.py
```

This will:
- Load your trained model
- Run it on all images in `counter_dataset`
- Save results with bounding boxes drawn in `runs/detect/test_results/`

Open the `runs/detect/test_results/` folder to see if your model detects counters correctly!

## 📊 Understanding Training Results

After training, check these files in `runs/detect/counter_train/`:

- `weights/best.pt` - Your best trained model (use this!)
- `weights/last.pt` - The last epoch model
- `results.png` - Training charts showing loss and accuracy
- `confusion_matrix.png` - Shows how well the model performs
- `val_batch0_pred.jpg` - Example predictions on validation images

**Good training signs:**
- Loss values go down over time
- mAP (mean Average Precision) goes up
- Validation predictions look accurate

## 🔧 Troubleshooting

### "CUDA out of memory" error
- Reduce `batch` size in `train_yolov11n.py` (try 4 or 2 instead of 8)
- Or use CPU by keeping `device="cpu"`

### Model doesn't detect counters well
- Add more labeled images (aim for 100+ images minimum)
- Make sure labels are accurate (boxes tightly around counters)
- Increase training epochs (try 200 instead of 100)
- Lower confidence threshold when testing (try 0.1 instead of 0.25)

### Training is very slow
- This is normal with CPU! Consider using Google Colab with free GPU
- Or reduce image size: change `imgsz=640` to `imgsz=416`

## 📝 Next Steps

Once you have a good model (`best.pt`):

1. Copy `best.pt` to your Electron app
2. Rename it to `counter_detector.pt` if needed
3. Update your vision system to use this new model
4. Test it with real camera images!

## 💡 Tips for Better Results

- **More images = better model**: Try to get 100-200+ labeled images
- **Varied images**: Different lighting, angles, backgrounds
- **Accurate labels**: Make sure boxes are tight around counters
- **Clean data**: Remove blurry or bad images
- **Test regularly**: After every training run, check test results

## 📚 Additional Resources

- [Ultralytics YOLOv11 Docs](https://docs.ultralytics.com/)
- [LabelImg Tutorial](https://github.com/heartexlabs/labelImg)

## ❓ Need Help?

If something doesn't work:
1. Check error messages carefully
2. Make sure all images have matching label files
3. Verify folder structure matches the layout above
4. Try with a smaller number of images first (10-20) to test the pipeline

