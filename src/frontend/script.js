/* =========================================================
   FESTIVALE - COMPLETE FRONTEND JAVASCRIPT
   ========================================================= */

/* =========================================================
   DATA
   ========================================================= */

const API_BASE_URL = "http://127.0.0.1:8000";
const AUTH_TOKEN_KEY = "festivaleAuthToken";

let cart = JSON.parse(localStorage.getItem("festivaleCart")) || [];
let orders = JSON.parse(localStorage.getItem("festivaleOrders")) || [];
let wishlist = JSON.parse(localStorage.getItem("festivaleWishlist")) || [];
let addresses = JSON.parse(localStorage.getItem("festivaleAddresses")) || [];

let authToken =
    localStorage.getItem(AUTH_TOKEN_KEY) ||
    sessionStorage.getItem(AUTH_TOKEN_KEY) ||
    null;

let user = authToken
    ? JSON.parse(localStorage.getItem("festivaleUser") || "null")
    : null;

if (!authToken) {
    localStorage.removeItem("festivaleUser");
    sessionStorage.removeItem(AUTH_TOKEN_KEY);
}

const products = [
    {
        id: 1,
        name: "Premium Cotton Kurta",
        category: "Fashion",
        price: 899,
        oldPrice: 1499,
        rating: 4.5,
        image: "https://images.unsplash.com/photo-1583391733956-6c78276477e2?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 2,
        name: "Women's Festive Saree",
        category: "Fashion",
        price: 1299,
        oldPrice: 2199,
        rating: 4.7,
        image: "https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 3,
        name: "Traditional Diya Set",
        category: "Home",
        price: 299,
        oldPrice: 499,
        rating: 4.6,
        image: "https://images.unsplash.com/photo-1603006905003-be475563bc59?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 4,
        name: "LED String Lights",
        category: "Home",
        price: 399,
        oldPrice: 799,
        rating: 4.4,
        image: "https://images.unsplash.com/photo-1543198126-a8ad8e47fb22?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 5,
        name: "Wireless Earbuds",
        category: "Electronics",
        price: 1499,
        oldPrice: 2999,
        rating: 4.3,
        image: "https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 6,
        name: "Smart Watch",
        category: "Electronics",
        price: 1999,
        oldPrice: 3999,
        rating: 4.2,
        image: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 7,
        name: "Festive Gift Box",
        category: "Gifts",
        price: 699,
        oldPrice: 999,
        rating: 4.8,
        image: "https://images.unsplash.com/photo-1513883049090-d0b7439799bf?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 8,
        name: "Chocolate Gift Pack",
        category: "Food",
        price: 549,
        oldPrice: 799,
        rating: 4.7,
        image: "https://images.unsplash.com/photo-1548907040-4d42a42e1a8a?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 9,
        name: "Decorative Toran",
        category: "Home",
        price: 249,
        oldPrice: 399,
        rating: 4.5,
        image: "https://images.unsplash.com/photo-1604608672516-f1b9e0c5a8f5?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 10,
        name: "Men's Festival Shoes",
        category: "Fashion",
        price: 1099,
        oldPrice: 1899,
        rating: 4.4,
        image: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 11,
        name: "Aroma Candle Set",
        category: "Home",
        price: 449,
        oldPrice: 699,
        rating: 4.6,
        image: "https://images.unsplash.com/photo-1602874801006-e26c9c7e9b2a?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 12,
        name: "Dry Fruit Gift Pack",
        category: "Food",
        price: 799,
        oldPrice: 1199,
        rating: 4.8,
        image: "https://images.unsplash.com/photo-1599599810769-bcde5a160d32?auto=format&fit=crop&w=600&q=80"
    },

    /* ELECTRONICS */
    {
        id: 13,
        name: "Portable Bluetooth Speaker",
        category: "Electronics",
        price: 1299,
        oldPrice: 1999,
        rating: 4.4,
        image: "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 14,
        name: "Slim Everyday Laptop",
        category: "Electronics",
        price: 54999,
        oldPrice: 64999,
        rating: 4.6,
        image: "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 15,
        name: "Premium Android Smartphone",
        category: "Electronics",
        price: 28999,
        oldPrice: 33999,
        rating: 4.5,
        image: "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 16,
        name: "Digital Mirrorless Camera",
        category: "Electronics",
        price: 44999,
        oldPrice: 52999,
        rating: 4.7,
        image: "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=600&q=80"
    },

    /* FASHION */
    {
        id: 17,
        name: "Classic Casual Hoodie",
        category: "Fashion",
        price: 999,
        oldPrice: 1599,
        rating: 4.4,
        image: "https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 18,
        name: "Classic UV Sunglasses",
        category: "Fashion",
        price: 799,
        oldPrice: 1299,
        rating: 4.3,
        image: "https://images.unsplash.com/photo-1511499767150-a48a237f0083?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 19,
        name: "Elegant Evening Dress",
        category: "Fashion",
        price: 1899,
        oldPrice: 2999,
        rating: 4.6,
        image: "https://images.unsplash.com/photo-1595777457583-95e059d581b8?auto=format&fit=crop&w=600&q=80"
    },

    /* HOME */
    {
        id: 20,
        name: "Modern Accent Chair",
        category: "Home",
        price: 4999,
        oldPrice: 6999,
        rating: 4.5,
        image: "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 21,
        name: "Decorative Indoor Plant",
        category: "Home",
        price: 599,
        oldPrice: 899,
        rating: 4.5,
        image: "https://images.unsplash.com/photo-1485955900006-10f4d324d411?auto=format&fit=crop&w=600&q=80"
    },

    /* BEAUTY */
    {
        id: 22,
        name: "Luxury Pink Lipstick",
        category: "Beauty",
        price: 699,
        oldPrice: 999,
        rating: 4.5,
        image: "https://images.unsplash.com/photo-1695634503935-2b085f0749ac?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 23,
        name: "Hydrating Face Serum",
        category: "Beauty",
        price: 899,
        oldPrice: 1299,
        rating: 4.6,
        image: "https://images.unsplash.com/photo-1754188609879-d2cb147969d9?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 24,
        name: "Daily Skincare Set",
        category: "Beauty",
        price: 1199,
        oldPrice: 1799,
        rating: 4.7,
        image: "https://images.unsplash.com/photo-1611930022073-b7a4ba5fcccd?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 25,
        name: "Professional Makeup Kit",
        category: "Beauty",
        price: 1499,
        oldPrice: 2299,
        rating: 4.6,
        image: "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 26,
        name: "Premium Perfume",
        category: "Beauty",
        price: 1599,
        oldPrice: 2499,
        rating: 4.5,
        image: "https://images.unsplash.com/photo-1541643600914-78b084683601?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 27,
        name: "Self-Care Beauty Box",
        category: "Beauty",
        price: 1799,
        oldPrice: 2699,
        rating: 4.8,
        image: "https://images.unsplash.com/photo-1754188609879-d2cb147969d9?auto=format&fit=crop&w=600&q=80"
    },

    /* GIFTS */
    {
        id: 28,
        name: "Luxury Celebration Gift Box",
        category: "Gifts",
        price: 1299,
        oldPrice: 1899,
        rating: 4.8,
        image: "https://images.unsplash.com/photo-1513883049090-d0b7439799bf?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 29,
        name: "Festive Hamper",
        category: "Gifts",
        price: 1599,
        oldPrice: 2199,
        rating: 4.7,
        image: "https://images.unsplash.com/photo-1549465220-1a8b9238cd48?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 30,
        name: "Elegant Gift Basket",
        category: "Gifts",
        price: 999,
        oldPrice: 1499,
        rating: 4.6,
        image: "https://images.unsplash.com/photo-1607082349566-187342175e2f?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 31,
        name: "Festival Surprise Box",
        category: "Gifts",
        price: 799,
        oldPrice: 1199,
        rating: 4.7,
        image: "https://images.unsplash.com/photo-1544816155-12df9643f363?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 32,
        name: "Premium Celebration Hamper",
        category: "Gifts",
        price: 1999,
        oldPrice: 2999,
        rating: 4.9,
        image: "https://images.unsplash.com/photo-1512909006721-3d6018887383?auto=format&fit=crop&w=600&q=80"
    },

    /* FOOD */
    {
        id: 33,
        name: "Assorted Festival Chocolates",
        category: "Food",
        price: 649,
        oldPrice: 899,
        rating: 4.7,
        image: "https://images.unsplash.com/photo-1575377427642-087cf684f29d?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 34,
        name: "Premium Tea Gift Set",
        category: "Food",
        price: 899,
        oldPrice: 1299,
        rating: 4.8,
        image: "https://images.unsplash.com/photo-1544787219-7f47ccb76574?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 35,
        name: "Gourmet Snack Hamper",
        category: "Food",
        price: 1199,
        oldPrice: 1699,
        rating: 4.6,
        image: "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=600&q=80"
    },
    {
        id: 36,
        name: "Festive Dry Fruit Box",
        category: "Food",
        price: 1099,
        oldPrice: 1599,
        rating: 4.8,
        image: "https://images.unsplash.com/photo-1599599810769-bcde5a160d32?auto=format&fit=crop&w=600&q=80"
    }
];

let currentProducts = [...products];


/* =========================================================
   INITIALIZATION
   ========================================================= */

document.addEventListener("DOMContentLoaded", async function () {

    setupFilters();
    installFrontendPolish();

    renderProducts(currentProducts);

    updateCartCount();

    updateProductCount();

    await restoreAuthSession();

    updateAccountGreeting();

});


/* =========================================================
   LOCAL STORAGE
   ========================================================= */

function saveCart() {
    localStorage.setItem(
        "festivaleCart",
        JSON.stringify(cart)
    );
}

function saveUser() {
    if (!user) {
        localStorage.removeItem("festivaleUser");
        return;
    }

    const safeUser = {
        id: user.id,
        name: user.name,
        email: user.email,
        is_active: user.is_active,
        createdAt: user.createdAt
    };

    localStorage.setItem(
        "festivaleUser",
        JSON.stringify(safeUser)
    );
}

function saveWishlist() {
    localStorage.setItem(
        "festivaleWishlist",
        JSON.stringify(wishlist)
    );
}

function saveOrders() {
    localStorage.setItem(
        "festivaleOrders",
        JSON.stringify(orders)
    );
}


/* =========================================================
   HTML ESCAPE
   ========================================================= */

