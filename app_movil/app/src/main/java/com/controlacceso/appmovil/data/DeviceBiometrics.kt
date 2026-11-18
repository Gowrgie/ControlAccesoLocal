package com.controlacceso.appmovil.data

import android.content.Context
import android.os.Build
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import androidx.core.content.ContextCompat
import androidx.fragment.app.FragmentActivity
import java.security.KeyPairGenerator
import java.security.KeyStore
import java.security.PrivateKey
import java.security.Signature
import java.security.spec.ECGenParameterSpec
import java.util.UUID
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException
import kotlinx.coroutines.suspendCancellableCoroutine

class DeviceBiometrics(context: Context) {
    private val prefs = context.getSharedPreferences("device_biometrics", Context.MODE_PRIVATE)
    private val keyStore get() = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }

    fun disponible(context: Context): Boolean =
        BiometricManager.from(context).canAuthenticate(
            BiometricManager.Authenticators.BIOMETRIC_STRONG
        ) == BiometricManager.BIOMETRIC_SUCCESS

    fun vinculada(): CredencialBiometrica? {
        val id = prefs.getString("id", null) ?: return null
        val alias = prefs.getString("alias", null) ?: return null
        return CredencialBiometrica(id, alias)
    }

    fun crearClave(): ClaveBiometricaNueva {
        val alias = "control_acceso_" + UUID.randomUUID()
        val spec = KeyGenParameterSpec.Builder(alias, KeyProperties.PURPOSE_SIGN)
            .setAlgorithmParameterSpec(ECGenParameterSpec("secp256r1"))
            .setDigests(KeyProperties.DIGEST_SHA256)
            .setUserAuthenticationRequired(true)
            .setInvalidatedByBiometricEnrollment(true)

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            spec.setUserAuthenticationParameters(0, KeyProperties.AUTH_BIOMETRIC_STRONG)
        } else {
            @Suppress("DEPRECATION")
            spec.setUserAuthenticationValidityDurationSeconds(-1)
        }

        val generador = KeyPairGenerator.getInstance(KeyProperties.KEY_ALGORITHM_EC, "AndroidKeyStore")
        generador.initialize(spec.build())
        val publica = generador.generateKeyPair().public.encoded
        return ClaveBiometricaNueva(alias, Base64.encodeToString(publica, Base64.NO_WRAP))
    }

    fun guardar(id: String, alias: String) {
        val anterior = vinculada()
        check(prefs.edit().putString("id", id).putString("alias", alias).commit())
        if (anterior != null && anterior.alias != alias) {
            descartar(anterior.alias)
        }
    }

    fun descartar(alias: String) {
        runCatching { keyStore.deleteEntry(alias) }
    }

    suspend fun firmar(activity: FragmentActivity, alias: String, reto: String): String =
        suspendCancellableCoroutine { continuation ->
            val clave = keyStore.getKey(alias, null) as? PrivateKey
            if (clave == null) {
                continuation.resumeWithException(IllegalStateException("Vuelve a activar la biometría."))
                return@suspendCancellableCoroutine
            }
            val firma = Signature.getInstance("SHA256withECDSA").apply { initSign(clave) }
            val executor = ContextCompat.getMainExecutor(activity)
            val prompt = BiometricPrompt(activity, executor, object : BiometricPrompt.AuthenticationCallback() {
                override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                    if (!continuation.isActive) return
                    try {
                        val operacion = checkNotNull(result.cryptoObject?.signature)
                        operacion.update(reto.toByteArray(Charsets.US_ASCII))
                        continuation.resume(Base64.encodeToString(operacion.sign(), Base64.NO_WRAP))
                    } catch (error: Exception) {
                        continuation.resumeWithException(error)
                    }
                }

                override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                    if (continuation.isActive) {
                        continuation.resumeWithException(ErrorBiometrico(errString.toString()))
                    }
                }
            })
            continuation.invokeOnCancellation { executor.execute { prompt.cancelAuthentication() } }
            val info = BiometricPrompt.PromptInfo.Builder()
                .setTitle("Confirma tu identidad")
                .setAllowedAuthenticators(BiometricManager.Authenticators.BIOMETRIC_STRONG)
                .setNegativeButtonText("Usar contraseña")
                .build()
            prompt.authenticate(info, BiometricPrompt.CryptoObject(firma))
        }
}

data class ClaveBiometricaNueva(val alias: String, val publica: String)
data class CredencialBiometrica(val id: String, val alias: String)
class ErrorBiometrico(message: String) : Exception(message)
