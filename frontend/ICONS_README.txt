PWA ICONS NEEDED
================

Please add two icon files to this directory:

1. icon-192.png (192x192 pixels)
2. icon-512.png (512x512 pixels)

You can:
- Create them with any image editor
- Use an online icon generator
- Run this on Linux/Mac with ImageMagick installed:
  convert -size 192x192 xc:#2563eb -gravity center -pointsize 72 -fill white -annotate +0+0 "DP" icon-192.png
  convert -size 512x512 xc:#2563eb -gravity center -pointsize 200 -fill white -annotate +0+0 "DP" icon-512.png

The PWA will work without icons, but they're needed for proper installation on mobile devices.