function escapeHtml(value) {

    return String(value ?? "").replace(
        /[&<>"']/g,
        function (character) {

            return {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#039;"
            }[character];

        }
    );

}


/* =========================================================
   TOAST
   ========================================================= */

function showToast(message) {

    const toast =
        document.getElementById("toast");

    if (!toast) {

        alert(message);

        return;

    }

    toast.textContent = message;

    toast.classList.add("show");

    clearTimeout(window.festivaleToastTimer);

    window.festivaleToastTimer =
        setTimeout(function () {

            toast.classList.remove("show");

        }, 2600);

}


function showLoadingModal(title = "Please wait", message = "Loading...") {
    openModal(`
        <div class="frontend-loading">
            <div>
                <div class="spinner"></div>
                <strong>${escapeHtml(title)}</strong>
                <p>${escapeHtml(message)}</p>
            </div>
        </div>
    `);
}


/* =========================================================
   BACKEND AUTHENTICATION
   ========================================================= */

async function apiRequest(path, options = {}) {

    const headers = {
        "Content-Type": "application/json",
        ...(options.headers || {})
    };

    if (authToken) {
        headers.Authorization = `Bearer ${authToken}`;
    }

    const response = await fetch(
        `${API_BASE_URL}${path}`,
        {
            ...options,
            headers
        }
    );

    let data = null;

    try {
        data = await response.json();
    } catch {
        data = null;
    }

    if (!response.ok) {
        const detail =
            data?.detail ||
            data?.message ||
            `Request failed (${response.status})`;

        throw new Error(
            typeof detail === "string"
                ? detail
                : "Request failed"
        );
    }

    return data;
}


function storeAuthToken(token, rememberMe = true) {

    authToken = token;

    localStorage.removeItem(AUTH_TOKEN_KEY);
    sessionStorage.removeItem(AUTH_TOKEN_KEY);

    if (rememberMe) {
        localStorage.setItem(
            AUTH_TOKEN_KEY,
            token
        );
    } else {
        sessionStorage.setItem(
            AUTH_TOKEN_KEY,
            token
        );
    }
}


function storeBackendUser(data) {

    user = {
        id: data.id,
        name: data.full_name,
        email: data.email,
        is_active: data.is_active,
        createdAt: data.created_at
    };

    saveUser();
    updateAccountGreeting();
}


async function restoreAuthSession() {

    if (!authToken) {
        user = null;
        return;
    }

    try {

        const profile =
            await apiRequest(
                "/api/v1/auth/me"
            );

        storeBackendUser(profile);

    } catch (error) {

        console.warn(
            "Backend session could not be restored:",
            error.message
        );

        authToken = null;
        user = null;

        localStorage.removeItem(
            AUTH_TOKEN_KEY
        );

        sessionStorage.removeItem(
            AUTH_TOKEN_KEY
        );

        localStorage.removeItem(
            "festivaleUser"
        );

    }

}


async function loginWithBackend(
    email,
    password,
    rememberMe = true
) {

    const response =
        await apiRequest(
            "/api/v1/auth/login",
            {
                method: "POST",
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            }
        );

    if (!response?.access_token) {
        throw new Error(
            "Login succeeded but no access token was returned."
        );
    }

    storeAuthToken(
        response.access_token,
        rememberMe
    );

    const profile =
        await apiRequest(
            "/api/v1/auth/me"
        );

    storeBackendUser(profile);

    return profile;
}


/* =========================================================
   PRODUCT DISPLAY
   ========================================================= */


function renderProducts(list = currentProducts) {

    const grid =
        document.getElementById("productsGrid");

    if (!grid) return;

    const empty =
        document.getElementById("noProducts");

    if (!list.length) {

        grid.innerHTML = "";

        if (empty) {

            empty.classList.remove("hidden");

        }

        return;

    }

    if (empty) {

        empty.classList.add("hidden");

    }

    grid.innerHTML =
        list.map(function (product) {

            const liked =
                wishlist.includes(product.id);

            const discount =
                product.oldPrice
                    ? Math.round(
                        (1 - product.price / product.oldPrice) * 100
                    )
                    : 0;

            return `

                <article class="product-card">

                    <button
                        class="wishlist-button ${liked ? "active" : ""}"
                        onclick="toggleWishlist(${product.id})"
                        aria-label="Wishlist"
                    >
                        ${liked ? "❤️" : "♡"}
                    </button>

                    ${
                        discount > 0
                            ? `
                                <span class="discount-badge">
                                    ${discount}% OFF
                                </span>
                              `
                            : ""
                    }

                    <div class="product-image-wrap">

                        <img
                            class="product-image"
                            src="${product.image}"
                            alt="${escapeHtml(product.name)}"
                            loading="lazy"
                            onerror="this.style.display='none';"
                        >

                    </div>

                    <div class="product-info">

                        <div class="product-category">
                            ${escapeHtml(product.category)}
                        </div>

                        <h3>
                            ${escapeHtml(product.name)}
                        </h3>

                        <div class="rating">

                            ⭐ ${product.rating}

                            <span class="review-count">
                                (${Math.floor(product.rating * 173)} reviews)
                            </span>

                        </div>

                        <div class="price-row">

                            <span class="price">
                                ₹${Number(product.price).toLocaleString("en-IN")}
                            </span>

                            ${
                                product.oldPrice
                                    ? `
                                        <span class="old-price">
                                            ₹${Number(product.oldPrice).toLocaleString("en-IN")}
                                        </span>
                                      `
                                    : ""
                            }

                        </div>

                        <div class="stock-label">
                            ✓ In stock
                        </div>

                        <div class="product-buttons">

                            <button
                                class="add-cart"
                                onclick="addToCart(${product.id})"
                            >
                                Add to Cart
                            </button>

                            <button
                                class="view-btn"
                                onclick="viewProduct(${product.id})"
                            >
                                View Details
                            </button>

                        </div>

                    </div>

                </article>

            `;

        }).join("");

    updateProductCount();

}


/* =========================================================
   FILTER SETUP
   ========================================================= */

function setupFilters() {

    const ids = [
        "categoryFilter",
        "priceFilter",
        "ratingFilter",
        "stockFilter",
        "sortSelect"
    ];

    ids.forEach(function (id) {

        const element =
            document.getElementById(id);

        if (!element) return;

        element.addEventListener(
            "change",
            applyProductFilters
        );

    });


    const search =
        document.getElementById("searchInput");

    if (search) {

        search.addEventListener(
            "input",
            applyProductFilters
        );

        search.addEventListener(
            "keydown",
            function (event) {

                if (event.key === "Enter") {

                    applyProductFilters();

                }

            }
        );

    }


    const searchButton =
        document.getElementById("searchButton");

    if (searchButton) {

        searchButton.addEventListener(
            "click",
            applyProductFilters
        );

    }

}


/* =========================================================
   APPLY ALL FILTERS
   ========================================================= */

function applyProductFilters() {

    const categoryElement =
        document.getElementById("categoryFilter");

    const priceElement =
        document.getElementById("priceFilter");

    const ratingElement =
        document.getElementById("ratingFilter");

    const stockElement =
        document.getElementById("stockFilter");

    const sortElement =
        document.getElementById("sortSelect");

    const searchElement =
        document.getElementById("searchInput");


    const category =
        categoryElement
            ? categoryElement.value
            : "all";

    const price =
        priceElement
            ? priceElement.value
            : "all";

    const rating =
        ratingElement
            ? Number(ratingElement.value)
            : 0;

    const stockOnly =
        stockElement
            ? stockElement.checked
            : false;

    const sort =
        sortElement
            ? sortElement.value
            : "featured";

    const searchText =
        searchElement
            ? searchElement.value.trim().toLowerCase()
            : "";


    currentProducts =
        products.filter(function (product) {

            const categoryMatch =
                category === "all" ||
                product.category === category;


            const searchMatch =
                !searchText ||
                product.name
                    .toLowerCase()
                    .includes(searchText) ||
                product.category
                    .toLowerCase()
                    .includes(searchText);


            let priceMatch = true;


            if (price === "0-1000") {

                priceMatch =
                    product.price < 1000;

            }

            else if (price === "1000-2000") {

                priceMatch =
                    product.price >= 1000 &&
                    product.price <= 2000;

            }

            else if (price === "2000-5000") {

                priceMatch =
                    product.price > 2000 &&
                    product.price <= 5000;

            }

            else if (price === "5000+") {

                priceMatch =
                    product.price > 5000;

            }


            const ratingMatch =
                product.rating >= rating;


            const stockMatch =
                !stockOnly ||
                product.stock !== false;


            return (
                categoryMatch &&
                searchMatch &&
                priceMatch &&
                ratingMatch &&
                stockMatch
            );

        });


    /* SORT */

    if (sort === "low") {

        currentProducts.sort(
            (a, b) => a.price - b.price
        );

    }

    else if (sort === "high") {

        currentProducts.sort(
            (a, b) => b.price - a.price
        );

    }

    else if (sort === "rating") {

        currentProducts.sort(
            (a, b) => b.rating - a.rating
        );

    }

    else if (sort === "name") {

        currentProducts.sort(
            (a, b) =>
                a.name.localeCompare(b.name)
        );

    }


    renderProducts(currentProducts);

    updateProductCount();

}


/* =========================================================
   CATEGORY FILTER
   ========================================================= */

function filterCategory(category) {

    const select =
        document.getElementById("categoryFilter");


    if (select) {

        if (category === "All") {

            select.value = "all";

        }

        else {

            const exists =
                [...select.options].some(
                    option =>
                        option.value === category
                );

            if (exists) {

                select.value = category;

            }

        }

    }


    applyProductFilters();


    const section =
        document.getElementById("productsSection");

    if (section) {

        section.scrollIntoView({
            behavior: "smooth"
        });

    }

}


/* =========================================================
   RESET FILTERS
   ========================================================= */

function resetFilters() {

    const category =
        document.getElementById("categoryFilter");

    const price =
        document.getElementById("priceFilter");

    const rating =
        document.getElementById("ratingFilter");

    const stock =
        document.getElementById("stockFilter");

    const sort =
        document.getElementById("sortSelect");

    const search =
        document.getElementById("searchInput");


    if (category)
        category.value = "all";

    if (price)
        price.value = "all";

    if (rating)
        rating.value = "0";

    if (stock)
        stock.checked = false;

    if (sort)
        sort.selectedIndex = 0;

    if (search)
        search.value = "";


    currentProducts =
        [...products];


    renderProducts(currentProducts);

    updateProductCount();

}


/* =========================================================
   SORT
   ========================================================= */

function sortProducts() {

    applyProductFilters();

}


/* =========================================================
   SEARCH
   ========================================================= */

function searchProducts() {

    applyProductFilters();

}


/* =========================================================
   PRODUCT COUNT
   ========================================================= */

function updateProductCount() {

    const count =
        document.getElementById("resultCount");

    if (!count) return;


    count.textContent =
        `${currentProducts.length} product${
            currentProducts.length === 1
                ? ""
                : "s"
        } found`;

}


/* =========================================================
   PRODUCT DETAILS
   ========================================================= */

function viewProduct(id) {

    const product = products.find(item => item.id === id);
    if (!product) return;

    const discount = product.oldPrice
        ? Math.round((1 - product.price / product.oldPrice) * 100)
        : 0;

    openModal(`
        <div class="product-detail enhanced-product-detail">
            <div class="product-detail-image">
                <img src="${product.image}" alt="${escapeHtml(product.name)}">
            </div>

            <div class="product-detail-info">
                <span class="section-label">${escapeHtml(product.category)}</span>
                <h2>${escapeHtml(product.name)}</h2>

                <div class="rating">
                    ⭐ ${product.rating}
                    <span class="review-count">Customer rating</span>
                </div>

                <div class="price-row">
                    <span class="price">₹${Number(product.price).toLocaleString("en-IN")}</span>
                    ${product.oldPrice ? `<span class="old-price">₹${Number(product.oldPrice).toLocaleString("en-IN")}</span>` : ""}
                </div>

                ${discount ? `<div class="discount-badge">${discount}% OFF</div>` : ""}

                <p class="stock-label">✓ In stock</p>
                <p>Enjoy festival shopping with FESTIVALE. This product is part of our festival collection.</p>

                <div class="detail-quantity-row">
                    <span>Quantity</span>
                    <div class="quantity-controls detail-quantity-controls">
                        <button type="button" onclick="changeDetailQuantity(-1)">−</button>
                        <span id="detailQuantity">1</span>
                        <button type="button" onclick="changeDetailQuantity(1)">+</button>
                    </div>
                </div>

                <div class="product-detail-actions">
                    <button class="auth-primary" onclick="addProductWithQuantity(${product.id}); closeModal();">Add to Cart</button>
                    <button class="auth-secondary" onclick="addProductWithQuantity(${product.id}); closeModal(); openCart();">Buy Now</button>
                </div>
            </div>
        </div>
    `);

    window.activeDetailProductId = product.id;
    window.activeDetailQuantity = 1;
}

function changeDetailQuantity(change) {
    window.activeDetailQuantity = Math.max(1, Number(window.activeDetailQuantity || 1) + change);
    const element = document.getElementById("detailQuantity");
    if (element) element.textContent = window.activeDetailQuantity;
}

function addProductWithQuantity(id) {
    const product = products.find(item => item.id === id);
    if (!product) return;

    const quantity = Math.max(1, Number(window.activeDetailQuantity || 1));
    const existing = cart.find(item => item.id === id);

    if (existing) existing.quantity += quantity;
    else cart.push({ id: product.id, quantity });

    saveCart();
    updateCartCount();
    renderCart();
    showToast(`${product.name} added to cart`);
}


/* =========================================================
   CART
   ========================================================= */

function addToCart(id) {

    const product =
        products.find(
            item => item.id === id
        );

    if (!product) return;


    const existing =
        cart.find(
            item => item.id === id
        );


    if (existing) {

        existing.quantity++;

    }

    else {

        cart.push({
            id: product.id,
            quantity: 1
        });

    }


    saveCart();

    updateCartCount();

    showToast(
        `${product.name} added to cart`
    );

}


function updateCartCount() {

    const count =
        document.getElementById("cartCount");

    if (!count) return;


    const total =
        cart.reduce(
            (sum, item) =>
                sum + item.quantity,
            0
        );


    count.textContent = total;

}


function openCart() {

    const panel =
        document.getElementById("cartPanel");

    const overlay =
        document.getElementById("cartOverlay");


    renderCart();


    if (panel) {

        panel.classList.add("open");

    }

    if (overlay) {

        overlay.classList.remove("hidden");

    }

}


function closeCart() {

    const panel =
        document.getElementById("cartPanel");

    const overlay =
        document.getElementById("cartOverlay");


    if (panel) {

        panel.classList.remove("open");

    }

    if (overlay) {

        overlay.classList.add("hidden");

    }

}


function renderCart() {

    const content =
        document.getElementById("cartContent");

    const subtotalElement =
        document.getElementById("cartSubtotal");


    if (!content) return;


    if (!cart.length) {

        content.innerHTML = `

            <div class="empty-state">

                <div class="empty-icon">
                    🛒
                </div>

                <h3>
                    Your cart is empty
                </h3>

                <p>
                    Add some festival favourites.
                </p>

            </div>

        `;

        if (subtotalElement) {

            subtotalElement.textContent =
                "₹0";

        }

        return;

    }


    let subtotal = 0;


    content.innerHTML =
        cart.map(function (item) {

            const product =
                products.find(
                    p => p.id === item.id
                );

            if (!product) return "";


            const itemTotal =
                product.price *
                item.quantity;


            subtotal += itemTotal;


            return `

                <div class="cart-item">

                    <img
                        src="${product.image}"
                        alt="${escapeHtml(product.name)}"
                    >

                    <div class="cart-item-info">

                        <strong>
                            ${escapeHtml(product.name)}
                        </strong>

                        <span>
                            ₹${Number(product.price).toLocaleString("en-IN")}
                        </span>

                        <div class="quantity-controls">

                            <button
                                onclick="changeQuantity(${product.id}, -1)"
                            >
                                −
                            </button>

                            <span>
                                ${item.quantity}
                            </span>

                            <button
                                onclick="changeQuantity(${product.id}, 1)"
                            >
                                +
                            </button>

                            <button
                                class="remove-cart"
                                onclick="removeFromCart(${product.id})"
                            >
                                Remove
                            </button>

                        </div>

                    </div>

                </div>

            `;

        }).join("");


    if (subtotalElement) {
        subtotalElement.textContent =
            `₹${subtotal.toLocaleString("en-IN")}`;
    }

    const existingActions = document.getElementById("cartExtraActions");
    if (existingActions) existingActions.remove();

    const cartPanel = document.getElementById("cartContent");
    if (cartPanel && cart.length) {
        const actions = document.createElement("div");
        actions.id = "cartExtraActions";
        actions.className = "cart-extra-actions";
        actions.innerHTML = `
            <button type="button" class="auth-secondary" onclick="clearCart()">Clear Cart</button>
            <button type="button" class="auth-primary" onclick="openCheckout()">Proceed to Checkout →</button>
        `;
        cartPanel.appendChild(actions);
    }

}


function changeQuantity(id, change) {

    const item =
        cart.find(
            product => product.id === id
        );

    if (!item) return;


    item.quantity += change;


    if (item.quantity <= 0) {

        cart =
            cart.filter(
                product =>
                    product.id !== id
            );

    }


    saveCart();

    updateCartCount();

    renderCart();

}


function removeFromCart(id) {

    cart =
        cart.filter(
            item => item.id !== id
        );


    saveCart();

    updateCartCount();

    renderCart();

    showToast("Product removed from cart");

}


function clearCart() {
    if (!cart.length) return;
    cart = [];
    saveCart();
    updateCartCount();
    renderCart();
    showToast("Cart cleared.");
}


/* =========================================================
   CHECKOUT
   ========================================================= */

function openCheckout() {

    if (!cart.length) {

        showToast("Your cart is empty.");

        return;

    }


    let subtotal = 0;


    cart.forEach(function (item) {

        const product =
            products.find(
                p => p.id === item.id
            );

        if (product) {

            subtotal +=
                product.price *
                item.quantity;

        }

    });


    openModal(`

        <div class="checkout-summary">

            <span class="section-label">
                SECURE CHECKOUT
            </span>

            <h2>
                Complete Your Order
            </h2>


            <div class="checkout-box">

                <div>
                    <span>Items</span>
                    <strong>${cart.reduce((sum, item) => sum + Number(item.quantity || 0), 0)}</strong>
                </div>

                <div>
                    <span>Subtotal</span>
                    <strong>
                        ₹${subtotal.toLocaleString("en-IN")}
                    </strong>
                </div>

                <div>
                    <span>Delivery</span>
                    <strong>FREE</strong>
                </div>

                <hr>

                <div>
                    <span>Total</span>
                    <strong>
                        ₹${subtotal.toLocaleString("en-IN")}
                    </strong>
                </div>

            </div>


            <span class="section-label">
                DELIVERY DETAILS
            </span>

            <div class="auth-form-grid">

                <label class="auth-field">

                    <span>
                        Full Name *
                    </span>

                    <div class="auth-input-wrap">

                        <span>👤</span>

                        <input
                            id="checkoutName"
                            type="text"
                            placeholder="Enter recipient's full name"
                            autocomplete="name"
                            value="${escapeHtml(user?.name || "")}"
                        >

                    </div>

                </label>


                <label class="auth-field">

                    <span>
                        Mobile Number *
                    </span>

                    <div class="auth-input-wrap">

                        <span>📱</span>

                        <input
                            id="checkoutPhone"
                            type="tel"
                            inputmode="numeric"
                            maxlength="10"
                            placeholder="10-digit mobile number"
                            autocomplete="tel"
                        >

                    </div>

                </label>


                <label class="auth-field">

                    <span>
                        House / Flat / Building *
                    </span>

                    <div class="auth-input-wrap">

                        <span>🏠</span>

                        <input
                            id="checkoutHouse"
                            type="text"
                            placeholder="Flat 402, Sunshine Apartments"
                            autocomplete="address-line1"
                        >

                    </div>

                </label>


                <label class="auth-field">

                    <span>
                        Area / Street / Locality *
                    </span>

                    <div class="auth-input-wrap">

                        <span>📍</span>

                        <input
                            id="checkoutArea"
                            type="text"
                            placeholder="MG Road, Andheri East"
                            autocomplete="address-line2"
                        >

                    </div>

                </label>


                <label class="auth-field">

                    <span>
                        Landmark
                    </span>

                    <div class="auth-input-wrap">

                        <span>🧭</span>

                        <input
                            id="checkoutLandmark"
                            type="text"
                            placeholder="Near City Mall (optional)"
                        >

                    </div>

                </label>


                <label class="auth-field">

                    <span>
                        City *
                    </span>

                    <div class="auth-input-wrap">

                        <span>🏙️</span>

                        <input
                            id="checkoutCity"
                            type="text"
                            placeholder="Mumbai"
                            autocomplete="address-level2"
                        >

                    </div>

                </label>


                <label class="auth-field">

                    <span>
                        State *
                    </span>

                    <div class="auth-input-wrap">

                        <span>🗺️</span>

                        <input
                            id="checkoutState"
                            type="text"
                            placeholder="Maharashtra"
                            autocomplete="address-level1"
                        >

                    </div>

                </label>


                <label class="auth-field">

                    <span>
                        PIN Code *
                    </span>

                    <div class="auth-input-wrap">

                        <span>📮</span>

                        <input
                            id="checkoutPincode"
                            type="text"
                            inputmode="numeric"
                            maxlength="6"
                            placeholder="400001"
                            autocomplete="postal-code"
                        >

                    </div>

                </label>

            </div>


            <p style="font-size:13px; color:#737b91; margin:8px 0 18px;">
                * Required fields. Please enter your complete delivery address.
            </p>


            <label class="form-group">

                <span>
                    Payment Method
                </span>

                <select id="paymentMethod">

                    <option value="UPI">
                        UPI
                    </option>

                    <option value="Card">
                        Credit / Debit Card
                    </option>

                    <option value="COD">
                        Cash on Delivery
                    </option>

                </select>

            </label>


            <button
                class="auth-primary auth-full"
                onclick="checkout()"
            >
                Place Order →
            </button>

        </div>

    `);

}


function buildCheckoutAddress() {

    const name =
        document.getElementById("checkoutName")?.value.trim();

    const phone =
        document.getElementById("checkoutPhone")?.value.trim();

    const house =
        document.getElementById("checkoutHouse")?.value.trim();

    const area =
        document.getElementById("checkoutArea")?.value.trim();

    const landmark =
        document.getElementById("checkoutLandmark")?.value.trim();

    const city =
        document.getElementById("checkoutCity")?.value.trim();

    const state =
        document.getElementById("checkoutState")?.value.trim();

    const pincode =
        document.getElementById("checkoutPincode")?.value.trim();


    if (!name || !phone || !house || !area || !city || !state || !pincode) {

        showToast("Please fill in all required delivery details.");

        return null;

    }


    if (!/^[6-9]\d{9}$/.test(phone)) {

        showToast("Please enter a valid 10-digit Indian mobile number.");

        return null;

    }


    if (!/^\d{6}$/.test(pincode)) {

        showToast("Please enter a valid 6-digit PIN code.");

        return null;

    }


    const lines = [
        name,
        phone,
        house,
        area,
        landmark,
        `${city}, ${state} - ${pincode}`
    ].filter(Boolean);


    return lines.join(", ");

}


async function checkout() {

    const address = buildCheckoutAddress();

    const payment =
        document.getElementById("paymentMethod")?.value;

    if (!address) {
        return;
    }

    if (!user || !authToken) {
        showToast("Please sign in before checkout.");
        return;
    }

    if (!cart.length) {
        showToast("Your cart is empty.");
        return;
    }

    let total = 0;
    let itemCount = 0;
    const productNames = [];

    cart.forEach(function (item) {
        const product = products.find(p => p.id === item.id);

        if (product) {
            total += Number(product.price) * Number(item.quantity);
            itemCount += Number(item.quantity);
            productNames.push(`${product.name} x${item.quantity}`);
        }
    });

    if (itemCount === 0 || total <= 0) {
        showToast("Your cart contains no valid products.");
        return;
    }

    const button = document.querySelector(".checkout-summary .auth-primary");
    if (button) {
        button.disabled = true;
        button.textContent = "Placing Order...";
    }

    try {
        const transaction = await apiRequest(
            "/api/v1/transactions/checkout",
            {
                method: "POST",
                body: JSON.stringify({
                    user_id: user.id,
                    product: productNames.join(", "),
                    amount: total,
                    items_count: itemCount,
                    payment_method: payment
                })
            }
        );

        const order = {
            id: transaction.order_id,
            date: transaction.created_at
                ? new Date(transaction.created_at).toLocaleString()
                : new Date().toLocaleString(),
            total: Number(transaction.amount ?? total),
            payment: transaction.payment_method ?? payment,
            address: address,
            items: [...cart],
            status: transaction.status ?? "completed",
            backendId: transaction.id,
            product: transaction.product
        };

        orders = orders.filter(existing => existing.id !== order.id);
        orders.push(order);
        saveOrders();

        if (!addresses.includes(address)) {
            addresses.push(address);
            localStorage.setItem(
                "festivaleAddresses",
                JSON.stringify(addresses)
            );
        }

        cart = [];
        saveCart();
        updateCartCount();
        renderCart();
        closeCart();

        openModal(`
            <div class="auth-success">
                <div class="success-circle">✓</div>
                <span class="auth-eyebrow">ORDER CONFIRMED</span>
                <h2>Thank you, ${escapeHtml(user.name)}!</h2>
                <p>Your order has been placed successfully.</p>
                <p>Order ID: <strong>${escapeHtml(order.id)}</strong></p>
                <p>Total: <strong>₹${order.total.toLocaleString("en-IN")}</strong></p>
                <button
                    class="auth-primary auth-full"
                    onclick="closeModal()"
                >
                    Continue Shopping →
                </button>
            </div>
        `);

    } catch (error) {
        console.error("Checkout failed:", error);
        showToast(`Checkout failed: ${error.message}`);

        if (button) {
            button.disabled = false;
            button.textContent = "Place Order →";
        }
    }
}



/* =========================================================
   WISHLIST
   ========================================================= */

function toggleWishlist(id) {

    if (wishlist.includes(id)) {

        wishlist =
            wishlist.filter(
                item => item !== id
            );

        showToast(
            "Removed from wishlist"
        );

    }

    else {

        wishlist.push(id);

        showToast(
            "Added to wishlist"
        );

    }


    saveWishlist();

    renderProducts(currentProducts);

}


function showWishlist() {

    const section =
        document.getElementById(
            "wishlistSection"
        );

    const grid =
        document.getElementById(
            "wishlistGrid"
        );

    const empty =
        document.getElementById(
            "emptyWishlist"
        );


    if (!section || !grid) return;


    section.style.display = "block";


    const wishlistProducts =
        products.filter(
            product =>
                wishlist.includes(
                    product.id
                )
        );


    if (!wishlistProducts.length) {

        grid.innerHTML = "";

        if (empty) {

            empty.classList.remove(
                "hidden"
            );

        }

    }

    else {

        if (empty) {

            empty.classList.add(
                "hidden"
            );

        }


        grid.innerHTML =
            wishlistProducts
                .map(function (product) {

                    return `

                        <article class="product-card">

                            <button
                                class="wishlist-button active"
                                onclick="toggleWishlist(${product.id}); showWishlist();"
                            >
                                ❤️
                            </button>

                            <div class="product-image-wrap">

                                <img
                                    class="product-image"
                                    src="${product.image}"
                                    alt="${escapeHtml(product.name)}"
                                >

                            </div>

                            <div class="product-info">

                                <div class="product-category">
                                    ${escapeHtml(product.category)}
                                </div>

                                <h3>
                                    ${escapeHtml(product.name)}
                                </h3>

                                <div class="rating">
                                    ⭐ ${product.rating}
                                </div>

                                <div class="price">
                                    ₹${Number(product.price).toLocaleString("en-IN")}
                                </div>

                                <div class="product-buttons">

                                    <button
                                        class="add-cart"
                                        onclick="addToCart(${product.id})"
                                    >
                                        Add to Cart
                                    </button>

                                    <button
                                        class="view-btn"
                                        onclick="viewProduct(${product.id})"
                                    >
                                        View Details
                                    </button>

                                </div>

                            </div>

                        </article>

                    `;

                }).join("");

    }


    section.scrollIntoView({
        behavior: "smooth"
    });

}


/* =========================================================
   ORDERS
   ========================================================= */

async function showOrders() {

    if (!user || !authToken) {
        openAccount();
        return;
    }

    openModal(`
        <div class="info-card">
            <div class="info-icon">📦</div>
            <span class="auth-eyebrow">ORDER HISTORY</span>
            <h2>My Orders</h2>
            <p>Loading your orders...</p>
        </div>
    `);

    try {
        const backendOrders = await apiRequest(
            `/api/v1/transactions?user_id=${encodeURIComponent(user.id)}&limit=50`
        );

        const cachedById = new Map((orders || []).map(order => [order.id, order]));

        orders = (Array.isArray(backendOrders) ? backendOrders : []).map(function (order) {
            const cached = cachedById.get(order.order_id) || {};
            return {
                ...cached,
                id: order.order_id,
                date: order.created_at ? new Date(order.created_at).toLocaleString("en-IN") : (cached.date || ""),
                total: Number(order.amount || 0),
                payment: order.payment_method || "",
                status: order.status || "completed",
                backendId: order.id,
                product: order.product || cached.product || "",
                itemsCount: order.items_count || cached.itemsCount || 0
            };
        });

        saveOrders();

        let content = `
            <div class="info-card order-history-header">
                <div class="info-icon">📦</div>
                <span class="auth-eyebrow">ORDER HISTORY</span>
                <h2>My Orders</h2>
                <p>${orders.length} order${orders.length === 1 ? "" : "s"} found.</p>
            </div>
        `;

        if (!orders.length) {
            content += `
                <div class="empty-state">
                    <div class="empty-icon">📦</div>
                    <h3>No orders yet</h3>
                    <p>Your placed orders will appear here.</p>
                    <button class="auth-primary" onclick="closeModal(); goHome();">Start Shopping →</button>
                </div>
            `;
        } else {
            orders.forEach(function (order) {
                const status = String(order.status || "completed").toLowerCase();
                content += `
                    <button type="button" class="order-card order-card-clickable" onclick="showOrderDetails('${escapeHtml(order.id || "")}')">
                        <div class="order-card-main">
                            <div class="order-card-icon">📦</div>
                            <div>
                                <strong>Order ${escapeHtml(order.id || "—")}</strong>
                                <p>${escapeHtml(order.date || "")}</p>
                                <p class="order-product-preview">${escapeHtml(order.product || "")}</p>
                            </div>
                        </div>
                        <div class="order-card-side">
                            <strong>₹${Number(order.total || 0).toLocaleString("en-IN")}</strong>
                            <span class="order-status ${status === "completed" ? "success" : ""}">${escapeHtml(order.status || "completed")}</span>
                            <small>${escapeHtml(order.payment || "")}</small>
                            <span class="order-view-link">View Details →</span>
                        </div>
                    </button>
                `;
            });
        }

        openModal(content);

    } catch (error) {
        console.error("Could not load orders:", error);
        openModal(`
            <div class="info-card">
                <div class="info-icon">⚠️</div>
                <span class="auth-eyebrow">ORDER HISTORY</span>
                <h2>Could not load orders</h2>
                <p>${escapeHtml(error.message)}</p>
                <button class="auth-primary auth-full" onclick="showOrders()">Try Again</button>
            </div>
        `);
    }
}

function showOrderDetails(orderId) {
    const order = orders.find(item => item.id === orderId);
    if (!order) {
        showToast("Order details are unavailable.");
        return;
    }

    const address = order.address || "Delivery address saved with this order";
    const status = String(order.status || "completed").toLowerCase();

    openModal(`
        <div class="order-details-page">
            <div class="order-details-top">
                <button class="back-link" onclick="showOrders()">← Back to My Orders</button>
                <span class="order-status success">${escapeHtml(order.status || "completed")}</span>
            </div>

            <div class="order-details-heading">
                <div class="info-icon">📦</div>
                <div>
                    <span class="auth-eyebrow">ORDER DETAILS</span>
                    <h2>${escapeHtml(order.id || "Order")}</h2>
                    <p>Placed on ${escapeHtml(order.date || "")}</p>
                </div>
            </div>

            <div class="order-details-grid">
                <section class="order-detail-section">
                    <h3>Items</h3>
                    <div class="detail-line">
                        <span>${escapeHtml(order.product || "Festival products")}</span>
                        <strong>${order.itemsCount || 1} item${Number(order.itemsCount || 1) === 1 ? "" : "s"}</strong>
                    </div>
                </section>

                <section class="order-detail-section">
                    <h3>Delivery Address</h3>
                    <p class="formatted-address">${escapeHtml(address).replace(/\n/g, "<br>")}</p>
                </section>

                <section class="order-detail-section">
                    <h3>Payment</h3>
                    <div class="detail-line">
                        <span>Payment method</span>
                        <strong>${escapeHtml(order.payment || "—")}</strong>
                    </div>
                    <div class="detail-line total-line">
                        <span>Total</span>
                        <strong>₹${Number(order.total || 0).toLocaleString("en-IN")}</strong>
                    </div>
                </section>
            </div>

            <div class="order-progress">
                <div class="progress-step active"><span>✓</span><strong>Order Placed</strong></div>
                <div class="progress-line ${status === "completed" ? "active" : ""}"></div>
                <div class="progress-step ${status === "completed" ? "active" : ""}"><span>${status === "completed" ? "✓" : "2"}</span><strong>Confirmed</strong></div>
                <div class="progress-line"></div>
                <div class="progress-step"><span>3</span><strong>Delivered</strong></div>
            </div>
        </div>
    `);
}



/* =========================================================
   ACCOUNT
   ========================================================= */

function openAccount() {

    if (user) {

        showAccountDashboard();

        return;

    }


    openModal(`

        <div class="account-landing">

            <div class="account-hero">

                <div class="auth-logo">
                    F
                </div>

                <div>

                    <span class="auth-eyebrow">
                        WELCOME TO FESTIVALE
                    </span>

                    <h2>
                        My Account
                    </h2>

                    <p>
                        Sign in to continue shopping
                        or create a new account.
                    </p>

                </div>

            </div>


            <div class="account-benefits">

                <div class="account-benefit">

                    <span>
                        🛍️
                    </span>

                    <strong>
                        Faster Shopping
                    </strong>

                    <small>
                        Save your details and shop easily.
                    </small>

                </div>


                <div class="account-benefit">

                    <span>
                        📦
                    </span>

                    <strong>
                        Track Orders
                    </strong>

                    <small>
                        Keep all your orders in one place.
                    </small>

                </div>


                <div class="account-benefit">

                    <span>
                        ❤️
                    </span>

                    <strong>
                        Save Favorites
                    </strong>

                    <small>
                        Build your personal wishlist.
                    </small>

                </div>

            </div>


            <div class="account-choice-grid">

                <button
                    class="account-choice primary-choice"
                    onclick="showSignIn()"
                >

                    <span class="choice-icon">
                        →
                    </span>

                    <span>

                        <strong>
                            Sign In
                        </strong>

                        <small>
                            Already have an account?
                        </small>

                    </span>

                </button>


                <button
                    class="account-choice secondary-choice"
                    onclick="showCreateAccount()"
                >

                    <span class="choice-icon">
                        +
                    </span>

                    <span>

                        <strong>
                            Create Account
                        </strong>

                        <small>
                            New to FESTIVALE?
                        </small>

                    </span>

                </button>

            </div>


            <div class="account-note">

                🔒 Secure and simple FESTIVALE
                account experience.

            </div>

        </div>

    `);

}


/* =========================================================
   CREATE ACCOUNT
   ========================================================= */

function showCreateAccount() {

    openModal(`

        <div class="auth-wrapper">

            <div class="auth-brand">

                <div class="auth-logo">
                    F
                </div>

                <div>

                    <span class="auth-eyebrow">
                        FESTIVALE MEMBERSHIP
                    </span>

                    <h2>
                        Create your account
                    </h2>

                    <p>
                        Join FESTIVALE and start shopping smarter.
                    </p>

                </div>

            </div>


            <div class="auth-benefits">

                <div>

                    <span>
                        🛍️
                    </span>

                    <strong>
                        Easy Shopping
                    </strong>

                    <small>
                        Save your favourite products.
                    </small>

                </div>


                <div>

                    <span>
                        📦
                    </span>

                    <strong>
                        Track Orders
                    </strong>

                    <small>
                        Manage all your orders in one place.
                    </small>

                </div>


                <div>

                    <span>
                        💗
                    </span>

                    <strong>
                        Wishlist
                    </strong>

                    <small>
                        Save products for later.
                    </small>

                </div>

            </div>


            <div class="auth-form-grid">

                <label class="auth-field">

                    <span>
                        Full Name
                    </span>

                    <div class="auth-input-wrap">

                        <span>
                            👤
                        </span>

                        <input
                            id="accountName"
                            type="text"
                            placeholder="Enter your full name"
                            autocomplete="name"
                        >

                    </div>

                </label>


                <label class="auth-field">

                    <span>
                        Email Address
                    </span>

                    <div class="auth-input-wrap">

                        <span>
                            ✉️
                        </span>

                        <input
                            id="accountEmail"
                            type="email"
                            placeholder="you@example.com"
                            autocomplete="email"
                        >

                    </div>

                </label>


                <label class="auth-field">

                    <span>
                        Password
                    </span>

                    <div class="auth-input-wrap">

                        <span>
                            🔐
                        </span>

                        <input
                            id="accountPassword"
                            type="password"
                            placeholder="Create a password"
                            autocomplete="new-password"
                            oninput="updatePasswordStrength()"
                        >

                        <button
                            type="button"
                            class="password-toggle"
                            onclick="togglePassword('accountPassword', this)"
                        >
                            ◉
                        </button>

                    </div>

                    <div class="password-strength">

                        <div class="strength-bar">

                            <span id="strengthFill"></span>

                        </div>

                        <small id="strengthText">
                            Use 8+ characters with letters and numbers.
                        </small>

                    </div>

                </label>


                <label class="auth-field">

                    <span>
                        Confirm Password
                    </span>

                    <div class="auth-input-wrap">

                        <span>
                            🔐
                        </span>

                        <input
                            id="accountPasswordConfirm"
                            type="password"
                            placeholder="Confirm your password"
                            autocomplete="new-password"
                        >

                        <button
                            type="button"
                            class="password-toggle"
                            onclick="togglePassword('accountPasswordConfirm', this)"
                        >
                            ◉
                        </button>

                    </div>

                </label>

            </div>


            <label class="terms-row">

                <input
                    id="accountTerms"
                    type="checkbox"
                >

                <span>
                    I agree to the FESTIVALE
                    <b>Terms & Conditions</b>
                    and
                    <b>Privacy Policy</b>.
                </span>

            </label>


            <button
                class="auth-primary auth-full"
                onclick="createAccount()"
            >
                Create My Account →
            </button>


            <div class="auth-divider">

                <span>
                    Already have an account?
                </span>

            </div>


            <button
                class="auth-secondary auth-full"
                onclick="showSignIn()"
            >
                Sign In Instead
            </button>

        </div>

    `);

}


/* =========================================================
   CREATE ACCOUNT ACTION
   ========================================================= */

async function createAccount() {

    const name =
        document.getElementById(
            "accountName"
        )?.value.trim();

    const email =
        document.getElementById(
            "accountEmail"
        )?.value.trim().toLowerCase();

    const password =
        document.getElementById(
            "accountPassword"
        )?.value || "";

    const confirm =
        document.getElementById(
            "accountPasswordConfirm"
        )?.value || "";

    const terms =
        document.getElementById(
            "accountTerms"
        )?.checked;

    if (!name || !email || !password || !confirm) {
        showToast("Please complete all fields.");
        return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        showToast("Please enter a valid email address.");
        return;
    }

    if (password.length < 8) {
        showToast("Password must contain at least 8 characters.");
        return;
    }

    if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) {
        showToast("Use at least one letter and one number.");
        return;
    }

    if (password !== confirm) {
        showToast("Passwords do not match.");
        return;
    }

    if (!terms) {
        showToast("Please accept the Terms & Conditions.");
        return;
    }

    const button =
        document.querySelector(".auth-primary.auth-full");

    if (button) {
        button.disabled = true;
        button.textContent = "Creating account...";
    }

    try {

        await apiRequest(
            "/api/v1/auth/register",
            {
                method: "POST",
                body: JSON.stringify({
                    email: email,
                    password: password,
                    full_name: name
                })
            }
        );

        await loginWithBackend(
            email,
            password,
            true
        );

        openModal(`

            <div class="auth-success">

                <div class="success-circle">
                    ✓
                </div>

                <span class="auth-eyebrow">
                    ACCOUNT CREATED
                </span>

                <h2>
                    Welcome, ${escapeHtml(name)}!
                </h2>

                <p>
                    Your FESTIVALE account is ready.
                    Your account has been securely created
                    on the FESTIVALE backend.
                </p>

                <button
                    class="auth-primary auth-full"
                    onclick="showAccountDashboard()"
                >
                    Start Shopping →
                </button>

            </div>

        `);

    } catch (error) {

        console.error(
            "Registration error:",
            error
        );

        let message = error.message;

        if (
            message.toLowerCase().includes("already") ||
            message.toLowerCase().includes("exist")
        ) {
            message =
                "An account with this email already exists. Please sign in.";
        }

        showToast(message);

        if (button) {
            button.disabled = false;
            button.textContent = "Create My Account →";
        }

    }

}


