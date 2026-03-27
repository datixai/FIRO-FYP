function login() {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  const error = document.getElementById("error");

  error.innerText = "";

  if (!email || !password) {
    error.innerText = "Please enter email and password";
    return;
  }

  // 🔹 Firebase Auth placeholder
  // Replace this with real Firebase auth
  if (email === "fire@dept.com" && password === "123456") {
    window.location.href = "dashboard.html"; // your existing dashboard
  } else {
    error.innerText = "Invalid credentials";
  }
}
