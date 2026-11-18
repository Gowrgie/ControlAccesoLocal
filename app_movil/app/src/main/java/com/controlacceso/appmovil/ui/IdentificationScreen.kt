package com.controlacceso.appmovil.ui

import androidx.activity.compose.LocalActivity
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.fragment.app.FragmentActivity
import com.controlacceso.appmovil.data.ApiClient
import com.controlacceso.appmovil.data.BiometricChallengeRequest
import com.controlacceso.appmovil.data.BiometricSessionRequest
import com.controlacceso.appmovil.data.DeviceBiometrics
import com.controlacceso.appmovil.data.ErrorBiometrico
import com.controlacceso.appmovil.data.LoginRequest
import java.io.IOException
import java.net.UnknownHostException
import java.security.GeneralSecurityException
import java.security.ProviderException
import javax.net.ssl.SSLException
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch

@Composable
fun IdentificationScreen(onLoggedIn: (String) -> Unit) {
    val context = LocalContext.current
    val activity = LocalActivity.current as? FragmentActivity
    val biometria = remember(context) { DeviceBiometrics(context) }
    val disponible = activity != null && biometria.disponible(context)
    var vinculada by remember(biometria) { mutableStateOf(biometria.vinculada()) }
    var activarBiometria by remember { mutableStateOf(false) }
    var identificador by remember { mutableStateOf("") }
    var clave by remember { mutableStateOf("") }
    var cargando by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()

    fun iniciar(operacion: suspend () -> String?) {
        if (cargando) return
        cargando = true
        error = null
        scope.launch {
            try {
                val token = operacion()
                if (!token.isNullOrBlank()) {
                    clave = ""
                    onLoggedIn(token)
                }
            } catch (_: UnknownHostException) {
                error = "No se encontró raspberrypi.local en la red."
            } catch (_: SSLException) {
                error = "No se pudo verificar la conexión HTTPS con la Raspberry Pi."
            } catch (_: IOException) {
                error = "No se pudo conectar con la Raspberry Pi."
            } catch (problema: ErrorBiometrico) {
                error = problema.message
            } catch (_: GeneralSecurityException) {
                error = "No se pudo usar la clave del teléfono. Ingresa con tu contraseña para volver a activar la biometría."
            } catch (_: ProviderException) {
                error = "El teléfono no pudo usar la biometría. Puedes ingresar con tu contraseña."
            } catch (cancelacion: CancellationException) {
                throw cancelacion
            } catch (_: IllegalStateException) {
                error = "No se pudo completar el inicio biométrico. Puedes ingresar con tu contraseña."
            } finally {
                cargando = false
            }
        }
    }

    Column(
        modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp),
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

        if (disponible) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Checkbox(
                    checked = activarBiometria,
                    onCheckedChange = { activarBiometria = it },
                    enabled = !cargando
                )
                Text("Activar biometría en este teléfono")
            }
        } else {
            Text(
                "La biometría fuerte no está disponible en este teléfono.",
                style = MaterialTheme.typography.bodySmall
            )
        }

        error?.let { mensaje -> Text(mensaje, color = MaterialTheme.colorScheme.error) }
        Spacer(modifier = Modifier.height(16.dp))

        Button(
            modifier = Modifier.fillMaxWidth(),
            enabled = !cargando && identificador.isNotBlank() && clave.isNotBlank(),
            onClick = {
                iniciar {
                    val nueva = if (activarBiometria && disponible) biometria.crearClave() else null
                    var guardada = false
                    try {
                        val respuesta = ApiClient.service.login(
                            LoginRequest(identificador.trim(), clave, nueva?.publica)
                        )
                        val sesion = respuesta.body()
                        if (!respuesta.isSuccessful || sesion?.token.isNullOrBlank()) {
                            error = mensajeLogin(respuesta.code(), biometrico = false)
                            return@iniciar null
                        }
                        if (nueva != null) {
                            val id = sesion?.biometricCredentialId
                            if (id.isNullOrBlank()) {
                                error = "El servidor no confirmó el vínculo biométrico. Puedes entrar con tu contraseña."
                                activarBiometria = false
                                return@iniciar null
                            }
                            biometria.guardar(id, nueva.alias)
                            guardada = true
                            vinculada = biometria.vinculada()
                        }
                        sesion?.token
                    } finally {
                        if (nueva != null && !guardada) biometria.descartar(nueva.alias)
                    }
                }
            }
        ) {
            Text(if (cargando) "Verificando…" else "Ingresar con ID y contraseña")
        }

        val credencial = vinculada
        if (activity != null && disponible && credencial != null) {
            OutlinedButton(
                onClick = {
                    clave = ""
                    iniciar {
                        val reto = ApiClient.service.createBiometricChallenge(
                            BiometricChallengeRequest(credencial.id)
                        )
                        val valor = reto.body()?.challenge
                        if (!reto.isSuccessful || valor.isNullOrBlank()) {
                            error = mensajeLogin(reto.code(), biometrico = true)
                            return@iniciar null
                        }
                        val firma = biometria.firmar(activity, credencial.alias, valor)
                        val respuesta = ApiClient.service.loginBiometrically(
                            BiometricSessionRequest(valor, firma)
                        )
                        val token = respuesta.body()?.token
                        if (!respuesta.isSuccessful || token.isNullOrBlank()) {
                            error = mensajeLogin(respuesta.code(), biometrico = true)
                            return@iniciar null
                        }
                        token
                    }
                },
                enabled = !cargando,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Ingresar con biometría")
            }
        }
    }
}

private fun mensajeLogin(codigo: Int, biometrico: Boolean): String = when (codigo) {
    401 -> if (biometrico) "La credencial biométrica no es válida. Reintenta o usa tu contraseña."
           else "Identificador o clave incorrectos."
    429 -> "Demasiados intentos. Espera antes de volver a intentar."
    503 -> "El servicio de autenticación no está disponible."
    else -> "No se pudo iniciar sesión."
}
