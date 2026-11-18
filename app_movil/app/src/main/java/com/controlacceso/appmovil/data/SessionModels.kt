package com.controlacceso.appmovil.data

import com.google.gson.annotations.SerializedName

data class LoginRequest(
    val identificador: String,
    val clave: String,
    @SerializedName("biometric_public_key") val biometricPublicKey: String? = null
)

data class SessionResponse(
    val token: String,
    val expira: String,
    @SerializedName("biometric_credential_id") val biometricCredentialId: String? = null
)

data class ErrorResponse(
    val error: String
)

data class BiometricChallengeRequest(
    @SerializedName("credential_id") val credentialId: String
)

data class BiometricChallenge(val challenge: String)

data class BiometricSessionRequest(val challenge: String, val signature: String)
