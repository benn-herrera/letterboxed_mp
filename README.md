# letterboxed_mp

Multiplatform Tech Demo Project

Implements a letterboxed puzzle solver for each platform.
The mobile and web platforms have implementations in each local language (kotlin, swift, javascript) plus bindings to a C++ implementation and a simple GUI that allows for choosing the implementation to use.

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
* All Platforms: run bootstrap.sh once
* Desktop Platforms
    * Run gen_desktop_project.sh
    * On Windows open .sln project under build_desktop/ with Visual Studio
    * On macOS/Linux open Ninja MultiConfig project under build_desktop with CLion
      * On macOS if you specify XCode cmake generator open .xcodeproj under build_desktop

* Android
    * Build app + lib project using Android Studio project in kotlin_project
    * C++ project is integrated
* iOS
    * Run build_swift_xcf.sh (builds xcframework consumed by swift lib)
    * Open swift_project/lbsolver.xcodeproj in XCode
* WASM
    * Run build_wasm_project.sh

Running & Testing
==================
* All platforms: see test_puzzles.txt for useful puzzles to test with
* Desktop
  * Runtime executables are in build_desktop/bin/
  * Test executables are in build_desktop/tests/
  * Desktop projects have multiple testing targets
  * Each test target can be built and debugged individually
    * RUN_ALL_TESTS (cmake --build build_desktop --target RUN_ALL_TESTS) does what it says on the tin.
  * gen_desktop_project.sh --test will build and run all of the tests. (easy one-shot pre-commit test)
* Android
  * Install & run on device using Android Studio
  * No Android-specific tests at this time
* iOS
  * Install & run on device using XCode
  * No iOS specific tests at this time
* Web/WASM
  * Run wasm_project/run_server.sh
    * serves up web app at http://localhost:8888
  * Has been checked to work with Firefox, Chrome, Safari on desktop and mobile

Notes on Git, SSH, and Multiple Credentials
============================================
* To handle per-repo ssh credentials
* Put your repo-specific SSH private key in [project]/.git/id_rsa
  * Make sure it is mode 600 (user-only read/write)
* Edit .git/config
  * Under [core] add ```sshCommand = ssh -o IdentitiesOnly=yes -i [abs/path/to/repo]/.git/id_rsa -F /dev/null```
  * ```-o IdentitiesOnly=yes``` is crucial on macOS - it prevents the keychain from overriding -i

