package com.controlacceso.appmovil

import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.fragment.app.FragmentActivity
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.controlacceso.appmovil.navigation.AppNavigation
import com.controlacceso.appmovil.ui.theme.AppMovilTheme

private const val PERMISO_RED_LOCAL = "android.permission.ACCESS_LOCAL_NETWORK"

class MainActivity : FragmentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            AppMovilTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    Box(modifier = Modifier.padding(innerPadding)) {
                        AccesoARedLocal { AppNavigation() }
                    }
                }
            }
        }
    }
}

@Composable
private fun AccesoARedLocal(contenido: @Composable () -> Unit) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

    fun tienePermiso(): Boolean = Build.VERSION.SDK_INT < 37 ||
        ContextCompat.checkSelfPermission(context, PERMISO_RED_LOCAL) ==
        PackageManager.PERMISSION_GRANTED

    var permitido by remember { mutableStateOf(tienePermiso()) }
    val solicitar = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { concedido -> permitido = concedido }

    // Actualiza el estado si el usuario cambia el permiso desde Ajustes.
    DisposableEffect(lifecycleOwner, context) {
        val observador = LifecycleEventObserver { _, evento ->
            if (evento == Lifecycle.Event.ON_RESUME) permitido = tienePermiso()
        }
        lifecycleOwner.lifecycle.addObserver(observador)
        onDispose { lifecycleOwner.lifecycle.removeObserver(observador) }
    }

    if (permitido) {
        contenido()
    } else {
        Column(
            modifier = Modifier.fillMaxSize().padding(24.dp),
            verticalArrangement = Arrangement.Center
        ) {
            Text("Conectar con la Raspberry Pi", style = MaterialTheme.typography.headlineSmall)
            Spacer(Modifier.height(16.dp))
            Text("Permite el acceso a la red local para iniciar sesión y solicitar acceso.")
            Spacer(Modifier.height(16.dp))
            Button(onClick = { solicitar.launch(PERMISO_RED_LOCAL) }) {
                Text("Permitir acceso a la red local")
            }
            TextButton(onClick = {
                context.startActivity(Intent(
                    Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                    Uri.parse("package:" + context.packageName)
                ))
            }) {
                Text("Abrir permisos en Ajustes")
            }
        }
    }
}
