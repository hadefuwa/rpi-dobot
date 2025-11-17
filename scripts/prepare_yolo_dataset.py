#!/usr/bin/env python3
"""
YOLO Dataset Preparation Script
Captures images from camera for training counter detection model
"""

import cv2
import os
import time
from pathlib import Path

def capture_training_images(output_dir: str = 'dataset/images', num_images: int = 50):
    """
    Capture training images from camera

    Args:
        output_dir: Directory to save images
        num_images: Number of images to capture
    """
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Initialize camera
    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not camera.isOpened():
        print("Error: Could not open camera")
        return

    print(f"Capturing {num_images} images. Press SPACE to capture, ESC to quit")
    print("Tips:")
    print("- Capture counters in different positions")
    print("- Include different lighting conditions")
    print("- Capture with 0, 1, 2, 3, 4+ counters visible")
    print("- Include some images with no counters")

    count = 0
    while count < num_images:
        ret, frame = camera.read()
        if not ret:
            continue

        # Display frame
        display_frame = frame.copy()
        cv2.putText(display_frame, f"Captured: {count}/{num_images}",
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(display_frame, "SPACE: Capture | ESC: Quit",
                   (10, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.imshow('Capture Training Images', display_frame)

        key = cv2.waitKey(1) & 0xFF

        # SPACE to capture
        if key == ord(' '):
            filename = os.path.join(output_dir, f'counter_{count:04d}.jpg')
            cv2.imwrite(filename, frame)
            print(f"Captured: {filename}")
            count += 1
            time.sleep(0.3)  # Debounce

        # ESC to quit
        elif key == 27:
            print("Capture cancelled")
            break

    camera.release()
    cv2.destroyAllWindows()

    print(f"\nCapture complete! {count} images saved to {output_dir}")
    print("\nNext steps:")
    print("1. Use labelImg or Roboflow to annotate images")
    print("2. Export in YOLO format")
    print("3. Train model using: yolo train data=dataset.yaml model=yolov8n.pt epochs=50")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Capture training images for YOLO')
    parser.add_argument('--output', default='dataset/images', help='Output directory')
    parser.add_argument('--num', type=int, default=50, help='Number of images to capture')

    args = parser.parse_args()

    capture_training_images(args.output, args.num)
