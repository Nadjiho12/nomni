# Computer vision

*Last updated: 2026-10-13 | Version-sensitive: model families (YOLO, SAM, VLMs) and library versions | Re-check current docs before pinning versions, prices, or API names.*

Image and video understanding: tasks, model choices, data pipelines, evaluation, and deployment. numpy/OpenCV snippets were run; deep-model training needs a GPU environment.

## Contents
1. Task map
2. Classical vision with OpenCV (runs)
3. Detection metrics: IoU, NMS, mAP (runs)
4. Deep learning workflow
5. Data: collection, labeling, augmentation
6. Model choices
7. OCR and document images
8. Video and tracking
9. Vision-language models (VLMs)
10. Deployment: edge and cloud
11. Failure modes
12. Verification

## 1. Task map

| Task | Output | Typical approach |
|---|---|---|
| Classification | label | Pretrained CNN/ViT + fine-tune |
| Detection | boxes + labels | YOLO/RT-DETR family, Faster R-CNN |
| Segmentation | pixel masks | U-Net, DeepLab, Mask R-CNN, SAM-style promptable models |
| Keypoints / pose | landmarks | HRNet, MediaPipe, YOLO-pose |
| OCR | text + layout | Tesseract, PaddleOCR, TrOCR, layout models |
| Embedding / retrieval | vectors | CLIP/SigLIP, DINO |
| Anomaly detection | defect map | Autoencoders, PatchCore, feature distance to normal |
| Depth / 3D | depth, point cloud | Monocular depth models, stereo, SfM |
| Image generation/editing | image | Diffusion models |
| Open-ended QA | text answers | VLM (image + prompt) |
Rule: start with classical image processing if the scene is controlled (fixed camera, lighting, simple contrast); use deep learning when appearance varies.

## 2. Classical vision with OpenCV (runs)

```python
import cv2, numpy as np
img = np.zeros((200, 300, 3), np.uint8); img[:] = (30, 30, 30)
cv2.rectangle(img, (40, 50), (120, 130), (0, 200, 255), -1); cv2.circle(img, (210, 100), 35, (255, 120, 0), -1)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
blur = cv2.GaussianBlur(gray, (5, 5), 0)
_, th = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY)
cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
found = sorted([(cv2.boundingRect(c), cv2.contourArea(c)) for c in cnts if cv2.contourArea(c) > 100], key=lambda t: t[0][0])
print("objects:", len(found), [b for b, _ in found])
edges = cv2.Canny(blur, 50, 150); print("edge pixels:", int((edges > 0).sum()))
tpl = img[50:130, 40:120]; res = cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED); print("template match score:", round(float(res.max()), 2))
```
Toolbox: color spaces (HSV for color thresholds), morphology (open/close), contours, Hough lines/circles, template matching, ORB/SIFT features + RANSAC homography for alignment, background subtraction (MOG2) for fixed cameras, camera calibration and undistortion, perspective transforms.

## 3. Detection metrics: IoU, NMS, mAP (runs)

```python
import numpy as np
def iou(a, b):                                           # boxes as [x1, y1, x2, y2]
    x1, y1, x2, y2 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0
def nms(boxes, scores, thr=0.5):
    order = list(np.argsort(scores)[::-1]); keep = []
    while order:
        i = order.pop(0); keep.append(int(i))
        order = [j for j in order if iou(boxes[i], boxes[j]) < thr]
    return keep
boxes = [[10, 10, 50, 50], [12, 12, 52, 52], [100, 100, 140, 140]]; scores = [0.9, 0.8, 0.7]
print("iou", round(iou(boxes[0], boxes[1]), 2), "keep", nms(boxes, scores))
```
Precision/recall for detection use an IoU threshold (0.5 typical) to match predictions to ground truth; **AP** is the area under the precision-recall curve per class; **mAP@0.5:0.95** averages over IoU thresholds. Also report per-class results, small-object performance, and false positives per image at your operating threshold. Segmentation: IoU/Dice per class.

## 4. Deep learning workflow

