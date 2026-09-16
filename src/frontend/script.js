/* =========================================================
   FESTIVALE - COMPLETE FRONTEND JAVASCRIPT
   ========================================================= */

/* =========================================================
   DATA
   ========================================================= */

let cart = JSON.parse(localStorage.getItem("festivaleCart")) || [];
let orders = JSON.parse(localStorage.getItem("festivaleOrders")) || [];
let wishlist = JSON.parse(localStorage.getItem("festivaleWishlist")) || [];
let addresses = JSON.parse(localStorage.getItem("festivaleAddresses")) || [];
let user = JSON.parse(localStorage.getItem("festivaleUser")) || null;

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

document.addEventListener("DOMContentLoaded", function () {

    setupFilters();

    renderProducts(currentProducts);

    updateCartCount();

    updateAccountGreeting();

    updateProductCount();

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
    localStorage.setItem(
        "festivaleUser",
        JSON.stringify(user)
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

    const product =
        products.find(
            item => item.id === id
        );

    if (!product) return;


    const discount =
        product.oldPrice
            ? Math.round(
                (1 - product.price / product.oldPrice) * 100
            )
            : 0;


    openModal(`

        <div class="product-detail">

            <div class="product-detail-image">

                <img
                    src="${product.image}"
                    alt="${escapeHtml(product.name)}"
                >

            </div>

            <div class="product-detail-info">

                <span class="section-label">
                    ${escapeHtml(product.category)}
                </span>

                <h2>
                    ${escapeHtml(product.name)}
                </h2>

                <div class="rating">
                    ⭐ ${product.rating}
                    <span class="review-count">
                        Customer rating
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

                ${
                    discount
                        ? `
                            <div class="discount-badge">
                                ${discount}% OFF
                            </div>
                          `
                        : ""
                }

                <p class="stock-label">
                    ✓ In stock
                </p>

                <p>
                    Enjoy festival shopping with
                    FESTIVALE. This product is part
                    of our festival collection.
                </p>

                <button
                    class="auth-primary auth-full"
                    onclick="addToCart(${product.id}); closeModal();"
                >
                    Add to Cart
                </button>

            </div>

        </div>

    `);

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
                    <strong>${cart.length}</strong>
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

            <label class="form-group">

                <span>
                    Delivery Address
                </span>

                <textarea
                    id="checkoutAddress"
                    placeholder="Enter your delivery address"
                    rows="3"
                ></textarea>

            </label>

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


function checkout() {

    const address =
        document.getElementById(
            "checkoutAddress"
        )?.value.trim();


    const payment =
        document.getElementById(
            "paymentMethod"
        )?.value;


    if (!address) {

        showToast(
            "Please enter your delivery address."
        );

        return;

    }


    if (!user) {

        showToast(
            "Please create an account first."
        );

        return;

    }


    let total = 0;


    cart.forEach(function (item) {

        const product =
            products.find(
                p => p.id === item.id
            );

        if (product) {

            total +=
                product.price *
                item.quantity;

        }

    });


    const order = {

        id:
            "FV" +
            Date.now()
                .toString()
                .slice(-8),

        date:
            new Date()
                .toLocaleString(),

        total: total,

        payment: payment,

        address: address,

        items:
            [...cart],

        status:
            "Order Placed"

    };


    orders.push(order);

    saveOrders();


    cart = [];

    saveCart();

    updateCartCount();

    closeCart();


    openModal(`

        <div class="auth-success">

            <div class="success-circle">
                ✓
            </div>

            <span class="auth-eyebrow">
                ORDER CONFIRMED
            </span>

            <h2>
                Thank you, ${escapeHtml(user.name)}!
            </h2>

            <p>
                Your order has been placed successfully.
            </p>

            <p>
                Order ID:
                <strong>${order.id}</strong>
            </p>

            <button
                class="auth-primary auth-full"
                onclick="closeModal()"
            >
                Continue Shopping →
            </button>

        </div>

    `);

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

function showOrders() {

    if (!user) {

        openAccount();

        return;

    }


    let content = `

        <div class="info-card">

            <div class="info-icon">
                📦
            </div>

            <span class="auth-eyebrow">
                ORDER HISTORY
            </span>

            <h2>
                My Orders
            </h2>

        </div>

    `;


    if (!orders.length) {

        content += `

            <div class="empty-state">

                <div class="empty-icon">
                    📦
                </div>

                <h3>
                    No orders yet
                </h3>

                <p>
                    Your placed orders will appear here.
                </p>

            </div>

        `;

    }

    else {

        orders
            .slice()
            .reverse()
            .forEach(function (order) {

                content += `

                    <div class="order-card">

                        <div>
                            <strong>
                                Order ${order.id}
                            </strong>

                            <p>
                                ${order.date}
                            </p>
                        </div>

                        <div>
                            <strong>
                                ₹${Number(order.total).toLocaleString("en-IN")}
                            </strong>

                            <p>
                                ${order.status}
                            </p>
                        </div>

                    </div>

                `;

            });

    }


    openModal(content);

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

function createAccount() {

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


    if (
        !name ||
        !email ||
        !password ||
        !confirm
    ) {

        showToast(
            "Please complete all fields."
        );

        return;

    }


    if (
        !/^[^\s@]+@[^\s@]+\.[^\s@]+$/
            .test(email)
    ) {

        showToast(
            "Please enter a valid email address."
        );

        return;

    }


    if (password.length < 8) {

        showToast(
            "Password must contain at least 8 characters."
        );

        return;

    }


    if (
        !/[A-Za-z]/.test(password) ||
        !/\d/.test(password)
    ) {

        showToast(
            "Use at least one letter and one number."
        );

        return;

    }


    if (password !== confirm) {

        showToast(
            "Passwords do not match."
        );

        return;

    }


    if (!terms) {

        showToast(
            "Please accept the Terms & Conditions."
        );

        return;

    }


    user = {

        name: name,

        email: email,

        password: password,

        createdAt:
            new Date().toISOString()

    };


    saveUser();

    updateAccountGreeting();


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
                Start exploring your festival favourites.
            </p>

            <button
                class="auth-primary auth-full"
                onclick="showAccountDashboard()"
            >
                Start Shopping →
            </button>

        </div>

    `);

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


function signIn() {

    const email =
        document.getElementById(
            "signInEmail"
        )?.value.trim().toLowerCase();


    const password =
        document.getElementById(
            "signInPassword"
        )?.value || "";


    if (!email || !password) {

        showToast(
            "Please enter your email and password."
        );

        return;

    }


    const savedUser =
        JSON.parse(
            localStorage.getItem(
                "festivaleUser"
            ) || "null"
        );


    if (!savedUser) {

        showToast(
            "No account found. Please create an account first."
        );

        return;

    }


    if (
        savedUser.email.toLowerCase() !== email ||
        savedUser.password !== password
    ) {

        showToast(
            "Incorrect email or password."
        );

        return;

    }


    user = savedUser;

    updateAccountGreeting();


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
                ${escapeHtml(savedUser.name)}!
            </h2>

            <p>
                Your account is ready.
                You can now access your orders
                and wishlist.
            </p>

            <button
                class="auth-primary auth-full"
                onclick="showAccountDashboard()"
            >
                Go to My Account →
            </button>

        </div>

    `);

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

    user = null;

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

    const data =
        trafficData[level];


    if (!data) return;


    const ids = {

        requestRate: data.request,

        cpuUsage: data.cpu + "%",

        responseTime: data.response + " ms",

        activeUsers: data.users,

        scalingDecision: data.decision,

        decisionText: data.action,

        decisionReason: data.reason,

        trafficLevel:
            level.toUpperCase(),

        recommendedAction:
            data.action

    };


    Object.keys(ids).forEach(
        function (id) {

            const element =
                document.getElementById(id);

            if (element) {

                element.textContent =
                    ids[id];

            }

        }
    );


    const cpuBar =
        document.getElementById(
            "cpuBar"
        );

    if (cpuBar) {

        cpuBar.style.width =
            data.cpu + "%";

    }


    const requestBar =
        document.getElementById(
            "requestBar"
        );

    if (requestBar) {

        requestBar.style.width =
            Math.min(
                data.request / 2.5,
                100
            ) + "%";

    }


    const responseBar =
        document.getElementById(
            "responseBar"
        );

    if (responseBar) {

        responseBar.style.width =
            Math.min(
                data.response / 5,
                100
            ) + "%";

    }


    const usersBar =
        document.getElementById(
            "usersBar"
        );

    if (usersBar) {

        usersBar.style.width =
            Math.min(
                data.users / 16,
                100
            ) + "%";

    }


    const instanceCount =
        document.getElementById(
            "instanceCount"
        );


    if (instanceCount) {

        instanceCount.textContent =
            data.cpu >= 80
                ? "4"
                : data.cpu >= 60
                    ? "3"
                    : "2";

    }


    const visual =
        document.getElementById(
            "instanceVisual"
        );


    if (visual) {

        const count =
            data.cpu >= 80
                ? 4
                : data.cpu >= 60
                    ? 3
                    : 2;


        visual.innerHTML =
            Array.from(
                { length: count },
                function () {

                    return `
                        <span class="instance-box">
                            EC2
                        </span>
                    `;

                }
            ).join("");

    }

}


function toggleAuto() {

    autoTraffic =
        !autoTraffic;


    if (autoTraffic) {

        let levels =
            [
                "low",
                "normal",
                "medium",
                "high",
                "festival"
            ];

        let index = 0;


        setTraffic(
            levels[index]
        );


        autoTrafficTimer =
            setInterval(
                function () {

                    index =
                        (index + 1) %
                        levels.length;

                    setTraffic(
                        levels[index]
                    );

                },
                2200
            );


        showToast(
            "Automatic traffic simulation enabled."
        );

    }

    else {

        clearInterval(
            autoTrafficTimer
        );

        autoTrafficTimer =
            null;


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

        setTraffic("normal");

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

window.toggleAuto =
    toggleAuto;

window.toggleAutoTraffic =
    toggleAutoTraffic;