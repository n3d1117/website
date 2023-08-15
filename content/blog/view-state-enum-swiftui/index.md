---
title: Modeling view state in SwiftUI using a generic enum
description: How to reduce boilerplate code when modeling view state in SwiftUI views by using a generic enum to handle common scenarios such as loading, success, and error states.
date: 2023-08-15T05:24:54.000Z
slug: view-state-enum-swiftui
tags: [ios, swift, swiftui]
toc: true
math: false
comments: true
---

## Introduction
In this post, we will explore how to reduce boilerplate code when modeling view state in SwiftUI views by using a generic enum to handle common scenarios such as loading, success, and error states.

## Introducing the ViewState enum
Let's start by creating the generic view state enum. We'll call it `ViewState` and it will have three cases: `success`, `failed`, and `loading`. The `success` case will have an associated value of type `T` which will be the type of the data we want to display in the view. The `failed` case will have an associated value of type `Error` which will be the error we want to display in the view. The `loading` case will not have an associated value.

```swift
enum ViewState<T>: Equatable where T: Equatable {
    case success(T)
    case failed(Error)
    case loading
    
    static func ==(lhs: ViewState, rhs: ViewState) -> Bool {
        switch (lhs, rhs) {
        case (.loading, .loading):
            return true
        case let (.success(lhsValue), .success(rhsValue)):
            return lhsValue == rhsValue
        case let (.failed(lhsError), .failed(rhsError)):
            return lhsError.localizedDescription == rhsError.localizedDescription
        default:
            return false
        }
    }
}
```

Note that we are conforming to the `Equatable` protocol. This is because we want to be able to compare two `ViewState` instances to see if they are equal. To do so, we are also constraining the generic type `T` to conform to the `Equatable` protocol, so that we easily can compare associated values of type `T` in the `success` case using the `==` operator.

## Example usage
Let's now see how we can use the `ViewState` enum in a SwiftUI view. We'll create a simple view that displays a list of news:

```swift
struct NewsView: View {
    
    @StateObject var viewModel = ViewModel()
    
    var body: some View {
        ZStack {
            switch viewModel.state {
            
            case .failed(let error):
                ErrorView(error: error)
            
            case .loading:
                ProgressView()
            
            case .success(let news):
                List {
                    ForEach(news) { newsEntry in
                        Text(newsEntry.title)
                    }
                }
                .refreshable { await viewModel.loadNews() }
            }
        }
        .task { await viewModel.loadNews() }
        .navigationTitle("News")
    }
}
```

We use a ZStack to display the correct view depending on the `state`, which are mutually exclusive. The state lives in a `ViewModel` class, which we will look at next. 

If the state is `.failed`, we display a generic `ErrorView`. If the state is `.loading`, we display a `ProgressView`. If the state is `.success`, we display a refreshable `List` of news entries. We also add a `.task` modifier to the ZStack to load the news when the view appears, and a `.navigationTitle` modifier to set the title of the view.

### Example view model

The View Model class is responsible for loading the news entries and updating the state accordingly. This is how it could look like:

```swift
extension NewsView {
    @MainActor final class ViewModel: ObservableObject {
        @Dependency(\.apiService) private var apiService
        
        @Published private(set) var state: ViewState<[NewsEntry]> = .loading
        
        func loadNews() async {
            do {
                let response: [NewsEntry] = try await apiService.fetchNews()
                state = .success(response.data)
            } catch {
                state = .failed(error)
            }
        }
    }
}
```

It has a `state` property of type `ViewState<[NewsEntry]>` which is the type of the state we want to display in the view, and defaults to `.loading` so that the progress view is shown immediately. It also has a `loadNews` method which loads the news entries from an external service and updates the state accordingly.

The news are loaded using the `apiService` dependency, which is injected using the `@Dependency` property wrapper. This is just an example inspired by the [Factory](https://github.com/hmlongco/Factory) library I recently explored (actual dependency injection techniques are out of scope for this post).

Since the `state` is marked as `@Published`, the view will automatically be updated when the state changes.

### Animations
We can also add animations to the view by using the `.animation` modifier. For example, if we want to animate the transition between the different states, we can do so by adding the `.animation` modifier to the ZStack:

```swift
ZStack {
    switch viewModel.state {
        /* ... */
    }
}
.animation(.default, value: viewModel.state) // [tl! highlight]
```

### Previews
One big advantage of using a generic enum to model view state is that we can easily create previews for all the different states. For example, we can create a preview for all the possible states by mocking the service that loads the news entries:

```swift
struct NewsView_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            // Preview with mocked news
            let _ = Dependencies.apiService.register {
                .mock(.data([
                    NewsEntry(id: 1, title: "One"),
                    NewsEntry(id: 2, title: "Two")
                ]))
            }
            let viewModel = NewsView.ViewModel()
            NewsView(viewModel: viewModel)
                .previewDisplayName("Mocked")
            
            // Preview with error
            let _ = Dependencies.apiService.register { .mock(.error(.example)) }
            let viewModel2 = NewsView.ViewModel()
            NewsView(viewModel: viewModel2)
                .previewDisplayName("Error")
            
            // Preview while loading
            let _ = Dependencies.apiService.register { .mock(.loading()) }
            let viewModel3 = NewsView.ViewModel()
            NewsView(viewModel: viewModel3)
                .previewDisplayName("Loading")
        }
    }
}
```

### Testing
In the same way, we can easily test that the view model sets the correct state when loading the news entries:

```swift
@MainActor final class NewsViewModelTests: XCTestCase {

    func testNewsLoadingInitialState() {
        let viewModel = NewsView.ViewModel()
        XCTAssertEqual(viewModel.state, .loading)
    }

    func testNewsLoadingSuccess() async throws {
        // Given
        let newsEntry: NewsEntry = .mock
        Dependencies.apiService.register {
            .mock(.data([newsEntry]))
        }
        let viewModel = NewsView.ViewModel()
        XCTAssertEqual(viewModel.state, .loading)
        
        // When
        await viewModel.loadNews()
        
        // Then
        XCTAssertEqual(viewModel.state, .success([newsEntry]))
    }
    
    func testNewsLoadingFail() async throws {
        // Given
        Dependencies.apiService.register {
            .mock(.error(.example))
        }
        let viewModel = NewsView.ViewModel()
        XCTAssertEqual(viewModel.state, .loading)
        
        // When
        await viewModel.loadNews()
        
        // Then
        XCTAssertEqual(viewModel.state, .failed(.example))
    }

}
```

### Notes
- This is not a silver bullet and may not be suitable for all use cases, but I found it quite useful in some of my projects for simple views that need to display data from an external service.
- One thing that it's missing is handling of empty state (i.e. when the state is `.success` but the data is empty). This could be a great use case for the newly introduced [ContentUnavailableView](https://developer.apple.com/documentation/swiftui/contentunavailableview)!

## Conclusion
I hope you enjoyed this post and that you found it useful. If you have any questions or feedback, please let me know by leaving a comment below. Thanks for reading!