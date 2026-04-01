---
title: "Recreating FotMob's excellent bracket UI in UIKit"
description: "Notes from building a FotMob-inspired tournament bracket view for UIKit and SwiftUI."
date: 2026-04-01T17:00:00+02:00
slug: bracket-view-fotmob
tags: [ios, swift, swiftui, uikit, open-source, reverse-engineering]
toc: true
math: false
comments: true
---

{{< note variant="info" >}}
I recently built [BracketView](https://github.com/n3d1117/BracketView), a clean-room reimplementation of the excellent horizontal bracket UI style used in [FotMob](https://www.fotmob.com).
This post is a first write-up of why and how I built it. The repo also includes a demo app you can run locally.
{{< /note >}}

## Introduction

Building a good horizontal bracket UI on mobile is harder than it looks, mainly given the limited screen width.

[FotMob](https://www.fotmob.com) (one of my favorite and - in my opinion - best designed iOS apps) did an excellent job on this with one of their recent updates. It is compact, readable, and does a good job of making a fairly messy data structure feel obvious. At some point I stopped thinking "this is a nice UI" and started thinking "Wow, I want to recreate this as a reusable component".

So I built [BracketView](https://github.com/n3d1117/BracketView): a bracket component for SwiftUI and UIKit, with a UIKit renderer underneath and a demo app to try it out.

## UI reference

For those not familiar with FotMob's bracket view, here's how it looks vs my final implementation:

{{< columns >}}

{{< column p="left" >}}
{{< video src="fotmob-demo.mp4" width="320" controls="true" preload="metadata" caption="FotMob's bracket UI" class="center" >}}
{{< /column >}}

{{< column p="right" >}}
{{< video src="bracketview-demo.mp4" width="320" controls="true" preload="metadata" caption="Final BracketView demo app" class="center" >}}
{{< /column >}}

{{< /columns >}}

I wanted something that actually behaved well while scrolling, paging, resizing, and updating.

### Alternatives

{{< columns >}}

{{< column p="left" >}}
{{< video src="sofascore.mp4" width="320" controls="true" preload="metadata" caption="SofaScore's horizontal bracket UI" class="center" >}}
{{< /column >}}

{{< column p="right" >}}
{{< video src="apple-sports.mp4" width="320" controls="true" preload="metadata" caption="Apple Sports bracket UI" class="center" >}}
{{< /column >}}

{{< /columns >}}

The first one is [SofaScore](https://www.sofascore.com)'s horizontal bracket implementation.
I am not a fan of it.
To me it does not make good use of the available space, and it only really readjusts the UI when paging snaps.
There is no meaningful interpolation during the swipe, so the whole thing feels more static than it should.

The other one is [Apple Sports](https://apps.apple.com/us/app/apple-sports/id6446788829).
I think it is an interesting implementation.
It lets the user resize the visible window through a fixed top UI control element, and it also does try to keep a focal window while you move through the bracket, though not in one linear motion. The bigger problem is that this component does not feel smooth or performant at all. There are hitches, micro-lags, animations that feel out of sync, and visible layout jumps - some of these you can see in this exact video. My guess, based on how it behaves, is that it is highly likely implemented in SwiftUI.
If that guess is right, it is a pretty good example of the sad state of SwiftUI in 2026 for building performant UIs (and why I chose UIKit for my own implementation).

All in all, I think FotMob's implementation is far superior to both of them.

## Reverse-engineering FotMob

Before I started implementing anything, I wanted to understand whether FotMob was doing something special under the hood or whether this was mostly just a nice-looking paged scroll view. So, I did what _every_ engineer does in 2026, and asked Codex to inspect the decrypted FotMob app binary directly, to see whether they were doing anything custom for the bracket.

Honestly, this part impressed me quite a bit. The agent got to useful answers quickly just by chaining together normal local tools and adjusting when one path did not help.

### Initial findings

It started with broad string searches:

```bash
strings -a path/to/FotMob.app/FotMob \
  | rg -i "bracket|playoff|knockout|round|paging|swipe|drag|snap"
```

That already surfaced a lot:

- `BracketViewController`
- `PlayoffViewController`
- `DrawBracketView`
- `BracketHorizontalView`
- `BracketVerticalView`
- `BracketRoundView`
- `BracketConnectorView`
- `_TtC6FotMob21BracketScrollDelegate`

So even before looking at any disassembly, it was pretty clear that FotMob had a dedicated bracket stack and a dedicated scroll delegate for it.

Then it tried symbol lookup:

```bash
nm -nm path/to/FotMob.app/FotMob 2>/dev/null \
  | xcrun swift-demangle \
  | rg "FotMob\\.(Bracket|Playoff|.*ScrollDelegate)"
```

That came back empty because the symbol table was mostly stripped.

Next it pulled Objective-C metadata out of the binary:

```bash
otool -ov path/to/FotMob.app/FotMob 2>/dev/null \
  | rg "BracketScrollDelegate|scrollViewWillEndDragging|scrollViewDidEndDragging|setAllowedSwipeDistance"
```

That uncovered real selector wiring on `BracketScrollDelegate`, including:

- `scrollViewWillEndDragging:withVelocity:targetContentOffset:`
- `scrollViewDidEndDragging:willDecelerate:`
- `setAllowedSwipeDistance:`

At that point, it was already obvious that this was not just a stock `isPagingEnabled` setup.

The next nice find was the class state itself:

```bash
strings -a -t x path/to/FotMob.app/FotMob \
  | rg "pageWidth|maxPageIndex|changeIndexThreshold|filterIndexThreshold|heightIndexThreshold|adjustScrollViewHeightThreshold"
```

That surfaced ivar names like:

- `pageWidth`
- `maxPageIndex`
- `changeIndexThreshold`
- `filterIndexThreshold`
- `heightIndexThreshold`
- `adjustScrollViewHeightThreshold`
- `lastReportedIndex`

Just from those names, you can already tell they probably split "which page should snap", "which round should count as selected", and "when should layout or height update" into separate decisions.

### Scroll behavior

Then Codex used `lldb` in batch mode to disassemble the scroll delegate methods directly:

```bash
lldb -b \
  -o 'target create path/to/FotMob.app/FotMob' \
  -o 'disassemble -s 0x10020940c -c 120' \
  -o quit
```

First, the metadata had already shown that `scrollViewWillEndDragging:withVelocity:targetContentOffset:` was implemented on `BracketScrollDelegate`.
Then the disassembly showed that this method delegates the actual snap decision to a helper:

```text
FotMob[0x100209514] <+64>:  mov    x1, x19
FotMob[0x100209518] <+68>:  mov    x20, x2
FotMob[0x10020951c] <+72>:  bl     0x10020934c   ; snap helper
```

And later in that helper you can see it converting the current page progress to an integer and conditionally stepping to the next page:

```text
FotMob[0x100209778] <+568>:  fmov   d0, #1.00000000
FotMob[0x10020977c] <+572>:  fcmp   d9, d0
FotMob[0x100209780] <+576>:  cset   w8, ge
FotMob[0x100209784] <+580>:  fcvtzs x24, d10
FotMob[0x100209788] <+584>:  adds   x8, x24, x8
```

Combined with the rest of the delegate disassembly, it led to the most useful conclusion from the whole session, that FotMob's `scrollViewWillEndDragging` does not just trust the predicted target offset and round at the midpoint, there is a velocity gate in there. Above that threshold, the logic snaps by swipe direction from the current page instead.

That lines up with how the real UI feels: a short flick can still advance the bracket, even when the projected resting point would not normally cross the usual halfway mark.

Codex then kept digging and decoded the flick cutoff to `0.2`. The rule it recovered was basically this:

- if `abs(velocity.x) <= 0.2`, use the projected destination and round normally
- if `abs(velocity.x) > 0.2`, ignore the projected midpoint and snap by direction from the current page using `ceil` or `floor`

I ended up replicating exactly that part in my own pager, because it was one of those small interaction details that immediately changed the feel of the component.

The translated version in my code looked like this:

```swift
if abs(velocityX) > 0.2 {
    proposedProgress = velocityX > 0 ? ceil(currentProgress) : floor(currentProgress)
} else {
    proposedProgress = round(targetProgress)
}
```

### What I used

The other useful conclusion was more architectural than visual: raw scroll progress does not seem to drive everything directly.
The names `changeIndexThreshold`, `filterIndexThreshold`, `heightIndexThreshold`, and `adjustScrollViewHeightThreshold` strongly suggest FotMob stages these transitions instead of tying them all to one number.

I did not want to copy that system 1:1, but the idea behind it was useful.
In my own code, that pushed me toward separating the physical page progress from the things that depend on it, like snapped selection, final card expansion, and vertical sync.

More than anything, the whole exercise made me appreciate how good today's agents have become at this kind of work.
A few years ago I would have expected this to be a slow evening of manually poking at a binary.
Instead, Codex used a handful of boring command-line tools, recovered bracket-specific classes and delegate methods, and got to a pretty solid model of the behavior fast enough to actually inform the implementation.

## Implementation

### UIKit renderer

The package supports both SwiftUI and UIKit.
The SwiftUI API looks like this:

```swift
@State private var selectedRoundID = rounds.defaultSelectedRoundID

var body: some View {
    BracketView(
        data: rounds,
        selectedRoundID: $selectedRoundID
    )
}
```

And the UIKit side looks like this:

```swift
let controller = BracketViewController(
    data: rounds,
    selectedRoundID: rounds.defaultSelectedRoundID,
    configuration: BracketViewConfiguration()
)
```

The renderer itself is UIKit, and it is manually laid out (no AutoLayout!). That was a deliberate choice. A bracket like this has a lot going on at once:

- horizontally paged content
- vertically scrollable content
- connectors between cards
- cards that change shape as rounds come in and out of focus
- remote images for team logos
- potentially a lot of cards in early rounds like a round of 64 or round of 128

For bigger brackets, the early rounds can get dense very quickly. That made me want tight control over layout, reuse, and scrolling cost. This approach reduced memory consumption of about 50% compared to having _just_ the match cards in SwiftUI.

So the SwiftUI layer is a wrapper around the UIKit renderer, and the heavy lifting happens there.

### Layout and paging logic

I split the package into two parts:

- `BracketViewCore` for models, layout math, paging math, and visibility rules
- `BracketView` for UIKit views, controllers, image loading, and the SwiftUI wrapper

The layout engine computes where each round header and card should sit, without knowing anything about `UIView`.

This also made it easier to add tests for the tricky parts:

- which source matches connect to which target match
- how page progress maps to rounds
- how focused and compact card sizes differ
- which rounds should stay mounted near the current page

### Multiple layouts per round

The basic problem is this: a round does not have just one "correct" frame.

When a round is focused, cards are spaced out and easy to read.
When it is not focused anymore, it needs to collapse so the next round can visually connect to it.

So the renderer works with a couple of different states:

- a focused layout
- an anchored layout
- a rendered layout that interpolates between them while paging

### Vertical focus while paging

The detail I like most is the vertical anchoring during horizontal paging. 

If you are looking at a match near the middle of the screen and you swipe to the next round, the content should not suddenly jump to some unrelated vertical position.
That feels awful.

Here is a demo of that behavior on a larger bracket:

{{< video src="focus.mp4" width="320" controls="true" preload="metadata" caption="Keeping the focal point stable while paging through a larger bracket" class="center" >}}

While dragging, the component tracks the match nearest the viewport center and tries to keep that same line of the bracket visually anchored as you move across rounds.

This matters a lot more once you get into large rounds like a round of 128 or round of 64.
There are so many cards on screen that if the viewport loses your place during a swipe, the whole thing immediately feels disorienting.

At a high level, this is handled by `BracketVerticalAnchorCoordinator`.
When a drag session starts, it finds the match closest to the viewport center and stores that as the thing to follow.
From there, it keeps an anchor point in viewport coordinates and asks the pager for the related match position in the next rounds.

The important part is that it does not just preserve raw `contentOffset.y`, but it also tracks a specific match line through the bracket and computes the vertical offset needed to keep that line in roughly the same visual place while the horizontal page progress changes.

`BracketViewController+VerticalSync` then applies that desired offset and clamps it safely against the current content height.
That is what keeps the interaction feeling focused instead of jumpy.

### Keeping it cheap

I kept profiling the bracket view to get the lowest memory consumption possible. Some optimizations helped with performance:

- only keep a small window of rounds mounted around the current page (this is also configurable)
- reuse card views instead of constantly creating and destroying them
- reuse connector layers too
- disable implicit Core Animation actions for connector path updates
- downsample remote team logos before caching them

## Conclusion

This was a fun project to build. There were a lot of small details and little interactions to tune, as well as layout math, paging math, visibility management and so on. I'm quite happy with the end result!

If you want to try it, the package and demo app are on GitHub:

- [n3d1117/BracketView](https://github.com/n3d1117/BracketView)

## Disclaimer

BracketView is an independent, unofficial reimplementation inspired by the bracket UI style seen in FotMob.
It is not affiliated with, endorsed by, or sponsored by FotMob or FotMob AS.
“FotMob” is a trademark of its respective owner.
This project does not include FotMob source code, assets, or proprietary data.
