# letterboxed_mp

Multiplatform Tech Demo Project

Implements a letterboxed puzzle solver for each platform.
The mobile and web platforms have implementations in each local language (kotlin, swift, javascript) plus bindings to a C++ implementation and a simple GUI that allows for choosling the implementation to use.

The desktop implementations run from the command line and only use the C++ implementation.

Supported Platforms
===================
* Windows
* Linux
* MacOS
* Android
* iOS
* Web/Mobile Web (WASM)

PreReqs
=======
* All Platforms
    * CMake 3.28.3+
    * Python 3.11+
        * pyenv (pipx install pyenv)
* Windows
    * Visual Studio 2022+ with C++ Desktop Workflow
    * Ninja not required but supported
* Linux
    * Clang 18.0+
    * Ninja
* MacOS
    * XCode Command line tools
    * Ninja not required but supported
    * CLion recommended but not required
* Android
    * Android Studio 2024.1.1 (Koala) or later
    * Android NDK 23.3 or later
* iOS
    * XCode (can't deploy to iOS without it)
    * Same as MacOS + installed device SDKs
* WASM
    * emscripten

Building
========
* run bootstrap.sh (once)
* Desktop Platforms
    * run gen_desktop_project.sh
    * on windows/macos open IDE project under build/
    * on linux use ninja project under build/
* Android
    * Build
* iOS
    * TBD
* WASM
    * TBD
