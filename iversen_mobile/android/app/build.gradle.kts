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
        }
    }
}

// Bloc Chaquopy — syntaxe actuelle (séparée du bloc android).
chaquopy {
    defaultConfig {
        version = "3.11"
        // En local sur Windows (ce PC) : chemin explicite vers Python 3.11.
        // Sur GitHub Actions (Linux) : la variable d'environnement
        // CHAQUOPY_BUILD_PYTHON (définie dans le workflow) pointe vers
        // "python3.11" installé par le runner — sans quoi ce chemin Windows
        // ferait échouer la compilation sur GitHub.
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

flutter {
    source = "../.."
}