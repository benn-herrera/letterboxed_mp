// swift-tools-version:6.0
import PackageDescription

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
    dependencies: [
    ],
    targets: [
        .target(
            name: "lbsolverlib",
            dependencies: ["lbsolverlibC"]
        ),
        .target(
            name: "lbsolverlibC",
            dependencies: [
                Target.Dependency.targetItem(name: "bng", condition: nil)
            ],
            publicHeadersPath: "include",
            linkerSettings: [
              .linkedFramework("bng")
            ]
        ),
        .binaryTarget(
          name: "bng",
          path: xcfPath(name: "bng")
        ),
    ],
    cLanguageStandard: .c17
)