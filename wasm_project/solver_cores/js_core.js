var js_core = null

class Word {
  constructor(word_text) {
    this.text = word_text.toLowerCase()
    this.chars = new Set(this.text) 
  }
}

class PuzzleDict {
  static a_idx = 'a'.charCodeAt(0)

  constructor(word_list) {
    this.buckets = []
    for(var i = 0; i < 26; ++i) {
      this.buckets.push([])
    }

    if (word_list != null) {
      for (let word_text of word_list) {
        let word = this._to_usable_word(word_text)
        if (word != null) {
          this._bucket_for_word(word).push(word)
        }
      }
    }
  }

  filter_clone(word_predicate) {
    let dupe = new PuzzleDict(null)
    for (var i = 0; i < 26; ++i) {
      let dst_bucket = dupe.buckets[i]
      for (let w of this.buckets[i]) {
        if (word_predicate(w)) {
          dst_bucket.push(w)
        }
      }
    }
    return dupe
  }

  is_empty() {
    return this.buckets.find(function(b) { return b.size > 0; }) == null
  }

  bucket(ch) {
    return this.buckets[
      ch.charCodeAt(0) - PuzzleDict.a_idx
    ]    
  }

  _bucket_for_word(word) {
    return this.buckets[
      word.text.charCodeAt(0) - PuzzleDict.a_idx
    ]
  }

  _to_usable_word(text) {
    if (text.length < 3) {
      return null
    }
    let word = new Word(text)
    if (word.chars.size > 12) {
      return null
    }
    for (var i = 0; i < word.text.length - 1; ++i) {
      if (word.text[i] == word.text[i+1]) {
        return null
      }
    }
    return word
  }
}

function js_core_init(word_list, on_ready) {
  js_core = new PuzzleDict(word_list)
  if (on_ready != null) {
    on_ready()
  }
}

function js_core_solve(box) {
  assert(js_core != null, "js_core_init() not called")
  let sides = [new Word(box.slice(0, 3)), new Word(box.slice(4, 7)), new Word(box.slice(8, 11)), new Word(box.slice(12, 15))]
  let combined_sides = new Word(sides[0].text + sides[1].text + sides[2].text + sides[3].text)
  let pd = js_core.filter_clone(
    function(w) {
      // has letters not in puzzle
      if (w.chars.union(combined_sides.chars).size > 12) {
        return false
      }
      var last_side = null
      for(let c of w.text) {
        if (last_side != null && last_side.chars.has(c)) {
          // uses same side twice in a row
          return false
        }
        last_side = sides.find(function(e) { return e.chars.has(c); })
      }
      return true
    })
  let solutions = []

  for (let start0 of combined_sides.text) {
    for (let word0 of pd.bucket(start0)) {
      // one word solution
      if (word0.chars.size == 12) {
        solutions.push(word0.text)
        continue
      }
      let start1 = word0.text.slice(-1)[0]
      for (let word1 of pd.bucket(start1)) {
        // two word solution
        if (word0.chars.union(word1.chars).size == 12) {
          solutions.push(word0.text + " -> " + word1.text)
        }
      }
    }
  }

  solutions.sort(
    function(a, b) {
      return a.length - b.length
    }
  )

  return solutions.join('\n')  
}

