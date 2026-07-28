package luoos.android.ui.apps

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import luoos.android.ui.theme.LuoColors

/**
 * CalculatorScreen — a standard four-function calculator with percent and
 * sign-toggle, styled to match the rest of Luo OS.
 */
@Composable
fun CalculatorScreen() {
    var display by remember { mutableStateOf("0") }
    var pendingOperand by remember { mutableStateOf<Double?>(null) }
    var pendingOperator by remember { mutableStateOf<Char?>(null) }
    var startNewEntry by remember { mutableStateOf(false) }

    fun applyPending() {
        val current = display.toDoubleOrNull() ?: return
        val operand = pendingOperand
        val operator = pendingOperator
        if (operand != null && operator != null) {
            val result = when (operator) {
                '+' -> operand + current
                '-' -> operand - current
                '×' -> operand * current
                '÷' -> if (current != 0.0) operand / current else Double.NaN
                else -> current
            }
            display = formatResult(result)
        }
    }

    fun onDigit(d: String) {
        display = if (display == "0" || startNewEntry) d else display + d
        startNewEntry = false
    }

    fun onDecimal() {
        if (startNewEntry) { display = "0."; startNewEntry = false; return }
        if (!display.contains(".")) display += "."
    }

    fun onOperator(op: Char) {
        applyPending()
        pendingOperand = display.toDoubleOrNull()
        pendingOperator = op
        startNewEntry = true
    }

    fun onEquals() {
        applyPending()
        pendingOperand = null
        pendingOperator = null
        startNewEntry = true
    }

    fun onClear() {
        display = "0"
        pendingOperand = null
        pendingOperator = null
        startNewEntry = false
    }

    fun onToggleSign() {
        display = display.toDoubleOrNull()?.let { formatResult(-it) } ?: display
    }

    fun onPercent() {
        display = display.toDoubleOrNull()?.let { formatResult(it / 100.0) } ?: display
    }

    Column(
        Modifier.fillMaxSize().background(LuoColors.background).padding(16.dp)
    ) {
        // Display
        Box(
            Modifier.fillMaxWidth().weight(1f),
            contentAlignment = Alignment.BottomEnd
        ) {
            Text(
                display,
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Light,
                fontSize = 48.sp,
                color = LuoColors.textBright,
                textAlign = TextAlign.End,
                maxLines = 1
            )
        }

        Spacer(Modifier.height(16.dp))

        val rows = listOf(
            listOf("C" to CalcButtonType.FUNCTION, "±" to CalcButtonType.FUNCTION, "%" to CalcButtonType.FUNCTION, "÷" to CalcButtonType.OPERATOR),
            listOf("7" to CalcButtonType.DIGIT, "8" to CalcButtonType.DIGIT, "9" to CalcButtonType.DIGIT, "×" to CalcButtonType.OPERATOR),
            listOf("4" to CalcButtonType.DIGIT, "5" to CalcButtonType.DIGIT, "6" to CalcButtonType.DIGIT, "-" to CalcButtonType.OPERATOR),
            listOf("1" to CalcButtonType.DIGIT, "2" to CalcButtonType.DIGIT, "3" to CalcButtonType.DIGIT, "+" to CalcButtonType.OPERATOR),
            listOf("0" to CalcButtonType.DIGIT, "." to CalcButtonType.DIGIT, "=" to CalcButtonType.EQUALS)
        )

        rows.forEach { row ->
            Row(
                Modifier.fillMaxWidth().padding(vertical = 4.dp),
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                row.forEach { (label, type) ->
                    val weight = if (label == "0") 2f else 1f
                    CalcButton(
                        label = label,
                        type = type,
                        modifier = Modifier.weight(weight),
                        onClick = {
                            when (type) {
                                CalcButtonType.DIGIT -> if (label == ".") onDecimal() else onDigit(label)
                                CalcButtonType.OPERATOR -> onOperator(label[0])
                                CalcButtonType.EQUALS -> onEquals()
                                CalcButtonType.FUNCTION -> when (label) {
                                    "C" -> onClear()
                                    "±" -> onToggleSign()
                                    "%" -> onPercent()
                                }
                            }
                        }
                    )
                }
            }
        }
    }
}

private enum class CalcButtonType { DIGIT, OPERATOR, EQUALS, FUNCTION }

@Composable
private fun CalcButton(label: String, type: CalcButtonType, modifier: Modifier, onClick: () -> Unit) {
    val bg = when (type) {
        CalcButtonType.OPERATOR, CalcButtonType.EQUALS -> LuoColors.accent
        CalcButtonType.FUNCTION -> LuoColors.cardAlt
        CalcButtonType.DIGIT -> LuoColors.card
    }
    val fg = when (type) {
        CalcButtonType.OPERATOR, CalcButtonType.EQUALS -> LuoColors.background
        else -> LuoColors.textBright
    }
    Box(
        modifier
            .height(64.dp)
            .background(bg, CircleShape)
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        Text(label, fontFamily = FontFamily.Monospace, fontSize = 22.sp, color = fg)
    }
}

private fun formatResult(value: Double): String {
    if (value.isNaN() || value.isInfinite()) return "Error"
    return if (value == value.toLong().toDouble()) {
        value.toLong().toString()
    } else {
        // Trim trailing zeros but keep it readable
        "%.6f".format(value).trimEnd('0').trimEnd('.')
    }
}
