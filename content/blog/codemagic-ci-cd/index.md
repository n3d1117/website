---
title: Building, testing and releasing native iOS apps using Codemagic
description: My experience using the Codemagic platform to set up continuous integration, testing and automated deployments for a native iOS app written in Swift.
date: 2022-11-07T05:24:54.000Z
slug: codemagic-ci-cd
tags: [ios, swift, ci, codemagic]
toc: true
math: false
comments: true
---

{{< note variant="info" >}}
In this blog post, I will share my experience using Codemagic to set up continuous integration, testing, and automated deployments for a native iOS app written in Swift.
{{< /note >}}

## Introduction
As a developer, I am always looking for ways to streamline my workflow and make my development process more efficient. One of the tools that I have found to be useful in this regard is the [Codemagic](https://codemagic.io/builds) platform. Having used [GitHub Actions](https://github.com/features/actions) in the past for my CI/CD needs, I was curious about how Codemagic compares (note: I have yet to try [Xcode Cloud](https://developer.apple.com/xcode-cloud/)), so I gave it a try.

Codemagic is designed with a user-friendly interface that makes it easy to navigate and set up your CI/CD pipeline. It supports a wide range of mobile platforms, including iOS, Android, React Native, Cordova, Ionic and Flutter. There is also a comprehensive [documentation](https://docs.codemagic.io) that guides you through the process of setting up your pipeline step by step.

## Pricing
Codemagic offers various [pricing plans](https://codemagic.io/pricing/) but I went with their (pretty generous) _free_ tier, which includes:

- 500 build minutes / month
- macOS M1 VM (Apple M1 chip / Mac mini 3.2GHz Quad Core / 8GB)
- max 120 minutes build timeout (maximum duration of a single build)

Which seems like a great starter plan for personal or hobby projects.

## Setup
After [signing up](https://codemagic.io/signup), it's time to setup your first application:
1. Head over to the [apps](https://codemagic.io/apps) page and click on "Add application"
2. Select your Git provider (I use GitHub) and your repository. Note that adding repos from GitHub requires authorizing Codemagic and installing the Codemagic CI/CD GitHub App to a GitHub account.[^1]

{{< columns >}}

{{< column p="left" >}}
{{< img src="connect_repository.png" caption="Codemagic: Selecting a Git provider" w="500" >}}
{{< /column >}}

{{< column p="right" >}}
{{< img src="setup_application.png" caption="Codemagic: Setting up the application" w="500" >}}
{{< /column >}}

{{< /columns >}}

3. Specify the project type (*iOS App* in my case) and click "Finish: Add application".

## Configuration
In order to configure your CI/CD with Codemagic, you need to add a file named `codemagic.yaml` to  the root directory of the repository and commit it to version control.
You can find [extensive documentation](https://docs.codemagic.io/yaml-basic-configuration/yaml-getting-started/) for the YAML syntax and various usages of the configuration file.

When detected in the repository, `codemagic.yaml` is automatically used for configuring builds triggered in response to the events defined in the file. Builds can also be started manually by clicking **Start new build** in Codemagic and selecting the branch and workflow to build in the **Specify build** configuration popup.[^2]

### The Codemagic YAML file
Here's the `codemagic.yaml` I ended up using for my native iOS app (you can also find it on [my GitHub repository](https://github.com/n3d1117/stats-ios/blob/main/codemagic.yaml)):

```yaml
workflows:
  build:
    name: iOS Build & Test
    max_build_duration: 15 # in minutes
    instance_type: mac_mini_m1
    triggering:
      events:
        - push
        - pull_request
    scripts:
      - name: Build
        script: |
          xcodebuild build \
            -project "Stats.xcodeproj" \
            -scheme "Stats" \
            CODE_SIGN_IDENTITY="" \
            CODE_SIGNING_REQUIRED=NO \
            CODE_SIGNING_ALLOWED=NO
      - name: Extract .ipa (unsigned)
        script: |
          mkdir Payload
          cp -r $HOME/Library/Developer/Xcode/DerivedData/**/Build/Products/Debug-iphoneos/*.app Payload
          zip -r build.ipa Payload
          rm -rf Payload
    artifacts:
    - build.ipa
```

This YAML file is setting up a workflow for a continuous integration and continuous deployment (CI/CD) pipeline for an iOS app written in Swift. The pipeline is triggered by events such as a push to the repository or a pull request, and it runs on a `mac_mini_m1` instance type.

- The workflow has a single job called "iOS Build & Test" that is set to run for a maximum of 15 minutes. The job consists of two scripts:
    * The **Build** script is running the `xcodebuild` command to build the project named "Stats.xcodeproj" with the scheme "Stats". Some flags are passed to avoid code signing, which I didn't need
    * The **Extract .ipa (unsigned)** script creates a `Payload` directory, copies the app files from the build folder to the `Payload` directory, creates an `.ipa` file from the `Payload` directory, and then deletes the `Payload` directory
- Finally, the job defines an *artifact*, which is a file that can be generated by the pipeline and will show up later in the [builds](https://codemagic.io/builds) section. In this case, it's the `build.ipa` extracted earlier.

### Builds
Your app's builds will show up in the [builds](https://codemagic.io/builds) page, along with their status and eventual artifacts that can be downloaded.
Logs can be viewed for each build to investigate issues.

My builds averaged 2 minutes of compute time (note that I skipped the whole iOS signing setup though), which is very fast for a free tier, thanks to the M1 machines.

{{< columns >}}

{{< column p="left" >}}
{{< img src="builds.png" caption="Codemagic: Builds page" w="500" >}}
{{< /column >}}

{{< column p="right" >}}
{{< img src="build_logs.png" caption="Codemagic: Viewing a build's logs" w="500" >}}
{{< /column >}}

{{< /columns >}}

### Automated GitHub releases on Git tag push
The `codemagic.yaml` configuration is very powerful and has lots of integrations. A great use case is deploying an app to Github releases for successful builds triggered on tag creation.

To setup deployments to GitHub releases you need:
- Your app needs to be hosted on GitHub
- Use git tags (this won't work with commits)
- Add your GitHub [personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) to Codemagic's environment variables (see [documentation](https://docs.codemagic.io/yaml-publishing/github-releases/#configuring-codemagic))[^3]

    1. Open your Codemagic app settings, and go to the Environment variables tab.
    2. Enter the desired variable name, e.g. `GITHUB_TOKEN` and enter the token value as **Variable value**
    3. Create a new Group and give it any name (i.e. `GitHub`). Make sure the **Secure** option is selected and add the variable:

{{< img src="env_var.png" caption="Codemagic: Adding an environment variable" w="600" >}}

- Include the **group name** in your `codemagic.yaml` and configure build triggering on tag creation. Don’t forget to add a branch pattern and ensure the webhook exists:
```yaml
workflows:
  build:
    environment:
      groups:
        - GitHub
    triggering:
      events:
        - tag
      branch_patterns:
        - pattern: "*"
          include: true
          source: true
```

- Add the following script after the build or publishing scripts (edit the build artifacts path to match your setup):

```yaml
- name: Publish to GitHub Releases w/ artifact
  script: |
    #!/usr/bin/env zsh

    # Publish only for tag builds
    if [ -z ${CM_TAG} ]; then
      echo "Not a tag build, will not publish GitHub release"
      exit 0
    fi

    gh release create "${CM_TAG}" \
      --title "<Your Application Name> ${CM_TAG}" \
      build.ipa
```

You can find more options about `gh release create` usage, such as including release notes, from the [GitHub CLI official docs](https://cli.github.com/manual/gh_release_create).

Upon a tag push and successful build, here's how the release looks like on the GitHub website:

{{< img src="release.png" caption="Codemagic: Automated GitHub release with artifact" w="600" >}}

## Testing
Sadly, adding automated testing to my Codemagic configuration did not go as planned.

As per [documentation](https://docs.codemagic.io/yaml-testing/testing/), I added the following script to the `scripts` configuration section, before the build commands:
```yaml
- name: Automated tests
  script: |
    #!/bin/sh
    set -ex
    xcode-project run-tests \
      --project "Stats.xcodeproj" \
      --scheme "Stats" \
      --device "iPhone 11" \
      --test-xcargs "CODE_SIGNING_ALLOWED=NO"
  test_report: build/ios/test/*.xml
```

However, despite my relatively simple test suite (13 unit tests), I noticed some mixed results on my builds:
- Sometimes, tests passed but took way too long (over 8 minutes, whereas the build step usually takes less than a minute and a half)
- In other instances, tests **timed out** after taking longer than 15 minutes

{{< columns >}}

{{< column p="left" >}}
{{< img src="xcode_tests.png" caption="Test suite for the [Stats](https://github.com/n3d1117/stats-ios) app I'm using" w="500" >}}
{{< /column >}}

{{< column p="right" >}}
{{< img src="tests_pass.png" caption="Codemagic: Automated tests passing" w="500" >}}
{{< img src="tests_fail.png" caption="Codemagic: Automated tests sometimes timing out" w="500" >}}
{{< /column >}}

{{< /columns >}}

It could be that the issue for these flaky tests lies in my configuration, I didn't have time to investigate further. I simply commented out the test script for now.

## Conclusion
My experience using the Codemagic platform to set up continuous integration, testing and automated deployments for a native iOS app written in Swift was a **positive** one:

* Many platforms are supported
* Performance is great even for the free tier, especially when compared to GitHub actions
* Build machines and tools such as Xcode are [regularly updated](https://docs.codemagic.io/specs/versions-macos/)
* My use case was very limited, but Codemagic offers a ton of integrations for common actions (iOS code signing, build notifications, Fastlane, Jira, artifact publishing, REST APIs and much more)
* Good community support on their [Discussions](https://github.com/codemagic-ci-cd/codemagic-docs/discussions) page

Altough I could not make my tests run reliably, I still recommend giving Codemagic a try. 🥳

[^1]: Codemagic docs: [Adding apps to Codemagic](https://docs.codemagic.io/getting-started/adding-apps/).
[^2]: Codemagic docs: [Using codemagic.yaml](https://docs.codemagic.io/yaml-basic-configuration/yaml-getting-started/).
[^3]: Codemagic docs: [Github Releases with codemagic.yaml](https://docs.codemagic.io/yaml-publishing/github-releases/).
