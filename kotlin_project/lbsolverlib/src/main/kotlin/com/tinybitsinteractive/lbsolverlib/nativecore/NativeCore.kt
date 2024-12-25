package com.tinybitsinteractive.lbsolverlib.nativecore

import com.tinybitsinteractive.lbsolverlib.Logger
import com.tinybitsinteractive.lbsolverlib.SolverCore
import java.nio.file.Path

internal class NativeCore : SolverCore {
    private val logger by lazy {
        Logger.factory.create("NativeCore")
    }

    override fun setup(box: String, wordsPath: Path): String? {
        logger.info("setup")
        return "NYI"
    }

    override fun solve(): String {
        logger.info("solve")
        return ""
    }
}
