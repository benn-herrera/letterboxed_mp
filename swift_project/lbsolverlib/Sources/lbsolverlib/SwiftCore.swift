import Foundation

private class Word {
    init(_ word_text: String) {
        self.text = word_text.lowercased()
        self.chars = Set<Character>(word_text)
    }
    init(_ word_text: String.SubSequence) {
        self.text = word_text.lowercased()
        self.chars = Set<Character>(word_text)
    }
    let text: String
    let chars: Set<Character>
}

private class PuzzleDict {
    internal static let a_ascii = "a".first!.asciiValue!
    
    private var buckets: [[Word]] = PuzzleDict.make_buckets()
    private var _count: Int = 0
    
    internal var count: Int {
        get { return _count }
    }
    
    private static func make_buckets() -> [[Word]] {
        var buckets: [[Word]] = []
        for i in 0...25 {
            buckets.append([])
        }
        return buckets
    }
    
    internal func clone_filtered(filter: (Word) -> Bool ) -> PuzzleDict {
        var pd = PuzzleDict()
        for (i, src_bucket) in buckets.enumerated() {
            for word in src_bucket {
                if filter(word) {
                    pd.buckets[i].append(word)
                    pd._count += 1
                }
            }
        }
        print("clone_filtered(): filtered count: \(pd.count)")
        return pd
    }
    
    private static func to_usable_word(word_text: String.SubSequence) -> Word? {
        // can't be shorter than 3 or have more than 12 unique letters
        if (word_text.count < 3) {
            return nil
        }
        let word = Word(word_text)
        if (word.chars.count > 12) {
            return nil
        }
        // can't have double letters
        for i in 0...(word_text.count - 2) {
            let ci0 =  word_text.index(word_text.startIndex, offsetBy: i)
            let ci1 = word_text.index(word_text.startIndex, offsetBy: i + 1)
            if word_text[ci0...ci0] == word_text[ci1...ci1] {
                return nil
            }
        }
        return word
    }

    private static func bucket_index(_ word: Word) -> Int {
        Int(word.text.first!.asciiValue! - a_ascii)
    }
    
    private func add_word(_ word: Word) {
        buckets[PuzzleDict.bucket_index(word)].append(word)
        _count += 1
    }
    
    internal func load(words_path: URL, is_prefiltered: Bool) -> Bool {
        buckets = PuzzleDict.make_buckets()
        do {
            let words_text = try String(contentsOfFile: words_path.path(), encoding: .utf8).split(separator: "\n")
            if (is_prefiltered) {
                for word_text in words_text {
                    add_word(Word(word_text))
                }
                print("load(): prefiltered count: \(count)")
            } else {
                for word_text in words_text {
                    if let word = PuzzleDict.to_usable_word(word_text: word_text) {
                        add_word(word)
                    }
                }
                print("load(): usable count: \(count)")
            }
        } catch {
            return false
        }
        assert(count > 1024)
        return true
    }
    
    internal func save(_ words_path: URL) {
        var out_text = ""
        for bucket in buckets {
            for word in bucket {
                out_text += "\(word.text)\n"
            }
        }
        do {
            try out_text.write(toFile: words_path.path(), atomically: true, encoding: .utf8)
        }
        catch {
        }
    }

    internal func bucket(letter: Character) -> [Word] {
        return buckets[Int(letter.asciiValue! - PuzzleDict.a_ascii)]
    }
}

internal class SwiftCore : SolverCore {
    private var puzzle_dict = PuzzleDict()
    
    func setup(cache_path: URL, words_path: URL) -> String? {
        let filtered_words_path = URL(fileURLWithPath: cache_path.path() + "/words_pre.txt")
        if puzzle_dict.load(words_path: filtered_words_path, is_prefiltered: true) {
            print("loaded prefiltered \(filtered_words_path)")
            return nil
        }
        if puzzle_dict.load(words_path: words_path, is_prefiltered: false) {
            print("loaded unfiltered \(words_path)")
            puzzle_dict.save(filtered_words_path)
            print("saved filtered \(filtered_words_path)")
            return nil
        }
        return "failed loading dictionary"
    }
    
    func solve(puzzle: String) -> String {
        assert(puzzle.count == 15)
        var sides_text = puzzle.split(separator: " ")
        assert(sides_text.count == 4)
        var sides: [Word] = []
        for side_text in sides_text {
            sides.append(Word(side_text))
        }
        var combined_sides = Word(sides_text.joined())
        
        func side_idx(_ c: Character) -> Int {
            return sides.indices.first(where: { sides[$0].chars.contains(c) })!
        }

        var pd = puzzle_dict.clone_filtered {
            word in
            // has letters not in puzzle
            if (word.chars.union(combined_sides.chars).count > 12) {
                return false
            }
            var side = -1
            for c in word.text {
                if (side != -1 && sides[side].chars.contains(c)) {
                    // has successive letters on the same side
                    return false
                }
                side = side_idx(c)
            }
            return true
        }
        
        var solutions: [String] = []
        for start0 in combined_sides.chars {
            for word0 in pd.bucket(letter: start0) {
                // one word solution
                if (word0.chars.count == 12) {
                    solutions.append(word0.text)
                    continue
                }
                let start1 = word0.text.last!
                for word1 in pd.bucket(letter: start1) {
                    // two word solution
                    if (word0.chars.union(word1.chars).count == 12) {
                        solutions.append("\(word0.text) -> \(word1.text)")
                    }
                }
            }
        }
        solutions.sort { lhs, rhs in lhs.count < rhs.count }
        return solutions.joined(separator: "\n")
    }
}
