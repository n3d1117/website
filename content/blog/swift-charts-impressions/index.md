---
title: "A first look at Swift Charts: building a horizontal bar chart"
description: "An introduction to the Swift Charts library and a look at how to build a horizontal bar chart using some sample data."
date: 2022-12-05T05:24:54.000Z
slug: swift-charts-impressions
tags: [ios, swift, swiftui]
toc: true
math: false
comments: true
---

## Introduction
[Swift Charts](https://developer.apple.com/documentation/charts) is a new library that was introduced by Apple during WWDC22. It provides a set of views and modifiers that can be used to create charts and graphs in [SwiftUI](https://developer.apple.com/xcode/swiftui/).

{{< note variant="info" >}}
In this post, we will take a first look at Swift Charts by building a horizontal bar chart using some sample data.
{{< /note >}}

## Data model
Let's start by creating a data model. We will define a struct called `Entry`, which will represent the data that we want to display in our chart. Each `Entry` will have a period and an amount:

```swift
private struct Entry: Identifiable {
    let id = UUID()
    let period: String
    let amount: Int
}
```

Note that we are conforming our `Entry` struct to the `Identifiable` protocol by providing a default `id` property. This is required by the `Chart` initializer we're going to use later.

Next, we will create an array of `Entry` objects that will be used to populate our chart. We will use the following sample data:

```swift
// torchlight! {"lineNumbers": false}
let data: [Entry] = [
    .init(period: "Today", amount: 5),
    .init(period: "This Week", amount: 50),
    .init(period: "This Month", amount: 100),
    .init(period: "This Year", amount: 150),
    .init(period: "All Time", amount: 220),
]
```

## Chart view
Now, let's build our horizontal bar chart. We will wrap it in a `VStack` to give it some padding and a nice title.

Make sure to `import Charts` at the top of your Swift file.

```swift
VStack(alignment: .leading, spacing: spacing) {
    Text("Downloads")
        .font(.title3)
        .fontWeight(.semibold)
    
    GroupBox {
        Chart(data) { item in
            BarMark(
                x: .value("Amount", item.amount),
                y: .value("Period", item.period)
            )
        }
        .fixedSize(horizontal: false, vertical: true)
    }
}
```

Inside the `Chart` view, we are using a BarMark to create the bars for our chart. We are setting the `x` and `y` values for each bar using the amount and period properties of each `Entry`.

We use the `.fixedSize(horizontal: false, vertical: true)` modifier to make sure that the chart is not stretched vertically, and instead, it takes up the minimum amount of space required to display the chart.

Here's the initial result:

{{< img src="result_1.png" caption="Initial result with no customization" w="450" >}}

It's not very pretty yet, but we can easily customize it to make it look better. 

### Customization
Let's start by adding a trailing annotation to each bar. We will use the `annotation` modifier on the `BarkMark` to do this:

```swift
Chart(data) { item in
    BarMark(/* ... */)
    .annotation(position: .trailing) { // [tl! focus:4]
        Text(item.amount.formatted())
            .foregroundColor(.secondary)
            .font(.caption)
    }
}
```

The annotation will display the amount of downloads for each period. Then we'll add a y-axis label displaying the period. We will use the `chartYAxis` modifier to do this:

```swift
Chart(data) { item in
    /* ... */
}
.fixedSize(horizontal: false, vertical: true)
.chartYAxis {  // [tl! focus:5]
    AxisMarks(preset: .extended, position: .leading) { _ in
        AxisValueLabel(horizontalSpacing: 15)
            .font(.footnote) // [tl! focus] 
    }
}
```

Finally, we can adjust the thickness of the bars by providing a `width` value to the `BarMark` initializer:

```swift
BarMark(
    /* ... */
    width: .fixed(8) // [tl! highlight]
)
```

And there you have it! With just a few lines of code, we've created a nice-looking horizontal bar chart using Swift Charts. Here's the final result:

{{< img src="result_2.png" caption="Final result" w="450" >}}

This is just a small example of what is possible with Swift Charts. There are many other types of charts and graphs that can be created using this library, like line charts, pie charts, scatterplots, histograms, and more.

To learn more about Swift Charts and its capabilities, check out the [official documentation](https://developer.apple.com/documentation/charts)!