package com.controlacceso.appmovil.data

data class LoginRequest(
    val identificador: String,
    val clave: String
)

data class SessionResponse(
    val token: String,
    val expira: String
)

data class ErrorResponse(
    val error: String
)