import Foundation

public enum SolverType {
    case Swift
    case Native
}

public class Solver {
    public static func clean_puzzle(_ pz: String) -> String {
        var pz_clean = ""
        var live_count = 0
        for c in pz.lowercased() {
            if (pz_clean.contains(c) || !c.isLetter) {
                continue
            }
            live_count += 1
            pz_clean.append(c)
            if (live_count == 12) {
                break
            }
            if (live_count % 3) == 0 {
                pz_clean.append(" ")
            }
        }
        return pz_clean
    }
    
    public init() {}
        
    public func setup(type: SolverType, cache_path: URL, words_path: URL) -> String? {
        return nil
    }
    
    public func solve(_ puzzle: String) -> String {
        return "abcdef -> ghijkl\nabcdef -> ghijkl\nabcdef -> ghijkl\nabcdef -> ghijkl\nabcdef -> ghijkl\nabcdef -> ghijkl"
    }
    
    private var engine_handle: Int64? = nil
}
