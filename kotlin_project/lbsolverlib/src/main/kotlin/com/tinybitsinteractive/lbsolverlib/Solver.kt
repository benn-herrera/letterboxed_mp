package com.tinybitsinteractive.lbsolverlib

import java.net.HttpURLConnection
import java.net.URL
import java.nio.file.Path
import kotlin.io.path.deleteIfExists
import kotlin.io.path.div
import kotlin.io.path.exists
import kotlin.io.path.writeLines
import kotlin.time.measureTime
import kotlin.time.measureTimedValue

typealias CompletionHandler = (solutions: String) -> Unit

class Solver(
             private val type: Type,
             private val box: String,
             cachePath: Path,
             private val onComplete: CompletionHandler)
    : Runnable
{
    enum class Type {
        Kotlin,
        Native
    }

    companion object {
        fun cleanSides(sides: String): String {
            var cleaned = ""
            var liveCount = 0
            for (c in sides) {
                val lc = c.lowercase()[0]
                if (lc.isLetter() && lc !in cleaned) {
                    cleaned += lc
                    ++liveCount
                    if (liveCount == 12) {
                        break
                    }
                    if ((liveCount % 3) == 0) {
                        cleaned += ' '
                    }
                }
            }
            return cleaned.trim()
        }
    }

    override fun run() {
        logger.info("run()")

        if (box != cleanSides(box) || box.length != 15) {
            onComplete("$box is not a valid puzzle")
            return
        }

        fetchWords()?.let { errMsg ->
            onComplete(errMsg)
            return@run
        }

        SolverCore.create(type).use { core ->
            val setupTime = measureTime {
                core.setup(wordsPath)?.let { errMsg ->
                    onComplete(errMsg)
                    return@run
                }
            }

            logger.metric("setup: $setupTime")

            val (solutions, solveTime) = measureTimedValue {
                core.solve(box)
            }

            logger.metric("solve: $solveTime")

            onComplete(solutions.ifEmpty { "No solutions found." })
        }
    }

    private val wordsPath = cachePath / wordsUrl.substring(wordsUrl.indexOfLast{ it == '/'} + 1)
    private val logger: Logger by lazy {
        Logger.factory.create("Solver")
    }

    private fun fetchWords(): String? {
        try {
            if (!wordsPath.exists()) {
                val downloadTime = measureTime {
                    with(URL(wordsUrl).openConnection() as HttpURLConnection) {
                        inputStream.bufferedReader().use { br ->
                            wordsPath.writeLines(br.readLines())
                        }
                    }
                }
                logger.metric("download words: $downloadTime")
            }
        } catch (_: Throwable) {
            wordsPath.deleteIfExists()
        }
        return if (wordsPath.exists()) null else "failed downloading words."
    }
}

val Solver.Companion.wordsUrl: String
  get() = "https://raw.githubusercontent.com/benn-herrera/letterboxed/refs/heads/main/src/letterboxed/words_alpha.txt"
