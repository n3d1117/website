---
title: Rendering mathematical expressions into HTML using Katex
description: This is a sample post for testing the integration of Katex in order to transform mathematical expressions from Markdown into visually appealing HTML, a useful feature for static websites.
date: 2021-05-31T05:24:54.000Z
slug: katex-math-html
tags: [math, html, katex]
toc: true
math: true
comments: true
---

## Introduction

{{< note variant="info" >}}
This is a sample post intended to test the integration of [Katex](https://katex.org/) within [Hugo](https://gohugo.io) in order to convert complex mathematical expressions from Markdown into visually appealing HTML, a useful feature for static websites.
{{< /note >}}

## Demo

Expressions in `TeX` format are inserted in markdown using code blocks surrounded by `$$`.

For example, the following:

```tex {linenos=false}
$$Gamma = \frac{1}{\lambda_t} \cdot \sum_{i=1}^L \frac{I_i}{C_i - I_i} + \gamma \cdot \sum_{i=1}^{L}d_i \cdot C_i$$
```

is then rendered in HTML as:

$$\Gamma = \frac{1}{\lambda_t} \cdot \sum_{i=1}^L \frac{I_i}{C_i - I_i} + \gamma \cdot \sum_{i=1}^{L}d_i \cdot C_i$$

Which not only looks great, it also has semantic annotations and respects dark mode!

This implementation uses [auto-render extension](https://katex.org/docs/autorender.html) under the hook to automatically render all the math in place.

**Inline equations** are also supported: $c = \\pm\\sqrt{a^2 + b^2}$

## More

Katex also offers a [CLI tool](https://katex.org/docs/cli.html) that can output raw HTML. Note that you will need to add Katex CSS and fonts to display the expression properly.

Refer to the [official documentation](https://katex.org/docs/api.html) for more details!
