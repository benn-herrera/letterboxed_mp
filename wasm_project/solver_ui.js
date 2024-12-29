var solver_ui_div = null
var puzzle_text = null
var solve_button = null
var solutions_div = null
var is_ready = false
var use_wasm = false

function solve_button_onclick(button, event) {
	if (button.disabled || !is_ready) {
		return
	}
	// defined in solver.js
	var solve_ms = performance.now()
	let solver_type = use_wasm ? SolverType.Wasm : SolverType.Javascript
	let solutions = solver_solve_puzzle(solver_type, puzzle_text.value)
	solve_ms = (performance.now() - solve_ms)
	let solution_matches= solutions.match(/\n/g)
	let solution_count = solution_matches != null ? solution_matches.length : 0
	solutions_div.innerHTML = `<i>${solution_count} solutions from ${solver_type} solver in ${solve_ms}ms</i>` + "<br><pre>"  +
		solutions + 
		"</pre>"
}

function use_wasm_onchange(check_box) {
	use_wasm = check_box.checked
}

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

function puzzle_text_onkeydown(text_field, event) {	
	if (event.keyCode == 13) {
		return solve_button_onclick(solve_button, null)
	}
}

function puzzle_text_onkeyup(text_field, event) {	
	let cleaned_value = clean_puzzle(text_field.value)
  let can_solve = is_ready && cleaned_value.length == 15
	solve_button.disabled = !can_solve
	text_field.value = cleaned_value
}

function init_solver_ui(ui_div) {
	solver_ui_div = ui_div
	puzzle_text = solver_ui_div.querySelector('.puzzle_text')
	assert(puzzle_text != null, "failed finding puzzle_text")

	solve_button = solver_ui_div.querySelector('.solve_button')
	assert(solve_button != null, "failed finding solve_button")

	solutions_div = solver_ui_div.querySelector('.solutions')
	assert(solutions_div != null, "failed finding solutions_div")

  solver_ui_div.querySelector('.use_wasm').checked = use_wasm

	solve_button.disabled = true
	puzzle_text.value = ""
	solutions_div.innerHTML = ""
	// defined in solver.js
	solver_init(
		function() {
			is_ready = true
			puzzle_text_onkeyup(puzzle_text)
		}
	)
}
