---
title: Simulating Bus Bunching with Python
description: A Monte Carlo simulation of transit delays and clumping
date: 2024-08-19
author: Demo Author
tags:
  - python
  - transportation
  - simulation
status: published
featured: false
---

If you've ever waited 20 minutes for a bus only to have three show up at once, you’ve experienced "bus bunching." It's a common problem in public transportation systems, and a surprisingly difficult one to solve.

Inspired by examples from the transit literature, I wrote a simple agent-based simulation in Python to study how random delays cause evenly spaced buses to clump together over time. Each bus travels along a loop with regular stops. At each stop, it encounters a random delay drawn from a normal distribution.

```python
def simulate_buses(n_buses, n_stops, steps=1000):
    positions = np.zeros(n_buses)
    for _ in range(steps):
        delays = np.random.normal(loc=1.0, scale=0.3, size=n_buses)
        positions += delays
        yield np.mod(positions, n_stops)
```

This results in beautifully chaotic patterns over time — buses that start evenly spaced slowly collapse into clusters. Below is a simple heatmap showing the density of arrivals at each stop over time:

![](/static/media/demo-bus-bunching.png)

By adding simple rules (e.g., dwell time increases with passengers), we can model the positive feedback loop that causes the bunching. There’s also room to experiment with countermeasures: enforced holding at timing stops, real-time spacing adjustments, etc.

While simplified, this model shows how emergent patterns like clumping can arise from randomness and simple behavior — and how simulation can be a great tool for intuition.
