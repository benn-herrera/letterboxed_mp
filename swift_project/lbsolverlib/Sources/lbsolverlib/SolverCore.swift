import Foundation

internal protocol SolverCore {
    func setup(cache_path: URL, words_path: URL) -> String?
    func solve(puzzle: String) -> String
}
