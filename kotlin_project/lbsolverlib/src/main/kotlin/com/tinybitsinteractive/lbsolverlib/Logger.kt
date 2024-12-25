package com.tinybitsinteractive.lbsolverlib

import android.util.Log

interface Logger {
    companion object {
        var factory: LoggerFactory = DefaultLoggerFactory()
    }
    fun info(msg: String)
    fun warn(msg: String)
    fun err(msg: String)
    fun metric(msg: String)
}

interface LoggerFactory {
    fun create(tag: String): Logger
}

class DefaultLoggerFactory : LoggerFactory {
    override fun create(tag: String): Logger {
        return DefaultLogger(tag)
    }
}

class PrintLoggerFactory : LoggerFactory {
    override fun create(tag: String): Logger {
        return PrintLogger(tag)
    }
}

private class DefaultLogger(private val tag: String) : Logger {
    override fun info(msg: String) { Log.i(tag, msg) }
    override fun warn(msg: String) { Log.w(tag, msg) }
    override fun err(msg: String) { Log.e(tag, msg) }
    override fun metric(msg: String) { Log.i(tag, "metric: $msg") }
}

private class PrintLogger(private val tag: String) : Logger {
    override fun info(msg: String) { println("info $tag: $msg") }
    override fun warn(msg: String) { println("warn $tag: $msg") }
    override fun err(msg: String) { println("err $tag: $msg") }
    override fun metric(msg: String) { println("metric $tag: $msg") }
}
