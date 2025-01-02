import Foundation

internal class NativeCore : SolverCore {
    func setup(cache_path: URL, words_path: URL) -> String? {
        return nil
    }
    
    func solve(puzzle: String) -> String {
        return "abcdef -> ghijkl\nabcdef -> ghijkl\nabcdef -> ghijkl\nabcdef -> ghijkl\nabcdef -> ghijkl\nabcdef -> ghijkl"
    }
}
