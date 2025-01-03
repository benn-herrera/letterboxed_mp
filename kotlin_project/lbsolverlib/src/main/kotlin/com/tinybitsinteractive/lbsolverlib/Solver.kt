package com.tinybitsinteractive.lbsolverlib

import java.net.HttpURLConnection
import java.net.URL
import java.nio.file.Path
import kotlin.io.path.deleteIfExists
import kotlin.io.path.div
import kotlin.io.path.exists
import kotlin.io.path.writeLines
import kotlin.time.Duration
import kotlin.time.measureTime
import kotlin.time.measureTimedValue

import com.tinybitsinteractive.lbsolverlib.kotlincore.KotlinCore
import com.tinybitsinteractive.lbsolverlib.nativecore.NativeCore

typealias CompletionHandler = (String?, elapsed: Duration?) -> Unit

class Solver {
    private var error: String? = null
    private var kotlinCore: SolverCore? = KotlinCore()
    private var nativeCore: SolverCore? = NativeCore()
    private val logger: Logger by lazy {
        Logger.factory.create("Solver")
    }

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

    fun setup(cachePath: Path, onReady: CompletionHandler) {
        logger.info("setup()")
        if (kotlinCore == null) {
            logger.err("destroy() has been called.")
            onReady("destroy() has been called.", null)
            return
        }
        Thread {
            val wordsPath = cachePath / wordsUrl.substring(wordsUrl.indexOfLast{ it == '/'} + 1)
            val setupTime = measureTime {
                if (error == null) {
                    error = fetchWords(wordsPath)
                }
                if (error == null) {
                    error = kotlinCore?.setup(cachePath, wordsPath)
                }
                if (error == null) {
                    error = nativeCore?.setup(cachePath, wordsPath)
                }
            }
            onReady(error, setupTime)
        }.start()
    }

    fun destroy() {
        kotlinCore?.destroy()
        kotlinCore = null
        nativeCore?.destroy()
        nativeCore = null
    }

    fun getError() = error

    fun solve(type: Type, box: String, onComplete: CompletionHandler) {
        logger.info("solve($type, $box)")

        if (kotlinCore == null) {
            logger.err("destroy() has been called.")
            onComplete("destroy() has been called.", null)
            return
        }

        if (box != cleanSides(box) || box.length != 15) {
            onComplete("$box is not a valid puzzle", null)
            return
        }

        val core = if (type == Type.Native) nativeCore!! else kotlinCore!!

        Thread {
            val (solutions, elapsed) = measureTimedValue {
                core.solve(box)
            }
            onComplete(solutions, elapsed)
        }.start()
    }

    private fun fetchWords(destPath: Path): String? {
        if (!destPath.exists()) {
            return null
        }
        try {
            with(URL(wordsUrl).openConnection() as HttpURLConnection) {
                inputStream.bufferedReader().use { br ->
                    destPath.writeLines(br.readLines())
                }
            }
        } catch (_: Throwable) {
            destPath.deleteIfExists()
            return "failed downloading words."
        }
        return null
    }
}

val Solver.Companion.wordsUrl: String
  get() = "https://raw.githubusercontent.com/benn-herrera/letterboxed/refs/heads/main/src/letterboxed/words_alpha.txt"
