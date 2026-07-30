package luoos.android.ui.apps

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import luoos.android.LuoOSApp
import luoos.android.models.LuoMemory
import luoos.android.ui.theme.LuoColors
import java.text.SimpleDateFormat
import java.util.*

/**
 * CellsScreen — a real, browsable view of the AI's stored memory entries
 * (the same data written by LuoTools' "remember" tool and read by
 * "recall"), not a fabricated visualization. Each row is an actual row
 * from the memory database.
 */
@Composable
fun CellsScreen() {
    val context = LocalContext.current
    val db = remember { (context.applicationContext as LuoOSApp).database }
    val memories by db.memoryDao().getAllFlow().collectAsState(initial = emptyList())

    Column(Modifier.fillMaxSize().background(LuoColors.background)) {
        Column(Modifier.padding(20.dp, 16.dp, 20.dp, 8.dp)) {
            Text("Cells", fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold,
                 fontSize = 20.sp, color = LuoColors.textBright)
            Spacer(Modifier.height(4.dp))
            Text(
                "${memories.size} stored ${if (memories.size == 1) "memory" else "memories"}",
                fontFamily = FontFamily.Monospace, fontSize = 12.sp, color = LuoColors.textDim
            )
        }

        if (memories.isEmpty()) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text(
                    "No memories stored yet.\nAsk Luo to remember something in Chat.",
                    fontFamily = FontFamily.Monospace, fontSize = 12.sp, color = LuoColors.textDim,
                    textAlign = androidx.compose.ui.text.style.TextAlign.Center
                )
            }
        } else {
            LazyColumn(Modifier.fillMaxSize().padding(horizontal = 12.dp)) {
                items(memories, key = { it.id }) { memory ->
                    CellRow(memory)
                }
            }
        }
    }
}

@Composable
private fun CellRow(memory: LuoMemory) {
    val dateStr = remember(memory.timestamp) {
        SimpleDateFormat("MMM d, HH:mm", Locale.getDefault()).format(Date(memory.timestamp))
    }
    Column(
        Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp)
            .background(LuoColors.card, RoundedCornerShape(10.dp))
            .padding(14.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                memory.tag, fontFamily = FontFamily.Monospace, fontSize = 11.sp,
                color = LuoColors.accent2,
                modifier = Modifier
                    .background(LuoColors.accent2.copy(alpha = 0.15f), RoundedCornerShape(6.dp))
                    .padding(6.dp, 2.dp)
            )
            Spacer(Modifier.weight(1f))
            Text(dateStr, fontFamily = FontFamily.Monospace, fontSize = 10.sp, color = LuoColors.textFaint)
        }
        Spacer(Modifier.height(6.dp))
        Text(memory.content, fontFamily = FontFamily.Monospace, fontSize = 13.sp, color = LuoColors.textNormal)
    }
}
