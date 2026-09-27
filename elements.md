
## Headings by default: {: #headings-by-default }

# H1 Default styles for headings {: #h1-default-styles-for-headings }

## H2 Default styles for headings {: #h2-default-styles-for-headings }

### H3 Default styles for headings {: #h3-default-styles-for-headings }

#### H4 Default styles for headings {: #h4-default-styles-for-headings }

##### H5 Default styles for headings {: #h5-default-styles-for-headings }

###### H6 Default styles for headings {: #h6-default-styles-for-headings }

---

## Lists {: #lists }

### Ordered list example: {: #ordered-list-example }

1.    Poutine drinking vinegar bitters.
2.    Coloring book distillery fanny pack.
3.    Venmo biodiesel gentrify enamel pin meditation.
4.    Jean shorts shaman listicle pickled portland.
5.    Salvia mumblecore brunch iPhone migas.

---

### Unordered list example: {: #unordered-list-example }

-    Bitters semiotics vice thundercats synth.
-    Literally cred narwhal bitters wayfarers.
-    Kale chips chartreuse paleo tbh street art marfa.
-    Mlkshk polaroid sriracha brooklyn.
-    Pug you probably haven’t heard of them air plant man bun.

---

## Table

| Name  | Role      | Email             | Id Number |
|-------|-----------|-------------------|-----------|
| Alice | Developer | alice@example.com | 1         |
| Bob   | Designer  | bob@example.com   | 2         |
| Alex  | Developer | alex@example.com  | 3         |

---

## Quotes {: #quotes}

<blockquote class="q-left"> The longer I live, the more I realize that I am never wrong about anything, and that all the pains I have so humbly taken to verify my notions have only wasted my time! </blockquote>

> Design is not just what it looks like and feels like. Design is how it works.
>
> <cite>– Steve Jobs</cite>

---

## Callouts {. #callouts }

Useful information that users should know, even when skimming content.
{: .note }

Helpful advice for doing things better or more easily.
{: .tip }

Key information users need to know to achieve their goal.
{: .important }

Urgent info that needs immediate user attention to avoid problems.
{: .warning }

Advises about risks or negative outcomes of certain actions.
{: .caution }

---

## Syntax Highlighter {: #syntax-highlighter }

```css
 body {
    margin: 0;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    width: 100vw;
    background-color: #1c2021;
  }

li {
    width: 200px;
    min-height: 250px;
    border: 1px solid #000;
    display: inline-block;
    vertical-align: top;
    margin: 5px;
  }
```

```js
  $('.top').click(function () {
    $('html, body').stop().animate({ scrollTop: 0 }, 'slow', 'swing');
  });
  $(window).scroll(function () {
    if ($(this).scrollTop() > $(window).height()) {
      $('.top').addClass("top-active");
    } else {
      $('.top').removeClass("top-active");
    };
  });
```

---

## Images {: #images }

![Coding](/static/images/20.jpg)
*Photo by [Author](https://example.com) on [Site](https://example.com)*

<div class="gallery-box">
  <div class="gallery gallery-columns-2">
    <image src="/static/images/100.png" alt="Lifestyle" caption="A stunning shot" >
    <image src="/static/images/101.jpg" alt="Inspiration" caption="A stunning shot" >
    <image src="/static/images/102.jpg" alt="Friends" caption="A stunning shot" >
    <image src="/static/images/103.jpg" alt="Computers" caption="A stunning shot" >
    <image src="/static/images/21.jpg" alt="Computers" caption="A stunning shot" >
    <image src="/static/images/23.jpg" alt="Security" caption="A stunning shot" >
  </div>
  <p>A gallery of stunning shots</p>
</div>

---

## Youtube Embed {: #youtube-embed }

<div class="js-reframe" style="position: relative; width: 100%; padding-top: 50%;"><iframe src="https://www.youtube.com/embed/eItOR9tLfuM?si=pcgT1w0hTfvm5mM9" loading="lazy" frameborder="0" allowfullscreen="" style="position: absolute; width: 100%; height: 100%; left: 0px; top: 0px;"></iframe></div>

---

## Vimeo Embed {: #vimeo-embed }

<div class="js-reframe" style="position: relative; width: 100%; padding-top: 56.25%;"><iframe src="https://player.vimeo.com/video/148003889?h=d36b8b4cbb" loading="lazy" width="640" height="360" frameborder="0" allowfullscreen="" style="position: absolute; width: 100%; height: 100%; left: 0px; top: 0px;"></iframe></div>