const API_BASE_URL = "http://127.0.0.1:8000";
const TOKEN_KEY = "access_token";

const token = localStorage.getItem(TOKEN_KEY);
if (!token) window.location.replace("auth.html");

const productsList = document.getElementById("products-list");
const productStatus = document.getElementById("product-status");
const productCount = document.getElementById("product-count");
const adminLink = document.getElementById("admin-link");
const userName = document.getElementById("user-name");
const userMoney = document.getElementById("user-money");
const basketItems = document.getElementById("basket-items");
const basketTotal = document.getElementById("basket-total");
const basketStatus = document.getElementById("basket-status");

function tokenPayload(value) {
    try {
        const part = value.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
        return JSON.parse(decodeURIComponent(atob(part).split("").map(char => `%${char.charCodeAt(0).toString(16).padStart(2, "0")}`).join("")));
    } catch {
        return null;
    }
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

async function loadBasket() { const basket = await request("/basket"); basketItems.replaceChildren(); basketTotal.textContent = `$${Number(basket.total || 0).toFixed(2)}`; if (!basket.items?.length) { basketItems.innerHTML = '<p class="muted">Your basket is empty.</p>'; return; } basket.items.forEach(item => { const row = document.createElement("div"); row.className = "basket-row"; row.innerHTML = `<span>${item.name} × ${item.qty}</span><strong>$${Number(item.line_total).toFixed(2)}</strong>`; const remove = document.createElement("button"); remove.className = "row-action danger"; remove.textContent = "Remove"; remove.onclick = async () => { await request(`/basket/items/${item.product_id}`, { method: "DELETE" }); loadBasket(); }; row.append(remove); basketItems.append(row); }); }

function showProducts(products) {
    productsList.replaceChildren();
    productCount.textContent = `${products.length} ${products.length === 1 ? "item" : "items"}`;
    if (!products.length) {
        productsList.innerHTML = '<div class="empty-state">No products have been added yet.</div>';
        return;
    }
    products.forEach((product, index) => {
        const card = document.createElement("article");
        card.className = "product-card";
        const visual = document.createElement("div");
        visual.className = `product-visual tone-${index % 4}`;
        if (product.image) { const image = document.createElement("img"); image.src = product.image; image.alt = product.name || ""; visual.append(image); }
        else visual.textContent = (product.name || "P").charAt(0).toUpperCase();
        const details = document.createElement("div");
        details.className = "product-details";
        const name = document.createElement("h3");
        name.textContent = product.name || "Untitled product";
        const price = document.createElement("p");
        const amount = Number(product.price);
        price.textContent = Number.isFinite(amount) ? `$${amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : "Price unavailable";
        const controls = document.createElement("div"); controls.className = "buy-controls";
        const qty = document.createElement("input"); qty.type = "number"; qty.min = "1"; qty.max = "99"; qty.value = "1"; qty.className = "qty-input";
        const add = document.createElement("button"); add.className = "primary-button compact"; add.textContent = "Add"; add.onclick = async () => { await request("/basket/items", { method: "POST", body: JSON.stringify({ product_id: product.id, qty: Number(qty.value) }) }); loadBasket(); };
        controls.append(qty, add); details.append(name, price, controls);
        card.append(visual, details);
        productsList.append(card);
    });
}

async function loadPage() {
    productStatus.textContent = "Loading products…";
    productStatus.className = "status loading";
    try {
        const payload = tokenPayload(token);
        if (!payload?.sub) throw new Error("Your session is invalid. Please log in again.");
        const [products, currentUser] = await Promise.all([request("/products"), request(`/users/${encodeURIComponent(payload.sub)}`), loadBasket()]);
        showProducts(Array.isArray(products) ? products : []);
        userName.textContent = currentUser?.username || "Account";
        userMoney.textContent = `$${Number(currentUser?.money || 0).toFixed(2)}`;
        adminLink.hidden = currentUser?.role !== "admin";
        productStatus.textContent = "";
    } catch (error) {
        productStatus.textContent = error.message;
        productStatus.className = "status error";
    }
}

document.getElementById("logout-button").addEventListener("click", async () => {
    try { await request("/auth/logout", { method: "POST" }); } catch { /* local logout still succeeds */ }
    localStorage.removeItem(TOKEN_KEY);
    window.location.replace("auth.html");
});

document.getElementById("checkout-button").addEventListener("click", async () => { basketStatus.textContent = "Processing..."; try { const result = await request("/basket/checkout", { method: "POST" }); userMoney.textContent = `$${Number(result.money).toFixed(2)}`; basketStatus.textContent = "Purchase completed."; loadBasket(); } catch (error) { basketStatus.textContent = error.message; } });

loadPage();
