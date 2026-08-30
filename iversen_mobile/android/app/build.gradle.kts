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
            // Chaquopy accede aux classes Java (ex: ML Kit) via reflexion
            // depuis Python — R8 ne peut pas le voir et supprimerait ces
            // classes en les croyant inutilisees. On desactive donc la
            // minification ET la reduction des ressources (le plugin
            // Flutter active cette derniere par defaut pour les builds
            // release, ce qui exige minifyEnabled=true — d'ou le conflit
            // sans cette ligne).
            isMinifyEnabled = false
            isShrinkResources = false
        }
    }
}

// Bloc Chaquopy — syntaxe actuelle (séparée du bloc android).
chaquopy {
    defaultConfig {
        version = "3.11"
        // Uniquement utilisé au moment du build (sur la machine du
        // développeur) pour résoudre/télécharger les paquets pip listés
        // ci-dessous — jamais embarqué dans l'app. Valeur précédente : un
        // chemin Windows absolu propre à un seul poste de développement
        // ("C:/Users/brice/..."), ce qui cassait le build sur toute autre
        // machine (autre développeur, autre OS, CI...). On se rabat
        // maintenant sur "python3.11" résolu via le PATH, avec la variable
        // d'environnement CHAQUOPY_BUILD_PYTHON en échappatoire explicite si
        // un poste a besoin d'un chemin précis.
        buildPython(System.getenv("CHAQUOPY_BUILD_PYTHON") ?: "python3.11")
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
