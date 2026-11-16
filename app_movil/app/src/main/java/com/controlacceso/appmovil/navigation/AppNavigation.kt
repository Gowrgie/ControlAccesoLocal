package com.controlacceso.appmovil.navigation

import android.os.SystemClock
import androidx.activity.compose.BackHandler
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.controlacceso.appmovil.data.AccessRequestCreate
import com.controlacceso.appmovil.data.ApiClient
import com.controlacceso.appmovil.ui.IdentificationScreen
import com.controlacceso.appmovil.ui.RequestScreen
import com.controlacceso.appmovil.ui.ResultScreen
import java.io.IOException
import java.util.UUID
import kotlinx.coroutines.delay
import android.util.Log
import androidx.compose.runtime.rememberCoroutineScope
import kotlinx.coroutines.launch

object Routes {
    const val IDENTIFICATION = "identification"
    const val REQUEST = "request"
    const val RESULT = "result"
}

@Composable
fun AppNavigation(navController: NavHostController = rememberNavController()) {
    var tokenSesion by remember { mutableStateOf<String?>(null) }
    var solicitudId by remember { mutableStateOf<String?>(null) }
    var envioIntentado by remember { mutableStateOf(false) }

    val scope = rememberCoroutineScope()

    fun volverAlInicio() {
        val token = tokenSesion

        tokenSesion = null
        solicitudId = null
        envioIntentado = false
        navController.popBackStack(Routes.IDENTIFICATION, inclusive = false)

        if (token != null) {
            scope.launch {
                try {
                    val respuesta = ApiClient.service.logout("Bearer $token")
                    Log.i("ControlAccesoSesion", "Cierre de sesión HTTP ${respuesta.code()}")
                } catch (_: IOException) {
                    Log.w("ControlAccesoSesion", "La Raspberry Pi no confirmó el cierre de sesión")
                }
            }
        }
    }
    NavHost(
        navController = navController,
        startDestination = Routes.IDENTIFICATION
    ) {
        composable(Routes.IDENTIFICATION) {
            IdentificationScreen(onLoggedIn = { token ->
                tokenSesion = token
                solicitudId = null
                envioIntentado = false
                navController.navigate(Routes.REQUEST)
            })
        }

        composable(Routes.REQUEST) {
            val token = tokenSesion
            if (token == null) {
                LaunchedEffect(Unit) {
                    navController.popBackStack(Routes.IDENTIFICATION, inclusive = false)
                }
                return@composable
            }
            BackHandler { volverAlInicio() }
            

            var presenciaDetectada by remember(token) { mutableStateOf(false) }
            var mensajePresencia by remember(token) { mutableStateOf<String?>(null) }

            LaunchedEffect(token) {
                while (true) {
                    var esperaMs = 1_000L

                    try {
                        val respuesta = ApiClient.service.getPresence("Bearer $token")

                        when (respuesta.code()) {
                            200 -> {
                                presenciaDetectada = respuesta.body()?.present == true
                                mensajePresencia = null
                            }
                            401 -> {
                                tokenSesion = null
                                return@LaunchedEffect
                            }
                            429 -> {
                                presenciaDetectada = false
                                mensajePresencia = "Esperando para volver a consultar el PIR."
                                val segundos = respuesta.headers()["Retry-After"]
                                    ?.toLongOrNull()
                                    ?.coerceAtLeast(1L) ?: 1L
                                esperaMs = segundos * 1_000L
                            }
                            503 -> {
                                presenciaDetectada = false
                                mensajePresencia = "El PIR todavía no está disponible."
                            }
                            else -> {
                                presenciaDetectada = false
                                mensajePresencia = "No se pudo consultar el PIR."
                            }
                        }
                    } catch (_: IOException) {
                        presenciaDetectada = false
                        mensajePresencia = "No se pudo conectar con la Raspberry Pi."
                    }

                    delay(esperaMs)
                }
            }

            RequestScreen(
                presenceDetected = presenciaDetectada,
                mensajePresencia = mensajePresencia,
                onRequestAccess = {
                    if (presenciaDetectada && solicitudId == null) {
                        solicitudId = UUID.randomUUID().toString()
                        envioIntentado = false
                        navController.navigate(Routes.RESULT) {
                            launchSingleTop = true
                        }
                    }
                }
            )
        }

        composable(Routes.RESULT) {
            val token = tokenSesion
            val id = solicitudId
            if (token == null || id == null) {
                LaunchedEffect(Unit) {
                    navController.popBackStack(Routes.IDENTIFICATION, inclusive = false)
                }
                return@composable
            }

            var resultado by remember(id) { mutableStateOf("pending") }
            var mensaje by remember(id) { mutableStateOf<String?>(null) }
            var procesando by remember(id) { mutableStateOf(true) }
            var puedeConsultar by remember(id) { mutableStateOf(false) }
            var revision by remember(id) { mutableStateOf(0) }

            val bearer = "Bearer $token"



            BackHandler {
                if (!procesando) {
                    volverAlInicio()
                }
            }

            LaunchedEffect(token, id, revision) {
                procesando = true
                puedeConsultar = false
                resultado = "pending"
                mensaje = null

                try {
                    if (!envioIntentado) {
                        envioIntentado = true
                        val envio = try {
                            ApiClient.service.createAccessRequest(
                                bearer,
                                AccessRequestCreate(id)
                            )
                        } catch (_: IOException) {
                            null
                        }

                        when (envio?.code()) {
                            null, 202, 409 -> Unit
                            401 -> {
                                resultado = "error_sistema"
                                mensaje = "La sesión venció. Vuelve a iniciar sesión."
                                return@LaunchedEffect
                            }
                            403 -> {
                                resultado = "error_sistema"
                                mensaje = "La Raspberry Pi rechazó la solicitud. Comprueba la presencia y tu sesión."
                                return@LaunchedEffect
                            }
                            429 -> {
                                resultado = "error_sistema"
                                val segundos = envio?.headers()?.get("Retry-After")
                                mensaje = if (segundos != null) {
                                    "Demasiadas solicitudes. Espera $segundos segundos."
                                } else {
                                    "Demasiadas solicitudes. Espera antes de intentar de nuevo."
                                }
                                return@LaunchedEffect
                            }
                            else -> {
                                resultado = "error_sistema"
                                mensaje = "No se pudo confirmar el envío de la solicitud."
                                puedeConsultar = true
                                return@LaunchedEffect
                            }
                        }
                    }

                    val limite = SystemClock.elapsedRealtime() + 20_000L
                    while (SystemClock.elapsedRealtime() < limite) {
                        var esperaMs = 1_000L
                        val respuesta = try {
                            ApiClient.service.getAccessRequestStatus(bearer, id)
                        } catch (_: IOException) {
                            null
                        }

                        when (respuesta?.code()) {
                            200 -> {
                                val estado = respuesta?.body()
                                when (estado?.state) {
                                    "complete" -> {
                                        resultado = estado?.result ?: "error_sistema"
                                        mensaje = null
                                        return@LaunchedEffect
                                    }
                                    "expired" -> {
                                        resultado = "expired"
                                        mensaje = null
                                        return@LaunchedEffect
                                    }
                                    "busy" -> {
                                        mensaje = "El controlador está ocupado. Tu solicitud sigue en cola."
                                    }
                                    else -> mensaje = "Procesando…"
                                }
                            }
                            401 -> {
                                resultado = "error_sistema"
                                mensaje = "La sesión venció. Vuelve a iniciar sesión."
                                return@LaunchedEffect
                            }
                            403 -> {
                                resultado = "error_sistema"
                                mensaje = "Esta sesión no puede consultar la solicitud."
                                return@LaunchedEffect
                            }
                            429 -> {
                                val segundos = respuesta?.headers()?.get("Retry-After")
                                    ?.toLongOrNull()
                                    ?.coerceIn(1L, 60L) ?: 1L
                                esperaMs = segundos * 1_000L
                                mensaje = "Esperando para volver a consultar el estado."
                            }
                        }

                        val restanteMs = limite - SystemClock.elapsedRealtime()
                        if (restanteMs > 0) {
                            delay(minOf(esperaMs, restanteMs))
                        }
                    }

                    resultado = "error_sistema"
                    mensaje = "Aún no se pudo confirmar el resultado. Consulta el estado de la misma solicitud."
                    puedeConsultar = true
                } finally {
                    procesando = false
                }
            }

            ResultScreen(
                result = resultado,
                mensajeEstado = mensaje,
                procesando = procesando,
                onConsultarEstado = if (puedeConsultar) {
                    {
                        procesando = true
                        revision += 1
                    }
                } else {
                    null
                },
                onReturnToStandby = ::volverAlInicio
            )
        }
    }
}