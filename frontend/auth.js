/*
Change this value if your backend runs on another address or port.
For example:
    http://localhost:8000
    http://127.0.0.1:5000
*/
const API_BASE_URL = "http://127.0.0.1:8000";
const AUTH_TOKEN_STORAGE_KEY = "access_token";

if (localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)) {
    window.location.replace("index.html");
}

/*
Change these routes if your backend uses different endpoint names.
Current FastAPI routes are:
    POST /auth/login
    POST /auth/register
*/
const AUTH_ROUTES = {
    login: "/auth/login",
    register: "/auth/register",
};

const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");

const loginStatus = document.getElementById("login-status");
const registerStatus = document.getElementById("register-status");

const loginResult = document.getElementById("login-result");
const registerResult = document.getElementById("register-result");

async function apiRequest(path, options = {}) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        credentials:"include",
        headers: {
            "Content-Type": "application/json",
            ...options.headers,
        },
    });

    const contentType = response.headers.get("content-type");
    const data = contentType?.includes("application/json")
        ? await response.json()
        : await response.text();

    if (!response.ok) {
        throw new Error(getErrorMessage(data, response.status));
    }

    return data;
}

function getErrorMessage(data, statusCode) {
    if (typeof data === "string" && data.trim()) {
        return data;
    }

    if (data?.detail) {
        return typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail);
    }

    if (data?.message) {
        return data.message;
    }

    return `Request failed with status ${statusCode}`;
}

function setStatus(element, message = "", type = "") {
    element.textContent = message;
    element.className = "status";

    if (type) {
        element.classList.add(type);
    }
}

function showResult(element, data) {
    element.hidden = false;
    element.textContent = JSON.stringify(data, null, 2);
}

function clearResult(element) {
    element.hidden = true;
    element.textContent = "";
}

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const submitButton = loginForm.querySelector(
        'button[type="submit"]'
    );

    const username = document
        .getElementById("login-username")
        .value
        .trim();

    const password = document.getElementById("login-password").value;

    submitButton.disabled = true;
    clearResult(loginResult);
    setStatus(loginStatus, "Logging in...", "loading");

    try {
        const responseData = await apiRequest(AUTH_ROUTES.login, {
            method: "POST",
            body: JSON.stringify({ username, password }),
        });

        if (responseData?.access_token) {
            localStorage.setItem(
                AUTH_TOKEN_STORAGE_KEY,
                responseData.access_token
            );
            localStorage.setItem("user_email", responseData.email ?? "");
            localStorage.setItem("user_id", responseData.id ?? "");

            setStatus(loginStatus, "Login successful. Redirecting...", "success");
            window.location.replace("index.html");
            return;
        }

        setStatus(
            loginStatus,
            "Login request completed, but no access token was returned.",
            "error"
        );
        showResult(loginResult, responseData);
    } catch (error) {
        console.error("Could not login:", error);
        setStatus(loginStatus, `Could not login: ${error.message}`, "error");
    } finally {
        submitButton.disabled = false;
    }
});

registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const submitButton = registerForm.querySelector(
        'button[type="submit"]'
    );

    const username = document
        .getElementById("register-username")
        .value
        .trim();

    const email = document
        .getElementById("register-email")
        .value
        .trim();

    const password = document.getElementById("register-password").value;

    submitButton.disabled = true;
    clearResult(registerResult);
    setStatus(registerStatus, "Creating account...", "loading");

    try {
        const responseData = await apiRequest(AUTH_ROUTES.register, {
            method: "POST",
            body: JSON.stringify({ username, email, password }),
        });

        registerForm.reset();
        setStatus(registerStatus, "Registration request completed.", "success");
        showResult(registerResult, responseData);
    } catch (error) {
        console.error("Could not register:", error);
        setStatus(
            registerStatus,
            `Could not register: ${error.message}`,
            "error"
        );
    } finally {
        submitButton.disabled = false;
    }
});
