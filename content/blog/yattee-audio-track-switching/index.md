---
title: "Contributing audio track switching and default audio track selection to Yattee"
description: "How I added MPV audio track switching in Yattee and improved default audio track selection."
date: 2025-06-24T10:00:00.000Z
slug: yattee-audio-track-switching
tags: [ios, swift, swiftui, yattee, mpv, open-source]
toc: true
math: false
comments: true
---

{{< note variant="info" >}}
This post covers my contribution to [yattee/yattee](https://github.com/yattee/yattee) in [PR #874](https://github.com/yattee/yattee/pull/874): MPV audio track switching + default language improvements.
{{< /note >}}

## Introduction

[Yattee](https://github.com/yattee/yattee) is a polished, privacy-oriented video player for iOS, tvOS, and macOS.

I wanted to solve a practical playback issue: on YouTube adaptive streams, a video can expose multiple audio tracks (different languages, dubbed tracks, original audio), but switching between them in Yattee was not even possible in the player UI.

On top of that, default selection could prefer dubbed audio in some cases, which made foreign-language videos frustrating to watch.
This is a common YouTube annoyance too: if you watch, for example, Italian videos while abroad, the audio can often be the wrong language.

## The problem

In the streams I tested, audio metadata was encoded in URL query parameters (`xtags`), including track content type and language.
For example, the URL could include `acont=dubbed-auto:lang=en-US` for a dubbed track or `acont=original:lang=it` for the original Italian audio.

Before this change, that metadata was not used at all.

So the player needed:

1. A normalized audio track model
2. Track extraction from stream metadata
3. A way to switch tracks without losing playback position
4. A picker to choose tracks during playback

## Parsing and modeling audio tracks

In `InvidiousAPI`, I added parsing of `xtags` key-value pairs:

Yattee receives these stream URLs through [Invidious](https://github.com/iv-org/invidious), an open-source alternative front-end for YouTube that exposes video metadata and stream URLs through its own API.
So this parsing happens on Invidious-provided metadata, not by calling YouTube directly.

```swift
func extractXTags(from urlString: String) -> [String: String] {
    guard let urlComponents = URLComponents(string: urlString),
          let queryItems = urlComponents.queryItems,
          let xtagsValue = queryItems.first(where: { $0.name == "xtags" })?.value else {
        return [:]
    }
    guard let decoded = xtagsValue.removingPercentEncoding else { return [:] }
    
    // format: key1=value1:key2=value2
    return decoded
        .split(separator: ":")
        .reduce(into: [String: String]()) { result, pair in
            let parts = pair.split(separator: "=", maxSplits: 1).map(String.init)
            guard parts.count == 2 else { return }
            result[parts[0]] = parts[1]
        }
}
```

Then I introduced `Stream.AudioTrack` with:

- `url`
- `content` (for example dubbed/original)
- `language`

Plus helper fields:

- `displayLanguage`
- `description`
- `isDubbed`

That allowed sorting so original audio is preferred over dubbed tracks by default.

## Switching tracks in MPV

Yattee uses [MPV](https://mpv.io), an open-source media player engine, as one of its playback backends.

The implementation keeps track of the audio options available for the current stream and the currently selected one.

On the UI side, I added an audio track picker in the player controls so the available tracks show up as a normal selection menu during playback.

When the user picks a different track, the backend reloads playback with that track while preserving the current timestamp, so switching language does not restart the video.

I also reset audio-track state when changing video, so stale selection does not leak between different videos.

At the time of this PR, one limitation remained: when Invidious Companion was enabled, different audio tracks could resolve to the same `itag` URL, so switching tracks did not always change the final language.

## Result

{{< img src="result-ios.png" caption="iOS: audio track selector in player controls" w="320" >}}

{{< img src="result-macos.png" caption="macOS: playback settings showing selectable audio tracks" w="900" >}}

{{< img src="result-tvos.png" caption="tvOS: audio track selection integrated into the playback UI" w="900" >}}

## Conclusion

This was a small feature on paper, but it fixed a real annoyance when watching videos with multiple language tracks.

Since [PR #874](https://github.com/yattee/yattee/pull/874) (merged on June 17, 2025), this area was improved further.
As of February 25, 2026, the feature has not been reverted and the core logic is still in `main`, including `xtags` parsing and dubbed-vs-original prioritization.

- [Improve MPV backend audio track handling](https://github.com/yattee/yattee/commit/86e843305f4a753ec06359c8b638280c1da5ea59) added safer handling for multiple and single-track streams.
- [Fix array index out of bounds crash in audio track handling](https://github.com/yattee/yattee/commit/4b577a296b215baa4fadd1de7ebdbcd492887995) hardened backend and UI state access.
- [Fix audio track label showing "Original" instead of "Unknown"](https://github.com/yattee/yattee/commit/49278e13cde747ad673eaf5d7bdc874f245853df) improved track labeling.
- [Fix Invidious companion API endpoint path](https://github.com/yattee/yattee/commit/874b976da9a9f6c73b3940045eb49262a313fb17) corrected companion URL routing used for audio and video stream URLs.

## References

- [Yattee repository](https://github.com/yattee/yattee)
- [PR #874: MPV audio track switching and fix default audio language](https://github.com/yattee/yattee/pull/874)
- [Issue #852: wrong default audio language](https://github.com/yattee/yattee/issues/852)
- [MPV](https://mpv.io)
- [Invidious](https://github.com/iv-org/invidious)
- [Invidious Companion](https://github.com/iv-org/invidious-companion)
