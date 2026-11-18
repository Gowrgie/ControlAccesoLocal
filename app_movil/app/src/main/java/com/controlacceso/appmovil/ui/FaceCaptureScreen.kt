package com.controlacceso.appmovil.ui

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Matrix
import android.util.Base64
import android.view.Surface
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
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.controlacceso.appmovil.data.ApiClient
import com.controlacceso.appmovil.data.FaceChallenge
import com.controlacceso.appmovil.data.FaceChallengeRequest
import com.controlacceso.appmovil.data.FaceSessionRequest
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.security.MessageDigest
import java.util.concurrent.ExecutionException
import javax.net.ssl.SSLException
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.asExecutor
import kotlinx.coroutines.launch
import kotlinx.coroutines.suspendCancellableCoroutine

@Composable
fun FaceCaptureScreen(onLoggedIn: (String) -> Unit, onBack: () -> Unit) {
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
        Text("Ingresar con rostro", style = MaterialTheme.typography.headlineSmall)
        TextButton(onClick = onBack) { Text("Volver a identificación") }

        if (hasPermission) {
            FrontCameraPreview(onLoggedIn = onLoggedIn, modifier = Modifier.weight(1f))
        } else {
            Text("Concede permiso de cámara para verificar tu rostro.")
            Button(onClick = { requestPermission.launch(Manifest.permission.CAMERA) }) {
                Text("Permitir cámara")
            }
        }
    }
}

@Composable
private fun FrontCameraPreview(onLoggedIn: (String) -> Unit, modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val owner = LocalLifecycleOwner.current
    val mainExecutor = remember(context) { ContextCompat.getMainExecutor(context) }
    val previewView = remember(context) { PreviewView(context) }
    val preview = remember { Preview.Builder().build() }
    val imageCapture = remember { ImageCapture.Builder().build() }
    var ready by remember { mutableStateOf(false) }
    var capturing by remember { mutableStateOf(false) }
    var challenge by remember { mutableStateOf<FaceChallenge?>(null) }
    var frontImage by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()
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
                    message = "Mira de frente a la cámara y mantén la cabeza recta."
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
                scope.launch {
                    try {
                        val currentChallenge = challenge
                        val currentFront = frontImage
                        if (currentChallenge == null || currentFront == null) {
                            val image = imageCapture.capturarJpeg()
                            val digest = MessageDigest.getInstance("SHA-256")
                                .digest(Base64.decode(image, Base64.NO_WRAP))
                                .joinToString("") { byte -> "%02x".format(byte) }
                            val response = ApiClient.facial.createChallenge(FaceChallengeRequest(digest))
                            val newChallenge = response.body()
                            if (!response.isSuccessful || newChallenge == null) {
                                message = mensajeFacial(response.code(), response.headers()["Retry-After"])
                                return@launch
                            }
                            frontImage = image
                            challenge = newChallenge
                            message = if (newChallenge.direction == "izquierda") {
                                "Inclina la cabeza hacia tu hombro izquierdo y captura otra vez."
                            } else {
                                "Inclina la cabeza hacia tu hombro derecho y captura otra vez."
                            }
                        } else {
                            val tiltedImage = imageCapture.capturarJpeg()
                            challenge = null
                            frontImage = null
                            val response = ApiClient.facial.login(
                                FaceSessionRequest(currentChallenge.id, currentFront, tiltedImage)
                            )
                            val token = response.body()?.token
                            if (response.isSuccessful && !token.isNullOrBlank()) {
                                onLoggedIn(token)
                            } else {
                                message = mensajeFacial(response.code(), response.headers()["Retry-After"])
                            }
                        }
                    } catch (_: SSLException) {
                        challenge = null
                        frontImage = null
                        message = "No se pudo verificar la conexión HTTPS con la Raspberry Pi."
                    } catch (_: IOException) {
                        challenge = null
                        frontImage = null
                        message = "No se pudo conectar con la Raspberry Pi. Intenta de nuevo."
                    } catch (_: ImageCaptureException) {
                        message = "No se pudo capturar la imagen. Intenta de nuevo."
                    } catch (_: IllegalArgumentException) {
                        challenge = null
                        frontImage = null
                        message = "No se pudo preparar la captura. Intenta de nuevo."
                    } finally {
                        capturing = false
                    }
                }
            }
        ) {
            Text(
                if (capturing) "Procesando…"
                else if (challenge == null) "Capturar de frente"
                else "Capturar con inclinación"
            )
        }
    }
}

private fun mensajeFacial(code: Int, espera: String?): String = when (code) {
    401 -> "No se pudo verificar el rostro. Empieza de nuevo o ingresa con tu contraseña."
    429 -> if (espera == null) "Demasiados intentos. Intenta más tarde."
           else "Demasiados intentos. Espera ${espera} s."
    503 -> "El servicio facial no está disponible. Puedes ingresar con tu contraseña."
    else -> "No se pudo completar la verificación. Intenta de nuevo."
}

private suspend fun ImageCapture.capturarJpeg(): String = suspendCancellableCoroutine { continuation ->
    takePicture(
        Dispatchers.Default.asExecutor(),
        object : ImageCapture.OnImageCapturedCallback() {
            override fun onCaptureSuccess(image: ImageProxy) {
                try {
                    if (continuation.isActive) continuation.resume(codificarJpeg(image))
                } catch (error: RuntimeException) {
                    continuation.resumeWithException(IllegalArgumentException("Captura inválida", error))
                } finally {
                    image.close()
                }
            }

            override fun onError(exception: ImageCaptureException) {
                continuation.resumeWithException(exception)
            }
        }
    )
}

private fun codificarJpeg(image: ImageProxy): String {
    val bitmap = image.toBitmap()
    val factor = minOf(1f, 960f / maxOf(bitmap.width, bitmap.height))
    val matriz = Matrix().apply {
        postScale(factor, factor)
        postRotate(image.imageInfo.rotationDegrees.toFloat())
    }
    val ajustada = Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matriz, true)
    try {
        val buffer = ByteArrayOutputStream()
        check(ajustada.compress(Bitmap.CompressFormat.JPEG, 75, buffer))
        return Base64.encodeToString(buffer.toByteArray(), Base64.NO_WRAP)
    } finally {
        if (ajustada !== bitmap) ajustada.recycle()
        bitmap.recycle()
    }
}
