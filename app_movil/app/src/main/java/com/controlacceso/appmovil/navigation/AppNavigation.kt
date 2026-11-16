package com.controlacceso.appmovil.navigation


import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.controlacceso.appmovil.ui.IdentificationScreen
import com.controlacceso.appmovil.ui.RequestScreen
import com.controlacceso.appmovil.ui.ResultScreen

object Routes {
    const val IDENTIFICATION = "identification"
    const val REQUEST = "request"
    const val RESULT = "result"
}

@Composable
fun AppNavigation(navController: NavHostController = rememberNavController()) {
    NavHost(navController = navController, startDestination = Routes.IDENTIFICATION) {
        composable(Routes.IDENTIFICATION) {
            IdentificationScreen(onLoggedIn = { navController.navigate(Routes.REQUEST) })
        }
        composable(Routes.REQUEST) {
            RequestScreen(
                presenceDetected = false,
                onRequestAccess = { navController.navigate(Routes.RESULT) }
            )
        }
        composable(Routes.RESULT) {
            ResultScreen(
                result = "pending",
                onReturnToStandby = {
                    navController.popBackStack(Routes.IDENTIFICATION, inclusive = false)
                }
            )
        }
    }
}