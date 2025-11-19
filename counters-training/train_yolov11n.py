"""
YOLOv11n Training Script - Beginner Friendly
This script trains a YOLOv11 nano model to detect counters in images.
"""

# Import the YOLO class from ultralytics library
from ultralytics import YOLO

# Step 1: Load the pre-trained YOLOv11n model
# This is a tiny model that's already trained on general objects
# We will fine-tune it for our specific counter detection task
print("Loading YOLOv11n model...")
print("(This will download the model file if it's the first time, about 6MB)")
print()

# The model will be automatically downloaded from Ultralytics
model = YOLO("yolo11n.pt")  # Note: it's "yolo11n.pt" not "yolov11n.pt"

# Step 2: Train the model on our counter dataset
print("Starting training...")
print("This may take a while depending on your computer speed...")

# Training parameters (explained simply):
# - data: path to the YAML file that describes our dataset
# - epochs: how many times to go through all images (more = better but slower)
# - imgsz: resize all images to this size (640x640 is standard)
# - batch: how many images to process at once (lower if you get memory errors)
# - device: 'cpu' means use processor, '0' means use GPU if you have one
# - project: folder where results will be saved
# - name: name of this training run
# - patience: stop early if no improvement after this many epochs
# - save: save checkpoints during training
# - plots: create helpful charts to see how training went

results = model.train(
    data="counter-data.yaml",
    epochs=100,
    imgsz=640,
    batch=8,
    device="cpu",
    project="runs/detect",
    name="counter_train",
    patience=20,
    save=True,
    plots=True
)

# Step 3: Training is complete!
print("\n" + "="*50)
print("Training completed!")
print("="*50)
print("\nYour trained model is saved at:")
print("runs/detect/counter_train/weights/best.pt")
print("\nYou can use this file in your Electron app.")
print("\nTo test the model, run: python test_model.py")

