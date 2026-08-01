import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

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
      // Le serveur Python (démarré dans MainActivity.kt) écoute sur ce
      // port en local sur le téléphone lui-même — jamais sur internet.
      ..loadRequest(Uri.parse('http://127.0.0.1:8000'));
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