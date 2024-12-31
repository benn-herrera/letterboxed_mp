import { assert, SolverType } from "/modules/common.js"
import Solver from "/modules/solver.js"

const version = "0.7"
var solver_ui_div = null
var title_text = null
var puzzle_text = null
var solve_button = null
var solutions_div = null
var use_wasm_checkbox = null
var is_ready = false
var is_working = false

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

function show_working(op, work_i) {
	if (op == "start") {
		is_working = true
		work_i = 0
	} else if (op == "stop") {
		is_working = false
	}
	if (is_working) {
		solutions_div.innerHTML = "<i>working" + ".".repeat(work_i) + "</i>"
		setTimeout(
			() => { show_working(null, (work_i + 1) & 0x7) },
			50)
	}
}

function solve_button_onclick() {
	if (solve_button.disabled || !is_ready || is_working) {
		return
	}

	show_working("start")

	let solver_type = use_wasm_checkbox.checked ? SolverType.Wasm : SolverType.Javascript
	let on_solved = (solutions, solve_ms) => {
			show_working("stop")
			let solution_matches= solutions.match(/\n/g)
			let solution_count = solution_matches != null ? solution_matches.length + (solutions.slice(-1) != '\n') : 0
			solutions_div.innerHTML = (
				`<i>${solution_count} solutions from ${solver_type} solver in ${solve_ms}ms</i>` +
				"<br><pre>" + solutions + "</pre>"
			)
		}

	Solver.solve_puzzle(
		solver_type,
		puzzle_text.value,
		on_solved
	)	
}

function puzzle_text_onkeydown(event) {	
	if (event.keyCode == 13) {
		return solve_button_onclick()
	}
}

function puzzle_text_onkeyup() {
	let cleaned_value = clean_puzzle(puzzle_text.value)
  let can_solve = is_ready && cleaned_value.length == 15
	solve_button.disabled = !can_solve
	puzzle_text.value = cleaned_value
}

function solver_ui_init(ui_div) {
	solver_ui_div = ui_div

	title_text = solver_ui_div.querySelector(".title_text")
	title_text.innerText += ` ${version}`

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
	Solver.init(
		() => {
			is_ready = true
			console.log("is_ready=true")
			puzzle_text_onkeyup()
		}
	)
}

const SolverUI = { init: solver_ui_init }
export default SolverUI