package com.controlacceso.appmovil.data

import com.google.gson.annotations.SerializedName

data class AccessRequestCreate(
    @SerializedName("request_id") val requestId: String
)

data class AccessRequestStatus(
    @SerializedName("request_id") val requestId: String,
    val state: String,    // "present" | "pending" | "busy" | "complete" | "expired"
    val result: String?   // "autorizado" | "sin_permiso" | "no_reconocido" | "error_sistema" | null
)