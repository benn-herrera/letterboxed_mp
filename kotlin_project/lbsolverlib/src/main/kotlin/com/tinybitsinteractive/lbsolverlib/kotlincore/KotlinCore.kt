package com.tinybitsinteractive.lbsolverlib.kotlincore

import com.tinybitsinteractive.lbsolverlib.Logger
import com.tinybitsinteractive.lbsolverlib.SolverCore
import java.nio.file.Path
import kotlin.io.path.div
import kotlin.io.path.exists

internal class KotlinCore : SolverCore {
    private val logger by lazy {
        Logger.factory.create("KotlinCore")
    }
    private var dict: PuzzleDict? = PuzzleDict()

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

    override fun setup(cachePath: Path, wordsPath: Path): String? {
        logger.info("setup()")
        if (dict == null) {
            logger.err("destroy() already called")
            return "ERROR: destroy() already called"
        }
        if (dict!!.size != 0) {
            logger.err("setup() already called")
            return "ERROR: setup() already called"
        }
        val dictPath = cachePath / "puzzle_dict.txt"
        dict = PuzzleDict()
        if (dict!!.load(dictPath, isPrefiltered = true)) {
            return null
        }
        if (!dict!!.load(wordsPath, isPrefiltered = false)) {
            return "ERROR: failed preprocessing $wordsPath"
        }
        dict!!.save(dictPath)
        if (!dictPath.exists()) {
            return "preprocess failed.";
        }
        return null
    }

    override fun solve(box: String): String {
        logger.info("solve($box)")
        if (dict == null) {
            return "ERROR: not initialized"
        }

        val sides = boxToSides(box)
        val combinedSides = Word(box.replace(" ", ""))

        // we want the throw behavior - if the side isn't found there's been an error in filtering
        fun sideIdx(c: Char): Int = sides.indices.first { sides[it].chars.contains(c) }

        fun worksForPuzzle(word: Word): Boolean {
            // has letters not in puzzle
            if (word.chars.union(combinedSides.chars).size > combinedSides.chars.size) {
                return false
            }
            var side = -1
            for(c in word.text) {
                if (side != -1 && sides[side].chars.contains(c)) {
                    // has successive letters on the same side
                    return false
                }
                side = sideIdx(c)
            }
            return true
        }

        val pd = dict!!.clone_filtered { word ->
            worksForPuzzle(word)
        }

        val solutions = mutableListOf<String>()

        for (start0 in combinedSides.chars) {
            for (word0 in pd.bucket(start0)) {
                // one word solution
                if (word0.chars.size == combinedSides.chars.size) {
                    solutions.add(word0.text)
                    continue
                }
                val start1 = word0.text.last()
                for (word1 in pd.bucket(start1)) {
                    // two word solution
                    if (word0.chars.union(word1.chars).size == combinedSides.chars.size) {
                        solutions.add("${word0.text} -> ${word1.text}")
                    }
                }
            }
        }

        solutions.sortWith { a, b -> a.length - b.length }

        return buildString {
            solutions.forEach{ append( "$it\n" ) }
        }
    }

    override fun destroy() {
        dict = null
    }
}