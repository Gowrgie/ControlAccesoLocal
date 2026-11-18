package com.controlacceso.appmovil.ui

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.LocalLifecycleOwner
import java.util.concurrent.ExecutionException

@Composable
fun FaceCaptureScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    var hasPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) ==
                PackageManager.PERMISSION_GRANTED
        )
    }
    val requestPermission = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted -> hasPermission = granted }

    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text("Prueba de cámara frontal", style = MaterialTheme.typography.headlineSmall)
        TextButton(onClick = onBack) { Text("Volver a identificación") }

        if (hasPermission) {
            FrontCameraPreview(modifier = Modifier.weight(1f))
        } else {
            Text("Concede permiso de cámara para probar la captura.")
            Button(onClick = { requestPermission.launch(Manifest.permission.CAMERA) }) {
                Text("Permitir cámara")
            }
        }
    }
}

@Composable
private fun FrontCameraPreview(modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val owner = LocalLifecycleOwner.current
    val mainExecutor = remember(context) { ContextCompat.getMainExecutor(context) }
    val previewView = remember(context) { PreviewView(context) }
    val preview = remember { Preview.Builder().build() }
    val imageCapture = remember { ImageCapture.Builder().build() }
    var ready by remember { mutableStateOf(false) }
    var capturing by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf("Abriendo cámara…") }

    DisposableEffect(context, owner, preview, imageCapture) {
        val providerFuture = ProcessCameraProvider.getInstance(context)
        var provider: ProcessCameraProvider? = null
        var active = true

        providerFuture.addListener({
            if (active) {
                try {
                    val cameraProvider = providerFuture.get()
                    preview.setSurfaceProvider(previewView.surfaceProvider)
                    cameraProvider.bindToLifecycle(
                        owner, CameraSelector.DEFAULT_FRONT_CAMERA, preview, imageCapture
                    )
                    provider = cameraProvider
                    ready = true
                    message = "Coloca tu rostro frente a la cámara."
                } catch (_: IllegalArgumentException) {
                    message = "El dispositivo no tiene una cámara frontal disponible."
                } catch (_: ExecutionException) {
                    message = "No se pudo iniciar la cámara."
                } catch (_: SecurityException) {
                    message = "Se necesita permiso para abrir la cámara."
                } catch (_: IllegalStateException) {
                    message = "No se pudo abrir la cámara en esta pantalla."
                }
            }
        }, mainExecutor)

        onDispose {
            active = false
            provider?.unbind(preview, imageCapture)
        }
    }

    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(12.dp)) {
        AndroidView(factory = { previewView }, modifier = Modifier.fillMaxWidth().weight(1f))
        Text(message)
        Button(
            enabled = ready && !capturing,
            onClick = {
                capturing = true
                imageCapture.takePicture(
                    mainExecutor,
                    object : ImageCapture.OnImageCapturedCallback() {
                        override fun onCaptureSuccess(image: ImageProxy) {
                            image.close()
                            capturing = false
                            message = "Captura realizada."
                        }

                        override fun onError(exception: ImageCaptureException) {
                            capturing = false
                            message = "No se pudo capturar la imagen. Intenta de nuevo."
                        }
                    }
                )
            }
        ) {
            Text(if (capturing) "Capturando…" else "Capturar imagen")
        }
    }
}
