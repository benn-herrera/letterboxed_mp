import Foundation

internal class NativeCore : SolverCore {
    func setup(cache_path: URL, words_path: URL) -> String? {
        Thread.sleep(forTimeInterval: 1.0)
        return nil
    }
    
    func solve(puzzle: String) -> String {
        Thread.sleep(forTimeInterval: 2.0)
        return "abcdef -> ghijkl\nabcdef -> ghijkl\nabcdef -> ghijkl\nabcdef -> ghijkl\nabcdef -> ghijkl\nabcdef -> ghijkl"
    }
}