/* =========================================================
   SIGN IN
   ========================================================= */

function showSignIn() {

    openModal(`

        <div class="signin-hero">

            <div class="auth-logo">
                F
            </div>

            <span class="auth-eyebrow">
                WELCOME BACK
            </span>

            <h2>
                Sign in to FESTIVALE
            </h2>

            <p>
                Access your orders, wishlist
                and personalized shopping experience.
            </p>

        </div>


        <div class="auth-form-grid signin-form">

            <label class="auth-field">

                <span>
                    Email Address
                </span>

                <div class="auth-input-wrap">

                    <span>
                        ✉️
                    </span>

                    <input
                        id="signInEmail"
                        type="email"
                        placeholder="you@example.com"
                        autocomplete="email"
                    >

                </div>

            </label>


            <label class="auth-field">

                <span>
                    Password
                </span>

                <div class="auth-input-wrap">

                    <span>
                        🔐
                    </span>

                    <input
                        id="signInPassword"
                        type="password"
                        placeholder="Enter your password"
                        autocomplete="current-password"
                    >

                    <button
                        type="button"
                        class="password-toggle"
                        onclick="togglePassword('signInPassword', this)"
                    >
                        ◉
                    </button>

                </div>

            </label>

        </div>


        <div class="remember-row">

            <label>

                <input
                    type="checkbox"
                    id="rememberMe"
                    checked
                >

                Remember me

            </label>


            <button
                type="button"
                class="forgot-button"
                onclick="showToast('Password recovery will be connected to the backend.')"
            >
                Forgot password?
            </button>

        </div>


        <button
            class="auth-primary auth-full"
            onclick="signIn()"
        >
            Sign In →
        </button>


        <div class="auth-divider">

            <span>
                New to FESTIVALE?
            </span>

        </div>


        <button
            class="auth-secondary auth-full"
            onclick="showCreateAccount()"
        >
            Create a New Account
        </button>

    `);

}


