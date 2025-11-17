# YOLO Counter Detection Training Guide

This guide shows you how to train a YOLOv8 model to detect counters on your conveyor belt.

## Overview

**Time required:** 1-2 hours
**Images needed:** 30-50 photos
**Training time:** 10-30 minutes (on PC with GPU)

## Step 1: Capture Training Images (15 mins)

On your Raspberry Pi, capture ~50 images:

```bash
cd ~/rpi-dobot
python3 scripts/prepare_yolo_dataset.py --num 50
```

**Tips for good training data:**
- Capture counters in different positions on the belt
- Include 0, 1, 2, 3, 4+ counters per image
- Capture in different lighting (bright, dim, shadows)
- Include some "hard" cases (overlapping counters, edge of frame)
- Capture from the same camera angle you'll use in production

The images will be saved to `dataset/images/`

## Step 2: Annotate Images (30-45 mins)

You need to draw bounding boxes around each counter.

### Option A: Use Roboflow (Easiest - Recommended)

1. Go to https://roboflow.com (free account)
2. Create new project → Object Detection
3. Upload your 50 images
4. Annotate each counter with a box (label: "counter")
5. Generate → Export → YOLO v8 format
6. Download the zip file

### Option B: Use labelImg (Offline)

```bash
pip install labelImg
labelImg dataset/images
```

1. Draw boxes around each counter
2. Save as YOLO format
3. Label each box as "counter"

## Step 3: Prepare Dataset

Your dataset should look like this:

```
dataset/
├── images/
│   ├── train/
│   │   ├── counter_0001.jpg
│   │   ├── counter_0002.jpg
│   │   └── ...
│   └── val/
│       ├── counter_0040.jpg
│       └── ...
├── labels/
│   ├── train/
│   │   ├── counter_0001.txt
│   │   ├── counter_0002.txt
│   │   └── ...
│   └── val/
│       ├── counter_0040.txt
│       └── ...
└── dataset.yaml
```

**dataset.yaml:**
```yaml
path: ./dataset  # dataset root dir
train: images/train  # train images
val: images/val  # val images

# Classes
names:
  0: counter
```

Split your images:
- 80% for training (`images/train/`)
- 20% for validation (`images/val/`)

## Step 4: Train the Model (On your PC - requires GPU)

**On your PC (not Raspberry Pi):**

Install Ultralytics:
```bash
pip install ultralytics
```

Train the model:
```bash
yolo train data=dataset.yaml model=yolov8n.pt epochs=50 imgsz=640
```

**Training parameters:**
- `model=yolov8n.pt` - Nano model (fastest, works on Pi)
- `epochs=50` - More = better accuracy (30-100 recommended)
- `imgsz=640` - Image size (640 is good for Pi)

Training takes 10-30 minutes on a GPU.

The trained model will be saved to: `runs/detect/train/weights/best.pt`

## Step 5: Deploy to Raspberry Pi

Copy the trained model to your Pi:

```bash
scp runs/detect/train/weights/best.pt pi@rpi:~/rpi-dobot/models/counter_detector.pt
```

On the Pi, create models directory:
```bash
mkdir -p ~/rpi-dobot/models
```

## Step 6: Update Backend to Use Custom Model

Edit `pwa-dobot-plc/backend/app.py` and add model loading on startup:

```python
# Load YOLO model on startup
model_path = os.path.expanduser('~/rpi-dobot/models/counter_detector.pt')
if os.path.exists(model_path):
    camera_service.load_yolo_model(model_path)
    logger.info(f"Loaded custom YOLO model: {model_path}")
else:
    logger.warning(f"Custom model not found: {model_path}")
```

## Step 7: Test Detection

1. Restart your backend service:
   ```bash
   sudo systemctl restart dobot-backend
   ```

2. Open Vision System UI
3. Detection should now use your trained YOLO model!

## Expected Results

With 30-50 well-annotated images:
- **Precision:** 90-98% (few false positives)
- **Recall:** 95-99% (rarely misses counters)
- **FPS:** 15-25 fps on Raspberry Pi 4/5
- **Works in:** Sunlight, shadows, different belt speeds

## Troubleshooting

### "Low accuracy after training"
- Add more diverse images (different lighting, positions)
- Train for more epochs (try 100)
- Check annotations are correct

### "Model too slow on Pi"
- Use yolov8n.pt (nano) not yolov8s.pt or larger
- Reduce image size to 416 or 320

### "False positives (detects non-counters)"
- Add "negative examples" (images with no counters)
- Increase confidence threshold in UI

### "Misses counters at edge of frame"
- Add more training images with counters at edges
- Increase IOU threshold

## Advanced: Fine-tuning

If you want even better accuracy:

1. **Collect more data:** 100-200 images instead of 50
2. **Data augmentation:** Roboflow can auto-generate variations
3. **Longer training:** 100-200 epochs
4. **Hard negative mining:** Add images of things that look like counters but aren't

## Why YOLO is Better Than OpenCV

| Feature | YOLO | SimpleBlobDetector |
|---------|------|-------------------|
| Works in sunlight | ✅ | ❌ |
| Handles shadows | ✅ | ❌ |
| No parameter tuning | ✅ | ❌ Needs manual tuning |
| Ignores reflections | ✅ | ❌ |
| Reliable | ✅ 95%+ | ❌ 50-70% |
| Setup time | 1-2 hours once | Hours of tweaking |

Once trained, YOLO "just works" - no more parameter adjustment!
