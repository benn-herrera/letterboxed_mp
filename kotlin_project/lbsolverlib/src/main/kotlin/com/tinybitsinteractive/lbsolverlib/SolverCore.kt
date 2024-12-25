package com.tinybitsinteractive.lbsolverlib

import com.tinybitsinteractive.lbsolverlib.kotlincore.KotlinCore
import com.tinybitsinteractive.lbsolverlib.nativecore.NativeCore
import java.nio.file.Path

internal interface SolverCore {
    companion object {
        fun create(type: Solver.Type): SolverCore {
            return when(type) {
                Solver.Type.Kotlin -> {
                   KotlinCore()
                }
                Solver.Type.Native -> {
                    NativeCore()
                }
            }
        }
    }
    fun setup(box: String, wordsPath: Path): String?
    fun solve(): String
}
