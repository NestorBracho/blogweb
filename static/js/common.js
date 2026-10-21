document.addEventListener("DOMContentLoaded", function() {
  'use strict';

  const html = document.querySelector('html'),
    globalWrap = document.querySelector('.global-wrap'),
    body = document.querySelector('body'),
    menuToggle = document.querySelector(".hamburger"),
    menuList = document.querySelector(".main-nav"),
    searchOpenButton = document.querySelectorAll(".search-button, .hero__search"),
    searchCloseIcon = document.querySelector(".search__close"),
    searchOverlay = document.querySelector(".search__overlay"),
    searchInput = document.querySelector(".search__text"),
    search = document.querySelector(".search"),
    toggleTheme = document.querySelector(".toggle-theme"),
    blogViewButton = document.querySelector(".blog__toggle"),
    splides = document.querySelector(".logos"),
    imagesOverlay = document.querySelector('.images-overlay'),
    btnScrollToTop = document.querySelector(".top");


  /* =======================================================
  // Menu + Search + Theme Switcher + Blog List View
  ======================================================= */
  menuToggle.addEventListener("click", () => {
    setMenu(!menuList.classList.contains("is-visible"));
  });

  searchOpenButton.forEach(button => {
    button.addEventListener("click", searchOpen);
  });

  searchCloseIcon.addEventListener("click", () => {
    searchClose();
  });

  searchOverlay.addEventListener("click", () => {
    searchClose();
  });

  if (blogViewButton) {
    blogViewButton.addEventListener("click", () => {
      viewToggle();
    });
  }


  // Menu (aria-expanded tells screen readers whether it is open)
  function setMenu(open) {
    menuToggle.classList.toggle("is-open", open);
    menuToggle.setAttribute("aria-expanded", open);
    menuList.classList.toggle("is-visible", open);
  }

  // Dropdown Menu: the toggle is the button right before its menu
  const dropdownToggles = document.querySelectorAll('.dropdown-toggle');

  function setDropdown(toggle, open) {
    toggle.setAttribute('aria-expanded', open);
    toggle.nextElementSibling.classList.toggle('is-visible', open);
  }

  dropdownToggles.forEach(function(toggle) {
    toggle.addEventListener('click', function() {
      dropdownToggles.forEach(function(other) {
        if (other !== toggle) {
          setDropdown(other, false);
        }
      });

      setDropdown(toggle, toggle.getAttribute('aria-expanded') !== 'true');
    });
  });

  document.addEventListener('click', function(e) {
    if (!e.target.closest('.nav__item')) {
      dropdownToggles.forEach(function(toggle) {
        setDropdown(toggle, false);
      });
    }
  });


  // Search
  let searchOpener = null;

  function searchOpen(e) {
    searchOpener = e.currentTarget;
    search.classList.add("is-visible");
    body.classList.add("search-is-visible");
    globalWrap.classList.add("is-active");
    setMenu(false);
    setTimeout(function () {
      searchInput.focus();
    }, 250);
  }

  function searchClose() {
    if (!search.classList.contains("is-visible")) {
      return;
    }
    search.classList.remove("is-visible");
    body.classList.remove("search-is-visible");
    globalWrap.classList.remove("is-active");
    // Keyboard users carry on from the button that opened the search
    if (searchOpener) {
      searchOpener.focus();
    }
  }

  // Escape closes whatever is open and gives the focus back to the button that opened it
  document.addEventListener('keydown', function(e){
    if (e.key == 'Escape') {
      searchClose();

      dropdownToggles.forEach(function(toggle) {
        if (toggle.getAttribute('aria-expanded') === 'true') {
          setDropdown(toggle, false);
          toggle.focus();
        }
      });

      if (menuList.classList.contains("is-visible")) {
        setMenu(false);
        menuToggle.focus();
      }
    }
  });


  // Theme Switcher (a toggle button: aria-pressed is true in dark mode)
  if (toggleTheme && isToggleEnabled) {
    toggleTheme.setAttribute("aria-pressed", html.classList.contains("dark-mode"));
    toggleTheme.addEventListener("click", () => {
      const isDarkMode = html.classList.contains("dark-mode");
      if (isDarkMode) {
        setTheme("light");
        localStorage.setItem("theme", "light");
      } else {
        setTheme("dark");
        localStorage.setItem("theme", "dark");
      }
      toggleTheme.setAttribute("aria-pressed", !isDarkMode);
    });
  }


  // Blog List View
  function viewToggle() {
    if (html.classList.contains('view-list')) {
      html.classList.remove('view-list');
      localStorage.removeItem("classView");
      document.documentElement.removeAttribute("list");
    } else {
      html.classList.add('view-list');
      localStorage.setItem("classView", "list");
      document.documentElement.setAttribute("list", "");
    }
  }


  /* ============================
  // Logos Slider
  ============================ */
  if (splides) {
    new Splide(splides, {
      direction: 'ltr',
      clones: 8,
      gap: 16,
      autoWidth: true,
      drag: true,
      arrows: false,
      pagination: false,
      type: 'loop',
      autoScroll: {
        autoStart: true,
        speed: 0.4,
        pauseOnHover: false,
        pauseOnFocus: false
      },
      intersection: {
        inView: {
          autoScroll: true,
        },
        outView: {
          autoScroll: false,
        }
      },
    }).mount(window.splide.Extensions);
  }


  /* ================================================================
  // Stop Animations During Window Resizing and Switching Theme Modes
  ================================================================ */
  let disableTransition;

  if (toggleTheme) {
    toggleTheme.addEventListener("click", () => {
      stopAnimation();
    });
  }

  window.addEventListener("resize", () => {
    stopAnimation();
  });

  function stopAnimation() {
    document.body.classList.add("disable-animation");
    clearTimeout(disableTransition);
    disableTransition = setTimeout(() => {
      document.body.classList.remove("disable-animation");
    }, 100);
  };

  /* =======================
  // Responsive Videos
  ======================= */
  reframe(".post__content iframe:not(.reframe-off), .page__content iframe:not(.reframe-off)");


  /* =======================
  // LazyLoad Images
  ======================= */
  var lazyLoadInstance = new LazyLoad({
    elements_selector: ".lazy"
  })


  /* =======================
  // Zoom Image
  ======================= */
  if (imagesOverlay) {
    const images = document.querySelectorAll('.post__content img, .page__content img, .gallery__image img'),
      enlargeLabel = imagesOverlay.dataset.enlargeLabel;
    let zoomedImage = null;

    const clearOverlay = () => {
      imagesOverlay.classList.remove('active');
      imagesOverlay.innerHTML = '';
      // Keyboard users carry on from the image they enlarged
      if (zoomedImage) {
        zoomedImage.focus();
        zoomedImage = null;
      }
    };

    const createImageElement = (src, alt) => {
      const img = document.createElement('img');
      img.src = src;
      img.alt = alt;
      return img;
    };

    const createDescriptionElement = (description) => {
      const descriptionElem = document.createElement('p');
      descriptionElem.textContent = description;
      descriptionElem.classList.add('image-overlay__description');
      return descriptionElem;
    };

    const openOverlay = (image) => {
      const galleryImage = image.closest('.gallery__image');
      const description = galleryImage?.querySelector('.gallery__image__caption')?.textContent || '';
      imagesOverlay.classList.add('active');

      imagesOverlay.innerHTML = '';
      imagesOverlay.appendChild(createImageElement(image.dataset.src || image.src, image.alt));

      if (description) {
        imagesOverlay.appendChild(createDescriptionElement(description));
      }

      zoomedImage = image;
      imagesOverlay.focus();
    };

    images.forEach(image => {
      // A button for keyboards and screen readers: Enter or Space enlarges it, like a click
      image.setAttribute('role', 'button');
      image.setAttribute('tabindex', '0');
      image.setAttribute('aria-label', image.alt ? `${enlargeLabel}: ${image.alt}` : enlargeLabel);

      image.addEventListener('click', () => {
        openOverlay(image);
      });

      image.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          openOverlay(image);
        }
      });
    });

    imagesOverlay.addEventListener('click', clearOverlay);

    // Escape closes the enlarged image, and the focus stays on it until then: the page behind is covered
    document.addEventListener('keydown', e => {
      if (!imagesOverlay.classList.contains('active')) {
        return;
      }
      if (e.key === 'Escape') {
        clearOverlay();
      } else if (e.key === 'Tab') {
        e.preventDefault();
      }
    });
  }


  // =====================
  // Copy Code Button
  // =====================
  document.querySelectorAll('.post__content pre.highlight, .page__content pre.highlight, .highlight pre')
  .forEach(function (pre) {
    const button = document.createElement('button');
    const copyText = 'Copy';
    button.type = 'button';
    button.ariaLabel = 'Copy code to clipboard';
    button.innerText = copyText;
    button.addEventListener('click', function () {
      let code = pre.querySelector('code').innerText;
      try {
        code = code.trimEnd();
      } catch (e) {
        code = code.trim();
      }
      navigator.clipboard.writeText(code);
      button.innerText = 'Copied!';
      setTimeout(function () {
        button.blur();
        button.innerText = copyText;
      }, 2e3);
    });
    pre.appendChild(button);
  });


  // // =====================
  // // Load More Posts
  // // =====================
  // var load_posts_button = document.querySelector(".load-more-posts");
  //
  // load_posts_button && load_posts_button.addEventListener("click", function (e) {
  //   e.preventDefault();
  //   var t = load_posts_button.textContent;
  //   load_posts_button.classList.add("button--loading"), load_posts_button.textContent = "Loading";
  //   var o = document.querySelector(".pagination"),
  //       n = pagination_next_url.split("/page")[0] + "/page/" + pagination_next_page_number + "/";
  //   fetch(n).then(function (e) {
  //     if (e.ok) return e.text()
  //   }).then(function (e) {
  //     var n = document.createElement("div");
  //     n.innerHTML = e;
  //     for (var a = document.querySelector(".grid"), i = n.querySelectorAll(".grid__post"), l = 0; l < i.length; l++) a.appendChild(i.item(l));
  //     new LazyLoad({elements_selector: ".lazy"}), pagination_next_page_number++, pagination_next_page_number > pagination_available_pages_number && (o.style.display = "none")
  //   }).finally(function () {
  //     load_posts_button.classList.remove("button--loading");
  //     load_posts_button.textContent = t;
  //   })
  // });


  /* =======================
  // Flash Messages
  ======================= */
  setTimeout(() => {
    document.querySelectorAll('.messages').forEach(el => {
      el.classList.add('fade-out');
      setTimeout(() => {
        el.style.display = 'none';
      }, 1000);
    });
  }, 5000);


  /* =======================
  // Scroll Top Button
  ======================= */
  window.addEventListener("scroll", function () {
  window.scrollY > window.innerHeight ? btnScrollToTop.classList.add("is-active") : btnScrollToTop.classList.remove("is-active");
  });

  btnScrollToTop.addEventListener("click", function () {
    if (window.scrollY != 0) {
      window.scrollTo({
        top: 0,
        left: 0,
        behavior: "smooth"
      })
    }
    // The button hides at the top, so keyboard users carry on from the first link of the page
    document.querySelector(".logo__link").focus({preventScroll: true});
  });

});
