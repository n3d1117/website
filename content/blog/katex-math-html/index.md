---
title: Rendering beautiful mathematical expressions into HTML using Katex
description: This is a sample post for testing Katex integration as a Publish plugin in order to render beautiful mathematical expressions from Markdown into HTML.
date: 2019-01-13T05:24:54.000Z
slug: katex-math-html
tags: [poetry, time]
toc: true
math: true
---

This is a sample post for testing [Katex CLI](https://katex.org/docs/cli.html) integration as a [Publish](https://github.com/JohnSundell/Publish) plugin in order to render beautiful mathematical expressions from Markdown into HTML, useful for static websites. 

## Demo

Expressions in `TeX` format are inserted in markdown using code blocks with `math_formula` language. For example, the following:

```tex
$$Gamma = \frac{1}{\lambda_t} \cdot \sum_{i=1}^L \frac{I_i}{C_i - I_i} + \gamma \cdot \sum_{i=1}^{L}d_i \cdot C_i$$
```

is then rendered in HTML as:

$$\\Gamma = \\frac{1}{\\lambda_t} \\cdot \\sum_{i=1}^L \\frac{I_i}{C_i - I_i} + \\gamma \\cdot \\sum_{i=1}^{L}d_i \\cdot C_i$$

Which not only looks great, it also has semantic annotations and respects dark mode!

## Katex CLI Installation

```bash
npm install katex
# or globally
npm install -g katex
```

## Example Usage

```bash
echo "c = \pm\sqrt{a^2 + b^2}" | katex
```

The command above will output: 

Which then translates to inline: $c = \\pm\\sqrt{a^2 + b^2}$

Note that you will need to add Katex CSS and fonts to display the expression properly. 

Refer to the [official documentation](https://katex.org/docs/cli.html) for more details.
