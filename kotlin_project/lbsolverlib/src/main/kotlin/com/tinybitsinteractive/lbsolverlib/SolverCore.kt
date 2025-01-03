package com.tinybitsinteractive.lbsolverlib

import java.nio.file.Path

internal interface SolverCore {
    fun setup(cachePath: Path, wordsPath: Path): String?
    fun solve(box: String): String
    fun destroy()
}
