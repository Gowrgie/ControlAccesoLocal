package com.controlacceso.appmovil.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun RequestScreen(
    presenceDetected: Boolean = false,
    mensajePresencia: String? = null,
    onRequestAccess: () -> Unit
) {
    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.Center
    ) {
        Text(text = "Solicitud de acceso", style = MaterialTheme.typography.headlineSmall)
        Spacer(modifier = Modifier.height(16.dp))
        Text(
            text = mensajePresencia ?: if (presenceDetected) {
                "Presencia detectada"
            } else {
                "Esperando presencia (PIR)"
            }
        )
        Spacer(modifier = Modifier.height(16.dp))
        Button(
            onClick = onRequestAccess,
            enabled = presenceDetected,
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Solicitar acceso")
        }
    }
}