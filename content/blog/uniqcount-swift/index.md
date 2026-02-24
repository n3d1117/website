---
title: "Uniqcount: estimating unique elements with a tiny amount of memory"
description: "A practical look at building a memory-efficient distinct-elements estimator in Swift, based on the CVM streaming algorithm."
date: 2026-02-19T12:00:00.000Z
slug: uniqcount-swift
tags: [swift, algorithms, streaming, math]
toc: true
math: true
comments: true
---

{{< note variant="info" >}}
I built [`uniqcount`](https://github.com/n3d1117/uniqcount) after reading the [Quanta piece](https://www.quantamagazine.org/computer-scientists-invent-an-efficient-new-way-to-count-20240516/) and the revised [paper](https://arxiv.org/abs/2301.10191).
This post explains the algorithm, the Swift implementation choices, and what I could reproduce from the article's claims.
{{< /note >}}

## Introduction

The problem: given a stream of values, estimate how many distinct values appeared.

For small inputs, exact counting is easy: insert everything into a set and read `count`.
For large streams, exact counting can use too much memory, so approximate counting is useful.

### Problem

Write the stream as:

$$A = \langle a_1, a_2, \dots, a_m \rangle$$

The target quantity is:

$$F_0(A) = |\{a_1, a_2, \dots, a_m\}|$$

So $F_0(A)$ is the number of distinct values seen at least once.

### Estimator

In this post I use the estimator from the paper; people call it CVM after the authors (Chakraborty, Vinodchandran, and Meel).
It keeps:

- a sample set $X$
- a sampling probability $p$

Interpret $p$ as a coin bias:

- if $p = 1$, keep every eligible value
- if $p = 1/2$, keep on heads
- if $p = 1/4$, keep with probability $25\%$

For each new stream element $a_i$:

1. remove $a_i$ from $X$ (if present)
2. add $a_i$ back with probability $p$
3. if $|X|$ reaches a threshold, keep each item in $X$ with probability $1/2$, then set $p \leftarrow p/2$

Final estimate:

$$\hat{F_0} = \frac{|X|}{p}$$

The remove-then-add step is important. It gives each distinct token one fresh coin flip at the current rate.
For example, with `cat, cat, dog` and $p = 1/2$, the second `cat` replaces the first `cat` sample decision instead of accumulating extra weight.

A useful intuition is Quanta's whiteboard example with capacity 100:

- fill the board at $p = 1$
- when full, flip coins and keep about half, then set $p = 1/2$
- repeat each time the board fills

Their sample run ends with $k = 6$ (so $p = 1/2^6$) and $|X| = 61$:

$$\hat{F_0} = 61 \cdot 2^6 = 3904$$

The exact distinct count reported there is 3967, so the estimate is close.

### Choosing the threshold

The paper sets threshold from $\varepsilon$, $\delta$, and stream length $m$:

$$\text{threshold} = \left\lceil \frac{12}{\varepsilon^2} \log_2\left(\frac{8m}{\delta}\right) \right\rceil$$

- $\varepsilon$: target relative error
- $\delta$: allowed failure probability
- $m$: stream length

Theorem 2 states that with this threshold, output is within $(1 \pm \varepsilon)$ of $F_0$ with probability at least $1 - \delta$.

For Hamlet in this post ($m = 36107$), $\varepsilon = 0.1$, $\delta = 0.05$ gives threshold 26955.
That is much larger than the exact distinct count (4962), so this setting behaves like exact counting on this dataset.

## Swift implementation

I implemented this in Swift as a small CLI tool. The repo is [n3d1117/uniqcount](https://github.com/n3d1117/uniqcount).

High-level codebase layout:

- `Core.swift`: estimator logic, tokenizer, threshold calculation, and trial runner
- `UniqCount.swift`: CLI entry point (parse args, load input, run experiment)
- `Reporting.swift`: aggregates trial stats and prints run/trial/summary tables

High-level execution flow:

1. parse CLI options (`--memory` or `--epsilon --delta`, trials, seed)
2. load the file once and tokenize it once
3. resolve threshold
4. run independent trials in parallel with deterministic per-trial seeds
5. aggregate results and print either one estimate or a full report

CLI modes:

- fixed threshold via `--memory`
- formula-based threshold via `--epsilon --delta`

Default run:

```bash
swift run uniqcount --path /tmp/hamlet.txt
```

### Optimizations

- **Tokenize once, then map to integer IDs**
  Each unique token gets a `UInt32` ID, and all trials run on IDs rather than strings.

- **Bit-mask sampling in the hot loop**
  Sampling uses `(rng.next() & mask) == 0` for probabilities of the form \(1/2^k\).

- **Cached scale factor**
  Estimate uses \(|X| \cdot 2^k\) with a cached multiplier instead of repeated `pow` calls.

- **Deterministic downsampling order**
  Before thinning, the set is sorted so fixed-seed runs stay reproducible across launches.

- **Parallel trials with stable output order**
  Trials run concurrently, but each trial writes to a fixed result index.

- **ASCII fast path + Unicode fallback tokenizer**
  ASCII input uses a byte-level path; non-ASCII uses a Unicode-safe path.

## Results

### Hamlet

I used [`hamlet.txt` from Project Gutenberg](https://www.gutenberg.org/cache/epub/1524/pg1524.txt), with seed 42 and 30 trials per config.

The tokenization rule I used is:

- keep letters, digits, and apostrophe (`'`)
- lowercase everything
- split on all other characters

Examples:

- `KING,` -> `king`
- `can't` -> `can't`
- `to-be` -> `to`, `be`
- `Act 3` -> `act`, `3`

Dataset stats:

- tokens: 36107
- exact distinct: 4962

I used 30 trials because this is a randomized estimator. A single run can be lucky or unlucky; 30 runs gives stable mean/max error while keeping runtime short.

| Config | Threshold | Mean relative error | Max relative error | Mean trial time |
|---|---:|---:|---:|---:|
| `--memory 100` | 100 | 8.279% | 36.719% | 13.329 ms |
| `--memory 250` | 250 | 6.355% | 21.241% | 15.203 ms |
| `--memory 500` | 500 | 3.929% | 15.760% | 18.847 ms |
| `--memory 1000` | 1000 | 2.631% | 5.764% | 28.637 ms |
| `--memory 2000` | 2000 | 1.760% | 5.119% | 32.285 ms |

As memory increases, both average and worst-case error decrease.
In practical terms, with exact distinct count 4962, a mean relative error of 2.631% means the estimate is off by about 131 tokens on average.  
At 8.279%, the average gap is about 411 tokens.

Paper-parameter runs:

| Config | Threshold | Mean relative error | Max relative error | Mean trial time |
|---|---:|---:|---:|---:|
| `--epsilon 0.2 --delta 0.1` | 6439 | 0.000% | 0.000% | 17.520 ms |
| `--epsilon 0.15 --delta 0.05` | 11980 | 0.000% | 0.000% | 15.178 ms |
| `--epsilon 0.1 --delta 0.05` | 26955 | 0.000% | 0.000% | 15.568 ms |

Each threshold is larger than 4962, so downsampling does not trigger and output is exact on this dataset.

Quanta reports averages of 3955 (`memory = 100`) and 3964 (`memory = 1000`) for true value 3967 over five runs.
I reproduced the same trend (higher memory gives tighter estimates), but not identical absolute numbers, which depends on tokenization and dataset details.

### Reproducing

```bash
curl -L 'https://www.gutenberg.org/cache/epub/1524/pg1524.txt' -o /tmp/hamlet.txt
git clone https://github.com/n3d1117/uniqcount.git
cd uniqcount
```

```bash
swift run uniqcount --path /tmp/hamlet.txt --memory 1000 --trials 30 --seed 42 --report
```

```bash
swift run uniqcount --path /tmp/hamlet.txt --epsilon 0.1 --delta 0.05 --trials 30 --seed 42 --report
```

### Output

This is a real run with `--memory 1000`, `--trials 10`, `--seed 42`.

```bash
swift run --quiet uniqcount --path /tmp/hamlet.txt --memory 1000 --trials 10 --seed 42 --report
```

```text
Run:
+----------------+-----------------+
| Field          |           Value |
+----------------+-----------------+
| path           | /tmp/hamlet.txt |
| tokens         |           36107 |
| exact_distinct |            4962 |
| trials         |              10 |
| threshold      |            1000 |
| seed           |              42 |
+----------------+-----------------+

Trials:
+-------+-------+----------+----------+--------+--------+
| Trial | Exact | Estimate | RelError | TimeMs | Status |
+-------+-------+----------+----------+--------+--------+
|     1 |  4962 |     4952 |   0.202% | 24.383 | ok     |
|     2 |  4962 |     4936 |   0.524% | 26.288 | ok     |
|     3 |  4962 |     5192 |   4.635% | 25.172 | ok     |
|     4 |  4962 |     4936 |   0.524% | 25.575 | ok     |
|     5 |  4962 |     4840 |   2.459% | 24.973 | ok     |
|     6 |  4962 |     5192 |   4.635% | 25.656 | ok     |
|     7 |  4962 |     4840 |   2.459% | 27.580 | ok     |
|     8 |  4962 |     5208 |   4.958% | 23.779 | ok     |
|     9 |  4962 |     4800 |   3.265% | 25.830 | ok     |
|    10 |  4962 |     4776 |   3.748% | 24.304 | ok     |
+-------+-------+----------+----------+--------+--------+

Summary:
+---------------------+-----------+
| Metric              |     Value |
+---------------------+-----------+
| trials              |        10 |
| failures(bottom)    |         0 |
| failure_rate        |    0.000% |
| mean_relative_error |    2.741% |
| max_relative_error  |    4.958% |
| mean_trial_time     | 25.354 ms |
+---------------------+-----------+
```

## Conclusion

For this use case, the algorithm is valid.

- The paper provides a formal $(\varepsilon, \delta)$ guarantee.
- The implementation reproduces the expected memory/error tradeoff.
- The Quanta-style claim is reproducible at the behavior level: small memory is noisier, larger memory is steadier.

In practice, use small fixed memory when bounded space matters most.
Use a formula-based threshold when you want stronger guarantees and can spend more memory.

## References

- [Computer Scientists Invent an Efficient New Way to Count](https://www.quantamagazine.org/computer-scientists-invent-an-efficient-new-way-to-count-20240516/) on Quanta Magazine
- [Distinct Elements in Streams: An Algorithm for the (Text) Book (arXiv:2301.10191)](https://arxiv.org/abs/2301.10191)
- [n3d1117/uniqcount](https://github.com/n3d1117/uniqcount) on GitHub
- [Hamlet, Prince of Denmark (Project Gutenberg)](https://www.gutenberg.org/cache/epub/1524/pg1524.txt)
