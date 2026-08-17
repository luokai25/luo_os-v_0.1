package luoos.android.ui.apps

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.PointF
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.compose.ui.platform.LocalLifecycleOwner
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.facemesh.FaceMesh
import com.google.mlkit.vision.facemesh.FaceMeshDetection
import com.google.mlkit.vision.facemesh.FaceMeshDetectorOptions
import luoos.android.ui.theme.LuoColors
import java.util.concurrent.Executors

/**
 * PerceptionScreen — a real, on-device face mesh view: CameraX for the live
 * feed, ML Kit's Face Mesh Detection API (468 points, fully offline) for
 * the actual landmark points, drawn over the preview.
 *
 * This uses Google's own official ML Kit API surface directly; nothing
 * here is derived from any other project's implementation.
 */
@Composable
fun PerceptionScreen() {
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
        PermissionPrompt(
            message = "Perception needs camera access to detect a live face mesh.",
            onRequest = { permissionLauncher.launch(Manifest.permission.CAMERA) }
        )
        return
    }

    var meshPoints by remember { mutableStateOf<List<PointF>>(emptyList()) }
    var previewSize by remember { mutableStateOf(Pair(1, 1)) }

    Box(Modifier.fillMaxSize().background(LuoColors.background)) {
        FaceMeshCameraPreview(
            onMeshDetected = { points, imgSize ->
                meshPoints = points
                previewSize = imgSize
            }
        )

        // Overlay the real detected mesh points on top of the live preview.
        Canvas(Modifier.fillMaxSize()) {
            if (meshPoints.isEmpty() || previewSize.first == 0) return@Canvas
            val scaleX = size.width / previewSize.first
            val scaleY = size.height / previewSize.second
            meshPoints.forEach { p ->
                drawCircle(
                    color = androidx.compose.ui.graphics.Color(0xFF4FC3F7),
                    radius = 1.6f,
                    center = Offset(p.x * scaleX, p.y * scaleY)
                )
            }
        }

        Text(
            "Perception — ${meshPoints.size} points",
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
private fun FaceMeshCameraPreview(onMeshDetected: (List<PointF>, Pair<Int, Int>) -> Unit) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val executor = remember { Executors.newSingleThreadExecutor() }

    val detector = remember {
        FaceMeshDetection.getClient(
            FaceMeshDetectorOptions.Builder()
                .setUseCase(FaceMeshDetectorOptions.FACE_MESH)
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
                            .addOnSuccessListener { meshes: List<FaceMesh> ->
                                val allPoints = meshes.flatMap { mesh ->
                                    mesh.allPoints.map { PointF(it.position.x, it.position.y) }
                                }
                                onMeshDetected(allPoints, Pair(inputImage.width, inputImage.height))
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
                        CameraSelector.DEFAULT_FRONT_CAMERA,
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
private fun PermissionPrompt(message: String, onRequest: () -> Unit) {
    Box(
        Modifier.fillMaxSize().background(LuoColors.background).padding(32.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(message, fontFamily = FontFamily.Monospace, fontSize = 13.sp,
                 color = LuoColors.textNormal, textAlign = androidx.compose.ui.text.style.TextAlign.Center)
            Spacer(Modifier.height(16.dp))
            Button(onClick = onRequest, colors = ButtonDefaults.buttonColors(containerColor = LuoColors.accent)) {
                Text("Grant camera access", fontFamily = FontFamily.Monospace, color = LuoColors.background)
            }
        }
    }
}