async function signIn() {

    const email =
        document.getElementById(
            "signInEmail"
        )?.value.trim().toLowerCase();

    const password =
        document.getElementById(
            "signInPassword"
        )?.value || "";

    const rememberMe =
        document.getElementById(
            "rememberMe"
        )?.checked ?? true;

    if (!email || !password) {
        showToast(
            "Please enter your email and password."
        );
        return;
    }

    const button =
        document.querySelector(
            ".auth-primary.auth-full"
        );

    if (button) {
        button.disabled = true;
        button.textContent = "Signing in...";
    }

    try {

        const profile =
            await loginWithBackend(
                email,
                password,
                rememberMe
            );

        openModal(`

            <div class="auth-success">

                <div class="success-circle">
                    ✓
                </div>

                <span class="auth-eyebrow">
                    SIGNED IN
                </span>

                <h2>
                    Welcome back,
                    ${escapeHtml(profile.full_name)}!
                </h2>

                <p>
                    You are securely signed in.
                    Your orders, wishlist and account
                    are now connected to FESTIVALE.
                </p>

                <button
                    class="auth-primary auth-full"
                    onclick="showAccountDashboard()"
                >
                    Go to My Account →
                </button>

            </div>

        `);

    } catch (error) {

        console.error(
            "Login error:",
            error
        );

        showToast(
            "Incorrect email or password."
        );

        if (button) {
            button.disabled = false;
            button.textContent = "Sign In →";
        }

    }

}


