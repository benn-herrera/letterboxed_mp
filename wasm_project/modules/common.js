function assert(cond, msg) {
  if (!cond) {
    let msg = "ASSERT FAILURE" + (msg != null ? (": " + msg) : "")
    console.error(msg)
    alert(msg)
  }
}

function hit_url(url, on_response) {
  var request = new XMLHttpRequest()
  request.timeout = 3000
  request.open('GET', url, true)
  request.ontimeout = function() {
  }
  request.onload = function() {
    on_response(request.responseText)
  }
  request.send(null);    
}

export { assert, hit_url }
