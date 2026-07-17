const API_BASE_URL = "http://127.0.0.1:8000";
const TOKEN_KEY = "access_token";
const token = localStorage.getItem(TOKEN_KEY);
if (!token) window.location.replace("auth.html");

const statusBox = document.getElementById("admin-status");
const productForm = document.getElementById("product-form");
const userForm = document.getElementById("user-form");
let currentUserId = null;

function tokenPayload(value) {
    try {
        const part = value.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
        return JSON.parse(atob(part));
    } catch { return null; }
}

async function request(path, options = {}) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        credentials: "include",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}`, ...options.headers },
    });
    const data = response.headers.get("content-type")?.includes("application/json") ? await response.json() : await response.text();
    if (!response.ok) throw new Error(data?.detail || data?.message || `Request failed (${response.status})`);
    return data;
}

function setStatus(message = "", type = "") {
    statusBox.textContent = message;
    statusBox.className = `status ${type}`.trim();
}

function actionButton(label, action, id, kind = "") {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `row-action ${kind}`.trim();
    button.textContent = label;
    button.dataset.action = action;
    button.dataset.id = id;
    return button;
}

function renderProducts(products) {
    const list = document.getElementById("admin-products-list");
    list.replaceChildren();
    document.getElementById("admin-product-count").textContent = `${products.length} total`;
    products.forEach(product => {
        const row = document.createElement("div"); row.className = "admin-row";
        const main = document.createElement("div"); main.className = "row-main";
        if (product.image) { const image = document.createElement("img"); image.src = product.image; image.alt = ""; image.className = "admin-thumb"; row.append(image); }
        const title = document.createElement("strong"); title.textContent = product.name;
        const meta = document.createElement("span"); meta.textContent = `$${Number(product.price).toFixed(2)} · #${product.id}`;
        main.append(title, meta);
        const actions = document.createElement("div"); actions.className = "row-actions";
        const edit = actionButton("Edit", "edit-product", product.id); edit.dataset.name = product.name; edit.dataset.price = product.price;
        actions.append(edit, actionButton("Delete", "delete-product", product.id, "danger"));
        row.append(main, actions); list.append(row);
    });
    if (!products.length) list.innerHTML = '<div class="empty-state small">No products yet.</div>';
}

function renderUsers(users) {
    const list = document.getElementById("admin-users-list");
    list.replaceChildren();
    document.getElementById("admin-user-count").textContent = `${users.length} total`;
    users.forEach(user => {
        const row = document.createElement("div"); row.className = "admin-row";
        const main = document.createElement("div"); main.className = "row-main";
        const title = document.createElement("strong"); title.textContent = user.username;
        const meta = document.createElement("span"); meta.textContent = `${user.email} · ${user.role || "user"} · $${Number(user.money || 0).toFixed(2)}`;
        main.append(title, meta);
        const actions = document.createElement("div"); actions.className = "row-actions";
        if (String(user.id) !== String(currentUserId)) { actions.append(actionButton("Balance", "edit-user-money", user.id)); actions.append(actionButton("Delete", "delete-user", user.id, "danger")); }
        row.append(main, actions); list.append(row);
    });
    if (!users.length) list.innerHTML = '<div class="empty-state small">No users yet.</div>';
}

async function loadData() {
    const [products, users] = await Promise.all([request("/products"), request("/users")]);
    renderProducts(Array.isArray(products) ? products : []);
    renderUsers(Array.isArray(users) ? users : []);
}

async function initialize() {
    setStatus("Checking admin access…", "loading");
    try {
        const payload = tokenPayload(token);
        currentUserId = payload?.sub;
        if (!currentUserId) throw new Error("Invalid session");
        const user = await request(`/users/${encodeURIComponent(currentUserId)}`);
        if (user?.role !== "admin") {
            window.location.replace("index.html");
            return;
        }
        await loadData();
        setStatus();
    } catch (error) { setStatus(error.message, "error"); }
}

productForm.addEventListener("submit", async event => {
    event.preventDefault();
    const id = document.getElementById("product-id").value;
    const file = document.getElementById("product-image").files[0];
    const body = { name: document.getElementById("product-name").value.trim(), price: Number(document.getElementById("product-price").value) };
    if (file) body.image = await new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(reader.result); reader.onerror = reject; reader.readAsDataURL(file); });
    setStatus(id ? "Updating product…" : "Adding product…", "loading");
    try {
        await request(id ? `/products?id=${encodeURIComponent(id)}` : "/products", { method: id ? "PUT" : "POST", body: JSON.stringify(body) });
        resetProductForm(); await loadData(); setStatus(id ? "Product updated." : "Product added.", "success");
    } catch (error) { setStatus(error.message, "error"); }
});

userForm.addEventListener("submit", async event => {
    event.preventDefault(); setStatus("Adding user…", "loading");
    try {
        await request("/users", { method: "POST", body: JSON.stringify({ username: document.getElementById("user-username").value.trim(), email: document.getElementById("user-email").value.trim(), password: document.getElementById("user-password").value, money: Number(document.getElementById("user-money").value || 0) }) });
        userForm.reset(); await loadData(); setStatus("User added.", "success");
    } catch (error) { setStatus(error.message, "error"); }
});

function resetProductForm() {
    productForm.reset(); document.getElementById("product-id").value = "";
    document.getElementById("product-submit").textContent = "Add product";
    document.getElementById("product-cancel").hidden = true;
}
document.getElementById("product-cancel").addEventListener("click", resetProductForm);

document.addEventListener("click", async event => {
    const button = event.target.closest("[data-action]"); if (!button) return;
    if (button.dataset.action === "edit-product") {
        document.getElementById("product-id").value = button.dataset.id;
        document.getElementById("product-name").value = button.dataset.name;
        document.getElementById("product-price").value = button.dataset.price;
        document.getElementById("product-submit").textContent = "Save changes";
        document.getElementById("product-cancel").hidden = false;
        document.getElementById("product-name").focus(); return;
    }
    if (button.dataset.action === "edit-user-money") {
        const amount = window.prompt("New user balance:", "0");
        if (amount === null || !Number.isFinite(Number(amount)) || Number(amount) < 0) return;
        setStatus("Updating balance...", "loading");
        try { await request(`/users?id=${encodeURIComponent(button.dataset.id)}`, { method: "PUT", body: JSON.stringify({ money: Number(amount) }) }); await loadData(); setStatus("Balance updated.", "success"); }
        catch (error) { setStatus(error.message, "error"); }
        return;
    }
    const resource = button.dataset.action === "delete-user" ? "users" : "products";
    if (!window.confirm(`Delete this ${resource.slice(0, -1)}?`)) return;
    button.disabled = true; setStatus("Deleting…", "loading");
    try { await request(`/${resource}/${encodeURIComponent(button.dataset.id)}`, { method: "DELETE" }); await loadData(); setStatus("Item deleted.", "success"); }
    catch (error) { button.disabled = false; setStatus(error.message, "error"); }
});

document.getElementById("logout-button").addEventListener("click", async () => {
    try { await request("/auth/logout", { method: "POST" }); } catch { /* local logout still succeeds */ }
    localStorage.removeItem(TOKEN_KEY); window.location.replace("auth.html");
});

initialize();
