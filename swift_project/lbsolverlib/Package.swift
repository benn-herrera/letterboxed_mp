// swift-tools-version: 6.0
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription
import Foundation

func xcframework_rel_path(name: String) -> String {
    let unpacked_name = name + ".xcframework"
    let zipped_name = unpacked_name + ".zip"
    let pkg_dir = String(String(#file).dropLast("Package.swift".count))
    let zip_exists = FileManager.default.fileExists(atPath: pkg_dir + zipped_name)
    if zip_exists {
        return zipped_name
    }
    return unpacked_name
}

let package = Package(
    name: "lbsolverlib",
    platforms: [
      .iOS(.v16)
    ],
    products: [
        .library(
            name: "lbsolverlib",
            targets: [
                "lbsolverlib"
            ]
        )
    ],
    dependencies: [],
    targets: [
        .target(
            name: "lbsolverlib",
            dependencies: [ "bng_bridge" ]
        ),
        // required bridging module for C API framework
        .target(
            name: "bng_bridge",
            dependencies: [
                Target.Dependency.targetItem(name: "bng", condition: nil)
            ],
            publicHeadersPath: "include",
            linkerSettings: [
                .linkedFramework("bng")
            ]
        ),
        // C API framework
        .binaryTarget(
          name: "bng",
          path: xcframework_rel_path(name: "bng")
        )
    ],
    cLanguageStandard: .c17
)
