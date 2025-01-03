package com.tinybitsinteractive.lbsolverlib.kotlincore

import com.tinybitsinteractive.lbsolverlib.Logger
import java.io.BufferedWriter
import java.nio.file.Path
import kotlin.io.path.bufferedReader
import kotlin.io.path.exists
import kotlin.io.path.outputStream

internal class Word(wordText: String) {
    val text: String = wordText.lowercase()
    val chars: Set<Char> = text.toSet()
}

internal class PuzzleDict {
    private var buckets = createBuckets()
    private val logger: Logger by lazy {
        Logger.factory.create("PuzzleDict")
    }

    companion object {
        private fun createBuckets() : Array<List<Word>> {
            return Array(26) { listOf() }
        }

        private fun toUsableWord(wordText: String): Word? {
            // can't be shorter than 3 or have more than 12 unique letters
            if (wordText.length < 3) {
                return null
            }
            val word = Word(wordText)
            if (word.chars.size > 12) {
                return null
            }
            // can't have double letters
            for (i in 0..(wordText.length - 2)) {
                if (wordText[i] == wordText[i+1]) {
                    return null
                }
            }
            return word
        }

        private fun bucketIndex(word: Word) = word.text.first() - 'a'
    }

    fun load(wordsPath: Path, isPrefiltered: Boolean): Boolean {
        if (!wordsPath.exists()) {
            return false
        }
        val reader = wordsPath.bufferedReader()
        var rawCount = 0
        val mutableBuckets = Array<MutableList<Word>>(26) { mutableListOf() }
        if (isPrefiltered) {
            reader.forEachLine { wordText ->
                val word = Word(wordText)
                mutableBuckets[bucketIndex(word)].add(word)
                ++rawCount
            }
        }
        else {
            reader.forEachLine { wordText ->
                toUsableWord(wordText)?.let { word -> mutableBuckets[bucketIndex(word)].add(word) }
                ++rawCount
            }
        }
        buckets.indices.forEach { buckets[it] = mutableBuckets[it] }
        val pfx = if (isPrefiltered) "pre" else "un"
        logger.info("PuzzleDict[${size}] created from $rawCount ${pfx}filtered words.")
        return true
    }

    fun clone_filtered(filter: (word: Word) -> Boolean): PuzzleDict {
        val clone = PuzzleDict()
        val mutableBuckets = Array<MutableList<Word>>(26) { mutableListOf() }
        for (bucket_i in buckets.indices) {
            for (word in buckets[bucket_i]) {
                if (filter(word)) {
                    mutableBuckets[bucket_i].add(word)
                }
            }
        }
        clone.buckets.indices.forEach { clone.buckets[it] = mutableBuckets[it] }
        logger.info("PuzzleDict[${clone.size}] cloned from $size prefiltered words.")
        return clone
    }

    val size: Int
        get() {
            var count = 0
            buckets.forEach { count += it.size }
            return count
        }

    fun clear() {
        buckets = createBuckets()
    }

    fun isEmpty() = buckets.firstOrNull { it.isNotEmpty() } == null
    fun isNotEmpty() = buckets.firstOrNull { it.isNotEmpty() } != null

    fun bucket(letter: Char): List<Word> {
        assert(letter in 'a'..'z')
        return buckets[letter - 'a']
    }

    fun save(writer: BufferedWriter) {
        for (bucket in buckets) {
            for (word in bucket) {
                writer.write(word.text)
                writer.newLine()
            }
            writer.flush()
        }
        logger.info("PuzzleDict[$size] saved to cache.")
    }

    fun save(path: Path) {
        path.outputStream().bufferedWriter().use {
            save(it)
        }
    }
}
