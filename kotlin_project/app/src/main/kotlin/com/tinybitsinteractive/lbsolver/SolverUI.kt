package com.tinybitsinteractive.lbsolver

import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.border
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.TextRange
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.TextFieldValue
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tinybitsinteractive.lbsolver.ui.theme.LetterboxedSolverTheme
import com.tinybitsinteractive.lbsolverlib.Solver

@Composable
fun SolverUI(modifier: Modifier = Modifier, preview: Boolean = false) {
    var sidesTFV by remember {
        // start with example puzzle to make it easy to try out
        mutableStateOf(TextFieldValue(""))
    }
    val exampleSolutions by lazy { "lorem -> ipsum\n".repeat(3) }
    var solutions by remember { mutableStateOf(if (preview) exampleSolutions else "") }
    var working by remember { mutableStateOf(false) }
    var nativeSolver by remember { mutableStateOf(false) }
    var wasNativeSolver by remember { mutableStateOf(false) }
    val context = LocalContext.current

    Column(
        modifier = modifier
    ) {
        Text(
            modifier = Modifier
                .height(40.dp)
                .align(Alignment.CenterHorizontally)
                .padding(bottom = 8.dp),
            fontWeight = FontWeight.Bold,
            fontSize = 24.sp,
            text = "Letterboxed Solver"
        )
        Row (
            modifier = Modifier
                .align(Alignment.CenterHorizontally)
        )
        {
            TextField(
                modifier = Modifier
                    .align(Alignment.CenterVertically)
                    .width(width = (15 * 12).dp)
                ,
                label = { Text(text = "Enter Puzzle Sides") },
                value = sidesTFV,
                onValueChange = { tfv ->
                    val cleaned = Solver.cleanSides(tfv.text)
                    sidesTFV = TextFieldValue(
                        cleaned,
                        TextRange(cleaned.length)
                    )
                    if (cleaned.length != 15) {
                        synchronized(solutions) {
                            solutions = ""
                            working = false
                        }
                    }
                }
            )

            val hasPuzzle = sidesTFV.text.length == 15
            val hasSolution = solutions.isNotEmpty()
            val isSolveButton = !hasSolution || wasNativeSolver != nativeSolver
            val buttonText = if (isSolveButton) "Solve" else "Clear"
            val solveOrClearEnabled = hasSolution or hasPuzzle
            val solve = {
                synchronized(solutions) {
                    wasNativeSolver = nativeSolver
                    solutions = ""
                    working = true
                }
                val solver = Thread(
                    Solver(
                        if (nativeSolver) Solver.Type.Native else Solver.Type.Kotlin,
                        cachePath = context.cacheDir.toPath(),
                        box = sidesTFV.text
                    ) { results, duration ->
                        synchronized(solutions) {
                            duration?.let { duration ->
                                val result_count = results.count{ c -> c == '\n' }
                                solutions = "$result_count results in $duration\n$results"
                                true
                            } ?: run {
                                solutions = results
                            }
                            working = false
                        }
                    })
                solver.start()
            }
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
                    onClick = if (isSolveButton) solve else clear,
                    enabled = solveOrClearEnabled,
                    content = {
                        Text(buttonText)
                    }
                )
                Row {
                    Checkbox(
                        onCheckedChange = { nativeSolver = it },
                        checked = nativeSolver,
                    )
                    Text("Native")
                }
            }
        }
        synchronized(solutions) {
            if (working || solutions.isNotEmpty()) {
                Column(
                    modifier = Modifier
                        .padding(horizontal = 4.dp)
                        .padding(top = 4.dp)
                ) {
                    val mod = Modifier
                        .border(width = 1.dp, color = Color(0.0f, 0.0f, 0.0f))
                        .padding(start = 5.dp)
                        .fillMaxWidth()
                    if (solutions.isNotEmpty()) {
                        Text("Solutions:",
                            modifier = Modifier
                                .height(30.dp)
                            )
                        Text(
                            solutions,
                            modifier = mod
                                .verticalScroll(rememberScrollState())
                        )
                    } else {
                        WorkingIndicator(label = "Working ", modifier = mod)
                    }
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