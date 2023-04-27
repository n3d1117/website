---
title: Recreating the App Store's expandable text in SwiftUI
description: Recreating the expandable text view used in the App Store's app description using SwiftUI. The view will be able to expand its content by tapping on a "more" button.
date: 2022-07-06T05:24:54.000Z
slug: swiftui-expandable-text
tags: [ios, swift, swiftui]
toc: true
math: false
comments: true
---

{{< note variant="info" >}}
In this post, we'll recreate the expandable text view used in the App Store's app description. The view will be implemented in SwiftUI, and will be able to expand its content by tapping on a "more" button.
{{< /note >}}

## The ExpandableText view

Here's what we're going to build:

{{< img src="demo.png" caption="The final result" w="550" >}}

Full code available on [GitHub](https://github.com/n3d1117/ExpandableText)! We start by creating a new SwiftUI view called `ExpandableText`:


```swift
public struct ExpandableText: View {
    private let text: String

    public init(_ text: String) {
        self.text = text.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    // Body goes here
}
```

We pass the text within the view initializer, trimmed of any leading or trailing whitespace and newline characters.

We keep track of the expanded state with a `@State` variable called `isExpanded`. We leverage the `lineLimit` modifier to return nil (as many lines as needed) if `isExpanded` is false, and a fixed value otherwise (3 for example).

```swift
@State private var isExpanded: Bool = false

public var body: some View {
    Text(.init(text))
        .frame(maxWidth: .infinity, alignment: .leading)
        .lineLimit(isExpanded ? nil : 3)
}
```

Note that if the text fits within the fixed line limit, we don't need to make it expand. To check this, we introduce a `@State` variable called `isTruncated`. This variable will be true if the text is actually truncated when forced to fit in 3 lines, false otherwise.

To check if text is truncated in SwiftUI, we follow the technique used in [this great blog post from Federico Zanetello](https://www.fivestars.blog/articles/trucated-text/):

```swift
@State private var isTruncated: Bool = false
@State private var intrinsicSize: CGSize = .zero
@State private var truncatedSize: CGSize = .zero

public var body: some View {
    Text(.init(text))
        .frame(maxWidth: .infinity, alignment: .leading)
        .lineLimit(isExpanded ? nil : lineLimit)
        .readSize { size in
            truncatedSize = size
            isTruncated = truncatedSize != intrinsicSize
        }
        .background(
            Text(.init(text))
                .frame(maxWidth: .infinity, alignment: .leading)
                .lineLimit(nil)
                .fixedSize(horizontal: false, vertical: true)
                .hidden()
                .readSize { size in
                    intrinsicSize = size
                    isTruncated = truncatedSize != intrinsicSize
                }
        )
}
```

The text size when not truncated is calculated in the background, using the `background` modifier, and compared to the actual text size when constrained to the line limit. If the two sizes are different, then the text definitely requires truncation.

The `readSize` modifier for reading a SwiftUI view's size at runtime is adapted from [another awesome blog post](https://www.fivestars.blog/articles/swiftui-share-layout-information/) on fivestars:

```swift
struct SizePreferenceKey: PreferenceKey {
    static var defaultValue: CGSize = .zero
    static func reduce(value: inout CGSize, nextValue: () -> CGSize) {}
}

extension View {
    func readSize(onChange: @escaping (CGSize) -> Void) -> some View {
        background(
            GeometryReader { geometryProxy in
                Color.clear
                    .preference(key: SizePreferenceKey.self, value: geometryProxy.size)
            }
        )
        .onPreferenceChange(SizePreferenceKey.self, perform: onChange)
    }
}
```

### Trimming multiple new lines when text is truncated
If the text is truncated, we want to remove any 2+ newlines from the text. This is to avoid having newlines at the end of the truncated text, which would look weird. The App Store does this as well.

```swift
var body: some View {
    Text(.init(!isExpanded && isTruncated ? textTrimmingDoubleNewlines : text))
        /* ... */
}

private var textTrimmingDoubleNewlines: String {
    text.replacingOccurrences(of: #"\n\s*\n"#, with: "\n", options: .regularExpression)
}
```

We use a regular expression to replace any double newlines with a single newline. The regular expression is `\n\s*\n`, which matches any newline character followed by any number of whitespace characters followed by another newline character. The replacement string is just a single newline character.


### Adding the expand button...
At the end of the text, we add a `more` button that expands the text when tapped. We use the `overlay` modifier to add the button on top of the text, and position it at the trailing edge of the last text baseline.

```swift
public var body: some View {
    Text(/* ... */)
        /* ... */
        .overlay(alignment: .trailingLastTextBaseline) { // [tl! focus:8]
            if !isExpanded, isTruncated {
                Button {
                    withAnimation { isExpanded.toggle() }
                } label: {
                    Text("more")
                }
            }
        }
}
```

### ...and a fade effect
To make the text fade out when it's truncated, we use a `LinearGradient` mask. We use a `VStack` to mask the top of the text, and a `HStack` to mask the trailing edge of the text. The `LinearGradient` is used to fade out the text from the trailing edge. The size of the `LinearGradient` is determined by the size of the `more` button, which is calculated in the background.

```swift
@State private var moreTextSize: CGSize = .zero

public var body: some View {
    Text(/* ... */)
        /* ... */
        .applyingTruncationMask(size: moreTextSize, enabled: !isExpanded && isTruncated) // [tl! focus:5]
        .background(
            Text(moreButtonText)
                .hidden()
                .readSize { moreTextSize = $0 }
        )
}
```

The `applyingTruncationMask` modifier is defined as follows:

```swift
private struct TruncationTextMask: ViewModifier {

    let size: CGSize
    let enabled: Bool
    
    @Environment(\.layoutDirection) private var layoutDirection

    func body(content: Content) -> some View {
        if enabled {
            content
                .mask(
                    VStack(spacing: 0) {
                        Rectangle()
                        HStack(spacing: 0) {
                            Rectangle()
                            HStack(spacing: 0) {
                                LinearGradient(
                                    gradient: Gradient(stops: [
                                        Gradient.Stop(color: .black, location: 0),
                                        Gradient.Stop(color: .clear, location: 0.9)
                                    ]),
                                    startPoint: layoutDirection == .rightToLeft ? .trailing : .leading,
                                    endPoint: layoutDirection == .rightToLeft ? .leading : .trailing
                                )
                                .frame(width: size.width, height: size.height)

                                Rectangle()
                                    .foregroundColor(.clear)
                                    .frame(width: size.width)
                            }
                        }.frame(height: size.height)
                    }
                )
        } else {
            content
                .fixedSize(horizontal: false, vertical: true)
        }
    }
}

extension View {
    func applyingTruncationMask(size: CGSize, enabled: Bool) -> some View {
        modifier(TruncationTextMask(size: size, enabled: enabled))
    }
}
```

Note that we use the `@Environment(\.layoutDirection)` property wrapper to determine the layout direction, and flip the gradient start and end points if the layout direction is right-to-left.

### Accessibility
Because we used standard SwiftUI elements, the expandable text supports color scheme variants out of the box:
{{< img src="color_scheme_variant.png" caption="Color scheme variant" w="700" >}}

And also dynamic type variants:
{{< img src="dynamic_type_variant.png" caption="Full dynamic type support" w="700" >}}

Note that the `more` button is not visible in the `X Small` dynamic type variant, because the text fits within the line limit.

## Conclusion
In this post, we've seen how to create an expandable text view in SwiftUI. We've also seen how to use the `background` and `overlay` modifiers to calculate the size of a view at runtime, and how to use a `LinearGradient` mask to fade out the text when it's truncated.

The full source code for this post is available on [GitHub](https://github.com/n3d1117/ExpandableText) as a Swift package!

## References
- [How to read a view size in SwiftUI](https://www.fivestars.blog/articles/swiftui-share-layout-information/) on fivestars.blog
- [How to check if Text is truncated in SwiftUI?](https://www.fivestars.blog/articles/trucated-text/) on fivestars.blog
- [NuPlay/ExpandableText](https://github.com/NuPlay/ExpandableText) for inspiration and some portions of code

