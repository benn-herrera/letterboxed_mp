import Foundation

public enum SolverType {
    case Swift
    case Native
}

public typealias CompletionHandler = (String?, TimeInterval) -> Void

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
    
    public func get_error() -> String? {
        return error
    }
    
    public func setup(cache_path: URL, on_ready: @escaping CompletionHandler) {
        Thread.detachNewThread {
            let words_path = URL(fileURLWithPath: cache_path.path() + "/words_alpha.txt")
            let start = Date()
            if let dl_err = Solver.download_words(words_path) {
                self.error = dl_err
                on_ready(self.error, Date().timeIntervalSince(start))
                return
            }
            let swift_core = SwiftCore()
            if let sc_err = swift_core.setup(cache_path: cache_path, words_path: words_path) {
                self.error = self.error != nil ? (self.error! + "\n" + sc_err) : sc_err
            }
            else {
                self.swift_core = swift_core
            }
            let native_core = NativeCore()
            if let nc_err = native_core.setup(cache_path: cache_path, words_path: words_path) {
                self.error = self.error != nil ? (self.error! + "\n" + nc_err) : nc_err
            }
            else {
                self.native_core = native_core
            }
            on_ready(self.error, Date().timeIntervalSince(start))
        }
    }
    
    public func solve(_ puzzle: String, type: SolverType, on_complete: @escaping CompletionHandler) {
        Thread.detachNewThread {
            guard let core = (type == .Native ? self.native_core : self.swift_core) else {
                on_complete("error: \(type) solver core not set up", 0)
                return
            }
            let start = Date()
            let solutions = core.solve(puzzle: puzzle)
            let elapsed = Date().timeIntervalSince(start)
            on_complete(solutions, elapsed)
        }
    }
    
    // https://www.advancedswift.com/download-and-cache-images-in-swift/
    private static func download_words(_ dest_path: URL) -> String? {
        if FileManager.default.fileExists(atPath: dest_path.path()) {
            print("dictionary cache exists: \(dest_path)")
            return nil
        }
        // force synchronous - this is already running on a thread.
        let force_sync = DispatchSemaphore(value: 0)
        var err_msg: String = ""
        let task = URLSession.shared.downloadTask(with: Solver.words_url) {
            (tempURL, response, error) in
            defer { force_sync.signal() }
            // Early exit on error
            guard let tempURL = tempURL else {
                err_msg = "failed downloading \(Solver.words_url) to \(dest_path)"
                return
            }
            print("downloaded \(Solver.words_url) -> \(tempURL)")
            do {
                try FileManager.default.copyItem(
                    at: tempURL,
                    to: dest_path
                )
            } catch {
                err_msg = "failed copying \(tempURL) to \(dest_path)"
                force_sync.signal()
                return
            }
            print("copied \(tempURL) -> \(dest_path)")
        }
        task.resume()
        force_sync.wait()
        return err_msg.isEmpty ? nil : err_msg
    }
    
    private var swift_core: SolverCore? = nil
    private var native_core: SolverCore? = nil
    private var error: String? = nil

    private static let words_url =
        URL(string: "https://raw.githubusercontent.com/benn-herrera/letterboxed/refs/heads/main/src/letterboxed/words_alpha.txt")!
}
