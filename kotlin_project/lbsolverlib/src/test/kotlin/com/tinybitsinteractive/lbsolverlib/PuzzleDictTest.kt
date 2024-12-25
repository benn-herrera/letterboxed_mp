package com.tinybitsinteractive.lbsolverlib

import com.tinybitsinteractive.lbsolverlib.kotlincore.PuzzleDict
import com.tinybitsinteractive.lbsolverlib.kotlincore.Word
import org.junit.Test

import org.junit.Assert.*
import java.io.StringReader
import java.io.StringWriter

class PuzzleDictTest {
    init {
        // logging must be mocked for unit tests
        Logger.factory = PrintLoggerFactory()
    }

    companion object {
        val testWordsUnfiltered =
            "aabc\n" +
                    "Abc\n" +
                    "abcdefghijklm\n" +
                    "bcabcabcabcabcabC\n" +
                    "mm\n"
        val testWordsFiltered = "abc\nbcabcabcabcabcabc\n"
    }

    @Test
    fun wordCheck() {
        val checkWord = Word("AbCdEa")
        // assure word constructor converts to all lower case
        assertEquals("abcdea", checkWord.text)
        assertEquals(checkWord.chars, "abcde".toSet() )
    }

    @Test
    fun unfilteredSourceConstructorCheck() {
        val testDict =
            PuzzleDict(StringReader(testWordsUnfiltered).buffered())
        assertEquals(2, testDict.size,)
        assert(!testDict.isEmpty())
        assert(testDict.isNotEmpty())
        assertEquals(1, testDict.bucket('a').size)
        assertEquals("abc", testDict.bucket('a').first().text)
        assertEquals(1, testDict.bucket('b').size)
        assertEquals("bcabcabcabcabcabc", testDict.bucket('b').first().text)
    }

    @Test
    fun saveCheck() {
        val testDict =
            PuzzleDict(StringReader(testWordsUnfiltered).buffered())
        val writer = StringWriter()
        testDict.save(writer.buffered())
        val cachedDict = writer.toString().replace("\r", "")
        assertEquals(
            testWordsFiltered,
            cachedDict)
    }

    @Test
    fun filteredCacheSourceConstructorCheck() {
        val testDict =
            PuzzleDict(StringReader(testWordsFiltered).buffered()) { word ->
                word.text.first() == 'b'
            }
        assertEquals(1, testDict.size)
        assertEquals(0, testDict.bucket('a').size)
        assertEquals("bcabcabcabcabcabc", testDict.bucket('b').first().text)
    }
}
