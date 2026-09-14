/* =========================================================
   Smart Student Assistant — UI interactions (ES6+)
   ========================================================= */
(() => {
    "use strict";

    document.addEventListener("DOMContentLoaded", () => {
        initNavbar();
        initActiveLinks();
        initRevealAnimations();
        initToasts();
        initPasswordToggles();
        initNavToggles();
        initStaggeredCards();
        initRegisterRoles();
    });

    /* ---------- Sticky navbar shadow on scroll ---------- */
    function initNavbar() {
        const navbar = document.querySelector(".navbar");
        if (!navbar) return;

        const onScroll = () => {
            navbar.classList.toggle("scrolled", window.scrollY > 12);
        };

        window.addEventListener("scroll", onScroll, { passive: true });
        onScroll();
    }

    /* ---------- Mobile menu toggle ---------- */
    function initNavToggles() {
        const toggle = document.querySelector(".nav-toggle");
        const links = document.querySelector(".nav-links");

        document.querySelectorAll("[data-nav-toggle]").forEach((btn) => {
            btn.addEventListener("click", () => {
                if (!links) return;
                const open = links.classList.toggle("open");
                btn.classList.toggle("open", open);
                btn.setAttribute("aria-expanded", open ? "true" : "false");
            });
        });

        if (toggle && links) {
            links.addEventListener("click", (e) => {
                if (e.target.closest("a")) {
                    links.classList.remove("open");
                    toggle.classList.remove("open");
                }
            });
        }
    }

    /* ---------- Highlight active nav link ---------- */
    function initActiveLinks() {
        const path = window.location.pathname;
        document.querySelectorAll(".nav-links a[data-nav]").forEach((link) => {
            const href = link.getAttribute("href") || "";
            if (href !== "/" && path.startsWith(href)) {
                link.classList.add("active");
            }
        });
    }

    /* ---------- Scroll-reveal animations ---------- */
    function initRevealAnimations() {
        const items = document.querySelectorAll(".reveal");
        if (!items.length) return;

        if (!("IntersectionObserver" in window)) {
            items.forEach((el) => el.classList.add("is-visible"));
            return;
        }

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("is-visible");
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
        );

        items.forEach((el) => observer.observe(el));
    }

    /* ---------- Staggered entrance for grid cards ---------- */
    function initStaggeredCards() {
        document.querySelectorAll(".grid-cards, .dashboard-grid, .stats-row").forEach((container) => {
            Array.from(container.children || []).forEach((child, index) => {
                child.style.setProperty("--i", index);
            });
        });
    }

    /* ---------- Auto-dismiss Django messages ---------- */
    function initToasts() {
        const container = document.querySelector(".messages-container");
        if (!container) return;

        container.querySelectorAll(".message-toast").forEach((toast) => {
            const delay = parseInt(toast.dataset.delay || "4500", 10);

            setTimeout(() => {
                toast.classList.add("toast-leave");
                toast.addEventListener("animationend", () => toast.remove(), { once: true });
            }, delay);

            toast.addEventListener("click", () => {
                toast.classList.add("toast-leave");
                toast.addEventListener("animationend", () => toast.remove(), { once: true });
            });

            toast.setAttribute("role", "status");
            toast.setAttribute("aria-live", "polite");
        });
    }

    /* ---------- Register: hide/show CV by role ---------- */
    function initRegisterRoles() {
        const roleField = document.getElementById("id_role");
        const cvInput = document.getElementById("id_cv_file");
        if (!roleField || !cvInput) return;

        const cvGroup = cvInput.closest(".form-group");

        const update = () => {
            const isInstructor = roleField.value === "instructor";
            if (cvGroup) cvGroup.hidden = !isInstructor;
            cvInput.required = isInstructor;
        };

        roleField.addEventListener("change", update);
        update();
    }

    /* ---------- Password visibility toggle ---------- */
    function initPasswordToggles() {
        document.querySelectorAll("[data-password-toggle]").forEach((toggler) => {
            const selector = toggler.getAttribute("data-password-toggle");
            const input = toggler.closest(".form-control")
                ? toggler.closest(".form-control").querySelector('input[type="password"], input[type="text"]')
                : document.querySelector(selector);

            if (!input) return;

            toggler.addEventListener("click", () => {
                const isVisible = input.type === "text";
                input.type = isVisible ? "password" : "text";
                const label = isVisible ? "Show password" : "Hide password";
                toggler.setAttribute("aria-label", label);
                toggler.setAttribute("aria-pressed", isVisible ? "false" : "true");
                toggler.innerHTML = isVisible
                    ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"></path><circle cx="12" cy="12" r="3"></circle></svg>'
                    : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m3 3 18 18"></path><path d="M10.6 5.1A10.8 10.8 0 0 1 12 5c6.5 0 10 7 10 7a18.7 18.7 0 0 1-3.1 4.1"></path><path d="M6.2 6.2C3.6 8.2 2 12 2 12s3.5 7 10 7a9.8 9.8 0 0 0 4.2-.9"></path><path d="M9.9 9.9a3 3 0 1 0 4.2 4.2"></path></svg>';
                input.focus();
            });
        });
    }
})();