/* =========================================================
   PASSWORD
   ========================================================= */

function togglePassword(
    inputId,
    button
) {

    const input =
        document.getElementById(
            inputId
        );

    if (!input) return;


    if (input.type === "password") {

        input.type = "text";

        if (button)
            button.textContent = "◉";

    }

    else {

        input.type = "password";

        if (button)
            button.textContent = "◉";

    }

}


function updatePasswordStrength() {

    const input =
        document.getElementById(
            "accountPassword"
        );

    const fill =
        document.getElementById(
            "strengthFill"
        );

    const text =
        document.getElementById(
            "strengthText"
        );


    if (!input || !fill || !text)
        return;


    const password =
        input.value;


    let score = 0;


    if (password.length >= 8)
        score++;

    if (/[A-Z]/.test(password))
        score++;

    if (/[a-z]/.test(password))
        score++;

    if (/\d/.test(password))
        score++;

    if (/[^A-Za-z0-9]/.test(password))
        score++;


    const percentage =
        Math.min(score, 4) * 25;


    fill.style.width =
        percentage + "%";


    if (!password) {

        text.textContent =
            "Use 8+ characters with letters and numbers.";

    }

    else if (score <= 2) {

        text.textContent =
            "Weak password";

    }

    else if (score === 3) {

        text.textContent =
            "Good password";

    }

    else {

        text.textContent =
            "Strong password";

    }

}


/* =========================================================
   ACCOUNT DASHBOARD
   ========================================================= */

function showAccountDashboard() {

    if (!user) {

        openAccount();

        return;

    }


    openModal(`

        <div class="account-dashboard">

            <div class="account-hero">

                <div class="auth-logo">
                    ${escapeHtml(
                        user.name
                            .charAt(0)
                            .toUpperCase()
                    )}
                </div>

                <div>

                    <span class="auth-eyebrow">
                        MY FESTIVALE
                    </span>

                    <h2>
                        Hello, ${escapeHtml(user.name)}
                    </h2>

                    <p>
                        ${escapeHtml(user.email)}
                    </p>

                </div>

            </div>


            <div class="account-grid">

                <button
                    class="account-action"
                    onclick="showOrders()"
                >
                    📦
                    <strong>
                        My Orders
                    </strong>
                </button>


                <button
                    class="account-action"
                    onclick="showWishlist(); closeModal()"
                >
                    ❤️
                    <strong>
                        Wishlist
                    </strong>
                </button>


                <button
                    class="account-action"
                    onclick="showAddresses()"
                >
                    📍
                    <strong>
                        Addresses
                    </strong>
                </button>


                <button
                    class="account-action"
                    onclick="editProfile()"
                >
                    👤
                    <strong>
                        Edit Profile
                    </strong>
                </button>

            </div>


            <button
                class="auth-secondary auth-full"
                onclick="logout()"
            >
                Sign Out
            </button>

        </div>

    `);

}


/* =========================================================
   PROFILE
   ========================================================= */

function editProfile() {

    openModal(`

        <div class="auth-wrapper">

            <span class="auth-eyebrow">
                ACCOUNT SETTINGS
            </span>

            <h2>
                Edit Profile
            </h2>

            <p>
                Update your FESTIVALE profile.
            </p>


            <div class="auth-form-grid">

                <label class="auth-field">

                    <span>
                        Full Name
                    </span>

                    <div class="auth-input-wrap">

                        <span>
                            👤
                        </span>

                        <input
                            id="profileName"
                            value="${escapeHtml(user.name)}"
                        >

                    </div>

                </label>


                <label class="auth-field">

                    <span>
                        Email Address
                    </span>

                    <div class="auth-input-wrap">

                        <span>
                            ✉️
                        </span>

                        <input
                            id="profileEmail"
                            type="email"
                            value="${escapeHtml(user.email)}"
                        >

                    </div>

                </label>

            </div>


            <button
                class="auth-primary auth-full"
                onclick="saveProfile()"
            >
                Save Changes
            </button>

        </div>

    `);

}


function saveProfile() {

    const name =
        document.getElementById(
            "profileName"
        )?.value.trim();


    const email =
        document.getElementById(
            "profileEmail"
        )?.value.trim();


    if (!name || !email) {

        showToast(
            "Please fill all fields."
        );

        return;

    }


    user.name = name;

    user.email = email;


    saveUser();

    updateAccountGreeting();


    showToast(
        "Profile updated successfully."
    );


    showAccountDashboard();

}


/* =========================================================
   LOGOUT
   ========================================================= */

function logout() {

    authToken = null;
    user = null;

    localStorage.removeItem(
        AUTH_TOKEN_KEY
    );

    sessionStorage.removeItem(
        AUTH_TOKEN_KEY
    );

    localStorage.removeItem(
        "festivaleUser"
    );

    updateAccountGreeting();

    closeModal();

    showToast(
        "You have been signed out."
    );

}


/* =========================================================
   ADDRESS
   ========================================================= */

function showAddresses() {

    let content = `

        <div class="info-card">

            <div class="info-icon">
                📍
            </div>

            <span class="auth-eyebrow">
                DELIVERY
            </span>

            <h2>
                My Addresses
            </h2>

        </div>

    `;


    if (!addresses.length) {

        content += `

            <div class="empty-state">

                <div class="empty-icon">
                    📍
                </div>

                <h3>
                    No saved addresses
                </h3>

                <p>
                    Add an address for faster checkout.
                </p>

            </div>

        `;

    }

    else {

        addresses.forEach(
            function (address, index) {

                content += `

                    <div class="address-card">

                        <strong>
                            Address ${index + 1}
                        </strong>

                        <p>
                            ${escapeHtml(address)}
                        </p>

                        <button
                            class="auth-secondary"
                            onclick="deleteAddress(${index})"
                        >
                            Delete
                        </button>

                    </div>

                `;

            }
        );

    }


    content += `

        <button
            class="auth-primary auth-full"
            onclick="addAddress()"
        >
            + Add New Address
        </button>

    `;


    openModal(content);

}


function addAddress() {

    openModal(`

        <div class="auth-wrapper">

            <span class="auth-eyebrow">
                DELIVERY ADDRESS
            </span>

            <h2>
                Add Address
            </h2>

            <label class="auth-field">

                <span>
                    Address
                </span>

                <div class="auth-input-wrap">

                    <textarea
                        id="newAddress"
                        rows="4"
                        placeholder="Enter your full address"
                    ></textarea>

                </div>

            </label>

            <button
                class="auth-primary auth-full"
                onclick="saveAddress()"
            >
                Save Address
            </button>

        </div>

    `);

}


function saveAddress() {

    const input =
        document.getElementById(
            "newAddress"
        );


    const value =
        input
            ? input.value.trim()
            : "";


    if (!value) {

        showToast(
            "Please enter an address."
        );

        return;

    }


    addresses.push(value);

    localStorage.setItem(
        "festivaleAddresses",
        JSON.stringify(addresses)
    );


    showToast(
        "Address saved."
    );


    showAddresses();

}


function deleteAddress(index) {

    addresses.splice(
        index,
        1
    );


    localStorage.setItem(
        "festivaleAddresses",
        JSON.stringify(addresses)
    );


    showAddresses();

}


/* =========================================================
   ACCOUNT GREETING
   ========================================================= */

function updateAccountGreeting() {

    const element =
        document.getElementById(
            "accountGreeting"
        );


    if (!element) return;


    if (user) {

        element.textContent =
            `Hello, ${user.name}`;

    }

    else {

        element.textContent =
            "Hello, Sign in";

    }

}


/* =========================================================
   FRONTEND POLISH / RESPONSIVE UI
   ========================================================= */

