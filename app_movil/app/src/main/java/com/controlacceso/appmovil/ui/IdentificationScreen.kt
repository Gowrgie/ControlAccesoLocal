package com.controlacceso.appmovil.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.controlacceso.appmovil.data.ApiClient
import com.controlacceso.appmovil.data.LoginRequest
import java.io.IOException
import java.net.UnknownHostException
import javax.net.ssl.SSLException
import kotlinx.coroutines.launch

@Composable
fun IdentificationScreen(
    onLoggedIn: (String) -> Unit,
    onFaceCapture: () -> Unit
) {
    var identificador by remember { mutableStateOf("") }
    var clave by remember { mutableStateOf("") }
    var cargando by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()

    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.Center
    ) {
        Text("Identificación", style = MaterialTheme.typography.headlineSmall)
        Spacer(modifier = Modifier.height(16.dp))

        OutlinedTextField(
            value = identificador,
            onValueChange = { identificador = it },
            label = { Text("Identificador") },
            modifier = Modifier.fillMaxWidth(),
            enabled = !cargando,
            singleLine = true
        )

        Spacer(modifier = Modifier.height(8.dp))

        OutlinedTextField(
            value = clave,
            onValueChange = { clave = it },
            label = { Text("Clave") },
            modifier = Modifier.fillMaxWidth(),
            enabled = !cargando,
            singleLine = true,
            visualTransformation = PasswordVisualTransformation()
        )

        error?.let { mensaje ->
            Spacer(modifier = Modifier.height(8.dp))
            Text(mensaje, color = MaterialTheme.colorScheme.error)
        }

        Spacer(modifier = Modifier.height(16.dp))

        Button(
            modifier = Modifier.fillMaxWidth(),
            enabled = !cargando && identificador.isNotBlank() && clave.isNotBlank(),
            onClick = {
                cargando = true
                error = null
                scope.launch {
                    try {
                        val respuesta = ApiClient.service.login(
                            LoginRequest(identificador.trim(), clave)
                        )
                        val token = respuesta.body()?.token

                        if (respuesta.code() == 200 && token != null && token.isNotBlank()) {
                            clave = ""
                            onLoggedIn(token)
                        } else {
                            error = when (respuesta.code()) {
                                401 -> "Identificador o clave incorrectos."
                                429 -> "Demasiados intentos. Espera antes de volver a intentar."
                                503 -> "El servicio de autenticación no está disponible."
                                else -> "No se pudo iniciar sesión."
                            }
                        }
                    } catch (_: UnknownHostException) {
                        error = "No se encontró raspberrypi.local en la red."
                    } catch (_: SSLException) {
                        error = "No se pudo verificar la conexión HTTPS con la Raspberry Pi."
                    } catch (_: IOException) {
                        error = "No se pudo conectar con la Raspberry Pi."
                    } finally {
                        cargando = false
                    }
                }
            }
        ) {
            Text(if (cargando) "Verificando…" else "Ingresar con ID y contraseña")
        }

        OutlinedButton(
            onClick = {
                clave = ""
                error = null
                onFaceCapture()
            },
            enabled = !cargando,
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Ingresar con rostro")
        }
    }
}
