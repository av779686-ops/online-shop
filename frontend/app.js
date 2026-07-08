/*
Change this value if your backend runs on another address or port.
For example:
    http://localhost:8000
    http://127.0.0.1:5000
*/
const API_BASE_URL = "http://127.0.0.1:8000";
const AUTH_TOKEN_STORAGE_KEY = "access_token";

if (!localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)) {
    window.location.replace("auth.html");
}

/*
Change these routes if your backend uses different endpoint names.

For example, if your endpoint is /api/users:
    users: "/api/users"
*/
const API_ROUTES = {
    users: "/users",
    products: "/products",
};


// HTML elements

const userForm = document.getElementById("user-form");
const productForm = document.getElementById("product-form");

const usersList = document.getElementById("users-list");
const productsList = document.getElementById("products-list");

const userStatus = document.getElementById("user-status");
const productStatus = document.getElementById("product-status");

const refreshUsersButton = document.getElementById(
    "refresh-users-button"
);

const refreshProductsButton = document.getElementById(
    "refresh-products-button"
);

const logoutButton = document.getElementById("logout-button");


// General API request function

async function apiRequest(path, options = {}) {
    const url = `${API_BASE_URL}${path}`;
    const accessToken = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);

    console.log("URLLL--->", url)
    const response = await fetch(url, {
        ...options,

        headers: {
            "Content-Type": "application/json",
            ...(accessToken
                ? { Authorization: `Bearer ${accessToken}` }
                : {}),
            ...options.headers,
        },
    });

    // DELETE endpoints often return HTTP 204 with no response body.
    if (response.status === 204) {
        return null;
    }

    const contentType = response.headers.get("content-type");
    let responseData;

    if (contentType?.includes("application/json")) {
        responseData = await response.json();
    } else {
        responseData = await response.text();
    }

    if (!response.ok) {
        const errorMessage = getErrorMessage(
            responseData,
            response.status
        );

        throw new Error(errorMessage);
    }
    console.log(responseData);
    return responseData;
}


// Extract a useful message from different backend error formats.

function getErrorMessage(data, statusCode) {
    if (typeof data === "string" && data.trim()) {
        return data;
    }

    if (data?.detail) {
        if (typeof data.detail === "string") {
            return data.detail;
        }

        return JSON.stringify(data.detail);
    }

    if (data?.message) {
        return data.message;
    }

    return `Request failed with status ${statusCode}`;
}


// Support several common list response formats:
//
// [ {...}, {...} ]
// { "users": [ {...}, {...} ] }
// { "products": [ {...}, {...} ] }
// { "data": [ {...}, {...} ] }
// { "items": [ {...}, {...} ] }

function extractCollection(responseData, collectionName) {
    if (Array.isArray(responseData)) {
        return responseData;
    }

    if (Array.isArray(responseData?.[collectionName])) {
        return responseData[collectionName];
    }

    if (Array.isArray(responseData?.data)) {
        return responseData.data;
    }

    if (Array.isArray(responseData?.items)) {
        return responseData.items;
    }

    return [];
}


function setStatus(element, message = "", type = "") {
    element.textContent = message;
    element.className = "status";

    if (type) {
        element.classList.add(type);
    }
}


function createDeleteButton(resourceName, resourceId) {
    const button = document.createElement("button");

    button.type = "button";
    button.className = "button button-danger";
    button.textContent = "Delete";

    button.dataset.resource = resourceName;
    button.dataset.id = resourceId;

    return button;
}


// Users

async function loadUsers() {
    setStatus(userStatus, "Loading users...", "loading");
    usersList.innerHTML = "";

    try {
        const responseData = await apiRequest(API_ROUTES.users);
        const users = extractCollection(responseData);

        renderUsers(responseData);

        setStatus(
            userStatus,
            `Loaded ${users.length} user(s).`,
            "success"
        );
    } catch (error) {
        console.error("Could not load users:", error);

        setStatus(
            userStatus,
            `Could not load users: ${error.message}`,
            "error"
        );
    }
}


function renderUsers(users) {
    console.log("USER", users);
    usersList.innerHTML = "";

    if (users.length === 0) {
        const message = document.createElement("div");

        message.className = "empty-message";
        message.textContent = "No users found.";

        usersList.appendChild(message);
        return;
    }

    users.forEach((user) => {
        const card = document.createElement("article");
        card.className = "card";

        const title = document.createElement("h3");
        title.textContent = user.username ?? "Unknown username";

        card.appendChild(title);

        // Do not display passwords in the interface.
        const passwordInformation = document.createElement("p");
        passwordInformation.textContent = "Password: hidden";

        card.appendChild(passwordInformation);

        // Show ID only when the backend returned one.
        if (user.id !== undefined && user.id !== null) {
            const idInformation = document.createElement("p");
            idInformation.textContent = `ID: ${user.id}`;

            const footer = document.createElement("div");
            footer.className = "card-footer";

            footer.appendChild(
                createDeleteButton("users", user.id)
            );

            card.appendChild(idInformation);
            card.appendChild(footer);
        }

        usersList.appendChild(card);
    });
}


userForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const submitButton = userForm.querySelector(
        'button[type="submit"]'
    );

    const username = document
        .getElementById("username")
        .value
        .trim();

    const password = document.getElementById("password").value;

    if (!username || !password) {
        setStatus(
            userStatus,
            "Username and password are required.",
            "error"
        );

        return;
    }

    const newUser = {
        username,
        password,
    };

    submitButton.disabled = true;
    setStatus(userStatus, "Creating user...", "loading");

    try {
        await apiRequest(API_ROUTES.users, {
            method: "POST",
            body: JSON.stringify(newUser),
        });

        userForm.reset();

        setStatus(
            userStatus,
            "User created successfully.",
            "success"
        );

        await loadUsers();
    } catch (error) {
        console.error("Could not create user:", error);

        setStatus(
            userStatus,
            `Could not create user: ${error.message}`,
            "error"
        );
    } finally {
        submitButton.disabled = false;
    }
});


// Products

async function loadProducts() {
    setStatus(productStatus, "Loading products...", "loading");
    productsList.innerHTML = "";

    try {
        const responseData = await apiRequest(
            API_ROUTES.products
        );

        const products = extractCollection(
            responseData,
            "products"
        );

        renderProducts(products);

        setStatus(
            productStatus,
            `Loaded ${products.length} product(s).`,
            "success"
        );
    } catch (error) {
        console.error("Could not load products:", error);

        setStatus(
            productStatus,
            `Could not load products: ${error.message}`,
            "error"
        );
    }
}


function renderProducts(products) {
    productsList.innerHTML = "";

    if (products.length === 0) {
        const message = document.createElement("div");

        message.className = "empty-message";
        message.textContent = "No products found.";

        productsList.appendChild(message);
        return;
    }

    products.forEach((product) => {
        const card = document.createElement("article");
        card.className = "card";

        const title = document.createElement("h3");
        title.textContent = product.name ?? "Unknown product";

        const price = document.createElement("p");

        const numericPrice = Number(product.price);

        price.textContent = Number.isFinite(numericPrice)
            ? `Price: $${numericPrice.toFixed(2)}`
            : `Price: ${product.price ?? "Not specified"}`;

        card.appendChild(title);
        card.appendChild(price);

        if (product.id !== undefined && product.id !== null) {
            const idInformation = document.createElement("p");
            idInformation.textContent = `ID: ${product.id}`;

            const footer = document.createElement("div");
            footer.className = "card-footer";

            footer.appendChild(
                createDeleteButton("products", product.id)
            );

            card.appendChild(idInformation);
            card.appendChild(footer);
        }

        productsList.appendChild(card);
    });
}


productForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const submitButton = productForm.querySelector(
        'button[type="submit"]'
    );

    const name = document
        .getElementById("product-name")
        .value
        .trim();

    const priceInput = document.getElementById(
        "product-price"
    ).value;

    const price = Number(priceInput);

    if (!name) {
        setStatus(
            productStatus,
            "Product name is required.",
            "error"
        );

        return;
    }

    if (!Number.isFinite(price) || price < 0) {
        setStatus(
            productStatus,
            "Price must be a valid non-negative number.",
            "error"
        );

        return;
    }

    const newProduct = {
        name,
        price,
    };

    submitButton.disabled = true;
    setStatus(productStatus, "Creating product...", "loading");

    try {
        await apiRequest(API_ROUTES.products, {
            method: "POST",
            body: JSON.stringify(newProduct),
        });

        productForm.reset();

        setStatus(
            productStatus,
            "Product created successfully.",
            "success"
        );

        await loadProducts();
    } catch (error) {
        console.error("Could not create product:", error);

        setStatus(
            productStatus,
            `Could not create product: ${error.message}`,
            "error"
        );
    } finally {
        submitButton.disabled = false;
    }
});


// Delete users and products using event delegation.

document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-resource][data-id]");

    if (!button) {
        return;
    }

    const resourceName = button.dataset.resource;
    const resourceId = button.dataset.id;

    const confirmed = window.confirm(
        `Delete this ${resourceName.slice(0, -1)}?`
    );

    if (!confirmed) {
        return;
    }

    const statusElement =
        resourceName === "users"
            ? userStatus
            : productStatus;

    button.disabled = true;

    setStatus(
        statusElement,
        "Deleting item...",
        "loading"
    );

    try {
        const resourceRoute = API_ROUTES[resourceName];

        await apiRequest(
            `${resourceRoute}/${encodeURIComponent(resourceId)}`,
            {
                method: "DELETE",
            }
        );

        setStatus(
            statusElement,
            "Item deleted successfully.",
            "success"
        );

        if (resourceName === "users") {
            await loadUsers();
        } else {
            await loadProducts();
        }
    } catch (error) {
        console.error("Could not delete item:", error);

        setStatus(
            statusElement,
            `Could not delete item: ${error.message}`,
            "error"
        );

        button.disabled = false;
    }
});


refreshUsersButton.addEventListener("click", loadUsers);
refreshProductsButton.addEventListener("click", loadProducts);

logoutButton.addEventListener("click", () => {
    localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
    localStorage.removeItem("user_email");
    localStorage.removeItem("user_id");
    window.location.replace("auth.html");
});


// Load data when the page is opened.

document.addEventListener("DOMContentLoaded", () => {
    loadUsers();
    loadProducts();
});
