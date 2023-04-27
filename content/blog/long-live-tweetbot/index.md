---
title: Long live Tweetbot
description: How to continue using the Tweetbot iOS app after it has been suspended by replacing its Twitter API key with your own, using a man-in-the-middle proxy to redirect authentication requests.
date: 2023-01-19T05:24:54.000Z
slug: long-live-tweetbot
tags: [ios, tweetbot, twitter, mitm, proxy]
toc: true
math: false
comments: true
---

{{< note variant="warning" >}}
**EDIT as of Feb 28th, 2023:** Tapbots released a final update to Tweetbot (`v7.2.2`) which removes the entire app functionality, and encourages users to transfer their Tweetbot subscription into [Ivory](https://tapbots.com/ivory/). This article however is still relevant if you keep using `v7.2.1` of the app. If you updated by accident, you can downgrade using [this guide](https://github.com/qnblackcat/How-to-Downgrade-apps-on-AppStore-with-iTunes-and-Charles-Proxy/).
{{< /note >}}

This post describes how to continue using the [Tweetbot](https://tapbots.com/tweetbot/) iOS app after [it was suspended](https://mashable.com/article/twitter-elon-musk-third-party-client-api-tweetbot-twitterrific/) by replacing its Twitter API key with your own, using a man-in-the-middle proxy to reroute authentication requests.

## Introduction

I've been a [Tweetbot](https://tapbots.com/tweetbot/) user for as long as I can remember, and it's by far my favorite iOS app ever. As such, I was **devastated** to learn on January 12th, 2023, Twitter [suspended _all_ third party clients overnight](https://mashable.com/article/twitter-elon-musk-third-party-client-api-tweetbot-twitterrific/) by revoking access to their API keys.

{{< img src="tweetbot_icon.png" caption="Evolution of the iOS Tweetbot icon through the years (2011-2023)" w="400" >}}

From the [Tweetbot memorial](https://tapbots.com/tweetbot/):
> On January 12th, 2023, without warning, Elon Musk ordered his employees at Twitter to suspend access to 3rd party clients which instantly locked out hundreds of thousands of users from accessing Twitter from their favorite clients. We’ve invested over 10 years building Tweetbot for Twitter and it was shut down in a blink of an eye. We are very sorry to all of our customers who chose Tweetbot as their way to interact with Twitter’s service and we thank you so much for the many years of support and feedback.

{{< columns >}}

{{< column p="left" >}}
{{< img src="tweetbot_error_alert.png" caption="Tweetbot error alert after being revoked" w="400" >}}
{{< /column >}}

{{< column p="right" >}}
{{< img src="tweetbot_goodbye.png" caption="Tweetbot goodbye alert" w="350" >}}
{{< /column >}}

{{< /columns >}}

After a decade of using Tweetbot, I couldn't stand using the official Twitter iOS app, for a number of reasons:
- Riddled with ads and trackers
- No UI customization options (such as inline media)
- Does not show my feed in chronological order by default

## A glimpse of hope
Even though I have mostly moved to [Mastodon](https://joinmastodon.org), not everyone has moved yet, so I started looking for solutions. That's when I stumbled upon [this post](https://notnow.dev/notice/ARh4u5BJD8mf2jG5yK) by developer [Zhuowei Zhang](https://zhuoweizhang.net), who suggested a way to use a custom API key to login and added a link to his [GitHub repo](https://github.com/zhuowei/TweetbotLoginProxy) for a proof of concept.

As it turns out, it totally works!

## Reviving Tweetbot
Here's how I got Tweetbot working again on my iOS device.

### 1. Create a new Twitter application
* Head over to Twitter's [developer portal](https://developer.twitter.com) and add a new Application
    * Note: You may need to create a Project first
    * Make sure you copy your app's API Key and Secret somewhere
    * When asked for **Type of app**, select "Native App"
    * Use `tweetbot:///request_token` as the callback URI
    * Once done, you need to enable "Elevated access" for your project

{{< columns >}}

{{< column p="left" >}}
{{< img src="twitter_app_info.png" caption="Twitter app details" w="500" >}}
{{< /column >}}

{{< column p="right" >}}
{{< img src="twitter_elevated_access.png" caption="Grant `Elevated access` to your app's project" w="500" >}}
{{< /column >}}

{{< /columns >}}

### 2. Set up local proxy server and redirection
* Install [mitmproxy](https://mitmproxy.org) (if you're using a Mac, run `brew install mitmproxy`)
* Clone the [zhuowei/TweetbotLoginProxy](https://github.com/zhuowei/TweetbotLoginProxy) GitHub repository
* Edit `run.sh.template` by adding your app's API key and secret, and rename the file to `run.sh`
* Set up a local proxy to redirect Tweetbot's authentication servers to your own local instance:

    ```bash
    // torchlight! {"lineNumbers": false}
    mitmweb --map-remote "@https://push.tapbots.com/@http://localhost:3000/"
    ```
* Run the local server with:

    ```bash
    // torchlight! {"lineNumbers": false}
    npm install && ./run.sh
    ```

### 3. Connect to the proxy
* Make sure your iOS device is connected to the same network as your computer, and take note of your computer's local IP address (on macOS you can find it by alt-clicking the WiFi icon in your menu bar)
* On your iOS device, go to Settings -> Wi-Fi and click the (i) button next to the name of your Wi-Fi network
* Scroll down and click on `Configure Proxy`, check `Manual` and enter your computer's IP address in the `Server` field and `8080` in the `Port` field. Click `Save` to save your changes.

{{< img src="proxy.png" caption="Configuring proxy on iOS" w="400" >}}

* Next, we need to install mitmproxy's **Certificate Authority** to intercept HTTPS requests. From your iOS device, head over to [mitm.it](https://mitm.it) and click on `get mitmproxy-ca-cert.pem` button under the iOS section
* You will be asked if you want to download the configuration profile - press `Allow` button. Now go back to the Settings app. You will see `Profile Downloaded` cell at the top. Pressing it will open the `Install Profile` dialog with Install button at the top - press it and verify the installation with your passcode[^1]
* Go back to the Settings app home page and go `General` -> `About` -> `Certificate Trust Settings`. Make sure the switch next to `mitmproxy` text is on. At this point, your `mitmproxy` instance should be showing HTTP requests that iOS and various apps are making in the background[^1].

{{< columns >}}

{{< column p="left" >}}
{{< img src="mitm_1.png" caption="Installing `mitmproxy`'s profile" w="400" >}}
{{< /column >}}

{{< column p="right" >}}
{{< img src="mitm_2.png" caption="Trusting `mitmproxy`'s profile" w="400" >}}
{{< /column >}}

{{< /columns >}}

### 4. Test it out
Finally, open the Tweetbot app on your iOS device and try to log in.
With some luck, you should be redirected to Twitter's authorization page, showing the App you created earlier:

{{< img src="twitter_auth.png" caption="Twitter showing the authorization page for your own app" w="350" >}}

{{< note variant="success" >}}
That's it! 🎉 Once logged in, you should be able to use Tweetbot normally. You can stop the `mitmproxy` instance and disable proxy configuration on your iOS device.
{{< /note >}}

You should also be able to see `mitmproxy` correctly rerouting your HTTP requests through the local proxy running on port `3000`:

{{< img src="mitmproxy_logs.png" caption="HTTP logs from `mitmproxy`" w="600" >}}

## Disclaimer
This is for educational purposes only. Use at your own risk!

Also consider supporting the developers behind Tweetbot by purchasing a subscription for their upcoming [Ivory](https://tapbots.com/ivory/) app!

## Credits
* [zhuowei/TweetbotLoginProxy](https://github.com/zhuowei/TweetbotLoginProxy) by [Zhuowei Zhang](https://zhuoweizhang.net)

[^1]: [Setting up mitmproxy with iOS 15](https://www.trickster.dev/post/setting-up-mitmproxy-with-ios15/).
