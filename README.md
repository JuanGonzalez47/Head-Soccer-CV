# 🧠 Head Soccer — Computer Vision Controlled Edition

This project is an experimental fork of [Old Head Soccer](https://github.com/Nicolasbort/Old-Head-Soccer), redesigned to explore **human-motion control** using **computer vision**.

The goal is to replace traditional keyboard inputs with **body movement detection** — using your hands, head, and feet captured by your webcam.

---

## 🎯 Project Goals

- Replace keyboard inputs (`A`, `D`, `W`, `Space`) with camera-based gesture recognition.
- Experiment with different **segmentation and tracking techniques** (Mediapipe, background subtraction, color tracking, etc.).
- Build a working **MVP** (Minimum Viable Product) demonstrating real-time gameplay controlled by your movements.
- Serve as a sandbox for testing **vision-to-control pipelines** in Python.

---

## 🕹️ Controls (Planned Mapping)

| Game Action | Real-World Movement | Vision Technique |
|--------------|--------------------|------------------|
| Move Left | Left hand open palm | Hand detection |
| Move Right | Right hand open palm | Hand detection |
| Jump | Head up motion | Pose tracking |
| Shoot | Foot kick gesture | Pose tracking / motion detection |

---

## ⚙️ Tech Stack

- **Python 3.9+**
- **graphics.py** – for rendering the original 2D game
- **OpenCV** – webcam capture and image processing
- **Mediapipe** – body, hand, and pose detection
- **NumPy** – optional for data smoothing or calculations
- **playsound** / **Pillow** – from original game
