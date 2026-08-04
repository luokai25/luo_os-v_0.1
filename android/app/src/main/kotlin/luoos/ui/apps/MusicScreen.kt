package luoos.android.ui.apps

import android.content.ContentUris
import android.media.MediaPlayer
import android.provider.MediaStore
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.MusicNote
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import luoos.android.ui.theme.LuoColors

data class LuoTrack(val id: Long, val title: String, val artist: String, val uri: android.net.Uri)

/**
 * MusicScreen — real playback of the device's own audio files via
 * MediaStore + MediaPlayer, both standard Android APIs. Lists whatever
 * music is actually on the device rather than shipping placeholder tracks.
 */
@Composable
fun MusicScreen() {
    val context = LocalContext.current
    val tracks = remember { queryDeviceTracks(context) }

    var currentTrack by remember { mutableStateOf<LuoTrack?>(null) }
    var isPlaying by remember { mutableStateOf(false) }
    var player by remember { mutableStateOf<MediaPlayer?>(null) }

    fun play(track: LuoTrack) {
        player?.release()
        val newPlayer = MediaPlayer().apply {
            setDataSource(context, track.uri)
            setOnPreparedListener { it.start() }
            setOnCompletionListener { isPlaying = false }
            prepareAsync()
        }
        player = newPlayer
        currentTrack = track
        isPlaying = true
    }

    fun togglePause() {
        val p = player ?: return
        if (p.isPlaying) { p.pause(); isPlaying = false } else { p.start(); isPlaying = true }
    }

    DisposableEffect(Unit) {
        onDispose { player?.release() }
    }

    Column(Modifier.fillMaxSize().background(LuoColors.background)) {
        Text("Music", fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold,
             fontSize = 20.sp, color = LuoColors.textBright,
             modifier = Modifier.padding(20.dp, 16.dp, 20.dp, 8.dp))

        if (tracks.isEmpty()) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("No audio files found on this device",
                     fontFamily = FontFamily.Monospace, fontSize = 13.sp, color = LuoColors.textDim)
            }
        } else {
            LazyColumn(Modifier.weight(1f).padding(horizontal = 12.dp)) {
                items(tracks, key = { it.id }) { track ->
                    TrackRow(
                        track = track,
                        isCurrent = track.id == currentTrack?.id,
                        onClick = { play(track) }
                    )
                }
            }
        }

        currentTrack?.let { track ->
            NowPlayingBar(track = track, isPlaying = isPlaying, onTogglePlay = { togglePause() })
        }
    }
}

@Composable
private fun TrackRow(track: LuoTrack, isCurrent: Boolean, onClick: () -> Unit) {
    Row(
        Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(
            Icons.Default.MusicNote, contentDescription = null,
            tint = if (isCurrent) LuoColors.accent else LuoColors.textDim,
            modifier = Modifier.size(20.dp)
        )
        Spacer(Modifier.width(12.dp))
        Column {
            Text(track.title, fontFamily = FontFamily.Monospace, fontSize = 14.sp,
                 color = if (isCurrent) LuoColors.accent else LuoColors.textNormal, maxLines = 1)
            Text(track.artist, fontFamily = FontFamily.Monospace, fontSize = 11.sp, color = LuoColors.textFaint, maxLines = 1)
        }
    }
}

@Composable
private fun NowPlayingBar(track: LuoTrack, isPlaying: Boolean, onTogglePlay: () -> Unit) {
    Row(
        Modifier.fillMaxWidth().background(LuoColors.card).padding(16.dp, 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(Modifier.weight(1f)) {
            Text(track.title, fontFamily = FontFamily.Monospace, fontSize = 13.sp, color = LuoColors.textBright, maxLines = 1)
            Text(track.artist, fontFamily = FontFamily.Monospace, fontSize = 11.sp, color = LuoColors.textDim, maxLines = 1)
        }
        Box(
            Modifier.size(40.dp).background(LuoColors.accent, CircleShape).clickable(onClick = onTogglePlay),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                if (isPlaying) Icons.Default.Pause else Icons.Default.PlayArrow,
                contentDescription = if (isPlaying) "Pause" else "Play",
                tint = LuoColors.background
            )
        }
    }
}

private fun queryDeviceTracks(context: android.content.Context): List<LuoTrack> {
    val tracks = mutableListOf<LuoTrack>()
    val projection = arrayOf(
        MediaStore.Audio.Media._ID,
        MediaStore.Audio.Media.TITLE,
        MediaStore.Audio.Media.ARTIST
    )
    val selection = "${MediaStore.Audio.Media.IS_MUSIC} != 0"

    context.contentResolver.query(
        MediaStore.Audio.Media.EXTERNAL_CONTENT_URI,
        projection, selection, null,
        "${MediaStore.Audio.Media.TITLE} ASC"
    )?.use { cursor ->
        val idCol = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media._ID)
        val titleCol = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media.TITLE)
        val artistCol = cursor.getColumnIndexOrThrow(MediaStore.Audio.Media.ARTIST)

        while (cursor.moveToNext()) {
            val id = cursor.getLong(idCol)
            val uri = ContentUris.withAppendedId(MediaStore.Audio.Media.EXTERNAL_CONTENT_URI, id)
            tracks.add(
                LuoTrack(
                    id = id,
                    title = cursor.getString(titleCol) ?: "Unknown",
                    artist = cursor.getString(artistCol) ?: "Unknown artist",
                    uri = uri
                )
            )
        }
    }
    return tracks
}
