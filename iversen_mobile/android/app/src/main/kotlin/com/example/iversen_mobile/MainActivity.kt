package com.example.iversen_mobile

import android.os.Bundle
import io.flutter.embedding.android.FlutterActivity
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform

class MainActivity : FlutterActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Démarre l'interpréteur Python embarqué (Chaquopy) une seule fois,
        // dès l'ouverture de l'appli — avant même que l'écran Flutter
        // s'affiche.
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }

        // Lance le serveur local (voir android_entry.py, prochaine étape),
        // dans un thread Python en arrière-plan.
        val py = Python.getInstance()
        val entry = py.getModule("android_entry")
        entry.callAttr("start_server_in_background", 8000)
    }
}