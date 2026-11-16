package com.controlacceso.appmovil.ui


import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun ResultScreen(
    result: String = "pending",
    onReturnToStandby: () -> Unit
) {
    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.Center
    ) {
        Text(text = "Resultado", style = MaterialTheme.typography.headlineSmall)
        Spacer(modifier = Modifier.height(16.dp))
        Text(text = mensajePara(result))
        Spacer(modifier = Modifier.height(16.dp))
        Button(onClick = onReturnToStandby, modifier = Modifier.fillMaxWidth()) {
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