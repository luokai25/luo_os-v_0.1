pluginManagement {
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
    // NOTE: gradle/libs.versions.toml is auto-detected by Gradle convention —
    // do NOT also declare it via versionCatalogs { create("libs") { ... } },
    // that registers "libs" twice and fails with "you can only call 'from' once".
}

rootProject.name = "LuoOS"
include(":app")
