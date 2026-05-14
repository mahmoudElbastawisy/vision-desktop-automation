# vision-desktop-automation
Vision-based desktop automation system for dynamic Notepad icon grounding on Windows.
# Vision-Based Desktop Automation with Dynamic Icon Grounding

A resilient desktop automation system that visually locates applications using:

* Gemini multimodal grounding
* OCR-based text detection
* OpenCV template matching

instead of relying on hardcoded screen coordinates.

The system dynamically discovers the Notepad desktop icon, launches the application through real visual grounding, writes content, saves files through the actual Windows UI, and adapts to changing desktop layouts.

---

# Demo

## Visual Grounding Examples

### OCR Grounding

<img width="1920" height="1080" alt="notepad_grounding_20260513_193354_890443" src="https://github.com/user-attachments/assets/80d26a14-1174-456e-b7ab-69949fbeb818" />


### Template Matching

<img width="1920" height="1080" alt="notepad_grounding_20260514_044738_175391" src="https://github.com/user-attachments/assets/afec9b0f-3978-442a-8ee9-5ece22681f08" />


### Gemini Vision Grounding

```text
[ INSERT GEMINI ANNOTATED SCREENSHOT HERE ]
```

---

# Key Features

* Dynamic desktop icon grounding
* Multi-strategy visual detection pipeline
* Gemini-powered semantic icon localization
* OCR label detection using EasyOCR
* OpenCV template matching fallback
* Real Windows UI automation
* Screenshot annotation and debugging
* Graceful API degradation with fallback data
* Retry handling and fault tolerance
* Modular architecture with clean separation of concerns

---

# How It Works

The workflow intentionally avoids:

* hardcoded coordinates
* subprocess launching
* shell execution
* Start Menu automation

Instead, the system interacts with the desktop visually.

## Workflow Pipeline

```text
Fetch Posts
     ↓
Capture Desktop Screenshot
     ↓
Locate Notepad Icon
(Gemini → OCR → Template Matching)
     ↓
Double Click Icon
     ↓
Validate Window
     ↓
Write Content
     ↓
Save Through Windows Dialog
     ↓
Close Notepad
     ↓
Repeat
```

---

# Grounding Architecture

## 1. Gemini Vision Grounding

An optional multimodal grounding layer powered by Google Gemini.

The system uses a two-stage semantic localization process:

### Stage 1 — Region Detection

Gemini analyzes the full desktop screenshot and predicts which region likely contains the target icon.

Example:

```json
{
  "quarter": "top_left",
  "confidence": 0.91
}
```

### Stage 2 — Coordinate Localization

The predicted region is cropped and sent back to Gemini for fine-grained localization.

Example:

```json
{
  "found": true,
  "bbox": [120, 80, 210, 170],
  "center": [165, 125],
  "confidence": 0.88
}
```

The crop-local coordinates are then converted back into full-screen coordinates and validated before automation begins.

### Why This Matters

Unlike traditional automation systems, Gemini grounding introduces:

* semantic UI understanding
* adaptive desktop reasoning
* layout-aware icon discovery
* coarse-to-fine visual localization

---

## 2. OCR Grounding

The OCR layer detects desktop labels such as:

```text
Notepad
```

using EasyOCR.

The pipeline includes:

* text normalization
* exact-match prioritization
* confidence filtering
* bounding box extraction

This method works even when icon visuals change.

---

## 3. Template Matching

OpenCV template matching acts as a deterministic fallback layer.

The system:

1. loads a known icon template
2. converts images to grayscale
3. performs normalized template matching
4. extracts ranked candidate locations

This method provides:

* fast detection
* pixel-level matching
* deterministic fallback behavior

---

# Fault Tolerance & Resilience

The system was designed to fail gracefully.

## Grounding Fallback Order

```text
Gemini → OCR → Template Matching
```

If any layer fails:

* invalid JSON
* low confidence
* network errors
* OCR issues
* missing templates

another grounding strategy continues automatically.

---

## API Fallback Handling

If the JSONPlaceholder API becomes unavailable:

* timeout
* connection reset
* invalid response

the workflow automatically switches to local fallback sample posts so the automation can still complete successfully.

---

# Project Structure

```text
vision-desktop-automation/
│
├── assets/
│   └── templates/
│
├── screenshots/
│   ├── raw/
│   └── annotated/
│
├── src/
│   └── desktop_grounding/
│       ├── api/
│       ├── automation/
│       ├── utils/
│       ├── vision/
│       ├── config.py
│       └── main.py
│
├── pyproject.toml
└── README.md
```

---

# Technology Stack

| Technology    | Purpose                     |
| ------------- | --------------------------- |
| Python        | Core application            |
| PyAutoGUI     | Mouse & keyboard automation |
| MSS           | Screenshot capture          |
| Pillow        | Image processing            |
| EasyOCR       | OCR grounding               |
| OpenCV        | Template matching           |
| Google Gemini | Semantic visual grounding   |
| Requests      | API communication           |
| PyGetWindow   | Window validation           |
| Rich Logging  | Structured logging          |

---

# Configuration

The project uses centralized configuration through:

```text
config.py
```

Examples:

```python
ENABLE_GEMINI_GROUNDING = True
MAX_RETRIES = 3
OCR_MATCH_CONFIDENCE_THRESHOLD = 0.75
ICON_MATCH_CONFIDENCE_THRESHOLD = 0.85
```

Gemini grounding can be enabled or disabled instantly depending on performance or testing needs.

---

# Running The Project

## Install Dependencies

```bash
uv sync
```

## Run The Workflow

```bash
$env:PYTHONPATH="src"
uv run python -m desktop_grounding.main
```

---

# Example Output

```text
Desktop/
└── tjm-project/
    ├── post_1.txt
    ├── post_2.txt
    ├── post_3.txt
    └── ...
```

---

# Engineering Notes

## Why Avoid Hardcoded Coordinates?

Hardcoded desktop automation breaks when:

* icons move
* resolutions change
* monitors differ
* layouts change

This project solves that problem through dynamic visual grounding.

---

## Why Multiple Grounding Methods?

Desktop environments are unpredictable.

Combining:

* semantic reasoning
* OCR grounding
* deterministic computer vision

creates a significantly more resilient automation system.

---

## Why Keep Gemini Optional?

LLM-based grounding is powerful but slower than deterministic methods.

The optional configuration toggle allows:

```python
ENABLE_GEMINI_GROUNDING = False
```

for faster local execution.

---

# Future Improvements

Potential future extensions:

* multi-monitor support
* autonomous UI agents
* accessibility tree integration
* local multimodal models
* real-time object detection
* reinforcement learning navigation

---

# Final Notes

This project explores the intersection between:

* desktop automation
* computer vision
* multimodal AI systems
* resilient software engineering

The focus was not only automating a task, but designing a flexible visual grounding architecture capable of adapting to dynamic desktop environments.
