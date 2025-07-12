---
title: "Building a Type-Safe Routing System for SwiftUI"
description: A deep dive into creating a declarative, type-safe routing system for SwiftUI applications, with support for deep linking, state restoration, and universal links.
date: 2025-07-12T10:00:00.000Z
slug: swiftui-routing
tags: [ios, swift, swiftui, navigation, routing]
toc: true
math: false
comments: true
---

{{< note variant="info" >}}
In this post, we'll explore how to build a comprehensive routing system for SwiftUI applications. We'll cover type-safe navigation, modal presentation, deep linking, universal links and state restoration. The full source code is available on [GitHub](https://github.com/n3d1117/Routing)!
{{< /note >}}

## Introduction

SwiftUI's navigation system has come a long way since its introduction. We now have powerful tools like [`NavigationStack`](https://developer.apple.com/documentation/swiftui/navigationstack), [`NavigationPath`](https://developer.apple.com/documentation/swiftui/navigationpath), and the [`.navigationDestination`](https://developer.apple.com/documentation/swiftui/view/navigationdestination(for:destination:)) modifier that provide programmatic navigation capabilities. However, as applications grow in complexity, managing navigation state across multiple screens can become challenging.

I've been working on a routing system that addresses these challenges. It provides a declarative, type-safe approach to navigation that scales from simple push-and-pop scenarios to complex multi-modal flows with deep linking support.

## The Problem with Traditional Navigation

Before diving into the solution, let's examine the typical challenges with SwiftUI navigation. While modern SwiftUI navigation is powerful, it can become difficult to maintain as complexity grows:

```swift
// Traditional approach with NavigationStack and .navigationDestination
struct ContentView: View {
    @State private var showingSettings = false
    @State private var showingProfile = false
    @State private var selectedUser: User?
    @State private var navigationPath = NavigationPath()
    
    var body: some View {
        NavigationStack(path: $navigationPath) {
            HomeView()
                .navigationDestination(for: ProfileDestination.self) { destination in
                    ProfileView(userId: destination.userId)
                }
                .navigationDestination(for: SettingsDestination.self) { _ in
                    SettingsView()
                }
        }
        .sheet(isPresented: $showingSettings) {
            SettingsView()
        }
        .sheet(isPresented: $showingProfile) {
            if let user = selectedUser {
                ProfileView(user: user)
            }
        }
    }
}

// Where do I put this? In the same file? A separate file?
struct ProfileDestination: Hashable {
    let userId: String
}

struct SettingsDestination: Hashable {}
```

The `.navigationDestination` modifier is incredibly powerful, but it raises several questions: Where should these destination types be defined? How do we handle navigation from deeply nested views? What about combining programmatic navigation with deep linking? This approach quickly becomes unwieldy as you add more screens, and it's difficult to handle programmatic navigation, deep linking, or state restoration consistently.

## The Routing Architecture

The routing system I've built consists of four main components:

1. **`Routable`** - A protocol that defines a type that can be resolved into a destination view
2. **`Router`** - A property wrapper that manages navigation state and provides navigation methods
3. **`AppRoute`** - A user-defined enum that conforms to `Routable` and defines all possible destinations
4. **`View.withRouter()`** - A view modifier for injecting the router into the SwiftUI environment

Let's explore each component in detail.

### Defining Routes

The foundation of type-safe routing is the `Routable` protocol:

```swift
public protocol Routable: Hashable, Identifiable {
    associatedtype Destination: View
    @ViewBuilder var destination: Destination { get }
}
```

This protocol ensures that every route can be uniquely identified and resolved to a SwiftUI view. Here's how you define your app's routes:

```swift
enum AppRoute: Routable {
    case home
    case profile(userId: String)
    case settings
    case about
    
    var id: String {
        switch self {
        case .home: return "home"
        case .profile(let userId): return "profile-\(userId)"
        case .settings: return "settings"
        case .about: return "about"
        }
    }
    
    @ViewBuilder
    var destination: some View {
        switch self {
        case .home:
            HomeView()
        case .profile(let userId):
            ProfileView(userId: userId)
        case .settings:
            SettingsView()
        case .about:
            AboutView()
        }
    }
}
```

By using an enum with associated values, we get compile-time safety and can pass data between screens naturally. No more optional bindings or state management headaches!

### The Router Property Wrapper

The `Router` is implemented as a property wrapper that manages navigation state:

```swift
@propertyWrapper
public struct Router<Destination: Routable>: DynamicProperty {
    @State private var core = RouterCore<Destination>()
    
    public var wrappedValue: [Destination] {
        get { core.path }
        nonmutating set { core.path = newValue }
    }
    
    // Navigation methods
    public func navigate(to destination: Destination)
    public func goBack()
    public func popToRoot()
    public func present(_ destination: Destination, style: PresentationStyle = .sheet)
}
```

The router maintains a navigation path (array of destinations) and provides methods for common navigation operations. Internally, it uses SwiftUI's `@Observable` macro for efficient state updates.

### Setting Up the Router

To use the router in your app, you need to create an environment entry:

```swift
extension EnvironmentValues {
    @Entry var router: Router<AppRoute> = Router()
}
```

Then apply the router to your root view:

```swift
struct ContentView: View {
    var body: some View {
        HomeView()
            .withRouter(\.router)
    }
}
```

The `withRouter` modifier injects the router into the SwiftUI environment and sets up the necessary navigation infrastructure.

### Navigation in Action

Once set up, navigation becomes very simple:

```swift
struct HomeView: View {
    @Environment(\.router) private var router
    
    var body: some View {
        VStack(spacing: 20) {
            Button("View Profile") {
                router.navigate(to: .profile(userId: "123"))
            }
            
            Button("Settings") {
                router.present(.settings)
            }
            
            Button("About (Full Screen)") {
                router.present(.about, style: .fullScreenCover)
            }
        }
        .navigationTitle("Home")
    }
}
```

### Demo

Here's a routing demo straight from the [Example app](https://github.com/n3d1117/Routing/tree/main/RoutingDemo):

{{< video src="demo_routing.mp4" width="300" loop="true" muted="true" preload="metadata" caption="The routing system demonstrating navigation, modal presentation, and programmatic navigation" class="center" >}}

## Advanced Features

The routing system goes beyond basic navigation to support advanced features that are essential for production applications.

### Deep Linking Support

One of the most powerful features is built-in deep linking support. To enable deep linking, you first need to register your custom URL scheme in your app's `Info.plist` file (see [Apple's documentation](https://developer.apple.com/documentation/xcode/defining-a-custom-url-scheme-for-your-app) for details):

```xml
<key>CFBundleURLTypes</key>
<array>
    <dict>
        <key>CFBundleURLName</key>
        <string>com.yourapp.deeplink</string>
        <key>CFBundleURLSchemes</key>
        <array>
            <string>myapp</string>
        </array>
    </dict>
</array>
```

Then implement the `DeepLinkHandler` protocol:

```swift
struct MyDeepLinkHandler: DeepLinkHandler {
    func handle(_ url: URL) -> [AppRoute]? {
        guard url.scheme == "myapp" else { return nil }
        
        switch url.host {
        case "profile":
            if let userId = url.pathComponents.last {
                return [.profile(userId: userId)]
            }
        case "settings":
            return [.settings]
        case "about":
            return [.home, .about]
        default:
            break
        }
        
        return nil
    }
}
```

Then enable deep linking in your router configuration:

```swift
struct ContentView: View {
    var body: some View {
        HomeView()
            .withRouter(\.router, features: [
                .deepLinking(MyDeepLinkHandler())
            ])
    }
}
```

The router automatically handles the SwiftUI [`onOpenURL`](https://developer.apple.com/documentation/swiftui/view/onopenurl(perform:)) modifier and converts URLs into navigation actions. You can even return multiple routes to build complex navigation flows!

Here's deep linking in action straight from the [Example app](https://github.com/n3d1117/Routing/tree/main/RoutingDemo):

{{< video src="demo_deeplink.mov" width="700" loop="true" muted="true" preload="metadata" caption="Deep linking demonstration" class="center" >}}

### Universal Links

The system also supports universal links (HTTPS URLs) alongside custom URL schemes. This is particularly useful for web-to-app transitions. To enable universal links, you need to configure associated domains in your app's entitlements and host an `apple-app-site-association` file on your server (see [Apple's Universal Links documentation](https://developer.apple.com/documentation/xcode/supporting-universal-links-in-your-app) for setup details).

```swift
struct UniversalLinkHandler: DeepLinkHandler {
    func handle(_ url: URL) -> [AppRoute]? {
        guard url.scheme == "https", 
              url.host == "myapp.com" else { return nil }
        
        // Parse path components and return routes
        let pathComponents = url.pathComponents
        switch pathComponents.first {
        case "/profile":
            // Handle /profile/{ID} URLs
            if pathComponents.count > 1 {
                let userId = pathComponents[1]
                return [.profile(userId: userId)]
            }
            return [.profile(userId: "default")]
        case "/settings":
            return [.settings]
        default:
            return nil
        }
    }
}

// Enable both custom schemes and universal links
.withRouter(\.router, features: [
    .deepLinking(
        MyDeepLinkHandler(),
        includeUniversalLinks: true,
        universalLinkHandler: UniversalLinkHandler() // Optional: separate handler for universal links
    )
])
```

The `universalLinkHandler` parameter is optional. If not provided, the same handler will be used for both custom URL schemes and universal links. Under the hood, the router uses SwiftUI's [`onContinueUserActivity`](https://developer.apple.com/documentation/swiftui/view/oncontinueuseractivity(_:perform:)) modifier to handle universal links.

### State Restoration

For a polished user experience, the router supports automatic state restoration across app launches. Simply make your routes conform to `Codable`:

```swift
enum AppRoute: Routable, Codable {
    case home, profile(userId: String), settings
    // ... implementation
}
```

Then enable state restoration:

```swift
.withRouter(\.router, features: [
    .stateRestoration(key: "main_navigation")
])
```

The router uses SwiftUI's [`SceneStorage`](https://developer.apple.com/documentation/swiftui/scenestorage) to persist the navigation path and automatically restores it when the app relaunches. 

{{< video src="demo_state_restoration.mp4" width="300" loop="true" muted="true" preload="metadata" caption="State restoration demonstration - navigation stack is automatically restored when the app relaunches" class="center" >}}

{{< note variant="warning" >}}
Note that modal presentations are intentionally not restored, as users typically don't expect sheets to reappear after relaunching an app.
{{< /note >}}

### Multiple Independent Routers

For complex apps with multiple navigation flows (think `TabView` with independent navigation stacks), you can create separate routers:

```swift
extension EnvironmentValues {
    @Entry var homeRouter: Router<HomeRoute> = Router()
    @Entry var searchRouter: Router<SearchRoute> = Router()
}

TabView {
    HomeView()
        .withRouter(\.homeRouter)
        .tabItem { Label("Home", systemImage: "house") }
    
    SearchView()
        .withRouter(\.searchRouter)
        .tabItem { Label("Search", systemImage: "magnifyingglass") }
}
```

Each router maintains its own navigation state, ensuring complete isolation between features.

## Conclusion
I've been using the routing system I've shared here for a few internal projects and in my opinion it provides a solid foundation for SwiftUI navigation and is much easier to use than the traditional approach. Whether you're building a simple app or a complex multi-modal experience, type-safe routing can significantly improve your development workflow and user experience.

You can find the complete source code, including the demo project, on [GitHub](https://github.com/n3d1117/Routing). The package requires iOS 17+ and macOS 14+.

Feel free to reach out if you have any questions or feedback!
