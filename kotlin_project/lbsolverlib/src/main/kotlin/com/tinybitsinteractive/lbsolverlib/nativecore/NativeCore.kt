package com.tinybitsinteractive.lbsolverlib.nativecore

import android.os.Build
import com.tinybitsinteractive.lbsolverlib.Logger
import com.tinybitsinteractive.lbsolverlib.SolverCore
import java.nio.file.Path
import kotlin.io.path.pathString

internal class NativeCore : SolverCore {
    companion object {
        private var _isSupported = -1
        private fun loadLib(): Boolean {
            if (_isSupported == -1) {
                _isSupported = 0
                if (Build.SUPPORTED_ABIS[0] == "arm64-v8a") {
                    try {
                        System.loadLibrary("bng")
                        _isSupported = 1
                    } catch (_: Throwable) {
                    }
                }
            }
            return _isSupported == 1
        }
        val isSupported : Boolean by lazy { loadLib() }
        init {
            loadLib()
        }
    }
    private val logger by lazy {
        Logger.factory.create("NativeCore")
    }

    override fun setup(wordsPath: Path): String? {
        logger.info("setup")
        if (!isSupported) {
            return "DEVICE NOT SUPPORTED"
        }
        return setupJNI(wordsPath.pathString).ifEmpty { null }
    }

    override fun solve(box: String): String {
        logger.info("solve")
        if (!isSupported) {
            return "DEVICE NOT SUPPORTED"
        }
        return solveJNI(box)
    }

    private external fun setupJNI(wordsPath: String): String
    private external fun solveJNI(box: String): String
}
