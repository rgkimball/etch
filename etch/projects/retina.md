---
title: Retina
description: A machine learning model for detecting diabetic retinopathy
date_started: 2024-11-01
date_completed: 2025-01-15
status: completed
technologies:
  - Python
  - PyTorch
  - OpenCV
  - FastAPI
github_url: https://github.com/example/retina
featured: false
---

**Retina** is a deep learning project trained to identify diabetic retinopathy from retinal scans. The model was built as a weekend challenge and later extended into a mini-service with an API, preprocessing pipeline, and demo UI.

The dataset came from a public Kaggle competition, and performance was validated against held-out folds and third-party graders. It’s not FDA-cleared (obviously), but it performs surprisingly well for a side project.

### Highlights

- **CNN architecture**: Custom ResNet variant fine-tuned on retinal imagery
- **Preprocessing pipeline**: OpenCV used for image alignment, denoising, and normalization
- **Web API**: FastAPI wrapper for easy inference and integration
- **Dashboard demo**: Interactive UI for exploring predictions and heatmaps
- **Built for learning**: Annotated notebooks and modular code structure

---

> Try it: [retina.example.com](https://retina.example.com)  
> Code: [github.com/example/retina](https://github.com/example/retina)
