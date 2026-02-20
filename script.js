function signup(){
localStorage.setItem("user","loggedin");
window.location.href="dashboard.html";
}

function login(){
localStorage.setItem("user","loggedin");
window.location.href="dashboard.html";
}

function logout(){
localStorage.removeItem("user");
window.location.href="index.html";
}

if(
window.location.pathname.includes("dashboard") ||
window.location.pathname.includes("generator") ||
window.location.pathname.includes("integrations") ||
window.location.pathname.includes("analytics") ||
window.location.pathname.includes("traceability") ||
window.location.pathname.includes("settings")
){
if(localStorage.getItem("user") !== "loggedin"){
window.location.href="login.html";
}
}