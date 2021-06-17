# Models

Folder containing trained models on dataset of nine species.

## Results

### yolov5s imagesize 640

```md
al: Scanning '/mnt/fast/dataset/labels/val.cache' images and labels... 12560 found, 8 missing, 0 empty, 0
Class Images Labels P R mAP@.5 mAP@.5:.95: 100%|█| 393/
all 12568 24881 0.958 0.949 0.962 0.812
gjedde 12568 8351 0.986 0.998 0.994 0.959
gullbust 12568 349 0.92 0.987 0.986 0.821
rumpetroll 12568 2260 0.973 0.985 0.994 0.86
stingsild 12568 68 0.889 0.676 0.77 0.475
oreskyt 12568 6106 0.953 0.993 0.994 0.814
abbor 12568 2903 0.987 0.997 0.996 0.922
brasme 12568 50 0.958 0.919 0.937 0.66
mort 12568 1281 0.983 0.995 0.994 0.87
vederbuk 12568 3513 0.97 0.989 0.993 0.929
Speed: 0.9/0.8/1.7 ms inference/NMS/total per 640x640 image at batch-size 32
```

### yolov5m6 imagesize 768

```md
val: Scanning '/mnt/fast/dataset/labels/val.cache' images and labels... 12560 found, 8 missing, 0 empty, 0
Class Images Labels P R mAP@.5 mAP@.5:.95: 100%|█| 393/
all 12568 24881 0.977 0.948 0.961 0.852
gjedde 12568 8351 0.988 0.998 0.994 0.983
gullbust 12568 349 0.963 0.974 0.992 0.848
rumpetroll 12568 2260 0.993 0.966 0.994 0.862
stingsild 12568 68 0.944 0.75 0.786 0.565
oreskyt 12568 6106 0.987 0.986 0.995 0.831
abbor 12568 2903 0.992 0.993 0.995 0.951
brasme 12568 50 0.962 0.88 0.906 0.767
mort 12568 1281 0.989 0.995 0.995 0.895
vederbuk 12568 3513 0.978 0.986 0.993 0.962
Speed: 2.0/0.8/2.8 ms inference/NMS/total per 640x640 image at batch-size 32
```
