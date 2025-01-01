//
//  ContentView.swift
//  lbsolver
//
//  Created by Benn Herrera on 12/31/24.
//

import SwiftUI
import SwiftData

private func clean_puzzle(_ pz: String) -> String {
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

private func solve_puzzle(_ puzzle: String) -> String {
    return "abcdef -> ghijkl\nabcdef -> ghijkl\nabcdef -> ghijkl\nabcdef -> ghijkl\nabcdef -> ghijkl\nabcdef -> ghijkl"
}

struct ContentView: View {
    @Environment(\.modelContext) private var modelContext
    @State private var puzzle_text = "";
    @State private var solve_disabled = true
    @State private var use_native = false
    @State private var solutions_label = "solutions"
    @State private var solutions: String = ""

    func solve() {
        if (!solve_disabled) {
            solutions_label = "N solutions in Xms"
            solutions = solve_puzzle(puzzle_text)
        }
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
                        let pz_clean = clean_puzzle(new_text)
                        solve_disabled = !(pz_clean.count == 15)
                        puzzle_text = pz_clean
                    }
                
                Button(action: solve) {
                    Text("solve")
                        .padding()
                }
                .disabled(solve_disabled)
                
                Button (action: {
                    puzzle_text = ""
                    solutions = ""
                    solutions_label = "solutions"
                }) {
                    Text("clear")
                        .padding()
                }
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
