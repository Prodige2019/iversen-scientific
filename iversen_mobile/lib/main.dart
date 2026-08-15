import 'dart:io' show Platform;

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Iversen Scientific',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
      ),
      home: const IversenWebView(),
    );
  }
}

class IversenWebView extends StatefulWidget {
  const IversenWebView({super.key});

  @override
  State<IversenWebView> createState() => _IversenWebViewState();
}

class _IversenWebViewState extends State<IversenWebView> {
  late final WebViewController _controller;

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..loadRequest(Uri.parse('http://127.0.0.1:8000'));

    // webview_flutter ne gere pas nativement <input type="file"> sur
    // Android (limitation connue du plugin, confirmee par plusieurs
    // rapports de bugs officiels flutter/flutter) : sans ce branchement,
    // cliquer sur le bouton photo ne fait strictement rien. On ouvre
    // directement l'appareil photo via image_picker des qu'un champ
    // fichier est declenche cote WebView.
    if (Platform.isAndroid) {
      final androidController = _controller.platform as AndroidWebViewController;
      androidController.setOnShowFileSelector(_onShowFileSelector);
    }
  }

  Future<List<String>> _onShowFileSelector(FileSelectorParams params) async {
    final picker = ImagePicker();
    final photo = await picker.pickImage(source: ImageSource.camera);
    if (photo == null) return [];
    return ['file://${photo.path}'];
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: WebViewWidget(controller: _controller),
      ),
    );
  }
}
