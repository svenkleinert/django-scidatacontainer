const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));


// register copy-to-clipboard of api tokens
const btns = document.getElementsByClassName("btn-msg-copy");
for(var i=0; i<btns.length; i++) {
    var token = btns[i].id.split("_")[1];
    btns[i].addEventListener("click", function (e) {
        navigator.clipboard.writeText(token);
    });
}
