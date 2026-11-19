plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}
android {
    namespace = "ai.valis.app"
    compileSdk = 35
    // CI sets GITHUB_RUN_NUMBER; every build gets a higher versionCode so Android accepts it as an update.
    val runNumber = System.getenv("GITHUB_RUN_NUMBER")?.toIntOrNull() ?: 0
    defaultConfig {
        applicationId = "ai.valis.companion"; minSdk = 26; targetSdk = 35
        versionCode = 1000 + runNumber; versionName = "0.3.$runNumber"
    }
    // The permanent release key lives only in GitHub secrets (decoded to a file by the release workflow).
    val keystorePath = System.getenv("VALIS_KEYSTORE")
    signingConfigs {
        if (keystorePath != null) create("valis") {
            storeFile = file(keystorePath)
            storePassword = System.getenv("VALIS_KEYSTORE_PASSWORD")?.trim()
            keyAlias = System.getenv("VALIS_KEY_ALIAS")?.trim()
            keyPassword = System.getenv("VALIS_KEYSTORE_PASSWORD")?.trim()
        }
    }
    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfigs.findByName("valis")?.let { signingConfig = it }
        }
    }
    lint { checkReleaseBuilds = false }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
}
dependencies {
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
    implementation("androidx.datastore:datastore-preferences:1.1.1")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.google.android.filament:filament-android:1.56.0")
    implementation("com.google.android.filament:filament-utils-android:1.56.0")
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.json:json:20240303")
}
