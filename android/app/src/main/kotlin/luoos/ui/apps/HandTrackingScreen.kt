package luoos.android.ui.apps

import android.Manifest
import android.content.pm.PackageManager
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.compose.ui.platform.LocalLifecycleOwner
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.pose.Pose
import com.google.mlkit.vision.pose.PoseDetection
import com.google.mlkit.vision.pose.PoseLandmark
import com.google.mlkit.vision.pose.defaults.PoseDetectorOptions
import luoos.android.ui.theme.LuoColors
import java.util.concurrent.Executors

/**
 * HandTrackingScreen — a real, on-device pose/hand tracking view. ML Kit
 * does not offer a dedicated finger-level hand-landmark API on Android;
 * its Pose Detection API (33 full-body skeletal points, including wrists,
 * elbows, and other hand-relevant landmarks) is the genuinely supported,
 * on-device option, so this screen highlights specifically the hand/arm
 * landmarks from that skeleton rather than the full body.
 *
 * CameraX for the live feed, ML Kit's Pose Detection for the landmarks,
 * drawn over the preview — the same real, official Google API surface
 * used in PerceptionScreen, applied to a different detector.
 */
@Composable
fun HandTrackingScreen() {
    val context = LocalContext.current
    var hasCameraPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) ==
                PackageManager.PERMISSION_GRANTED
        )
    }
    val permissionLauncher = androidx.activity.compose.rememberLauncherForActivityResult(
        androidx.activity.result.contract.ActivityResultContracts.RequestPermission()
    ) { granted -> hasCameraPermission = granted }

    LaunchedEffect(Unit) {
        if (!hasCameraPermission) permissionLauncher.launch(Manifest.permission.CAMERA)
    }

    if (!hasCameraPermission) {
        PermissionPromptHand(
            message = "Hand Tracking needs camera access to detect hand/arm landmarks.",
            onRequest = { permissionLauncher.launch(Manifest.permission.CAMERA) }
        )
        return
    }

    // Hand-relevant landmark types from ML Kit's 33-point pose skeleton —
    // wrists, elbows, and finger/thumb/pinky tips on both sides.
    val handLandmarkTypes = remember {
        setOf(
            PoseLandmark.LEFT_WRIST, PoseLandmark.RIGHT_WRIST,
            PoseLandmark.LEFT_ELBOW, PoseLandmark.RIGHT_ELBOW,
            PoseLandmark.LEFT_THUMB, PoseLandmark.RIGHT_THUMB,
            PoseLandmark.LEFT_INDEX, PoseLandmark.RIGHT_INDEX,
            PoseLandmark.LEFT_PINKY, PoseLandmark.RIGHT_PINKY
        )
    }

    var landmarkPoints by remember { mutableStateOf<List<Offset>>(emptyList()) }
    var previewSize by remember { mutableStateOf(Pair(1, 1)) }

    Box(Modifier.fillMaxSize().background(LuoColors.background)) {
        PoseCameraPreview(
            handLandmarkTypes = handLandmarkTypes,
            onPoseDetected = { points, imgSize ->
                landmarkPoints = points
                previewSize = imgSize
            }
        )

        Canvas(Modifier.fillMaxSize()) {
            if (landmarkPoints.isEmpty() || previewSize.first == 0) return@Canvas
            val scaleX = size.width / previewSize.first
            val scaleY = size.height / previewSize.second
            landmarkPoints.forEach { p ->
                drawCircle(
                    color = Color(0xFF7C4DFF),
                    radius = 10f,
                    center = Offset(p.x * scaleX, p.y * scaleY)
                )
            }
        }

        Text(
            "Hand Tracking — ${landmarkPoints.size} points",
            fontFamily = FontFamily.Monospace, fontSize = 12.sp,
            color = LuoColors.textNormal,
            modifier = Modifier
                .align(Alignment.TopStart)
                .background(LuoColors.background.copy(alpha = 0.6f))
                .padding(10.dp, 6.dp)
        )
    }
}

@Composable
private fun PoseCameraPreview(
    handLandmarkTypes: Set<Int>,
    onPoseDetected: (List<Offset>, Pair<Int, Int>) -> Unit
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val executor = remember { Executors.newSingleThreadExecutor() }

    val detector = remember {
        PoseDetection.getClient(
            PoseDetectorOptions.Builder()
                .setDetectorMode(PoseDetectorOptions.STREAM_MODE)
                .build()
        )
    }

    AndroidView(
        modifier = Modifier.fillMaxSize(),
        factory = { ctx ->
            val previewView = PreviewView(ctx)
            val cameraProviderFuture = ProcessCameraProvider.getInstance(ctx)

            cameraProviderFuture.addListener({
                val cameraProvider = cameraProviderFuture.get()

                val preview = Preview.Builder().build().also {
                    it.setSurfaceProvider(previewView.surfaceProvider)
                }

                val analysis = ImageAnalysis.Builder()
                    .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                    .build()

                analysis.setAnalyzer(executor) { imageProxy ->
                    val mediaImage = imageProxy.image
                    if (mediaImage != null) {
                        val inputImage = InputImage.fromMediaImage(
                            mediaImage, imageProxy.imageInfo.rotationDegrees
                        )
                        detector.process(inputImage)
                            .addOnSuccessListener { pose: Pose ->
                                val points = pose.allPoseLandmarks
                                    .filter { it.landmarkType in handLandmarkTypes }
                                    .map { Offset(it.position.x, it.position.y) }
                                onPoseDetected(points, Pair(inputImage.width, inputImage.height))
                            }
                            .addOnCompleteListener { imageProxy.close() }
                    } else {
                        imageProxy.close()
                    }
                }

                try {
                    cameraProvider.unbindAll()
                    cameraProvider.bindToLifecycle(
                        lifecycleOwner,
                        CameraSelector.DEFAULT_BACK_CAMERA,
                        preview,
                        analysis
                    )
                } catch (e: Exception) {
                    // Binding can fail if the lifecycle is already destroyed
                    // by the time this listener fires — safe to ignore since
                    // the screen is going away anyway.
                }
            }, ContextCompat.getMainExecutor(ctx))

            previewView
        }
    )
}

@Composable
private fun PermissionPromptHand(message: String, onRequest: () -> Unit) {
    Box(
        Modifier.fillMaxSize().background(LuoColors.background).padding(32.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(message, fontFamily = FontFamily.Monospace, fontSize = 13.sp,
                 color = LuoColors.textNormal, textAlign = TextAlign.Center)
            Spacer(Modifier.height(16.dp))
            Button(onClick = onRequest, colors = ButtonDefaults.buttonColors(containerColor = LuoColors.accent)) {
                Text("Grant camera access", fontFamily = FontFamily.Monospace, color = LuoColors.background)
            }
        }
    }
}
