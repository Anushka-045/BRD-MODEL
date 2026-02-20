
function setTheme(theme){
  document.body.classList.remove('dark','light');
  document.body.classList.add(theme);
  localStorage.setItem('theme', theme);
}
const savedTheme = localStorage.getItem('theme') || 'dark';
setTheme(savedTheme);
function toggleSidebar(){
  document.querySelector(".container").classList.toggle("sidebar-hidden");
}