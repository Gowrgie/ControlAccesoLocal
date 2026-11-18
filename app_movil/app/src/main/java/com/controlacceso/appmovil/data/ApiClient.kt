package com.controlacceso.appmovil.data

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object ApiClient {

    // Cambia esto por la IP o el nombre local real de la Raspberry Pi cuando la tengas.
    private const val BASE_URL = "https://raspberrypi.local:8000/"

    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BASIC
    }

    private val okHttpClient = OkHttpClient.Builder()
        .connectTimeout(2, TimeUnit.SECONDS)  // NFR-14: menos de 2 segundos por llamada
        .readTimeout(2, TimeUnit.SECONDS)
        .addInterceptor(loggingInterceptor)
        .build()

    private val retrofit by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    val service: ApiService by lazy { retrofit.create(ApiService::class.java) }

    val facial: FaceSessionApi by lazy {
        val client = okHttpClient.newBuilder()
            .readTimeout(12, TimeUnit.SECONDS)
            .writeTimeout(10, TimeUnit.SECONDS)
            .build()

        retrofit.newBuilder()
            .client(client)
            .build()
            .create(FaceSessionApi::class.java)
    }
}
