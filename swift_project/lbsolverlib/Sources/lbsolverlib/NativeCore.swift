import Foundation
import bng_bridge

internal class NativeCore : SolverCore {
    func setup(cache_path: URL, words_path: URL) -> String? {
        var setup_data = bng_bridge.BngEngineSetupData()
        let cache_path_str = cache_path.path()
        let words_path_str = words_path.path()
        let err_msg = cache_path_str.utf8CString.withUnsafeBufferPointer { cache_path_buf in
            let cache_path_cstr = cache_path_buf.baseAddress!
            return words_path_str.utf8CString.withUnsafeBufferPointer { words_path_buf in
                let words_path_cstr = words_path_buf.baseAddress
                setup_data.cachePath = cache_path_cstr
                setup_data.wordsPath = words_path_cstr
                if let err_msg_c = bng_bridge.bng_engine_setup(bng_handle, &setup_data) {
                    let err_msg = String(cString: err_msg_c)
                    free(err_msg_c)
                    return err_msg
                }
                return ""
            }
        }
        return err_msg.isEmpty ? nil : err_msg
    }
    
    func solve(puzzle: String) -> String {
        var solve_data = bng_bridge.BngEnginePuzzleData()
        var side_slices = puzzle.split(separator: " ")
        assert(puzzle.count == 15 && side_slices.count == 4)
        
        var side0 = String(side_slices[0])
        var side1 = String(side_slices[1])
        var side2 = String(side_slices[2])
        var side3 = String(side_slices[3])
        
        var solutions = side0.utf8CString.withUnsafeBufferPointer { side0_buf in
            let side0_cstr = side0_buf.baseAddress!
            return side1.utf8CString.withUnsafeBufferPointer { side1_buf in
                let side1_cstr = side1_buf.baseAddress!
                return side2.utf8CString.withUnsafeBufferPointer { side2_buf in
                    let side2_cstr = side2_buf.baseAddress!
                    return side3.utf8CString.withUnsafeBufferPointer { side3_buf in
                        let side3_cstr = side3_buf.baseAddress!
                        solve_data.sides.0 = side0_cstr
                        solve_data.sides.1 = side1_cstr
                        solve_data.sides.2 = side2_cstr
                        solve_data.sides.3 = side3_cstr
                        if let solutions_c = bng_bridge.bng_engine_solve(bng_handle, &solve_data) {
                            let solutions = String(cString: solutions_c)
                            free(solutions_c)
                            return solutions
                        }
                        return ""
                    }
                }
            }
        }
        return solutions
    }
    
    private var bng_handle = bng_bridge.bng_engine_create()
}