1. Define the decision the output drives and the cost of each error type.
2. Collect representative data (lighting, devices, angles, seasons, failure cases); split by **scene/session/subject**, not by random frame (avoid near-duplicate leakage).
3. Baseline: a pretrained model with a new head; log metrics.
4. Train with augmentation; validate on held-out scenes; examine failure images in a gallery grouped by error type.
5. Improve data first (more of the failure cases, label fixes), then model/size, then training tricks.
6. Calibrate thresholds on validation data to hit the required precision/recall; test once on a held-out set.
7. Deploy with monitoring (input brightness/blur distributions, confidence histograms, human-reviewed samples).

Fine-tuning detection (Ultralytics-style; not run here): `yolo detect train data=data.yaml model=yolo11n.pt imgsz=640 epochs=100`; dataset YAML lists train/val folders and class names; labels are normalized `class cx cy w h` text files.

## 5. Data: collection, labeling, augmentation

- Labeling tools: CVAT, Label Studio, Roboflow-style platforms. Write a labeling guide with examples of edge cases; measure inter-annotator agreement; audit 5-10% of labels.
- Active learning: label the examples the model is least sure about or that fail in production.
- Augmentations matched to reality: flips (if semantics allow), crops/scale, color jitter, blur/noise, motion blur, perspective, cutout, mosaic/mixup for detection. Do not augment in ways that change the label meaning (flipping text, left/right-specific defects).
- Synthetic data (rendered scenes, game engines, diffusion) for rare cases, always validated against real held-out images.
- Handle class imbalance with sampling, loss weighting, and per-class metrics.

## 6. Model choices

Edge/real-time: MobileNet/EfficientNet-Lite, YOLO nano/small, quantized INT8, TensorRT/ONNX Runtime/TFLite/CoreML. Accuracy-first server-side: larger CNNs/ViTs, Swin, DINOv2 features. Few labels: foundation features (CLIP/DINO) + linear probe or few-shot; SAM-style models for fast mask labeling. Always compare latency and accuracy on **your** hardware and data.

## 7. OCR and document images

Pipeline: image cleanup (deskew, denoise, binarize/contrast) → text detection → recognition → layout analysis (columns, tables, reading order) → post-processing (dictionary, regex validators, checksum for IDs) → field extraction. For forms and invoices combine OCR with layout-aware models or a VLM with a schema, and route low-confidence fields to review. Measure character/word error rate and field-level accuracy.

```python
# Tesseract (needs tesseract installed; not run here)
# import pytesseract; text = pytesseract.image_to_string(gray, lang="eng", config="--psm 6")
```

## 8. Video and tracking

Process frames with a sampling rate matched to motion; use detection + tracking (SORT/ByteTrack/DeepSORT) to maintain identities; smooth outputs temporally; define events from tracks (line crossing, dwell time, zone entry). Use batch/GPU decoding and a ring buffer so slow inference drops frames instead of lagging behind. Privacy: avoid storing identifiable footage, blur faces where possible, state retention policy, and follow local law.

## 9. Vision-language models (VLMs)

Use for open-ended description, visual QA, document understanding, and flexible classification where labels change often. Prompt with the question, desired schema, and constraints; ask for evidence ("where in the image"); validate structured outputs. Weaknesses: counting, fine spatial reasoning, small text, and hallucinated details; verify with a specialist model or rule when stakes are high. Evaluate on your own image set with a rubric.

## 10. Deployment: edge and cloud

- Export (ONNX/TFLite/TensorRT), quantize (INT8) and verify accuracy loss on the eval set, fix input preprocessing exactly as in training (resize, normalization, color order BGR vs RGB is a classic bug).
- Edge: power and thermal limits, offline operation, OTA updates with rollback, local buffering.
- Cloud: batch requests, autoscale GPUs, queue uploads, signed URLs, retention rules.
- Monitor drift in image statistics and in prediction confidence; sample images for periodic human review.

## 11. Failure modes

Train/test leakage across near-duplicate frames · domain shift (new camera, lighting) · label noise and inconsistent boxes · class imbalance · over-augmentation · preprocessing mismatch at inference · threshold chosen on the test set · small objects lost by downscaling · adversarial or spoofed inputs · privacy violations.

## 12. Verification

Run the OpenCV and IoU/NMS snippets; check metrics are computed on scene-split held-out data; view a gallery of errors; confirm training and inference preprocessing are identical (test one image through both paths); record latency on target hardware; mark GPU training and OCR engines **open gap** unless run.
