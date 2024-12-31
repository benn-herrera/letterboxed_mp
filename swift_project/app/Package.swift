// swift-tools-version:6.0
import PackageDescription

let package = Package(
  name: "lbsolver",
  platforms: [
    .iOS(.v16)
  ],
  products: [
    .library(
        name: "lbsolver",
        targets: [
            "lbsolver"
        ]
    )
  ],
  dependencies: [
    "lbsolverlib"
  ],
  targets: [
      .target(
          name: "lbsolver"
      ),
  ],
)
