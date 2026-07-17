const API_BASE_URL = "http://127.0.0.1:8000";
const TOKEN_KEY = "access_token";

if (localStorage.getItem(TOKEN_KEY)) window.location.replace("index.html");

const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const loginStatus = document.getElementById("login-status");
const registerStatus = document.getElementById("register-status");

async function request(path, body) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    const data = response.headers.get("content-type")?.includes("application/json") ? await response.json() : await response.text();
    if (!response.ok) {
        const detail = data?.detail;
        const message = Array.isArray(detail) ? detail.map(item => item.msg).join(". ") : detail;
        throw new Error(message || data?.message || `Request failed (${response.status})`);
    }
    return data;
}

function setStatus(element, message, type = "") {
    element.textContent = message;
    element.className = `status ${type}`.trim();
}

function openPanel(panelId) {
    document.querySelectorAll(".auth-tab").forEach(tab => {
        const active = tab.dataset.panel === panelId;
        tab.classList.toggle("active", active);
        tab.setAttribute("aria-selected", String(active));
    });
    document.querySelectorAll(".auth-content").forEach(panel => { panel.hidden = panel.id !== panelId; });
}

document.querySelectorAll(".auth-tab").forEach(tab => tab.addEventListener("click", () => openPanel(tab.dataset.panel)));

loginForm.addEventListener("submit", async event => {
    event.preventDefault();
    const button = loginForm.querySelector("button[type=submit]");
    button.disabled = true;
    setStatus(loginStatus, "Signing you in…", "loading");
    try {
        const data = await request("/auth/login", {
            username: document.getElementById("login-username").value.trim(),
            password: document.getElementById("login-password").value,
        });
        if (!data?.access_token) throw new Error("The server did not return an access token.");
        localStorage.setItem(TOKEN_KEY, data.access_token);
        setStatus(loginStatus, "Welcome back. Redirecting…", "success");
        window.location.replace("index.html");
    } catch (error) {
        setStatus(loginStatus, error.message, "error");
    } finally { button.disabled = false; }
});

registerForm.addEventListener("submit", async event => {
    event.preventDefault();
    const button = registerForm.querySelector("button[type=submit]");
    const username = document.getElementById("register-username").value.trim();
    button.disabled = true;
    setStatus(registerStatus, "Creating your account…", "loading");
    try {
        const data = await request("/auth/register", {
            username,
            email: document.getElementById("register-email").value.trim(),
            password: document.getElementById("register-password").value,
        });
        if (typeof data === "string") throw new Error(data);
        registerForm.reset();
        document.getElementById("login-username").value = username;
        openPanel("login-panel");
        setStatus(loginStatus, "Account created. You can log in now.", "success");
    } catch (error) {
        setStatus(registerStatus, error.message, "error");
    } finally { button.disabled = false; }
});
