import { assert } from "common"
import { solver_init, solver_solve_puzzle, SolverType } from "solver"

var solver_ui_div = null
var puzzle_text = null
var solve_button = null
var solutions_div = null
var use_wasm_checkbox = null
var is_ready = false

function clean_puzzle(text) {
	var clean_text = ""
	var char_set = new Set()
	for(let c of text.toLowerCase()) {
		if (char_set.has(c) || !c.match(/[a-z]/)) {
			continue
		}
		char_set.add(c)
		clean_text += c
		if (clean_text.length == 3 || clean_text.length == 7 || clean_text.length == 11) {
			clean_text += ' '
		}
	}
	return clean_text
}

function solve(solver_type) {
	var solve_ms = performance.now()
	let solutions = solver_solve_puzzle(solver_type, puzzle_text.value)
	solve_ms = (performance.now() - solve_ms)

	let solution_matches= solutions.match(/\n/g)
	let solution_count = solution_matches != null ? solution_matches.length : 0
	solutions_div.innerHTML = `<i>${solution_count} solutions from ${solver_type} solver in ${solve_ms}ms</i>` + "<br><pre>"  +
		solutions + 
		"</pre>"
}

function solve_button_onclick(event) {
	if (solve_button.disabled || !is_ready) {
		return
	}
	solutions_div.innerHTML = ""
	setTimeout(
		() => { solve(use_wasm_checkbox.checked ? SolverType.Wasm : SolverType.Javascript) },
		100)
}

function puzzle_text_onkeydown(event) {	
	if (event.keyCode == 13) {
		return solve_button_onclick(solve_button, null)
	}
}

function puzzle_text_onkeyup(event) {
	let cleaned_value = clean_puzzle(puzzle_text.value)
  let can_solve = is_ready && cleaned_value.length == 15
	solve_button.disabled = !can_solve
	puzzle_text.value = cleaned_value
}

function solver_ui_init(ui_div) {
	solver_ui_div = ui_div

	puzzle_text = solver_ui_div.querySelector('.puzzle_text')
	assert(puzzle_text != null, "failed finding puzzle_text")
	puzzle_text.addEventListener("keyup", puzzle_text_onkeyup)
	puzzle_text.addEventListener("keydown", puzzle_text_onkeydown)

	solve_button = solver_ui_div.querySelector('.solve_button')
	assert(solve_button != null, "failed finding solve_button")
	solve_button.addEventListener("click", solve_button_onclick)

	solutions_div = solver_ui_div.querySelector('.solutions')
	assert(solutions_div != null, "failed finding solutions_div")

  use_wasm_checkbox = solver_ui_div.querySelector('.use_wasm');
	assert(use_wasm_checkbox != null, "failed finding use_wasm_checkbox")  
  use_wasm_checkbox.checked = false

	solve_button.disabled = true
	puzzle_text.value = ""
	solutions_div.innerHTML = ""
	solver_init(
		() => {
			is_ready = true
			console.log("is_ready=true")
			puzzle_text_onkeyup(puzzle_text)
		}
	)
}

export { solver_ui_init }