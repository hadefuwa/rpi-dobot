"""
Test YOLOv11n Trained Model - Beginner Friendly
This script tests your trained model on images to see if it detects counters correctly.
"""

# Import the YOLO class from ultralytics library
from ultralytics import YOLO
import os

# Step 1: Load your trained model
# Change this path if your model is saved somewhere else
model_path = "runs/detect/counter_train/weights/best.pt"

print("Loading trained model...")
print(f"Model path: {model_path}")

# Check if the model file exists
if not os.path.exists(model_path):
    print("\nERROR: Model file not found!")
    print("Please train the model first by running: python train_yolov11n.py")
    exit()

# Load the model
model = YOLO(model_path)

# Step 2: Test on images from the counter_dataset folder
print("\nTesting model on counter images...")

# Path to your test images
test_images_folder = "counter_dataset"

# Check if folder exists
if not os.path.exists(test_images_folder):
    print(f"\nERROR: Folder '{test_images_folder}' not found!")
    exit()

# Run predictions on all images in the folder
# Results will be saved in runs/detect/predict folder
results = model.predict(
    source=test_images_folder,
    conf=0.25,  # Confidence threshold (0.25 means 25% sure)
    save=True,  # Save images with bounding boxes drawn
    project="runs/detect",
    name="test_results"
)

# Step 3: Show results
print("\n" + "="*50)
print("Testing completed!")
print("="*50)
print("\nResults saved at:")
print("runs/detect/test_results/")
print("\nOpen that folder to see your images with detected counters marked.")
print("\nEach image will have bounding boxes around detected counters.")

