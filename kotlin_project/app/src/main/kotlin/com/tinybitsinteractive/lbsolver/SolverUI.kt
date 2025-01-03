package com.tinybitsinteractive.lbsolver

import android.util.Log
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.border
import androidx.compose.foundation.focusable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.Text
import androidx.compose.material3.TextField
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.key.KeyEventType
import androidx.compose.ui.input.key.key
import androidx.compose.ui.input.key.type
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.TextRange
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.TextFieldValue
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tinybitsinteractive.lbsolver.ui.theme.LetterboxedSolverTheme
import com.tinybitsinteractive.lbsolverlib.Solver
import androidx.compose.ui.input.key.Key
import androidx.compose.ui.input.key.onPreviewKeyEvent

@Composable
fun SolverUI(modifier: Modifier = Modifier, preview: Boolean = false) {
    var sidesTFV by remember {
        // start with example puzzle to make it easy to try out
        mutableStateOf(TextFieldValue(""))
    }
    val logTag = "SolverUI"
    val exampleSolutions by lazy { "lorem -> ipsum\n".repeat(3) }
    var solutions by remember { mutableStateOf(if (preview) exampleSolutions else "") }
    var solutionsLabel by remember { mutableStateOf("Solutions:") }
    var working by remember { mutableStateOf(false) }
    var useNative by remember { mutableStateOf(false) }
    val context = LocalContext.current
    val solver by remember {
        val solver = mutableStateOf(Solver())
        solver.value.setup(context.cacheDir.toPath()) {
            errMsg, elapsed ->
            errMsg?.let {
                Log.e(logTag, it)
                true
            } ?: run {
                Log.i(logTag, "setup finished in ${elapsed}")
            }
        }
        solver
    }

    Column(
        modifier = modifier
    ) {
        Text(
            modifier = Modifier
                .height(28.dp)
                .align(Alignment.CenterHorizontally)
                .padding(bottom = 8.dp),
            fontWeight = FontWeight.Bold,
            fontSize = 20.sp,
            text = "Letterboxed Solver"
        )
        Row (
            modifier = Modifier
                .align(Alignment.CenterHorizontally)
        )
        {
            val solveEnabled = !working && sidesTFV.text.length == 15
            fun solve() {
                if (!solveEnabled) {
                    return
                }
                synchronized(solutions) {
                    solutions = ""
                    solutionsLabel = "Solutions:"
                    working = true
                }
                solver.solve(if (useNative) Solver.Type.Native else Solver.Type.Kotlin, sidesTFV.text) {
                        results, elapsed ->
                    val s = results ?: ""
                    var resultCount = s.count{ c -> c == '\n' }
                    if (s != "" && !s.endsWith('\n')) {
                        resultCount += 1
                    }
                    synchronized(solutions) {
                        elapsed?.let {
                            solutionsLabel = "$resultCount Solutions found in $it:"
                            solutions = s
                            true
                        } ?: run {
                            solutionsLabel = s
                        }
                        working = false
                    }
                }
            }

            TextField(
                modifier = Modifier
                    .align(Alignment.CenterVertically)
                    .width(width = (15 * 12).dp)
                    // https://stackoverflow.com/questions/73165141/jetpack-compose-capture-keydown-key-event-in-text-field
                    // onKeyEvent doesn't capture key down. ugh.
                    .focusable().onPreviewKeyEvent {
                        event ->
                        if (event.type == KeyEventType.KeyDown && (event.key == Key.Enter || event.key == Key.NumPadEnter)) {
                            solve()
                            true
                        }
                        else {
                            false
                        }
                    }
                ,
                label = { Text(text = "Enter Puzzle Sides") },
                value = sidesTFV,
                onValueChange = { tfv ->
                    val cleaned = Solver.cleanSides(tfv.text)
                    sidesTFV = TextFieldValue(
                        cleaned,
                        TextRange(cleaned.length)
                    )
                }
            )

            val clear = {
                synchronized(solutions) {
                    solutions = ""
                    working = false
                    sidesTFV = TextFieldValue()
                }
            }

            Column(
                modifier = Modifier
                    .align(Alignment.CenterVertically)
            ) {
                Button(
                    modifier = Modifier
                        .align(Alignment.CenterHorizontally)
                        .padding(start = 8.dp),
                    onClick = { solve() },
                    enabled = solveEnabled,
                    content = {
                        Text("solve")
                    }
                )
                Button(
                    modifier = Modifier
                        .align(Alignment.CenterHorizontally)
                        .padding(start = 8.dp),
                    onClick = clear,
                    enabled = true,
                    content = {
                        Text("clear")
                    }
                )
                Row {
                    Checkbox(
                        onCheckedChange = { useNative = it },
                        checked = useNative,
                    )
                    Text("native")
                }
            }
        }
        synchronized(solutions) {
            Column(
                modifier = Modifier
                    .padding(horizontal = 4.dp)
                    .padding(top = 4.dp)
            ) {
                val mod = Modifier
                    .padding(start = 5.dp)
                    .fillMaxWidth()
                Text(solutionsLabel,
                    modifier = Modifier
                        .height(30.dp),
                    fontWeight = FontWeight.Bold
                )
                if (working) {
                    WorkingIndicator(label = "Working ",
                        modifier = mod.border(width = 1.dp, color = Color(0.0f, 0.0f, 0.0f)))
                } else {
                    Text(
                        solutions,
                        modifier = mod
                            .verticalScroll(rememberScrollState())
                    )
                }
            }
        }
    }
}

@Composable
fun WorkingIndicator(label: String, modifier: Modifier) {
    val barLength = 12
    val trans = rememberInfiniteTransition(label = "stepTransition")
    val fstep by trans.animateFloat(
        initialValue = 0.0f,
        targetValue = barLength.toFloat(),
        animationSpec = infiniteRepeatable(
            animation = tween(600),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "stepValue"
    )
    val istep = (fstep + 0.5f).toInt()
    Text(
        text = label + "=".repeat(istep)
                + "(*)"
                + "=".repeat(barLength - istep),
        modifier = modifier
    )
}

@Preview(showBackground = true)
@Composable
fun SolverUIPreview() {
    LetterboxedSolverTheme {
        SolverUI(preview = true)
    }
}