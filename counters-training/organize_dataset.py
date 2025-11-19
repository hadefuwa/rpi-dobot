"""
Organize Dataset Script - Beginner Friendly
This script automatically splits your images and labels into train/val folders
"""

import os
import shutil
import random

print("="*50)
print("Organizing Dataset for YOLO Training")
print("="*50)
print()

# Step 1: Check if all folders exist
print("[Step 1/5] Checking folders...")

# Source folders
images_source = "counter_dataset"
labels_source = "counter_labels"

# Destination folders
train_images = "dataset/images/train"
val_images = "dataset/images/val"
train_labels = "dataset/labels/train"
val_labels = "dataset/labels/val"

# Check if source folders exist
if not os.path.exists(images_source):
    print(f"ERROR: '{images_source}' folder not found!")
    print("Make sure your images are in the counter_dataset folder.")
    exit()

if not os.path.exists(labels_source):
    print(f"ERROR: '{labels_source}' folder not found!")
    print("Make sure you extracted the label files to counter_labels folder.")
    exit()

print(f"[OK] Found {images_source} folder")
print(f"[OK] Found {labels_source} folder")
print()

# Step 2: Get all image files
print("[Step 2/5] Finding images...")

# Get all image files (jpg, jpeg, png)
image_files = []
for file in os.listdir(images_source):
    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
        image_files.append(file)

if len(image_files) == 0:
    print("ERROR: No image files found in counter_dataset folder!")
    exit()

print(f"[OK] Found {len(image_files)} images")
print()

# Step 3: Check that each image has a matching label file
print("[Step 3/5] Checking labels...")

valid_pairs = []
missing_labels = []

for image_file in image_files:
    # Get the label file name (same name but .txt extension)
    label_file = os.path.splitext(image_file)[0] + '.txt'
    label_path = os.path.join(labels_source, label_file)
    
    if os.path.exists(label_path):
        valid_pairs.append((image_file, label_file))
    else:
        missing_labels.append(image_file)

print(f"[OK] Found {len(valid_pairs)} image-label pairs")

if missing_labels:
    print(f"[WARNING] {len(missing_labels)} images don't have labels:")
    for img in missing_labels:
        print(f"  - {img}")
    print()

if len(valid_pairs) == 0:
    print("ERROR: No valid image-label pairs found!")
    print("Make sure your label files have the same names as your images.")
    exit()

# Step 4: Split into train and validation sets (80/20)
print("[Step 4/5] Splitting into train/val sets...")

# Shuffle the pairs randomly
random.seed(42)  # Use a fixed seed so results are reproducible
random.shuffle(valid_pairs)

# Calculate split point (80% train, 20% val)
split_point = int(len(valid_pairs) * 0.8)
train_pairs = valid_pairs[:split_point]
val_pairs = valid_pairs[split_point:]

print(f"[OK] Train set: {len(train_pairs)} images")
print(f"[OK] Validation set: {len(val_pairs)} images")
print()

# Step 5: Copy files to destination folders
print("[Step 5/5] Copying files...")

# Clear destination folders first
for folder in [train_images, val_images, train_labels, val_labels]:
    if os.path.exists(folder):
        # Remove all files in the folder
        for file in os.listdir(folder):
            file_path = os.path.join(folder, file)
            if os.path.isfile(file_path):
                os.remove(file_path)

# Copy training set
copied_train = 0
for image_file, label_file in train_pairs:
    # Copy image
    src_image = os.path.join(images_source, image_file)
    dst_image = os.path.join(train_images, image_file)
    shutil.copy2(src_image, dst_image)
    
    # Copy label
    src_label = os.path.join(labels_source, label_file)
    dst_label = os.path.join(train_labels, label_file)
    shutil.copy2(src_label, dst_label)
    
    copied_train += 1

print(f"[OK] Copied {copied_train} image-label pairs to training set")

# Copy validation set
copied_val = 0
for image_file, label_file in val_pairs:
    # Copy image
    src_image = os.path.join(images_source, image_file)
    dst_image = os.path.join(val_images, image_file)
    shutil.copy2(src_image, dst_image)
    
    # Copy label
    src_label = os.path.join(labels_source, label_file)
    dst_label = os.path.join(val_labels, label_file)
    shutil.copy2(src_label, dst_label)
    
    copied_val += 1

print(f"[OK] Copied {copied_val} image-label pairs to validation set")
print()

# Summary
print("="*50)
print("Dataset Organization Complete!")
print("="*50)
print()
print("Summary:")
print(f"  Total images: {len(valid_pairs)}")
print(f"  Training set: {len(train_pairs)} images ({len(train_pairs)/len(valid_pairs)*100:.1f}%)")
print(f"  Validation set: {len(val_pairs)} images ({len(val_pairs)/len(valid_pairs)*100:.1f}%)")
print()
print("Your dataset is now organized and ready for training!")
print()
print("Next step: Run the training script")
print("  python train_yolov11n.py")
print()

