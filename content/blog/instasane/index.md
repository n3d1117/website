---
title: "InstaSane: forcing Instagram's home feed back to chronological"
description: "A short write-up of InstaSane, a tweak that drops Instagram's algorithmic For You and keeps the home feed on chronological Following."
date: 2026-05-07T10:00:00+02:00
slug: instasane
tags: [ios, instagram, tweak, logos, theos, reverse-engineering]
toc: true
math: false
comments: true
---

{{< note variant="info" >}}
This is a short write-up of [InstaSane](https://github.com/n3d1117/InstaSane), a tweak I built to drop Instagram's `For you` feed and keep the home timeline on chronological `Following`.
{{< /note >}}

## Introduction

A while ago I [wrote a similar tweak for X/Twitter](/blog/2024/07/xnotforme/), because I just wanted the chronological `Following` timeline. Instagram does the same thing: the home feed defaults to `For you`, and even after switching to `Following`, the next cold start drops you back into the algorithm.

`For you` on Instagram is full of suggested posts, ads, random reels and stuff from people I do not follow. I do not want any of it. I just want to see the people I chose to follow, in order.

So I built [InstaSane](https://github.com/n3d1117/InstaSane), a tiny tweak that keeps the home feed on `Following`, in chronological order, cold starts included.

{{< img src="screenshot.png" caption="Instagram home feed forced to chronological `Following`" w="300" >}}

## Reverse-engineering Instagram

I asked Codex to inspect the decrypted Instagram binary directly (`v428.1.0` at the time of writing) and started from there.

The investigation took several sessions across a few evenings, with a lot of wrong turns and broken hooks along the way.

### Initial recon

The first session was mostly broad string searches against the decrypted binary, looking for anything that sounded feed-related:

```bash {linenos=false}
strings -a path/to/Instagram.app/Instagram \
  | rg -i "feed|following|for you|picker|pagination|chronological"
```

That surfaced, among many other things:

- `IGHomeMainFeedViewController`
- `IGHomeFeedPickerMenuController`
- `IGHomeFeedHeaderView`
- `IGMainFeedViewModel`
- `IGMainFeedNetworkSource`
- `IGDSAGatingManager`
- `feedStickyContentLaneSelection`
- `paginationSource`

Then to map out the Objective-C surface of those classes (selectors, ivar layouts, type encodings), Codex pulled the runtime metadata directly:

```bash {linenos=false}
otool -oV path/to/Instagram.app/Instagram \
  | rg -A 20 "IGHomeFeedPickerMenuController|IGMainFeedViewModel"
```

A few years ago I would have done this in Hopper or with `class-dump`, manually scrolling for an hour. Codex chained `strings`, `rg`, `otool`, and selective `lldb` disassembly, paged through the output, and came back with a ranked list of likely entry points.

### Picker menu

I started from the picker menu. Tap the home title, get a menu, choose `Following`. That has to be a delegate somewhere.

Codex found it pretty quickly:

```bash {linenos=false}
otool -oV path/to/Instagram.app/Instagram \
  | rg "IGHomeFeedPickerMenuController" -A 30
```

One thing I did not expect was the menu item enum. Visually the picker shows `For you` first and `Following` second, so I had assumed `For you = 0`, `Following = 1`. Turns out the actual values, recovered from a mix of metadata and disassembly, are:

```objc
static NSInteger const IGHomeFeedPickerMenuItemForYou = 0;
static NSInteger const IGHomeFeedPickerMenuItemFollowing = 5;
```

There are a few other internal feed types between them. So if you hook the picker against the visible index you end up selecting a completely unrelated feed.

So the first version of the tweak was: hook the picker, force `Following` to be selected.

To verify it actually fired, I had Codex add a distinctive emoji marker to all log lines and watched the device log live:

```bash {linenos=false}
idevicesyslog | rg --line-buffered "🧭"
```

I find this trick really useful for reversing tweaks. App logs are extremely noisy, generic prefixes get lost in the noise, and a one-character marker is trivial to grep for. Every time I tapped something in Instagram, my marker showed up or it did not, and that immediately told me whether a hook had run.

The tweak fired. The `Following` row was selected. And then Instagram served me `For you` content anyway.

### Network source

The picker only controls a UI state. The thing that actually decides what is in your feed is the network source, several layers below.

Codex zoomed in on `IGMainFeedViewModel` and `IGMainFeedNetworkSource`. The init signatures alone gave most of the answer away - they take an `initialPaginationSource` (an `NSString` like `"following"`), and the VM also has an `isInFollowingTab` flag.

So the next attempt was to force both at construction time:

```objc
%hook IGMainFeedViewModel
- (id)initWithDeps:(id)deps posts:(id)posts /* ...many args... */
        initialPaginationSource:(NSString *)paginationSource
        /* ... */
        isInFollowingTab:(BOOL)isInFollowingTab
        /* ... */ {
    paginationSource = @"following";
    isInFollowingTab = YES;
    return %orig;
}
%end
```

Aaaand that worked! The feed was now actually chronological.

However, it also broke the UI: the story tray avatars at the top got noticeably smaller. As it turns out, internally there is a "secondary feed" path, used for the Following sub-feed when it is not the primary surface, and it has its own tighter layout. By forcing `isInFollowingTab` at the VM level on the main home surface, I was opting into that secondary layout.

I asked Codex to correlate the regression with what we had just changed and propose the minimum fix to restore the original sizing:

```objc
%hook _TtC19IGStoryTrayUIModels24IGStoryTrayCellViewModel
- (double)avatarSizeAdjustment {
    return 28.5;
}
%end
```

A bit hacky, but it gets the story tray avatars back to the size you expect on the main feed.

### Cold starts

The other annoying behavior was cold starts. Even after all the above, killing the app and reopening it would land on `For you` again, then snap to `Following` once the network source kicked in.

Codex traced this to a different class: `IGMainFeedRequestConfigFactory`. The relevant method is:

```objc
- (id)generateHeadLoadRequestConfigWithReason:(NSInteger)reason
                                  /* ...many args... */
                              paginationSource:(id)paginationSource
                                  /* ... */;
```

`reason` is an enum describing why the feed is loading (cold start, refresh, scroll, deep link, etc.). After staring at a fair amount of disassembled control flow, Codex narrowed it down: when `paginationSource == "following"`, only certain reasons keep the request truly chronological. `reason = 3` is the one Instagram uses for pull-to-refresh, which is also the one that reliably gives back a chronological page.

So the fix was a one-liner:

```objc
%hook _TtC24IGMainFeedDataFetcherKit30IGMainFeedRequestConfigFactory
- (id)generateHeadLoadRequestConfigWithReason:(NSInteger)reason
        /* ...many args... */
        paginationSource:(id)paginationSource
        /* ... */ {
    if ([paginationSource isEqual:@"following"])
        reason = 3;
    return %orig;
}
%end
```

After that, cold starts came up chronological without flashing `For you` first.

## The final hooks

After all the back-and-forth, the actual tweak is small. The full source is in [n3d1117/InstaSane](https://github.com/n3d1117/InstaSane), but the shape is:

- `IGHomeFeedPickerMenuController` - reorder menu items so `Following` is at index 0; ignore taps on `Following` so the picker does not try to "switch" to a tab we are already on.
- `_TtC14IGHomeMainFeed28IGHomeMainFeedViewController` - on `viewWillAppear:`, set the `currentFeedMenuItem` ivar to the `Following` enum value.
- `IGHomeFeedHeaderView` - rewrite `For you` to `Following` whenever the title is set.
- `_TtC11IGDSAShared18IGDSAGatingManager` - return `1` from `feedStickyContentLaneSelection`. This is the persisted "preferred lane" that Instagram's DSA gating manager (the EU Digital Services Act compliance I guess?) reads to decide which feed to show. It defaults to `0` (For You), which is what causes the UI to keep snapping back. Forcing `1` (Following) makes it stick.
- `IGMainFeedNetworkSource` - force `paginationSource` to `"following"` at init and on every update.
- `_TtC24IGMainFeedDataFetcherKit30IGMainFeedRequestConfigFactory` - the `reason = 3` patch above.
- `_TtC19IGStoryTrayUIModels24IGStoryTrayCellViewModel` - the story tray sizing fix.

That is essentially it. Each one of those was a small Codex-driven detour, and the combined patch is under 80 lines of `Tweak.xm`.

{{< note variant="info" >}}
**Note**: the InstaSane patches have also been [merged into RyukGram](https://github.com/faroukbmiled/RyukGram/pull/19) and will ship as part of `v1.2.3` 🥳. So if you are already using RyukGram, you can get the same `Following`-only behavior from there directly.
{{< /note >}}

## Limits

Same disclaimers as XNotForMe: this is a quick tweak tied to a specific Instagram version (`v428.1.0` at the time of writing). Class names and selectors will drift, especially the Swift-mangled ones, and a future update can break any of this without warning.

{{< note variant="warning" >}}
**Disclaimer**

Instagram and related names/logos are trademarks of their respective owners. This project is independent and for educational/personal-use purposes only.
I am not responsible for misuse, account restrictions, data loss, device issues, or any other damage that may result from using this tweak.
{{< /note >}}

## Conclusion

Same conclusion as in [the FotMob post](/blog/2026/04/bracket-view-fotmob/): for this kind of binary reverse-engineering work, modern agents are *really* good. Codex chained commands together, kept iterating against device logs, and got to a working tweak much faster than I would have on my own.

The end result is an Instagram that finally does what I want: show me the people I follow, in order, and stop pushing attention traps.

To install this tweak, you need to either build it yourself or download the `.deb` from GitHub releases, and then inject it via your usual jailbreak or sideload workflow using a decrypted `.ipa` file.

## References

- [InstaSane repository](https://github.com/n3d1117/InstaSane)
- [XNotForMe](/blog/2024/07/xnotforme/) - the same idea, applied to X/Twitter
- [BracketView write-up](/blog/2026/04/bracket-view-fotmob/) - more on the Codex-assisted RE workflow
