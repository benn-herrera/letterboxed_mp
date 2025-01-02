import Foundation
import bng_bridge

internal class NativeCore : SolverCore {
    func setup(cache_path: URL, words_path: URL) -> String? {
        let cache_path_buf = cache_path.path().utf8CString.withUnsafeBufferPointer { return strdup($0.baseAddress!) }!
        let words_path_buf = words_path.path().utf8CString.withUnsafeBufferPointer { return strdup($0.baseAddress!) }!
        defer {
            free(cache_path_buf)
            free(words_path_buf)
        }
        
        var setup_data = bng_bridge.BngEngineSetupData()
        setup_data.cachePath = UnsafePointer(cache_path_buf)
        setup_data.wordsPath = UnsafePointer(words_path_buf)

        if let err_msg_c = bng_bridge.bng_engine_setup(bng_handle, &setup_data) {
            let err_msg = String(cString: err_msg_c)
            free(err_msg_c)
            return err_msg
        }
        
        return nil
    }
    
    func solve(puzzle: String) -> String {
        assert(puzzle.count == 15)
        var solve_data = bng_bridge.BngEnginePuzzleData()
        let sides_buf = puzzle.utf8CString.withUnsafeBufferPointer { return strdup($0.baseAddress!) }!
        defer {
            free(sides_buf)
        }
        // null terminate the sides
        sides_buf[3] = 0
        sides_buf[7] = 0
        sides_buf[11] = 0

        solve_data.sides.0 = UnsafePointer(sides_buf + 0)
        solve_data.sides.1 = UnsafePointer(sides_buf + 4)
        solve_data.sides.2 = UnsafePointer(sides_buf + 8)
        solve_data.sides.3 = UnsafePointer(sides_buf + 12)
        
        if let solutions_c = bng_bridge.bng_engine_solve(bng_handle, &solve_data) {
            let solutions = String(cString: solutions_c)
            free(solutions_c)
            return solutions
        }
        return ""
    }
    
    private var bng_handle = bng_bridge.bng_engine_create()
}
