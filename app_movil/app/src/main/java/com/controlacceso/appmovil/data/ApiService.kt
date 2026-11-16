package com.controlacceso.appmovil.data

import retrofit2.Response
import retrofit2.http.*

interface ApiService {

    @POST("sessions")
    suspend fun login(@Body request: LoginRequest): Response<SessionResponse>

    @DELETE("sessions")
    suspend fun logout(@Header("Authorization") bearerToken: String): Response<Unit>

    @GET("presence")
    suspend fun getPresence(@Header("Authorization") bearerToken: String): Response<PresenceResponse>

    @POST("access-requests")
    suspend fun createAccessRequest(
        @Header("Authorization") bearerToken: String,
        @Body request: AccessRequestCreate
    ): Response<AccessRequestStatus>

    @GET("access-requests/{requestId}")
    suspend fun getAccessRequestStatus(
        @Header("Authorization") bearerToken: String,
        @Path("requestId") requestId: String
    ): Response<AccessRequestStatus>
}