function installFrontendPolish() {
    if (document.getElementById("festivaleFrontendPolish")) return;

    const style = document.createElement("style");
    style.id = "festivaleFrontendPolish";
    style.textContent = `
        .enhanced-product-detail { display:grid; grid-template-columns:minmax(280px,1fr) minmax(280px,1fr); gap:28px; align-items:center; }
        .enhanced-product-detail img { width:100%; max-height:460px; object-fit:cover; border-radius:18px; }
        .detail-quantity-row { display:flex; align-items:center; justify-content:space-between; gap:16px; margin:22px 0; padding:14px 0; border-top:1px solid rgba(0,0,0,.08); border-bottom:1px solid rgba(0,0,0,.08); }
        .detail-quantity-controls { display:flex; align-items:center; gap:12px; }
        .product-detail-actions { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
        .cart-extra-actions { display:grid; grid-template-columns:1fr 1.4fr; gap:10px; margin-top:18px; padding-top:16px; border-top:1px solid rgba(0,0,0,.08); }
        .order-card-clickable { width:100%; text-align:left; border:0; cursor:pointer; display:flex; justify-content:space-between; gap:18px; align-items:center; }
        .order-card-main { display:flex; align-items:center; gap:14px; min-width:0; }
        .order-card-icon { width:46px; height:46px; display:grid; place-items:center; border-radius:12px; background:rgba(0,0,0,.05); flex:0 0 auto; }
        .order-product-preview { max-width:460px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .order-card-side { display:flex; flex-direction:column; align-items:flex-end; gap:5px; flex:0 0 auto; }
        .order-status { display:inline-flex; padding:4px 9px; border-radius:999px; background:rgba(0,0,0,.07); font-size:.82rem; }
        .order-status.success { background:rgba(34,197,94,.12); color:#15803d; }
        .order-view-link { font-size:.82rem; opacity:.75; }
        .order-details-top { display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:22px; }
        .back-link { border:0; background:none; cursor:pointer; font:inherit; padding:4px 0; opacity:.8; }
        .order-details-heading { display:flex; gap:16px; align-items:center; margin-bottom:24px; }
        .order-details-heading h2 { margin:4px 0; }
        .order-details-grid { display:grid; gap:14px; }
        .order-detail-section { padding:18px; border:1px solid rgba(0,0,0,.08); border-radius:14px; }
        .order-detail-section h3 { margin:0 0 12px; }
        .detail-line { display:flex; justify-content:space-between; gap:16px; padding:7px 0; }
        .total-line { margin-top:8px; padding-top:14px; border-top:1px solid rgba(0,0,0,.08); font-size:1.05rem; }
        .formatted-address { line-height:1.65; margin:0; white-space:normal; }
        .order-progress { display:flex; align-items:center; gap:8px; margin-top:22px; overflow-x:auto; padding:8px 2px; }
        .progress-step { display:flex; flex-direction:column; align-items:center; gap:5px; min-width:82px; text-align:center; opacity:.45; font-size:.78rem; }
        .progress-step span { width:30px; height:30px; display:grid; place-items:center; border-radius:50%; background:rgba(0,0,0,.08); }
        .progress-step.active { opacity:1; }
        .progress-step.active span { background:#16a34a; color:white; }
        .progress-line { height:2px; min-width:35px; flex:1; background:rgba(0,0,0,.12); }
        .progress-line.active { background:#16a34a; }
        .frontend-loading { display:grid; place-items:center; min-height:150px; text-align:center; }
        .frontend-loading .spinner { width:34px; height:34px; border:3px solid rgba(0,0,0,.12); border-top-color:currentColor; border-radius:50%; animation:festivaleSpin .8s linear infinite; margin-bottom:10px; }
        @keyframes festivaleSpin { to { transform:rotate(360deg); } }
        @media (max-width: 700px) {
            .enhanced-product-detail { grid-template-columns:1fr; gap:18px; }
            .enhanced-product-detail img { max-height:300px; }
            .product-detail-actions, .cart-extra-actions { grid-template-columns:1fr; }
            .order-card-clickable { align-items:flex-start; flex-direction:column; }
            .order-card-side { align-items:flex-start; }
            .order-details-top { align-items:flex-start; flex-direction:column; }
            .order-details-heading { align-items:flex-start; }
            .detail-line { flex-direction:column; gap:3px; }
            .order-progress { justify-content:flex-start; }
        }
        @media (max-width: 480px) {
            .order-card-main { align-items:flex-start; }
            .order-card-icon { width:38px; height:38px; }
            .order-product-preview { max-width:240px; }
        }
    `;
    document.head.appendChild(style);
}


/* =========================================================
   MODAL
   ========================================================= */

function openModal(content) {

    const modalContent =
        document.getElementById(
            "modalContent"
        );

    const overlay =
        document.getElementById(
            "modalOverlay"
        );


    if (!modalContent || !overlay)
        return;


    modalContent.innerHTML =
        content;


    overlay.style.display =
        "flex";

}


function closeModal() {

    const overlay =
        document.getElementById(
            "modalOverlay"
        );


    if (overlay) {

        overlay.style.display =
            "none";

    }

}


/* =========================================================
   HOME
   ========================================================= */

function goHome() {

    const home =
        document.getElementById(
            "homeSection"
        );


    if (home) {

        home.scrollIntoView({
            behavior: "smooth"
        });

    }


    currentProducts =
        [...products];


    const category =
        document.getElementById(
            "categoryFilter"
        );

    if (category)
        category.value = "all";


    renderProducts(
        currentProducts
    );

}


/* =========================================================
   NAVIGATION HELPERS
   ========================================================= */

function scrollToProducts() {

    const section =
        document.getElementById(
            "productsSection"
        );


    if (section) {

        section.scrollIntoView({
            behavior: "smooth"
        });

    }

}


function scrollToCloud() {

    const section =
        document.getElementById(
            "cloudSection"
        );


    if (section) {

        section.scrollIntoView({
            behavior: "smooth"
        });

    }

}


function openOrders() {

    showOrders();

}


function openWishlist() {

    showWishlist();

}


function toggleMobileMenu() {

    const menu =
        document.getElementById(
            "mobileMenu"
        );


    if (menu) {

        menu.classList.toggle(
            "open"
        );

    }

}


function closeMobileMenu() {

    const menu =
        document.getElementById(
            "mobileMenu"
        );


    if (menu) {

        menu.classList.remove(
            "open"
        );

    }

}


/* =========================================================
   INFORMATION
   ========================================================= */

function showInfo(title) {

    const information = {

        "About FESTIVALE": [
            "✨",
            "About FESTIVALE",
            "FESTIVALE is a smart festival-shopping experience designed for smooth browsing, ordering and intelligent cloud traffic simulation."
        ],

        "Careers": [
            "🚀",
            "Careers",
            "This academic project demonstrates modern e-commerce, cloud architecture and intelligent auto-scaling concepts."
        ],

        "Technology": [
            "☁️",
            "Technology",
            "The project combines a responsive frontend with backend APIs, database services and cloud auto-scaling architecture."
        ],

        "Help Center": [
            "💬",
            "Help Center",
            "Explore account, shopping cart, orders, filters and the cloud monitoring dashboard."
        ],

        "Returns": [
            "↩️",
            "Returns",
            "Return information shown here is part of the FESTIVALE academic project demo."
        ],

        "Contact": [
            "📧",
            "Contact Us",
            "Customer-support integration can be connected to the backend in the next project phase."
        ]

    };


    const info =
        information[title] ||
        [
            "ℹ️",
            title,
            "FESTIVALE information."
        ];


    openModal(`

        <div class="info-card">

            <div class="info-icon">
                ${info[0]}
            </div>

            <span class="auth-eyebrow">
                FESTIVALE
            </span>

            <h2>
                ${info[1]}
            </h2>

            <p>
                ${info[2]}
            </p>

            <button
                class="auth-primary auth-full"
                onclick="closeModal()"
            >
                Continue Shopping
            </button>

        </div>

    `);

}


function showAbout() {

    showInfo(
        "About FESTIVALE"
    );

}


function showCareers() {

    showInfo(
        "Careers"
    );

}


function showSeller() {

    showInfo(
        "Technology"
    );

}


function showHelp() {

    showInfo(
        "Help Center"
    );

}


function showReturns() {

    showInfo(
        "Returns"
    );

}


function showShipping() {

    openModal(`

        <div class="info-card">

            <div class="info-icon">
                🚚
            </div>

            <h2>
                Shipping Information
            </h2>

            <p>
                FESTIVALE provides reliable
                delivery services across supported
                locations.
            </p>

            <p>
                Delivery time depends on the
                product and destination.
            </p>

        </div>

    `);

}


/* =========================================================
   CLOUD MONITORING
   ========================================================= */

const trafficData = {

    low: {
        request: 30,
        cpu: 25,
        response: 110,
        users: 120,
        action: "Maintain",
        decision: "MAINTAIN",
        reason: "System is currently stable."
    },

    normal: {
        request: 60,
        cpu: 45,
        response: 150,
        users: 300,
        action: "Maintain",
        decision: "MAINTAIN",
        reason: "Current traffic is within normal capacity."
    },

    medium: {
        request: 100,
        cpu: 65,
        response: 210,
        users: 550,
        action: "Monitor",
        decision: "MONITOR",
        reason: "Traffic is increasing and resources are being monitored."
    },

    high: {
        request: 150,
        cpu: 82,
        response: 310,
        users: 900,
        action: "Scale Up",
        decision: "SCALE UP",
        reason: "CPU utilization is high and response time is increasing."
    },

    festival: {
        request: 240,
        cpu: 94,
        response: 520,
        users: 1600,
        action: "Scale Up",
        decision: "SCALE UP",
        reason: "Festival traffic exceeds the current instance capacity."
    }

};


let autoTraffic = false;

let autoTrafficTimer = null;


function setTraffic(level) {

    const data = trafficData[level];

    if (!data) return;

    window.currentTrafficLevel = level;

    // IMPORTANT: setTraffic only updates the visual traffic dashboard.
    // It does NOT call the scaling API. This prevents the automatic
    // traffic simulator from overwriting a manual scaling evaluation.
    const ids = {
        requestRate: data.request,
        cpuUsage: data.cpu + "%",
        responseTime: data.response + " ms",
        activeUsers: data.users,
        trafficLevel: level.toUpperCase()
    };

    Object.keys(ids).forEach(function (id) {

        const element = document.getElementById(id);

        if (element) {
            element.textContent = ids[id];
        }

    });

    const cpuBar = document.getElementById("cpuBar");

    if (cpuBar) {
        cpuBar.style.width = Math.min(data.cpu, 100) + "%";
    }

    const requestBar = document.getElementById("requestBar");

    if (requestBar) {
        requestBar.style.width =
            Math.min((data.request / 250) * 100, 100) + "%";
    }

    const responseBar = document.getElementById("responseBar");

    if (responseBar) {
        responseBar.style.width =
            Math.min((data.response / 1000) * 100, 100) + "%";
    }

    const usersBar = document.getElementById("usersBar");

    if (usersBar) {
        usersBar.style.width =
            Math.min((data.users / 1600) * 100, 100) + "%";
    }

}


async function evaluateTrafficSimulation(level) {

    const data = trafficData[level];

    if (!data) return;

    // Update the traffic visuals first. The API call is explicit here,
    // so manual Evaluate Scaling can never be triggered by setTraffic().
    setTraffic(level);

    return evaluateCloudScaling({
        cpu_percent: data.cpu,
        memory_percent: Math.min(data.cpu + 5, 95),
        request_rate: data.request,
        response_time_ms: data.response,
        current_instances: getCloudCurrentInstances(),
        apply_to_aws: true,
        source: "traffic_simulation"
    });

}


/* =========================================================
   CLOUD AUTO-SCALING INTEGRATION
   ========================================================= */

let cloudCurrentInstances = 2;
let cloudLastScalingResult = null;
let cloudHistoryLoaded = false;

// Every evaluation gets a sequence number. If an older automatic
// simulation request finishes after a newer manual evaluation, its
// result is ignored so it cannot overwrite the manual result.
let cloudEvaluationSequence = 0;

function getCloudCurrentInstances() {

    const input =
        document.getElementById("cloudInstances");

    const inputValue =
        input ? Number(input.value) : NaN;

    if (Number.isFinite(inputValue) && inputValue >= 1) {
        cloudCurrentInstances = Math.max(1, Math.min(50, inputValue));
    }

    return cloudCurrentInstances;
}


function setCloudCurrentInstances(value) {

    const parsed = Number(value);

    if (!Number.isFinite(parsed) || parsed < 1) {
        return;
    }

    cloudCurrentInstances =
        Math.max(1, Math.min(50, Math.round(parsed)));

    const input =
        document.getElementById("cloudInstances");

    if (input) {
        input.value = cloudCurrentInstances;
    }

    const display =
        document.getElementById("cloudCurrentInstances");

    if (display) {
        display.textContent = cloudCurrentInstances;
    }

}


function formatScalingAction(action) {

    return String(action || "maintain")
        .replace(/_/g, " ")
        .replace(/\b\w/g, function (letter) {
            return letter.toUpperCase();
        });

}


function getScalingDecisionClass(action) {

    const normalized =
        String(action || "maintain").toLowerCase();

    if (normalized === "scale_up") {
        return "scale-up";
    }

    if (normalized === "scale_down") {
        return "scale-down";
    }

    return "maintain";
}


