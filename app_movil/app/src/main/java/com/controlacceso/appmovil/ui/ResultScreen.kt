package com.controlacceso.appmovil.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.runtime.LaunchedEffect
import kotlinx.coroutines.delay

@Composable
fun ResultScreen(
    result: String = "pending",
    mensajeEstado: String? = null,
    procesando: Boolean = false,
    onConsultarEstado: (() -> Unit)? = null,
    onReturnToStandby: () -> Unit
) {
    // LAC-86: con un resultado definitivo (no está procesando, y no se le está
    // ofreciendo "Consultar estado"), regresa solo al inicio tras unos segundos.
    LaunchedEffect(procesando, onConsultarEstado) {
        if (!procesando && onConsultarEstado == null) {
            delay(6_000L)
            onReturnToStandby()
        }
    }

    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.Center
    ) {
        Text("Resultado", style = MaterialTheme.typography.headlineSmall)
        Spacer(modifier = Modifier.height(16.dp))
        Text(mensajeEstado ?: mensajePara(result))
        Spacer(modifier = Modifier.height(16.dp))

        if (onConsultarEstado != null) {
            Button(onClick = onConsultarEstado, enabled = !procesando) {
                Text("Consultar estado")
            }
            Spacer(modifier = Modifier.height(8.dp))
        }

        Button(onClick = onReturnToStandby, enabled = !procesando) {
            Text("Volver al inicio")
        }
    }
}

// FR-28: una falla técnica nunca se muestra como acceso denegado.
private fun mensajePara(result: String): String = when (result) {
    "autorizado" -> "Acceso autorizado"
    "sin_permiso" -> "Acceso denegado"
    "no_reconocido" -> "Usuario no reconocido"
    "error_sistema" -> "Falla técnica, intenta otro método"
    "expired" -> "La solicitud expiró, intenta de nuevo"
    else -> "Procesando…"
}