package luoos.android.ui.apps

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.ChevronLeft
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import luoos.android.ui.theme.LuoColors
import java.time.LocalDate
import java.time.YearMonth
import java.time.format.TextStyle
import java.util.Locale

data class LuoEvent(val date: LocalDate, val title: String)

/**
 * CalendarScreen — a plain local month-view calendar with tap-to-add
 * events, kept in-memory for now. Syncing with the device's real Calendar
 * app is a reasonable next step (this app already has the calendar_search_v0
 * and event_create_v1 tools available at the system level for the agent —
 * wiring this screen to the same underlying calendar is a natural
 * follow-up once a dedicated screen is confirmed useful on its own).
 */
@Composable
fun CalendarScreen() {
    var yearMonth by remember { mutableStateOf(YearMonth.now()) }
    var selectedDate by remember { mutableStateOf(LocalDate.now()) }
    var events by remember { mutableStateOf(listOf<LuoEvent>()) }
    var showAddDialog by remember { mutableStateOf(false) }

    Column(Modifier.fillMaxSize().background(LuoColors.background)) {
        MonthHeader(
            yearMonth = yearMonth,
            onPrev = { yearMonth = yearMonth.minusMonths(1) },
            onNext = { yearMonth = yearMonth.plusMonths(1) }
        )

        MonthGrid(
            yearMonth = yearMonth,
            selectedDate = selectedDate,
            eventDates = events.map { it.date }.toSet(),
            onSelect = { selectedDate = it }
        )

        Divider(color = LuoColors.subtleBorder)

        // Events for the selected day
        Row(
            Modifier.fillMaxWidth().padding(16.dp, 10.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                selectedDate.format(java.time.format.DateTimeFormatter.ofPattern("EEEE, MMM d")),
                fontFamily = FontFamily.Monospace, fontWeight = FontWeight.SemiBold,
                fontSize = 14.sp, color = LuoColors.textBright
            )
            Spacer(Modifier.weight(1f))
            IconButton(onClick = { showAddDialog = true }) {
                Icon(Icons.Default.Add, "Add event", tint = LuoColors.accent)
            }
        }

        val dayEvents = events.filter { it.date == selectedDate }
        if (dayEvents.isEmpty()) {
            Box(Modifier.fillMaxWidth().padding(16.dp)) {
                Text("No events", fontFamily = FontFamily.Monospace, fontSize = 12.sp, color = LuoColors.textDim)
            }
        } else {
            LazyColumn(Modifier.fillMaxWidth().padding(horizontal = 12.dp)) {
                items(dayEvents) { event ->
                    Text(
                        "• ${event.title}",
                        fontFamily = FontFamily.Monospace, fontSize = 13.sp,
                        color = LuoColors.textNormal,
                        modifier = Modifier.padding(vertical = 4.dp)
                    )
                }
            }
        }
    }

    if (showAddDialog) {
        AddEventDialog(
            date = selectedDate,
            onDismiss = { showAddDialog = false },
            onAdd = { title ->
                events = events + LuoEvent(selectedDate, title)
                showAddDialog = false
            }
        )
    }
}

@Composable
private fun MonthHeader(yearMonth: YearMonth, onPrev: () -> Unit, onNext: () -> Unit) {
    Row(
        Modifier.fillMaxWidth().padding(16.dp, 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        IconButton(onClick = onPrev) {
            Icon(Icons.Default.ChevronLeft, "Previous month", tint = LuoColors.accent)
        }
        Spacer(Modifier.weight(1f))
        Text(
            "${yearMonth.month.getDisplayName(TextStyle.FULL, Locale.getDefault())} ${yearMonth.year}",
            fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold,
            fontSize = 16.sp, color = LuoColors.textBright
        )
        Spacer(Modifier.weight(1f))
        IconButton(onClick = onNext) {
            Icon(Icons.Default.ChevronRight, "Next month", tint = LuoColors.accent)
        }
    }
}

@Composable
private fun MonthGrid(
    yearMonth: YearMonth,
    selectedDate: LocalDate,
    eventDates: Set<LocalDate>,
    onSelect: (LocalDate) -> Unit
) {
    val firstOfMonth = yearMonth.atDay(1)
    // Sunday = 7 in ISO; normalize so Sunday starts the week visually
    val leadingBlanks = firstOfMonth.dayOfWeek.value % 7
    val daysInMonth = yearMonth.lengthOfMonth()

    Column(Modifier.fillMaxWidth().padding(horizontal = 12.dp)) {
        Row(Modifier.fillMaxWidth()) {
            listOf("S", "M", "T", "W", "T", "F", "S").forEach { d ->
                Box(Modifier.weight(1f), contentAlignment = Alignment.Center) {
                    Text(d, fontFamily = FontFamily.Monospace, fontSize = 11.sp, color = LuoColors.textFaint)
                }
            }
        }

        val totalCells = leadingBlanks + daysInMonth
        val rowCount = (totalCells + 6) / 7

        for (row in 0 until rowCount) {
            Row(Modifier.fillMaxWidth()) {
                for (col in 0 until 7) {
                    val cellIndex = row * 7 + col
                    val dayNum = cellIndex - leadingBlanks + 1
                    Box(
                        Modifier.weight(1f).aspectRatio(1f).padding(2.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        if (dayNum in 1..daysInMonth) {
                            val date = yearMonth.atDay(dayNum)
                            val isSelected = date == selectedDate
                            val hasEvent = date in eventDates
                            Box(
                                Modifier
                                    .fillMaxSize()
                                    .background(
                                        if (isSelected) LuoColors.accent else LuoColors.card,
                                        CircleShape
                                    )
                                    .clickable { onSelect(date) },
                                contentAlignment = Alignment.Center
                            ) {
                                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                    Text(
                                        dayNum.toString(),
                                        fontFamily = FontFamily.Monospace, fontSize = 13.sp,
                                        color = if (isSelected) LuoColors.background else LuoColors.textNormal
                                    )
                                    if (hasEvent && !isSelected) {
                                        Box(
                                            Modifier.size(4.dp).background(LuoColors.accent2, CircleShape)
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun AddEventDialog(date: LocalDate, onDismiss: () -> Unit, onAdd: (String) -> Unit) {
    var text by remember { mutableStateOf("") }
    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = LuoColors.card,
        title = { Text("New event", fontFamily = FontFamily.Monospace, color = LuoColors.textBright) },
        text = {
            TextField(
                value = text,
                onValueChange = { text = it },
                placeholder = { Text("Event title", fontFamily = FontFamily.Monospace, color = LuoColors.textDim) },
                colors = TextFieldDefaults.colors(
                    focusedContainerColor = LuoColors.cardAlt,
                    unfocusedContainerColor = LuoColors.cardAlt,
                    focusedIndicatorColor = androidx.compose.ui.graphics.Color.Transparent,
                    unfocusedIndicatorColor = androidx.compose.ui.graphics.Color.Transparent,
                    cursorColor = LuoColors.accent
                )
            )
        },
        confirmButton = {
            TextButton(onClick = { if (text.isNotBlank()) onAdd(text.trim()) }) {
                Text("Add", color = LuoColors.accent, fontFamily = FontFamily.Monospace)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel", color = LuoColors.textDim, fontFamily = FontFamily.Monospace)
            }
        }
    )
}