async function evaluateCloudScaling(overrides = {}) {

    const cpuElement =
        document.getElementById("cloudCpu");

    const memoryElement =
        document.getElementById("cloudMemory");

    const requestElement =
        document.getElementById("cloudRequests");

    const latencyElement =
        document.getElementById("cloudLatency");

    const instanceElement =
        document.getElementById("cloudInstances");

    const cpu =
        Number(overrides.cpu_percent ??
            cpuElement?.value ?? 50);

    const memory =
        Number(overrides.memory_percent ??
            memoryElement?.value ?? 50);

    const requestRate =
        Number(overrides.request_rate ??
            requestElement?.value ?? 80);

    const responseTime =
        Number(overrides.response_time_ms ??
            latencyElement?.value ?? 300);

    const currentInstances =
        Number(overrides.current_instances ??
            getCloudCurrentInstances());

    const applyToAws =
        overrides.apply_to_aws !== undefined
            ? Boolean(overrides.apply_to_aws)
            : true;

    const evaluationId = ++cloudEvaluationSequence;
    const evaluationSource = overrides.source || "manual";

    const payload = {
        cpu_percent: Number.isFinite(cpu) ? cpu : 50,
        memory_percent: Number.isFinite(memory) ? memory : 50,
        request_rate: Number.isFinite(requestRate) ? requestRate : 80,
        response_time_ms: Number.isFinite(responseTime) ? responseTime : 300,
        current_instances:
            Number.isFinite(currentInstances)
                ? Math.max(1, Math.min(50, Math.round(currentInstances)))
                : 2,
        apply_to_aws: applyToAws
    };

    setCloudStatus(
        "Evaluating: CPU " + payload.cpu_percent +
        "% | Memory " + payload.memory_percent +
        "% | Requests " + payload.request_rate +
        "/s | Latency " + payload.response_time_ms +
        " ms | EC2 " + payload.current_instances +
        " | " + (evaluationSource === "manual" ? "Manual" : "Auto Simulation"),
        "loading"
    );

    const button =
        document.getElementById("evaluateScalingButton");

    if (button) {
        button.disabled = true;
        button.textContent = "Evaluating...";
    }

    try {

        const result = await apiRequest(
            "/api/v1/scaling/evaluate-and-act",
            {
                method: "POST",
                body: JSON.stringify(payload)
            }
        );

        // Ignore stale results from an older request. Manual evaluation
        // always wins over an automatic traffic request that started earlier.
        if (evaluationId !== cloudEvaluationSequence) {
            return result;
        }

        cloudLastScalingResult = result;

        updateScalingDashboard(result);

        await loadScalingHistory();

        return result;

    } catch (error) {

        console.error("Cloud scaling evaluation failed:", error);

        applyLocalScalingFallback(payload, error);

        return null;

    } finally {

        if (button) {
            button.disabled = false;
            button.textContent = "Evaluate Scaling";
        }

    }

}


function applyLocalScalingFallback(payload, error) {

    const cpu = Number(payload.cpu_percent);
    const memory = Number(payload.memory_percent);
    const latency = Number(payload.response_time_ms);
    const requestRate = Number(payload.request_rate);
    const current = Number(payload.current_instances);

    let action = "maintain";
    let desired = current;

    if (
        cpu >= 75 ||
        memory >= 80 ||
        latency >= 800 ||
        requestRate >= current * 80
    ) {

        action = "scale_up";

        const step =
            cpu >= 85 || latency >= 1200
                ? 2
                : 1;

        desired = Math.min(50, current + step);

    } else if (
        cpu <= 30 &&
        memory <= 40 &&
        latency <= 350 &&
        requestRate <= current * 25 &&
        current > 1
    ) {

        action = "scale_down";
        desired = Math.max(1, current - 1);

    }

    const fallbackResult = {
        decision: {
            action: action,
            current_instances: current,
            desired_instances: desired,
            confidence: 0,
            reason:
                "Backend unavailable. Local frontend fallback was used."
        },
        aws_applied: false,
        aws_message: error
            ? error.message
            : "Backend unavailable.",
        db_logged: false
    };

    updateScalingDashboard(
        fallbackResult,
        true
    );

    setCloudStatus(
        "Backend unavailable — local fallback",
        "warning"
    );

}


function updateScalingDashboard(result, localFallback = false) {

    console.log(
        "Updating scaling dashboard:",
        result
    );

    const decisionData =
        result?.decision || {};

    const action =
        String(decisionData.action || "maintain")
            .toLowerCase();

    const currentInstances =
        Number(
            decisionData.current_instances ??
            getCloudCurrentInstances()
        );

    const desiredInstances =
        Number(
            decisionData.desired_instances ??
            currentInstances
        );

    const confidence =
        decisionData.confidence;

    const reason =
        decisionData.reason ||
        "Scaling decision generated by the backend.";

    const displayAction =
        formatScalingAction(action);

    const displayDecision =
        action
            .replace(/_/g, " ")
            .toUpperCase();

    const scalingDecision =
        document.getElementById("scalingDecision");

    if (scalingDecision) {
        scalingDecision.textContent =
            displayDecision;
    }

    const decisionText =
        document.getElementById("decisionText");

    if (decisionText) {
        decisionText.textContent =
            displayAction;
    }

    const recommendedAction =
        document.getElementById("recommendedAction");

    if (recommendedAction) {
        recommendedAction.textContent =
            displayAction;
    }

    const trafficLevel =
        document.getElementById("trafficLevel");

    if (trafficLevel && window.currentTrafficLevel) {
        trafficLevel.textContent =
            String(window.currentTrafficLevel).toUpperCase();
    }

    const decisionReason =
        document.getElementById("decisionReason");

    if (decisionReason) {

        let text = reason;

        if (confidence !== undefined && confidence !== null) {
            text +=
                " Confidence: " +
                Math.round(Number(confidence) * 100) +
                "%.";
        }

        if (result.aws_applied) {
            text +=
                " AWS scaling action applied.";
        }

        if (result.aws_message) {
            text +=
                " " + result.aws_message;
        }

        if (localFallback) {
            text +=
                " This is a frontend fallback, not a backend/RL result.";
        }

        decisionReason.textContent = text;

    }

    setCloudCurrentInstances(
        desiredInstances
    );

    const currentDisplay =
        document.getElementById("cloudCurrentInstances");

    if (currentDisplay) {
        currentDisplay.textContent =
            currentInstances;
    }

    const desiredDisplay =
        document.getElementById("cloudDesiredInstances");

    if (desiredDisplay) {
        desiredDisplay.textContent =
            desiredInstances;
    }

    const confidenceDisplay =
        document.getElementById("cloudConfidence");

    if (confidenceDisplay) {

        confidenceDisplay.textContent =
            confidence === undefined ||
            confidence === null
                ? "—"
                : Math.round(Number(confidence) * 100) + "%";

    }

    const reasonDisplay =
        document.getElementById("cloudReason");

    if (reasonDisplay) {
        reasonDisplay.textContent = reason;
    }

    const awsStatus =
        document.getElementById("cloudAwsStatus");

    if (awsStatus) {

        if (result.aws_applied) {
            awsStatus.textContent =
                result.aws_message ||
                "Scaling action applied";
        } else {
            awsStatus.textContent =
                result.aws_message ||
                "No AWS action applied";
        }

    }

    const actionClass =
        getScalingDecisionClass(action);

    [scalingDecision, decisionText, recommendedAction]
        .filter(Boolean)
        .forEach(function (element) {

            element.classList.remove(
                "scale-up",
                "scale-down",
                "maintain"
            );

            element.classList.add(
                actionClass
            );

        });

    updateInstanceDisplay(
        desiredInstances
    );

}


function updateInstanceDisplay(count) {

    const safeCount =
        Math.max(
            1,
            Math.min(
                50,
                Number(count) || 1
            )
        );

    const instanceCount =
        document.getElementById("instanceCount");

    if (instanceCount) {
        instanceCount.textContent =
            Math.round(safeCount);
    }

    const visual =
        document.getElementById("instanceVisual");

    if (visual) {

        const visibleBoxes =
            Math.min(
                Math.round(safeCount),
                10
            );

        visual.innerHTML =
            Array.from(
                { length: visibleBoxes },
                function (_, index) {

                    return `
                        <span class="instance-box" title="EC2 instance ${index + 1}">
                            EC2
                        </span>
                    `;

                }
            ).join("");

        if (safeCount > 10) {

            visual.innerHTML += `
                <span class="instance-box" title="${Math.round(safeCount)} total instances">
                    +${Math.round(safeCount) - 10}
                </span>
            `;

        }

    }

}


function setCloudStatus(message, type = "info") {

    const status =
        document.getElementById("cloudStatus");

    if (!status) return;

    status.textContent = message;
    status.dataset.status = type;

}


async function loadScalingHistory() {

    const container =
        document.getElementById("scalingHistory");

    if (!container) return;

    try {

        const history =
            await apiRequest(
                "/api/v1/scaling/history"
            );

        const rows =
            Array.isArray(history)
                ? history
                : [];

        if (!rows.length) {

            container.innerHTML = `
                <div class="cloud-history-empty">
                    No scaling decisions recorded yet.
                </div>
            `;

            cloudHistoryLoaded = true;
            return;

        }

        const latest =
            rows
                .slice()
                .sort(function (a, b) {
                    return Number(b.id || 0) -
                        Number(a.id || 0);
                })
                .slice(0, 5);

        container.innerHTML =
            latest.map(function (item) {

                const action =
                    String(item.action || "maintain")
                        .toLowerCase();

                const current =
                    item.current_instances ?? "—";

                const desired =
                    item.desired_instances ?? "—";

                const confidence =
                    item.confidence !== undefined &&
                    item.confidence !== null
                        ? Math.round(
                            Number(item.confidence) * 100
                        ) + "%"
                        : "—";

                return `
                    <div class="cloud-history-row">
                        <div>
                            <strong>
                                ${escapeHtml(formatScalingAction(action))}
                            </strong>
                            <small>
                                ${escapeHtml(item.reason || "No reason provided")}
                            </small>
                        </div>

                        <div>
                            <strong>${escapeHtml(String(current))} → ${escapeHtml(String(desired))}</strong>
                            <small>${escapeHtml(confidence)} confidence</small>
                        </div>
                    </div>
                `;

            }).join("");

        cloudHistoryLoaded = true;

    } catch (error) {

        console.warn(
            "Could not load scaling history:",
            error.message
        );

        container.innerHTML = `
            <div class="cloud-history-empty">
                Scaling history unavailable.
            </div>
        `;

    }

}



function getSavedCloudInputs() {
    try {
        const saved = JSON.parse(sessionStorage.getItem("festivaleCloudManualInputs") || "null");
        if (saved && typeof saved === "object") return saved;
    } catch (e) {}
    return { cpu: 50, memory: 50, requests: 80, latency: 300, instances: 2 };
}

function saveCloudInputs() {
    const values = {
        cpu: document.getElementById("cloudCpu")?.value ?? "50",
        memory: document.getElementById("cloudMemory")?.value ?? "50",
        requests: document.getElementById("cloudRequests")?.value ?? "80",
        latency: document.getElementById("cloudLatency")?.value ?? "300",
        instances: document.getElementById("cloudInstances")?.value ?? "2"
    };
    sessionStorage.setItem("festivaleCloudManualInputs", JSON.stringify(values));
    return values;
}

function restoreCloudInputs() {
    const saved = getSavedCloudInputs();
    const map = {
        cloudCpu: saved.cpu,
        cloudMemory: saved.memory,
        cloudRequests: saved.requests,
        cloudLatency: saved.latency,
        cloudInstances: saved.instances
    };
    Object.entries(map).forEach(([id, value]) => {
        const el = document.getElementById(id);
        if (el && value !== undefined && value !== null) el.value = value;
    });
}

