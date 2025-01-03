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

    override fun setup(cachePath: Path, wordsPath: Path): String? {
        logger.info("setup()")
        handle?.let { handle ->
            if (!isSupported) {
                return "ERROR: DEVICE NOT SUPPORTED"
            }
            return setupJNI(handle, wordsPath.pathString, cachePath.pathString).ifEmpty { null }
        }
        logger.err("destroy() has been called.")
        return "ERROR: destroy() called"
    }

    override fun solve(box: String): String {
        logger.info("solve($box)")
        handle?.let { handle ->
            if (!isSupported) {
                return "ERROR: DEVICE NOT SUPPORTED"
            }
            return solveJNI(handle, box)
        }
        logger.err("destroy() has been called.")
        return "ERROR: destroy() called"
    }

    override fun destroy() {
        handle?.let { handle ->
            destroyJNI(handle)
        }
        handle = null
    }

    private var handle: Long? = createJNI()
    private external fun createJNI(): Long
    private external fun destroyJNI(handle: Long)
    private external fun setupJNI(handle: Long, wordsPath: String, cachePath: String): String
    private external fun solveJNI(handle: Long, box: String): String
}
