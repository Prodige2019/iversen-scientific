plugins {
    id("com.android.application")
    id("dev.flutter.flutter-gradle-plugin")
    id("com.chaquo.python")
}

android {
    namespace = "com.example.iversen_mobile"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        applicationId = "com.example.iversen_mobile"
        minSdk = 24
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName

        ndk {
            abiFilters.clear()
            abiFilters.add("armeabi-v7a")
            abiFilters.add("arm64-v8a")
        }
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("debug")
            // IMPORTANT : Chaquopy accede aux classes Java (ex: ML Kit) via
            // reflexion depuis Python — R8 ne peut pas le voir et supprime
            // ces classes en pensant qu'elles sont inutilisees, causant
            // "ModuleNotFoundError: No module named 'com'" au lancement.
            // Pratique standard recommandee pour tout projet Chaquopy.
            isMinifyEnabled = false
        }
    }
}

// Bloc Chaquopy — syntaxe actuelle (séparée du bloc android).
chaquopy {
    defaultConfig {
        version = "3.11"
        buildPython(System.getenv("CHAQUOPY_BUILD_PYTHON") ?: "C:/Users/brice/AppData/Local/Programs/Python/Python311/python.exe")
        pip {
            install("fastapi")
            install("uvicorn")
            install("sympy")
            install("pydantic")
            install("python-multipart")
            install("numpy")
            install("Pillow")
            install("reportlab")
            install("matplotlib")
            install("pypdf")
            install("python-docx")
        }
    }
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

dependencies {
    implementation("com.google.mlkit:text-recognition:16.0.1")
}

flutter {
    source = "../.."
}