function createCloudScalingControls() {

    const cloudSection =
        document.getElementById("cloudSection");

    if (!cloudSection) return;

    const savedCloudInputs = getSavedCloudInputs();

    if (document.getElementById("cloudScalingControls")) {
        return;
    }

    const wrapper =
        document.createElement("div");

    wrapper.id =
        "cloudScalingControls";

    wrapper.innerHTML = `

        <div style="
            margin-top:28px;
            padding:24px;
            border:1px solid rgba(255,255,255,.12);
            border-radius:18px;
            background:rgba(255,255,255,.04);
        ">

            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
                gap:16px;
                flex-wrap:wrap;
                margin-bottom:18px;
            ">

                <div>
                    <div style="
                        font-size:11px;
                        letter-spacing:2px;
                        opacity:.7;
                        margin-bottom:5px;
                    ">
                        LIVE CLOUD CONTROL
                    </div>

                    <h3 style="margin:0;">
                        Intelligent Auto-Scaling
                    </h3>

                    <p style="
                        margin:6px 0 0;
                        opacity:.7;
                        font-size:13px;
                    ">
                        Sends workload telemetry to the FastAPI scaling service.
                    </p>
                </div>

                <div
                    id="cloudStatus"
                    data-status="info"
                    style="
                        padding:8px 12px;
                        border-radius:999px;
                        background:rgba(255,255,255,.08);
                        font-size:12px;
                    "
                >
                    Ready
                </div>

            </div>


            <div style="
                display:grid;
                grid-template-columns:
                    repeat(auto-fit,minmax(150px,1fr));
                gap:12px;
            ">

                <label style="font-size:12px;">
                    CPU %
                    <input
                        id="cloudCpu"
                        type="number"
                        min="0"
                        max="100"
                        value="${savedCloudInputs.cpu}"
                        style="
                            width:100%;
                            margin-top:6px;
                            padding:10px;
                            border-radius:9px;
                            border:1px solid rgba(255,255,255,.15);
                            background:rgba(0,0,0,.18);
                            color:inherit;
                        "
                    >
                </label>

                <label style="font-size:12px;">
                    Memory %
                    <input
                        id="cloudMemory"
                        type="number"
                        min="0"
                        max="100"
                        value="${savedCloudInputs.memory}"
                        style="
                            width:100%;
                            margin-top:6px;
                            padding:10px;
                            border-radius:9px;
                            border:1px solid rgba(255,255,255,.15);
                            background:rgba(0,0,0,.18);
                            color:inherit;
                        "
                    >
                </label>

                <label style="font-size:12px;">
                    Requests / sec
                    <input
                        id="cloudRequests"
                        type="number"
                        min="0"
                        value="${savedCloudInputs.requests}"
                        style="
                            width:100%;
                            margin-top:6px;
                            padding:10px;
                            border-radius:9px;
                            border:1px solid rgba(255,255,255,.15);
                            background:rgba(0,0,0,.18);
                            color:inherit;
                        "
                    >
                </label>

                <label style="font-size:12px;">
                    Latency (ms)
                    <input
                        id="cloudLatency"
                        type="number"
                        min="0"
                        value="${savedCloudInputs.latency}"
                        style="
                            width:100%;
                            margin-top:6px;
                            padding:10px;
                            border-radius:9px;
                            border:1px solid rgba(255,255,255,.15);
                            background:rgba(0,0,0,.18);
                            color:inherit;
                        "
                    >
                </label>

                <label style="font-size:12px;">
                    Current EC2
                    <input
                        id="cloudInstances"
                        type="number"
                        min="1"
                        max="50"
                        value="${savedCloudInputs.instances}"
                        style="
                            width:100%;
                            margin-top:6px;
                            padding:10px;
                            border-radius:9px;
                            border:1px solid rgba(255,255,255,.15);
                            background:rgba(0,0,0,.18);
                            color:inherit;
                        "
                    >
                </label>

            </div>


            <div style="
                display:flex;
                gap:10px;
                flex-wrap:wrap;
                margin-top:16px;
            ">

                <button
                    id="evaluateScalingButton"
                    type="button"
                    class="auth-primary"
                >
                    Evaluate Scaling
                </button>

                <button
                    id="loadScalingHistoryButton"
                    type="button"
                    class="auth-secondary"
                >
                    Refresh History
                </button>

            </div>


            <div style="
                display:grid;
                grid-template-columns:
                    repeat(auto-fit,minmax(150px,1fr));
                gap:12px;
                margin-top:18px;
            ">

                <div style="
                    padding:14px;
                    border-radius:12px;
                    background:rgba(255,255,255,.04);
                ">
                    <small>Current Instances</small>
                    <strong
                        id="cloudCurrentInstances"
                        style="
                            display:block;
                            font-size:24px;
                            margin-top:4px;
                        "
                    >
                        ${cloudCurrentInstances}
                    </strong>
                </div>

                <div style="
                    padding:14px;
                    border-radius:12px;
                    background:rgba(255,255,255,.04);
                ">
                    <small>Desired Instances</small>
                    <strong
                        id="cloudDesiredInstances"
                        style="
                            display:block;
                            font-size:24px;
                            margin-top:4px;
                        "
                    >
                        ${cloudCurrentInstances}
                    </strong>
                </div>

                <div style="
                    padding:14px;
                    border-radius:12px;
                    background:rgba(255,255,255,.04);
                ">
                    <small>Confidence</small>
                    <strong
                        id="cloudConfidence"
                        style="
                            display:block;
                            font-size:24px;
                            margin-top:4px;
                        "
                    >
                        —
                    </strong>
                </div>

                <div style="
                    padding:14px;
                    border-radius:12px;
                    background:rgba(255,255,255,.04);
                ">
                    <small>AWS Status</small>
                    <strong
                        id="cloudAwsStatus"
                        style="
                            display:block;
                            font-size:13px;
                            margin-top:8px;
                        "
                    >
                        Not evaluated
                    </strong>
                </div>

            </div>


            <div style="
                margin-top:14px;
                padding:14px;
                border-radius:12px;
                background:rgba(255,255,255,.04);
            ">
                <small>Decision Reason</small>
                <p
                    id="cloudReason"
                    style="margin:7px 0 0;line-height:1.55;"
                >
                    No scaling decision has been evaluated yet.
                </p>
            </div>


            <div style="
                margin-top:18px;
            ">

                <div style="
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                    margin-bottom:10px;
                ">
                    <strong>Recent Scaling History</strong>
                    <span style="font-size:12px;opacity:.65;">
                        Latest 5 decisions
                    </span>
                </div>

                <div id="scalingHistory">
                    <div class="cloud-history-empty">
                        Loading scaling history...
                    </div>
                </div>

            </div>

        </div>

    `;

    cloudSection.appendChild(wrapper);

    const evaluateButton =
        document.getElementById("evaluateScalingButton");

    if (evaluateButton) {

        evaluateButton.onclick = async function (event) {
            event.preventDefault();
            event.stopPropagation();

            // Turn off automatic simulation so it cannot overwrite
            // the values while a manual test is running.
            if (autoTraffic) {
                autoTraffic = false;
                clearInterval(autoTrafficTimer);
                autoTrafficTimer = null;
                const autoButton = document.getElementById("autoTrafficButton");
                if (autoButton) autoButton.textContent = "Start Auto Simulation";
            }

            const values = saveCloudInputs();

            await evaluateCloudScaling({
                cpu_percent: Number(values.cpu),
                memory_percent: Number(values.memory),
                request_rate: Number(values.requests),
                response_time_ms: Number(values.latency),
                current_instances: Number(values.instances),
                apply_to_aws: true,
                source: "manual"
            });

            // Restore exactly what the user entered. The scaling result
            // may change the displayed desired/current instance count,
            // but it must never replace the manual input values.
            restoreCloudInputs();
        };

    }

    const historyButton =
        document.getElementById(
            "loadScalingHistoryButton"
        );

    if (historyButton) {

        historyButton.addEventListener(
            "click",
            function () {
                loadScalingHistory();
            }
        );

    }

    ["cloudCpu", "cloudMemory", "cloudRequests", "cloudLatency", "cloudInstances"].forEach(function (id) {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener("input", saveCloudInputs);
            input.addEventListener("change", saveCloudInputs);
        }
    });

    restoreCloudInputs();

    const instanceInput =
        document.getElementById("cloudInstances");

    if (instanceInput) {

        instanceInput.addEventListener(
            "change",
            function () {
                setCloudCurrentInstances(
                    instanceInput.value
                );
            }
        );

    }

}


function initializeCloudMonitoring() {

    createCloudScalingControls();

    updateInstanceDisplay(
        getCloudCurrentInstances()
    );

    loadScalingHistory();
    restoreCloudInputs();

}


/* =========================================================
   AUTOMATIC TRAFFIC SIMULATION
   ========================================================= */

function toggleAuto() {

    autoTraffic =
        !autoTraffic;

    const button =
        document.getElementById("autoTrafficButton");

    // Manual Evaluate Scaling is always independent of this switch.
    // Auto traffic is the only feature allowed to call setTraffic()
    // repeatedly in the background.

    if (autoTraffic) {

        const levels = [
            "low",
            "normal",
            "medium",
            "high",
            "festival"
        ];

        let index = 0;

        evaluateTrafficSimulation(
            levels[index]
        );

        autoTrafficTimer =
            setInterval(
                function () {

                    if (!autoTraffic) {
                        return;
                    }

                    index =
                        (index + 1) %
                        levels.length;

                    evaluateTrafficSimulation(
                        levels[index]
                    );

                },
                5000
            );

        if (button) {
            button.textContent =
                "Stop Auto Simulation";
        }

        showToast(
            "Automatic traffic simulation enabled."
        );

    } else {

        clearInterval(
            autoTrafficTimer
        );

        autoTrafficTimer =
            null;

        if (button) {
            button.textContent =
                "Start Auto Simulation";
        }

        showToast(
            "Automatic traffic simulation stopped."
        );

    }

}


function toggleAutoTraffic() {

    toggleAuto();

}


/* =========================================================
   INITIAL CLOUD STATE
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        initializeCloudMonitoring();

        // Show the normal dashboard values on first load,
        // but do NOT send an automatic scaling decision.
        // Manual evaluation is controlled only by the
        // "Evaluate Scaling" button.
        const initialData = trafficData.normal;

        const initialIds = {
            requestRate: initialData.request,
            cpuUsage: initialData.cpu + "%",
            responseTime: initialData.response + " ms",
            activeUsers: initialData.users,
            trafficLevel: "NORMAL",
            decisionText: "Ready",
            decisionReason: "Enter workload values and click Evaluate Scaling.",
            recommendedAction: "Ready"
        };

        Object.keys(initialIds).forEach(function (id) {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = initialIds[id];
            }
        });

        const cpuBar = document.getElementById("cpuBar");
        if (cpuBar) cpuBar.style.width = initialData.cpu + "%";

        const requestBar = document.getElementById("requestBar");
        if (requestBar) {
            requestBar.style.width =
                Math.min((initialData.request / 250) * 100, 100) + "%";
        }

        const responseBar = document.getElementById("responseBar");
        if (responseBar) {
            responseBar.style.width =
                Math.min((initialData.response / 1000) * 100, 100) + "%";
        }

        const usersBar = document.getElementById("usersBar");
        if (usersBar) {
            usersBar.style.width =
                Math.min((initialData.users / 1600) * 100, 100) + "%";
        }

    }
);


/* =========================================================
   CART OVERLAY
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const overlay =
            document.getElementById(
                "cartOverlay"
            );

        if (overlay) {

            overlay.addEventListener(
                "click",
                closeCart
            );

        }

    }
);


/* =========================================================
   GLOBAL COMPATIBILITY
   ========================================================= */

window.openAccount = openAccount;
window.openOrders = openOrders;
window.openWishlist = openWishlist;

window.showCreateAccount =
    showCreateAccount;

window.showSignIn =
    showSignIn;

window.createAccount =
    createAccount;

window.signIn =
    signIn;

window.togglePassword =
    togglePassword;

window.updatePasswordStrength =
    updatePasswordStrength;

window.filterCategory =
    filterCategory;

window.resetFilters =
    resetFilters;

window.searchProducts =
    searchProducts;

window.sortProducts =
    sortProducts;

window.applyProductFilters =
    applyProductFilters;

window.addToCart =
    addToCart;

window.openCart =
    openCart;

window.closeCart =
    closeCart;

window.changeQuantity =
    changeQuantity;

window.removeFromCart =
    removeFromCart;

window.openCheckout =
    openCheckout;

window.checkout =
    checkout;

window.toggleWishlist =
    toggleWishlist;

window.showWishlist =
    showWishlist;

window.showOrders =
    showOrders;

window.viewProduct =
    viewProduct;

window.goHome =
    goHome;

window.scrollToProducts =
    scrollToProducts;

window.scrollToCloud =
    scrollToCloud;

window.toggleMobileMenu =
    toggleMobileMenu;

window.closeMobileMenu =
    closeMobileMenu;

window.showInfo =
    showInfo;

window.showAbout =
    showAbout;

window.showCareers =
    showCareers;

window.showSeller =
    showSeller;

window.showHelp =
    showHelp;

window.showReturns =
    showReturns;

window.showShipping =
    showShipping;

window.showAccountDashboard =
    showAccountDashboard;

window.editProfile =
    editProfile;

window.saveProfile =
    saveProfile;

window.logout =
    logout;

window.showAddresses =
    showAddresses;

window.addAddress =
    addAddress;

window.saveAddress =
    saveAddress;

window.deleteAddress =
    deleteAddress;

window.openModal =
    openModal;

window.closeModal =
    closeModal;

window.setTraffic =
    setTraffic;

window.evaluateTrafficSimulation =
    evaluateTrafficSimulation;

window.toggleAuto =
    toggleAuto;

window.toggleAutoTraffic =
    toggleAutoTraffic;

window.evaluateCloudScaling =
    evaluateCloudScaling;

window.loadScalingHistory =
    loadScalingHistory;

window.initializeCloudMonitoring =
    initializeCloudMonitoring;