//
//  ContentView.swift
//  lbsolver
//
//  Created by Benn Herrera on 12/31/24.
//

import SwiftUI
import SwiftData
import lbsolverlib

struct ContentView: View {
    @Environment(\.modelContext) private var modelContext
    @State private var puzzle_text = "";
    @State private var solve_disabled = true
    @State private var use_native = false
    @State private var solutions_label = "solutions"
    @State private var solutions: String = ""
    @State private var lock = NSLock()

    func solve() {
        if (!solve_disabled) {
            set_solutions(solutions: "", elapsed: nil)
            Thread.detachNewThread {
                let start = Date()
                sleep(2)
                let solver = Solver()
                let _ = solver.setup(type: .Swift, cache_path: URL(fileURLWithPath:""), words_path: URL(fileURLWithPath: ""))
                let sols = solver.solve(puzzle_text)
                let elapsed = Date().timeIntervalSince(start)
                set_solutions(solutions: sols, elapsed: elapsed)
            }
        }
    }
    
    func set_solutions(solutions: String, elapsed: Double?) {
        self.lock.lock()
        defer { self.lock.unlock() }
        let solution_count = solutions.count { $0 == "\n" } + (solutions.last == "\n" ? 0 : 1)
        self.solutions = solutions
        if let elapsed {
            solutions_label = "\(solution_count) solutions in \(elapsed * 1000)ms"
        } else {
            solutions_label = "solutions"
        }
    }
    
    func clear() {
        self.lock.lock()
        defer { self.lock.unlock() }
        puzzle_text = ""
        solutions = ""
        solutions_label = "solutions"
    }
    
    var body: some View {
        Text("Letterboxed Solver")
            .font( .title )
            .padding()
        VStack(alignment: .leading) {
            HStack {
                TextField("Puzzle:", text: $puzzle_text)
                    .disableAutocorrection(true)
                    .padding()
                    .onSubmit(solve)
                    .onChange(of: puzzle_text) { old_text, new_text in
                        let pz_clean =  Solver.clean_puzzle(new_text)
                        solve_disabled = !(pz_clean.count == 15)
                        puzzle_text = pz_clean
                    }
                
                Button(action: solve) {
                    Text("solve")
                }
                .disabled(solve_disabled)
                .buttonStyle(.bordered)

                Button (action: clear) {
                    Text("clear")
                }
                .buttonStyle(.bordered)

                Toggle(isOn: $use_native) {
                    Text("native")
                }
                .toggleStyle(.button)
            }
            
            Text(solutions_label + ":")
                .italic()
                .fontWeight(.bold)
                .padding(.leading)
            Text(solutions)
                .padding(.leading)
        }
        .frame(minWidth: 0, maxWidth: .infinity, minHeight: 0, maxHeight: .infinity, alignment: .topLeading)
    }

    private func addItem() {
        withAnimation {
            let newItem = Item(timestamp: Date())
            modelContext.insert(newItem)
        }
    }
}

#Preview {
    ContentView()
        .modelContainer(for: Item.self, inMemory: true)
}
