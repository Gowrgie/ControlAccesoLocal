package com.controlacceso.appmovil.data

import com.google.gson.annotations.SerializedName
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

data class FaceChallengeRequest(
    @SerializedName("front_sha256") val frontSha256: String
)

data class FaceChallenge(
    @SerializedName("challenge_id") val id: String,
    val direction: String
)

data class FaceSessionRequest(
    @SerializedName("challenge_id") val challengeId: String,
    @SerializedName("front_image") val frontImage: String,
    @SerializedName("tilted_image") val tiltedImage: String
)

interface FaceSessionApi {
    @POST("sessions/face/challenge")
    suspend fun createChallenge(@Body request: FaceChallengeRequest): Response<FaceChallenge>

    @POST("sessions/face")
    suspend fun login(@Body request: FaceSessionRequest): Response<SessionResponse>
}
