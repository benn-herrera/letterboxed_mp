package com.tinybitsinteractive.lbsolverlib.kotlincore

import com.tinybitsinteractive.lbsolverlib.Logger
import com.tinybitsinteractive.lbsolverlib.SolverCore
import java.nio.file.Path
import kotlin.io.path.bufferedReader
import kotlin.io.path.div
import kotlin.io.path.exists
import kotlin.io.path.fileSize
import kotlin.time.measureTime

internal class KotlinCore : SolverCore {
    private val logger by lazy {
        Logger.factory.create("KotlinCore")
    }
    private var sides: Array<Word>? = null
    private var combinedSides: Word? = null
    private var dict: PuzzleDict? = null
    private var dictPath: Path? = null

    companion object {
        private fun boxToSides(box: String): Array<Word> {
            assert(box.length == 15) { "invalid puzzle. too few letters." }
            val sides = arrayOf(
                Word(box.substring(0, 3)),
                Word(box.substring(4, 7)),
                Word(box.substring(8, 11)),
                Word(box.substring(12, 15))
            )
            for (s in sides) {
                assert(s.chars.size == 3) {"bad puzzle. side has non-unique or letters."}
            }
            return sides
        }
    }

    override fun setup(wordsPath: Path): String? {
        assert(dictPath == null)

        val dictPath = wordsPath.parent / "puzzle_dict.txt"

        if (!dictPath.exists() || dictPath.fileSize() < 1024L) {
            assert(wordsPath.exists())
            val preprocessTime = measureTime {
                PuzzleDict(wordsPath.bufferedReader()).save(dictPath)
            }
            if (!dictPath.exists()) {
                return "preprocess failed.";
            }
            logger.metric("preprocess: $preprocessTime")
        }

        this.dictPath = dictPath
        return null
    }

    override fun solve(box: String): String {
        assert(dictPath != null)
        sides = boxToSides(box)
        combinedSides = Word(box.replace(" ", ""))

        val filterLoadTime = measureTime {
            dict = PuzzleDict(dictPath!!) { word ->
                worksForPuzzle(word)
            }
        }
        logger.metric("filterLoad: $filterLoadTime")

        assert(dict != null) { "internal error: solve called without successful setup" }
        val solutions = mutableListOf<String>()
        val dict = this.dict!!
        val combinedSides = this.combinedSides!!

        for (start0 in combinedSides.chars) {
            for (word0 in dict.bucket(start0)) {
                // one word solution
                if (word0.chars.size == combinedSides.chars.size) {
                    solutions.add(word0.text)
                    continue
                }
                val start1 = word0.text.last()
                for (word1 in dict.bucket(start1)) {
                    // two word solution
                    if (word0.chars.union(word1.chars).size == combinedSides.chars.size) {
                        solutions.add("${word0.text} -> ${word1.text}")
                    }
                }
            }
        }

        logger.info("${solutions.size} solutions found")

        solutions.sortWith { a, b -> a.length - b.length }

        return buildString {
            solutions.forEach{ append( "$it\n" ) }
        }
    }

    override fun close() = Unit

    // we want the throw behavior - if the side isn't found there's been an error in filtering
    private fun sideIdx(c: Char): Int = sides!!.indices.first { sides!![it].chars.contains(c) }

    private fun worksForPuzzle(word: Word): Boolean {
        // has letters not in puzzle
        if (word.chars.union(combinedSides!!.chars).size > combinedSides!!.chars.size) {
            return false
        }
        var side = -1
        for(c in word.text) {
            if (side != -1 && sides!![side].chars.contains(c)) {
                // has successive letters on the same side
                return false
            }
            side = sideIdx(c)
        }
        return true
    }
}