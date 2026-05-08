---
title: "XNotForMe: removing the 'For You' tab from X on iOS"
description: "A practical breakdown of the tiny tweak I wrote to hide X/Twitter's For You timeline and force the Following timeline."
date: 2024-07-15T10:00:00.000Z
slug: xnotforme
tags: [ios, twitter, tweak, logos, theos]
toc: true
math: false
comments: true
---

{{< note variant="info" >}}
This is a short write-up of [XNotForMe](https://github.com/n3d1117/XNotForMe), a quick tweak I built to hide the `For You` tab in X/Twitter.
{{< /note >}}

{{< note variant="info" >}}
**Update (May 2026)**: I rewrote the tweak for X `v11.88`. The original sections below still cover the `v10.3.2` version and the high-level idea; the new screenshot and pointers to the updated hooks are in [Update: May 2026](#update-may-2026-x-v1188).
{{< /note >}}

## Introduction

After [Twitter effectively banned third-party clients through API policy changes](https://www.theverge.com/2023/1/19/23562947/twitter-third-party-client-tweetbot-twitterific-ban-rules), I tried to keep using the official app.  
The main blocker for me was the forced `For You` feed. I only wanted the chronological `Following` timeline.

`For You` felt like a machine for endless scrolling: ads, unrelated topics, rage bait, and random noise designed to keep me in the app longer.

So I built a tiny tweak that does one thing: remove the `For You` tab.

{{< img src="xnotforme-following-only.png" caption="X timeline with only the `Following` tab visible" w="300" >}}

## Code

After some late-night tinkering, this is the quick-and-dirty tweak I ended up with:

```objc
#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>

@interface TFNScrollingSegmentedViewController : UIViewController
- (id)parentViewController;
@end

%hook TFNScrollingSegmentedViewController

-(NSInteger)pagingViewController:(id)arg1 numberOfPagesInSection:(id)arg2 {
    if([[self.parentViewController class] isEqual:NSClassFromString(@"THFHomeTimelineContainerViewController")]) {
        return 1;
    }
    return %orig;
}

-(NSInteger)selectedIndex {
    if([[self.parentViewController class] isEqual:NSClassFromString(@"THFHomeTimelineContainerViewController")]) {
        return 1;
    }
    return %orig;
}

-(NSInteger)initialSelectedIndex {
    if([[self.parentViewController class] isEqual:NSClassFromString(@"THFHomeTimelineContainerViewController")]) {
        return 1;
    }
    return %orig;
}

-(id)pagingViewController:(id)arg1 viewControllerAtIndexPath:(id)arg2 {
    if([[self.parentViewController class] isEqual:NSClassFromString(@"THFHomeTimelineContainerViewController")]) {
        return %orig(arg1, [NSIndexPath indexPathForRow:1 inSection:0]);
    }
    return %orig;
}

%end

@interface TFNScrollingHorizontalLabelView
- (id)delegate;
@end

%hook TFNScrollingHorizontalLabelView
- (void)layoutSubviews {
    if([[self.delegate class] isEqual:NSClassFromString(@"TFNScrollingSegmentedViewController")]) {
        TFNScrollingSegmentedViewController *segmentedController = (TFNScrollingSegmentedViewController *)self.delegate;
        if ([[segmentedController.parentViewController class] isEqual:NSClassFromString(@"THFHomeTimelineContainerViewController")]) {
            return;
        }
    }
    %orig;
}
%end
```

## Hooks

The tweak hooks two internal classes:

- `TFNScrollingSegmentedViewController`
- `TFNScrollingHorizontalLabelView`

### 1) Force one page and one selected index

In `TFNScrollingSegmentedViewController`, I override:

- `pagingViewController:numberOfPagesInSection:` -> return `1`
- `selectedIndex` -> return `1`
- `initialSelectedIndex` -> return `1`
- `pagingViewController:viewControllerAtIndexPath:` -> redirect to row `1`

The `viewControllerAtIndexPath` override is important. Even if the UI says there is one page, you still need to map that page to the right underlying controller.
In this setup, `Following` sits at row `1` in the app's internal pager, so the hook always redirects there.

### 2) Hide segmented labels

I also hook `layoutSubviews` in `TFNScrollingHorizontalLabelView`.

When the delegate is the home timeline segmented controller, I return early and skip layout:

```objc
- (void)layoutSubviews {
    if ([[self.delegate class] isEqual:NSClassFromString(@"TFNScrollingSegmentedViewController")]) {
        TFNScrollingSegmentedViewController *segmentedController = (TFNScrollingSegmentedViewController *)self.delegate;
        if ([[segmentedController.parentViewController class] isEqual:NSClassFromString(@"THFHomeTimelineContainerViewController")]) {
            return;
        }
    }
    %orig;
}
```

This prevents leftover tab labels from rendering.

## Installation

I usually run this with X `v10.3.2` and [BHTwitter](https://github.com/BandarHL/BHTwitter) `v4.0`, which strips ads and other annoyances on top of removing `For You`.

Install it by building the tweak from the [XNotForMe repository](https://github.com/n3d1117/XNotForMe) and injecting/signing it with your usual jailbreak or sideload workflow.

## Limits

This is a quick-and-dirty tweak tied to X app internals, so version changes can break it. It is not an App Store solution, and it does not try to cover every timeline surface. I tested it against X `v10.3.2` (as noted in the repo), and newer versions may need updated class names.

{{< note variant="warning" >}}
**Disclaimer**  

X, Twitter, and related names/logos are trademarks of their respective owners. This project is independent and for educational/personal-use purposes only.

I am not responsible for misuse, account restrictions, data loss, device issues, or any other damage that may result from using this tweak.
{{< /note >}}

## Update: May 2026 (X v11.88)

Two years on, X is still pushing `For You` and the original tweak no longer works on the current build. I rewrote it against `v11.88` and used the rewrite to fix two things that bothered me on the old version:

- the empty strip under the X logo where the tab labels used to live
- the timeline snapping back to the top on every cold start

{{< img src="xnotforme-v2.png" caption="X timeline on `v11.88`: `Following` only, no top tab strip, scroll position preserved across launches" w="300" >}}

The full source is in the same [n3d1117/XNotForMe repository](https://github.com/n3d1117/XNotForMe). Internals shifted enough that the hooks themselves changed, so I won't walk through them line by line - the [updated `Tweak.xm`](https://github.com/n3d1117/XNotForMe/blob/main/Tweak.xm) on `main` has the current set.

I also pushed an [`extras` branch](https://github.com/n3d1117/XNotForMe/tree/extras) with a few optional features layered on top: hiding promoted tweets and the "Who to follow" module, dropping the "new posts" pill, trimming the bottom tab bar down to Home and Search, killing Premium upsells, plus smaller toggles for sensitive-content warnings, GIF autoplay, Articles, search history, and reel-style video paging. Each lives in its own `%group` so it can be enabled independently.

## Conclusion

Modern social feeds are sadly engineered to be addictive and compulsive. If you do nothing, they pick what you see and how long you stay.

XNotForMe is my way of taking that control back: show me people I chose to follow, in order, and stop pushing attention traps.

## References

- [Twitter officially bans third-party clients with new developer rules (The Verge)](https://www.theverge.com/2023/1/19/23562947/twitter-third-party-client-tweetbot-twitterific-ban-rules)
- [XNotForMe repository](https://github.com/n3d1117/XNotForMe)
- [BHTwitter](https://github.com/BandarHL/BHTwitter)
- [InstaSane](/blog/2026/05/instasane/) - the same idea, applied to Instagram
