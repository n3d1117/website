---
title: Book Manager - Project Report
description: Developing Book Manager, a small Java app built using the Test Driven Development (TDD) model together with Build Automation and Continuous Integration techniques.
date: 2020-10-21T04:14:57.000Z
slug: book-manager
tags: [java, tdd, ci, github actions, docker, uni]
toc: true
math: false
---

## Introduction

The following report describes the process of developing **Book Manager**, a small Java app built using the _Test Driven Development_ (TDD) model together with _Build Automation_ and _Continuous Integration_ techniques, as seen in [Test-Driven Development, Build Automation, Continuous Integration](https://leanpub.com/tdd-buildautomation-ci) (official book from the course).

## High Level Description

Book Manager aims at replicating a simplified version of a digital library for managing books from your favorite authors. It supports the following features:

-   Add a new author by id and name
-   Add a new book given its id, title, author and print length
-   Delete an author (which also deletes all of his/her associated books)
-   Delete a book
-   Display all authors in alphabetical order
-   Display all books and sort them by title, author name or print length

The user is able to interact with the application through a simple GUI (Graphical User Interface), which offers support for all of the operations above.

## Tools and Techniques used

While the application might not seem very complex or feature-packed, the idea behind this project is to demonstrate the use of **Test Driven Development** process as a way to write more modularized and testable code.

### Local Environment

-   **Operating System**: macOS Catalina (10.15.6)
-   **Programming Language**: Java 8
-   **IDE**: [IntelliJ IDEA](https://www.jetbrains.com/idea/) (version 2020.2)

### Tools

#### Build Automation

| Name                                                                              | Description                                                                                                                                                                                                                                                                           |
| --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Maven](https://maven.apache.org)                                                 | Build automation tool for Java projects. Based on the concept of a project object model (POM), it can easily manage a project's build configuration, dependencies, plugins, testing and reporting.                                                                                    |
| [Maven Assembly Plugin](http://maven.apache.org/plugins/maven-assembly-plugin/)   | Maven plugin to create a JAR which contains the binary output of the project, along its unpacked dependencies (often called a _fat JAR_). Binds to Maven's `package` phase. Configured in **pom.xml**.                                                                                |
| [Build Helper Maven Plugin](https://www.mojohaus.org/build-helper-maven-plugin/)  | Maven plugin to assist with the Maven build lifecycle, used in this project to add non-standard test source folders (such as `src/it/java` for integration tests and `src/e2e/java` for end-to-end tests). Binds to Maven's `generate-test-sources` phase. Configured in **pom.xml**. |
| [Maven Failsafe Plugin](https://maven.apache.org/surefire/maven-failsafe-plugin/) | Maven plugin used to run integration and end-to-end tests using `mvn verify` command. Binds to Maven's `integration-test` and `verify` phases. Configured in **pom.xml**.                                                                                                             |
| [JaCoCo](https://www.eclemma.org/jacoco/)                                         | A code coverage library for Java, integrated with Maven through the [JaCoCo Maven Plugin](https://www.eclemma.org/jacoco/trunk/doc/maven.html). Useful to generate coverage reports. Configured in **pom.xml**.                                                                       |
| [PIT Mutation Testing](https://pitest.org)                                        | Java library to perform mutation testing on specified classes. Configured in **pom.xml**.                                                                                                                                                                                             |

#### Interface

| Name                                                                   | Description                                                                                                                                      |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| [Swing](https://docs.oracle.com/javase/8/docs/technotes/guides/swing/) | A set of components for building graphical user interfaces (GUIs) and adding rich graphics functionality and interactivity to Java applications. |
| [picocli](https://picocli.info)                                        | A framework for creating Java command line applications with almost zero code.                                                                   |

#### Database

| Name                                                                                                             | Description                                                                                                                  |
| ---------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| [MongoDB](https://www.mongodb.com)                                                                               | A general purpose, document-based, non-relational distributed database.                                                      |
| [MongoDB POJOs support](http://mongodb.github.io/mongo-java-driver/3.9/driver/getting-started/quick-start-pojo/) | Automatically serialize POJOs (Plain Old Java Objects) into MongoDB documents and viceversa.                                 |
| [Docker](https://www.docker.com)                                                                                 | OS-level software virtualization tool based on containers. Used in this project to virtualize the MongoDB database instance. |

#### Testing

| Name                                                                                                        | Description                                                                                                                                                                                                                      |
| ----------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [JUnit 4](https://junit.org/junit4/)                                                                        | Java testing framework, used throughout the project for unit, integration and end-to-end tests.                                                                                                                                  |
| [AssertJ](https://assertj.github.io/doc/) and [AssertJ Swing](https://assertj.github.io/doc/#assertj-swing) | A library that provides a rich set of assertions that dramatically improves test code readability.                                                                                                                               |
| [Mockito](https://site.mockito.org)                                                                         | Java mocking framework for unit tests, useful for testing components in isolation without needing their real dependencies.                                                                                                       |
| [Testcontainers](https://www.testcontainers.org)                                                            | Java library that supports JUnit tests, providing lightweight, self contained throwaway instances of **Docker** images (usually databases). Used in this project to write tests that access a real (virtualized) MongoDB server. |
| [Awaitility](https://github.com/awaitility/awaitility)                                                      | A small Java DSL for synchronizing asynchronous operations, providing a fluent API for expressing expectations of an asynchronous system in a readable way.                                                                      |
| [Apache Log4j](https://logging.apache.org/log4j/2.x/)                                                       | Java logging framework, supporting multiple log levels.                                                                                                                                                                          |

#### Version Control

| Name                         | Description                                                                                                                                                                                |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [Git](https://git-scm.com)   | Open source distributed version control system for tracking changes in source code. Used in this project from the very beginning. Client used: [Git Tower](https://www.git-tower.com/mac). |
| [GitHub](https://github.com) | Provides hosting for software development and version control using Git. Also used for Continuous Integration.                                                                             |

#### Continuous Integration and Code Quality

| Name                                                  | Description                                                                                                                                                                                                                                                                             |
| ----------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [GitHub Actions](https://github.com/features/actions) | Tool to automate, customize, and execute software development workflows right in your GitHub repository. Used in this project to enable Continuous Integration and automated deployment.                                                                                                |
| [Coveralls](https://coveralls.io)                     | Hosted analysis tool, providing statistics about code coverage. Used in this project on CI to check for 100% code coverage. It integrates very well with JaCoCo reports.                                                                                                                |
| [SonarQube](https://www.sonarqube.org)                | Open source platform that performs local static analysis of the code, in order to detect bugs, code smells, and security vulnerabilities for several programming languages (including Java). It can also be virtualized using Docker Compose. Used in this project to catch bugs early. |
| [SonarCloud](https://sonarcloud.io)                   | The cloud version of SonarQube. It offers free continuous code quality analyses and also decorates pull requests on GitHub.                                                                                                                                                             |

## System Architecture

This project is built using the **MVC** (Model-View-Controller) multilayer architecture, combined with the **Repository** pattern to implement the **Data Access Layer** (DAL). Due to the use of MongoDB _transactions_, a **Service** layer was also added to handle the business logic.
Let's see all these layers in depth.

### Model

This layer represents domain classes, with little to no logic in them. There are two main entities:

-   **Author**: represents an author with a unique identifier and a name.
-   **Book**: represents a book with its own identifier, title, print length and the id of the author who wrote it.

These classes are meant to be as simple as possible: beside the constructor and the getters/setters, all the other methods (`equals`, `hashCode` and `toString`) were generated automatically by the IDE.
To keep things simple, we also ignore the case where a book could have multiple authors.

### View

This layer is responsible for presenting information to the final user, such as displaying authors and books and notifying about the outcome of various interactions (adding/deleting items, showing errors etc). All operations that require data access are delegated to the Controller.

### Repository

This layer interfaces directly with the database, providing basic CRUD operations. There should be one repository for each entity of the model, and it should only access a single collection in isolation, regardless of the other collections.

### Service

This layer contains the business logic of the application, and it stands between the Controller and the Repository. Its responsibility is to handle all possible errors and to coordinate the usage of multiple repositories in case of relationships between objects (i.e when deleting an author, an `AuthorService` object must handle the deletion of the author, through the `AuthorRepository`, as well as the deletion of all his/her associated books, through the `BookRepository`). Due to the introduction of **transactions**, this layer (or its _transactional_ variant) is also responsbile for ensuring that the repositories are used inside a single atomic transaction, in order to avoid inconsistencies with the database. This is done through a `TransactionManager` interface that abstracts from the database implementation (thus can be mocked when testing the service), which can be used by the service through a _lambda_ function. More of this in the _Database_ section.

### Controller

This layer stands in between the user interface (View) and the business logic (Service), as it handles all requests made the user and it dispatches them to the correct Service implementation. It is also responsible for updating the view (in case of errors or when adding/removing items).

## Database

### Supporting MongoDB Transactions

When performing multi-document write operations, whether through a single write operation or multiple write operations, other operations may interleave. For this reason, writing to different documents in multiple collections may leave the database in an inconsistent state. Wrapping database operations in a single, atomic transaction solves this problem. For example:

-   Author `George Orwell` is deleted from the database;
-   All books from `George Orwell` should be deleted as well, but they belong to a different collection.

By wrapping both these operations in the same transaction, we can be sure that even if something goes wrong while deleting items, the database can be rolled back to a previous, consistent state with no issues. Here's how transactions were implemented in this project:

-   Since we need to handle multiple repositories (one for each entity of the model), the **factory pattern** was used to define a `RepositoryFactory` interface for creating concrete repositories:

```java
public interface RepositoryFactory {
    AuthorRepository createAuthorRepository();
    BookRepository createBookRepository();
}
```

-   A `TransactionManager` interface is defined for handling transactions. It abstracts from the database implementation and specific transaction details:

```java
public interface TransactionManager {
    <T> T doInTransaction(TransactionCode<T> code);
}
```

-   `TransactionCode` is a functional interface (a lambda function that takes a `RepositoryFactory` and returns a generic `T`):

```java
@FunctionalInterface
public interface TransactionCode<T> extends Function<RepositoryFactory, T> { }
```

-   `TransactionMongoManager` then implements `TransactionManager` and defines how to wrap the lambda in a MongoDB transaction using the `withTransaction(TransactionBody<T> body)` method of `ClientSession` (as seen in the [official documentation](https://docs.mongodb.com/manual/core/transactions/)):

```java
public class TransactionMongoManager implements TransactionManager {

    @Override
    public <T> T doInTransaction(TransactionCode<T> code) {
        T result = null;
        RepositoryFactory repositoryFactory = /* new concrete MongoRepositoryFactory */
        ClientSession clientSession = mongoClient.startSession();

        TransactionBody<T> body = (() -> code.apply(repositoryFactory));

        try {
            // Execute block in a MongoDB transaction
            result = clientSession.withTransaction(body);
        } catch (MongoException e) {
            // Handle exception here
        } finally {
            clientSession.close();
        }

        return result;
    }
}
```

-   Finally, a concrete _transactional_ service can then use `TransactionManager` to perform operations on repositories inside the `doInTransaction` lambda:

```java
public class AuthorTransactionalService implements AuthorService {

    private final TransactionManager transactionManager;

    /* ... */

    @Override
    public void delete(String authorId) {
        transactionManager.doInTransaction(factory -> {
            factory.createBookRepository().deleteAllBooksForAuthorId(authorId);
            factory.createAuthorRepository().delete(authorId);
            return null;
        });
    }

    /* ... */
}
```

Note that the repository itself is not aware of being used inside a transaction, since it's not its responsibility.

By abstracting transactions from a specific database implementation, the Service layer continues to be fully testable (its behavior can be verified by stubbing `TransactionManager.doInTransaction` and passing a mock repository factory). The concrete `TransactionManager` implementation can also be fully tested in isolation, to ensure the passed lambda actually executes inside a transaction, and that a _rollback_ is performed when something goes wrong.

**Note:** MongoDB natively supports multi-document transactions, but only when using **replica sets**. The following section explains how to set up a replica set in MongoDB.

### Setting up a MongoDB Single Node Replica Set

A replica set in MongoDB is a group of `mongod` processes that maintain the same data set, providing redundancy and high availability. The simplest replica set has just a **single node** (which defeats the whole purpose of replica sets, but is very useful in a testing environment).

A `Dockerfile` is included in the project to automatically deploy a MongoDB single node replica set instance:

-   Pull the official `mongo` image with tag `4.0`
-   Set the replica set name with the `--replSet NAME` command line option
-   Initiate the replica set by running `rs.initiate()` on the single node. This is done by using the `/docker-entrypoint-initdb.d/` folder, which is automatically configured to run any script inside it for additional configuration options, before the service starts. Here the goal is to have the entrypoint automatically run a `js` file that initiates the set.

```dockerfile
FROM mongo:4.0
RUN echo "rs.initiate();" > /docker-entrypoint-initdb.d/replica-init.js
CMD ["--replSet", "rs"]
```

This custom `mongo` image can be built with the following command, from the project folder:

```bash
docker build -t book-manager-db .
```

And can then be run on port `27107` with:

```bash
docker run -p 27017:27017 --rm book-manager-db
```

The replica set will be up within a few seconds.

**Note**: luckily, for running tests this is all done automatically by the [Testcontainers](https://www.testcontainers.org) library, leveraging the [new MongoDB module](https://www.testcontainers.org/modules/databases/mongodb/).

### Automatic POJOs (de)serialization

Instead of manually converting entity models to/from the default `Document` object, this project leverages [POJO MongoDB features](https://mongodb.github.io/mongo-java-driver/3.9/driver/getting-started/quick-start-pojo/) to automatically serialize Java objects into MongoDB documents and viceversa.

Before a POJO (Plain Old Java Object) can be used with the MongoDB driver, a `CodecRegistry` must be configured to include a codecs to handle the translation to and from [bson](https://mongodb.github.io/mongo-java-driver/3.9/bson/) (binary-encoded serialization of JSON-like documents) for the POJOs. The simplest way to do that is to use the `PojoCodecProvider.builder()` to create and configure a default `CodecProvider`:

```java
import static org.bson.codecs.configuration.CodecRegistries.fromProviders;
import static org.bson.codecs.configuration.CodecRegistries.fromRegistries;

// Configure the default CodecRegistry
CodecRegistry pojoCodecRegistry =  fromRegistries(
    MongoClientSettings.getDefaultCodecRegistry(),
    fromProviders(PojoCodecProvider.builder().automatic(true).build())
);
```

After creating the codec registry, the model type must be passed to the `getCollection` method in `MongoDatabase`, and the registry can then be added using the `withCodecRegistry` modifier of `MongoCollection`:

```java
MongoClient client = /* Create a new MongoClient here */
MongoCollection<Author> authorCollection = client.getDatabase(DB_NAME)
    .getCollection(DB_AUTHOR_COLLECTION, Author.class) // specify the model class here
    .withCodecRegistry(pojoCodecRegistry); // and then inject the registry
```

This makes it a lot easier to insert objects into a collection:

```java
authorCollection.insertOne(new Author("1", "George Orwell"));
```

And it is also easier to retrieve all objects from the collection:

```java
List<Author> authors = StreamSupport
    .stream(authorCollection.find().spliterator(), false)
    .collect(Collectors.toList());
```

## User Interface Screenshots

{{< img src="95751959-9be8f100-0c9f-11eb-97ba-69cde46cde69.png" caption="Main Interface" w="560" >}}
{{< img src="95749506-f5e7b780-0c9b-11eb-8c1f-0cb369583593.jpg" caption="Sorting books by author" w="560" >}}
{{< img src="95749507-f6804e00-0c9b-11eb-808c-3114cef15d1d.jpg" caption="Selecting an item enables the Delete button" w="560" >}}
{{< img src="95749505-f54f2100-0c9b-11eb-9776-10a09e829e22.jpg" caption="Displaying errors" w="560" >}}

## Tests

By following TDD, the application is fully tested. The **pyramid** shape has also been respected:

-   73 Unit tests
-   46 Integration tests
-   10 End-to-end tests

### Unit Tests

The **controller**, **service** and **view** components have all been tested in isolation through unit tests, mocking all possible dependencies with [Mockito](https://site.mockito.org). However, other components of the database layer, such as the **transaction manager** and the **repositories**, have actually been considered as **integration tests** (thus placed in the `src/it/java` folder), because they communicate with a real (virtualized) database. Furthermore, unit tests should be fast, as they are meant to be run after each change in the code, while database tests actually take a few seconds due to the startup time of the container.

[JUnit](https://junit.org/junit4/) was used as the main testing framework, together with [AssertJ](https://assertj.github.io/doc/) (and [AssertJ Swing](https://assertj.github.io/doc/#assertj-swing) for UI tests). All tests were written adopting the typical **exercise, setup, verify** structure and following the TDD methodology.

Of course, domain model classes weren't tested (and they were also excluded from code coverage), because they don't contain any particular logic.

### Integration Tests

The purpose of integration tests is to make sure that two or more components still work correctly when integrated together, even when interacting with an external dependency (such as a database). In this project, the only third party component is the MongoDB database, which has been virtualized using the [Testcontainers](https://www.testcontainers.org) library.
The [Awaitility](https://github.com/awaitility/awaitility) library has also been used for expressing asynchronous expectations.

The following interactions were tested (covering only the positive or interesting cases):

-   The integration between controller and service layers (the view is still mocked), while interacting with a real database
-   The behavior of both the repositories with a real database implementation
-   The integration between the controller and the real view
-   The integration between the service and the repository
-   The correct behavior of `TransactionMongoManager`, when communicating with a real MongoDB database implementation, to ensure transactions and rollbacks are executed correctly

Furthermore, particular attention has been paid to multithreading, in order to avoid race conditions when a method could be executed repeatedly by multiple concurrent threads (for example the user could spam the `Add` or `Delete` button several times in a row, resulting in a failure). A few tests have been added to cover such cases: race conditions have been recreated by spawning multiple threads, all calling the same controller methods concurrently (`addAuthor`, `deleteAuthor`, `addBook`, `addBook`), and then verifying that the database is still in a consistent state.
These cases have been fixed by making sure the controller methods are `synchronized`, to prevent thread interference.

### End-to-end Tests

Following a black-box approach, a few end-to-end tests have been added in order to verify the overall behavior of the application with all the components integrated together. These tests interact directly with the user interface and there is no explicit mention of any internal Java classes, simulating exactly what a normal user would do.

With end-to-end tests, the following situations were tested:

-   All initial UI elements are visible at startup
-   Adding a new author or book through the user interface results in the item added to the corrisponding list or table
-   Deleting an existing author or a book through the user interface results in the item being deleted from the corresponding list or table
-   Deleting an existing author through the user interface also results in his/her books being deleted from the list

### Code Coverage

By using TDD, code coverage requirements of 100% (using [JaCoCo](https://www.eclemma.org/jacoco/)) have been met successfully. The following classes have been excluded from calculations:

-   Domain model classes (`Book` and `Author`), because they have no logic inside them (and methods such as `equals`, `hashCode` and `toString` have been generated automatically by the IDE)
-   `TextFieldDocumentListener`, a custom Swing component, because it contains a method that is required by the `DocumentListener` interface but is never actually called throughout the app
-   `BookManagerSwingApp` because it's the main class that contains the method to run the application

100% code coverage checks are disabled by default when testing the project, and can be enabled by adding the `jacoco-check` profile to the Maven `verify` command:

```bash
mvn clean verify -P jacoco-check
```

### Mutation Testing

Mutation testing with [PIT](https://pitest.org) has also been used in the project, taking advantage of the **STRONGER** mutators group and a treshold of 100% (all mutants must be killed for the build to pass). The following classes have been excluded from mutation testing:

-   Domain model classes
-   All Swing and UI related classes, as they are not meant to be tested with PIT
-   `MongoRepositoryFactory`, a concrete factory implementation with no logic in it

However, those _hybrid_ tests that were considered integration tests (for the repositories and transaction manager) were included in mutation testing as well.

Mutation testing is disabled by default, and can be enabled by adding the `mutation-testing` profile to the Maven `verify` command:

```bash
mvn clean verify -P mutation-testing
```

### Logging

The application uses [Log4j](https://logging.apache.org/log4j/2.x/) for logging purposes. In particular, log4j was configured so that test code has a `DEBUG` logging level, while main code has a simplified environment with a `INFO` logging level.
This setup was accomplished by placing a slightly different `log4j.xml` configuration file in the test resources directory (`src/test/resources`) compared to the main resources directory (`src/main/resources`). When running tests, the test resource has precedence over the same file in the main resource directory.

## Code Quality

### Coveralls

To enable [Coveralls](https://coveralls.io) integration, the user must first enable the `jacoco-report` profile to generate the JaCoCo report, and then add the `coveralls:report` goal:

```bash
mvn clean verify -P jacoco-report coveralls:report -D repoToken=YOUR_COVERALLS_TOKEN
```

`YOUR_COVERALLS_TOKEN` is the Coveralls token that can be obtained directly from the website. From the [official documentation](https://github.com/trautonen/coveralls-maven-plugin#configuration), it is required when using any continuous integration server other than Travis CI.

**Note**: altough there is an [official GitHub action for posting coverage data to Coveralls](https://github.com/coverallsapp/github-action), it was not used in this project because it requires exporting coverage data in LCOV format, and at the time of writing JaCoCo is not capable of that. There are multiple [open GitHub issues](https://github.com/coverallsapp/github-action/issues/22) about it.

### SonarQube

To test the project locally with [SonarQube](https://www.sonarqube.org), a Docker Compose file is included in the `sonarqube` folder. To start the local analysis:

```bash
$ cd sonarqube
$ docker-compose up
$ cd ..
$ mvn clean verify sonar:sonar
```

### SonarCloud

To enable [SonarCloud](https://sonarcloud.io) code analysis, the user can enable the `sonar:sonar` goal when testing:

```bash
mvn clean verify sonar:sonar \
-D sonar.host.url=SONAR_URL \
-D sonar.organization=SONAR_ORGANIZATION \
-D sonar.projectKey=SONAR_PROJECT
```

`SONAR_URL`, `SONAR_ORGANIZATION` and `SONAR_PROJECT` must be replaced with the project's values, as seen in the SonarCloud dashboard. An environment variable `SONAR_TOKEN` must be also be specified, representing the SonarCloud token.

**Note**: there is also [a GitHub action](https://github.com/SonarSource/sonarcloud-github-action) for integrating SonarCloud analysis directly, but [it is not recommended](https://github.com/SonarSource/sonarcloud-github-action#do-not-use-this-github-action-if-you-are-in-the-following-situations) for projects that are using Maven (the `sonar:sonar` goal is preferred instead).

## Continuous Integration

### GitHub Actions

The project uses [GitHub Actions](https://github.com/features/actions) as a Continuous Integration server to build, test, and deploy the app right from GitHub's interface.

To enable GitHub Actions, a **workflow** (or more) must be added in the `.github/workflows` directory. A workflow is essentially a YAML (`.yml`) file that defines the actions to perform after a certain event is triggered in the repository, such as a commit or a pull request.
YAML syntax for workflows, from the [official documentation](https://docs.github.com/en/free-pro-team@latest/actions/reference/workflow-syntax-for-github-actions), defines the following terms:

-   `name`: the name of the workflow
-   `on`: the name of the GitHub event that triggers the workflow (e.g. `push`, `pull_request`...)
-   `jobs`: a workflow run is made up of one or more _jobs_ (they run in parallel by default)
    -   `name`: the name of the job
    -   `runs-on`: the type of machine to run the job on, `ubuntu-18.04` for this project
    -   `steps`: a job contains a sequence of tasks called _steps_, which can run commands or predefined actions
        -   `name`: the name of the step
        -   `uses`: specifies an _action_ (reusable unit of code) to run
        -   `run`: runs command-line programs using the operating system's shell
        -   `with`: optional input parameters defined by the action
        -   `env`: sets environment variables for steps to use in the runner environment
    -   `strategy`: creates a build matrix for the jobs
        -   `matrix`: allows you to create multiple jobs by performing variable substitution in a single job definition

The following public _actions_ were used in this project:

-   [actions/checkout@v2](https://github.com/actions/checkout): action for checking out a repo, so the workflow can access it
-   [actions/setup-java@v1](https://github.com/actions/setup-java): sets up a java environment with the specified version, e.g:

```yaml
uses: actions/setup-java@v1
  with:
    java-version: 8
```

-   [actions/cache@v2](https://github.com/actions/cache): enables caching specified directories to improve workflow execution time. In particular, two directories were cached:
    -   The `~/.m2` folder, as suggested in the [official guide](https://docs.github.com/en/free-pro-team@latest/actions/guides/building-and-testing-java-with-maven), to cache the contents of the Maven repository (where dependencies and plugins are stored). The cache key will be the hashed contents of `pom.xml`, so changes to `pom.xml` will invalidate the cache
    -   The `~/.sonar/cache` folder, to cache SonarCloud packages
-   [softprops/action-gh-release@v1](https://github.com/softprops/action-gh-release): allows creating a GitHub release, optionally uploading release assets. Used in this project to enable automated jar deployment when pushing git tags.

#### Main Workflow

The main workflow consists in two different jobs:

-   The first job (named `build`) is triggered after every push on the repository, and it builds and tests the project on a machine with Ubuntu 18.04 using Java 8. It performs code coverage checks, mutation testing and also sends reports to external services (Coveralls, using JaCoCo's report, and SonarCloud) to ensure code quality is preserved.
-   The second job (named `build-on-pr-merge`) is only triggered after merging a pull request (by checking if the commmit's message starts with "Merge pull request"), and takes advantage of the `matrix` strategy of GitHub Actions, spawning three jobs to build and test the project concurrently on Java 9, 11 and 13. To avoid duplicated reports, this job does not send any report to external services (altough it still performs code coverage checks and mutation testing).

**Note**: to increase reliability, all tests on CI are executed on a secondary desktop with [TightVNC](https://www.tightvnc.com), using the `execute-on-vnc.sh` script included in the project, as recommended in the [official AssertJ Swing documentation](https://joel-costigliola.github.io/assertj/assertj-swing-running.html). For this reason, before testing a VNC server is installed on the machine with the command `sudo apt-get install -y tightvncserver`.

```yaml
on: [push]

jobs:

  # First job: build and test on Java 8
  build:
    runs-on: ubuntu-18.04
    name: Build and test on Java 8
      steps:
        - name: Check out latest code
          uses: actions/checkout@v2
        - name: Set up JDK 8
          uses: actions/setup-java@v1
            with:
              java-version: 8
        - name: Cache Maven packages
          uses: actions/cache@v2
          with:
            path: ~/.m2
            key: ${{ runner.os }}-m2-${{ hashFiles('**/pom.xml') }}
            restore-keys: ${{ runner.os }}-m2
        - name: Cache SonarCloud packages
          uses: actions/cache@v2
          with:
            path: ~/.sonar/cache
            key: ${{ runner.os }}-sonar
            restore-keys: ${{ runner.os }}-sonar
        - name: Install tightvncserver
            run: sudo apt-get install -y tightvncserver
        - name: Run mvn clean verify (with jacoco, mutation testing, coveralls and sonar) w/ vnc
            run: |
              ./execute-on-vnc.sh \
              mvn clean verify \
              $ENABLED_PROFILES $ADDITIONAL_GOALS \
              -D repoToken=$COVERALLS_TOKEN \
              -D sonar.host.url=$SONAR_URL \
              -D sonar.organization=$SONAR_ORGANIZATION \
              -D sonar.projectKey=$SONAR_PROJECT
            env:
              ENABLED_PROFILES: -P jacoco-report,mutation-testing
              ADDITIONAL_GOALS: coveralls:report sonar:sonar
              COVERALLS_TOKEN: ${{ secrets.COVERALLS_REPO_TOKEN }}
              SONAR_URL: https://sonarcloud.io
              SONAR_ORGANIZATION: n3d1117-github
              SONAR_PROJECT: n3d1117_book-manager
              SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
              GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  # Second job: also build on Java 9, 11 and 13, but only after merging a PR
  build-on-pr-merge:
    if: startsWith(github.event.head_commit.message, 'Merge pull request')
      runs-on: ubuntu-18.04
      strategy:
        matrix:
          java: [9, 11, 13]
      name: Test on other Java versions
      steps:
        # same steps as above, using ${{ matrix.java }} as Java version
```

**Note**: `GITHUB_TOKEN` is a personal GitHub token required to access the repository. It can be generated from GitHub's web interface and safely stored using [GitHub secrets](https://docs.github.com/en/free-pro-team@latest/actions/reference/encrypted-secrets). The same goes for Sonar's and Coveralls' token.

#### Automated Jar Deployment

A secondary workflow was added that, when a **git tag** is pushed to a particular commit, automatically checks out the repository, compiles a **fat jar** (skipping tests to speed up the job) and deploys it as an asset through GitHub releases.

**Note**: the git tag must start with the letter `v` (e.g. `v1.0`) to signify a version change.

```yaml
on:
  push:
    tags:
        - v*
jobs:
  deploy:
    runs-on: ubuntu-18.04
    name: Automated release with .jar
    steps:
      - name: Check out latest code
        uses: actions/checkout@v2
      - name: Set up JDK 8
        uses: actions/setup-java@v1
        with:
          java-version: 8
      - name: Package fat .jar, skipping tests
          run: mvn -DskipTests=true clean package
      - name: Create Github release with tag and upload fat .jar as asset
        uses: softprops/action-gh-release@v1
        with:
          files: target/*-jar-with-dependencies.jar
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Automated Dependency Updates

Maven dependencies are automatically kept up-to-date using [Dependabot](https://dependabot.com), a bot that integrates natively within the GitHub interface. Dependabot periodically scans the project and checks for any outdated or insecure requirements. If any dependency is found to be out-of-date, a pull request is automatically created that updates it, and can be merged safely as long as the test suite remains green.

During the development of this project, Dependabot generated [seven pull requests](https://github.com/n3d1117/book-manager/pulls?q=is%3Apr+is%3Aclosed+label%3Adependencies) for various outdated dependencies (`junit`, `mockito-core`, `jacoco-maven-plugin`, `assertj-swing-unit`), all of which have been merged with no issues.

## Running the app

To run the app, the user can either manually build the fat Jar file using Maven (`mvn clean package`) or download a precompiled version from the [releases page](https://github.com/n3d1117/book-manager/releases).

After setting up the database instance (as seen in [Setting up a MongoDB Single Node Replica Set](#setting-up-a-mongodb-single-node-replica-set)), the app can be started with the following command:

```bash
java -jar target/book-manager-1.0-SNAPSHOT-jar-with-dependencies.jar [options]
```

These are the available command line options (defined with the [picocli](https://picocli.info) library):

| Option                    | Description                                                                 |
| ------------------------- | --------------------------------------------------------------------------- |
| `--mongo-replica-set-url` | The URL of the MongoDB replica set. Defaults to `mongodb://localhost:27017` |
| `--db-name`               | The database name. Defaults to `bookmanager`                                |
| `--db-author-collection`  | Name of the authors collection in database. Defaults to `authors`           |
| `--db-book-collection`    | Name of the books collection in database. Defaults to `books`               |

## Source Code

All the code and setup files used in this project are available on the [book-manager GitHub repository](https://github.com/n3d1117/book-manager).
