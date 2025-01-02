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
    @State private var lock = NSLock()
    @State private var puzzle_text = "";
    @State private var solve_disabled = true
    @State private var use_native = false
    @State private var solutions_label = ""
    @State private var solutions: String = ""
    @State private var solver: Solver = {
        let s = Solver()
        let cache_path = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)[0]
        s.setup(cache_path: cache_path) {
            err_msg, elapsed in
            if let err_msg {
                print("setup failes \(err_msg)")
            }
            else {
                print("setup completed in \(elapsed*1000)ms")
            }
        }
        return s
    }()

    func solve() {
        if (!solve_disabled) {
            set_solutions(solutions: "", elapsed: nil)
            solver.solve(puzzle_text, type: use_native ? .Native : .Swift) {
                sols, elapsed in
                set_solutions(solutions: sols ?? "", elapsed: elapsed)
            }
        }
    }
    
    func set_solutions(solutions: String, elapsed: Double?) {
        self.lock.lock()
        defer { self.lock.unlock() }
        var solution_count = 0
        if (!solutions.isEmpty) {
            solution_count = solutions.count { $0 == "\n" } + (solutions.last == "\n" ? 0 : 1)
        }
        self.solutions = solutions
        if let elapsed {
            solutions_label = "\(solution_count) solutions in \(elapsed * 1000)ms:"
        } else {
            solutions_label = "solutions:"
        }
    }
        
    func clear() {
        self.lock.lock()
        defer { self.lock.unlock() }
        puzzle_text = ""
        solutions = ""
        solutions_label = "solutions:"
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
            
            Text(solutions_label)
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
