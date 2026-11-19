plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}
android {
    namespace = "ai.valis.app"
    compileSdk = 35
    defaultConfig { applicationId = "ai.valis.companion"; minSdk = 26; targetSdk = 35; versionCode = 2; versionName = "0.2.0" }
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
}
