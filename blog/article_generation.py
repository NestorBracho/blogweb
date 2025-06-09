import os
import requests
import random
import math
from openai import OpenAI
from django.core.files.base import ContentFile
from django.utils.text import slugify
from django.utils.safestring import SafeString

from .models import Post, Category

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")


def estimate_read_time(text):
    words = len(text.split())
    return math.ceil(words / 200)  # average reading speed ~200 wpm


def get_unsplash_image_url(keyword):
    endpoint = "https://api.unsplash.com/photos/random"
    params = {
        "query": keyword,
        "orientation": "landscape",
        "client_id": UNSPLASH_ACCESS_KEY,
    }
    response = requests.get(endpoint, params=params)
    data = response.json()

    return data["urls"]["regular"]


def generate_article(topic):
    sections = random.randint(3, 6)
    word_target = random.randint(600, 1200)
    category = Category.objects.get(slug='programming')

    prompt = f"""
Generate a blog article in Markdown format about "{topic}". The article should have {sections} sections, 
a clear introduction and a conclusion.
Write it in a human style with natural variation in sentence structure and tone. Target around {word_target} words.
Return only the article body in English, no preamble.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system",
             "content": "You are a professional tech writer that explains things clearly and accurately."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
    )

    english_body = response.choices[0].message.content.strip()

    # Translate to Spanish
    translation_prompt = f"Translate the following Markdown article to Spanish:\n\n{english_body}"
    response_es = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system",
             "content": "You are a professional tech writer that explains things clearly and accurately."},
            {"role": "user", "content": translation_prompt}
        ],
        temperature=0.7,
    )

    spanish_body = response_es.choices[0].message.content.strip()

    # Get summary and title
    summary_prompt = f"""Summarize the following article in less than 160 characters. Then, provide a short SEO-friendly 
    title (max 60 characters) in both English and Spanish. Markdown format:
    Article:
    {english_body}
    Output format:
    short_description_en: ...
    short_description_es: ...
    title_en: ...
    title_es: ...
    """
    summary_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system",
             "content": "You are a professional tech writer that explains things clearly and accurately."},
            {"role": "user", "content": summary_prompt}
        ],
        temperature=0.7,
    )

    lines = summary_response.choices[0].message.content.strip().splitlines()
    short_description_en = lines[0].split(":", 1)[-1].strip()
    title_es = lines[2].split(":", 1)[-1].strip()
    short_description_es = lines[1].split(":", 1)[-1].strip()
    title_en = lines[3].split(":", 1)[-1].strip()
    slug = slugify(title_en)

    post = Post.objects.create(
        slug=slugify(title_en),
        title_es=title_es,
        title_en=title_en,
        body_es=spanish_body,
        body_en=english_body,
        description_es=short_description_es,
        description_en=short_description_en,
        category=category,
        read_time=estimate_read_time(english_body),
    )

    image_prompt = (f"High-quality illustration for a blog post titled: '{title_en}'. The image should represent: "
                    f"{short_description_en}. Professional, modern, engaging.")

    img_response = client.images.generate(
        model="dall-e-3",
        prompt=image_prompt,
        n=1,
        quality="hd",
        size="1024x1024"
    )
    filename = f"{slug}_cover.jpg"
    image_url = img_response.data[0].url
    image_response = requests.get(image_url)
    image_content = ContentFile(image_response.content)

    post.cover.save(filename, image_content)


def create_article_from_json():
    category = Category.objects.get(slug='programming')
    # article_json = {
    #   "title_en": "Vue vs React: Choosing the Best Frontend Framework",
    #   "title_es": "Vue vs React: El Mejor Framework Frontend",
    #   "short_description_en": "A hands-on comparison of Vue.js and React covering DX, learning curve, performance, and more.",
    #   "short_description_es": "Comparativa práctica de Vue.js y React: experiencia, curva de aprendizaje, rendimiento y más.",
    #   "read_time": 7,
    #   "body_en": "## Vue vs React: A Hands-On Comparison for Modern Frontend Development\n\nChoosing between **Vue.js** and **React** can feel like picking a side in a never-ending frontend battle. Both are powerful, popular, and widely used in production. But how do they differ in ways that matter to *you* as a developer?\n\nLet's break it down based on real-world concerns: developer experience, learning curve, component structure, community support, and performance.\n\n---\n\n## Developer Experience\n\nVue is known for its simplicity and elegance. It offers a cohesive experience out of the box, thanks to official tools like Vue Router and Vuex. You can scaffold a working app in minutes and feel productive right away.\n\nReact, on the other hand, is more flexible and less opinionated. You assemble your own toolchain, which can be empowering but also overwhelming for newcomers. JSX syntax, while powerful, may take a while to love.\n\n> “Vue feels like a well-curated toolkit. React feels like a toolbox where you get to choose your own adventure.”\n\n---\n\n## Learning Curve\n\nIf you’re new to frontend frameworks, Vue has a gentler learning curve. Its template syntax is similar to HTML, and the documentation is beginner-friendly.\n\nReact’s concepts like hooks, context, and component lifecycles can be tricky at first. However, once mastered, React unlocks powerful patterns for large applications.\n\n<p class=\"note\">New developers might find Vue more intuitive initially, while React rewards deeper understanding over time.</p>\n\n---\n\n## Component Structure\n\nBoth frameworks are component-based, but they approach it differently:\n\n### Vue Example:\n```vue\n<template>\n  <button @click=\"increment\">Clicked {{ count }} times</button>\n</template>\n\n<script>\nexport default {\n  data() {\n    return {\n      count: 0\n    }\n  },\n  methods: {\n    increment() {\n      this.count++\n    }\n  }\n}\n</script>\n```\n\n### React Example:\n```jsx\nimport { useState } from 'react';\n\nfunction Counter() {\n  const [count, setCount] = useState(0);\n  return (\n    <button onClick={() => setCount(count + 1)}>\n      Clicked {count} times\n    </button>\n  );\n}\n```\n\nVue separates concerns by file sections. React blends logic and markup using JSX. Both are valid, but one may feel more natural to you.\n\n---\n\n## Community Support and Ecosystem\n\n| Feature | Vue.js | React |\n|--------|--------|--------|\n| GitHub Stars | ★★★★☆ | ★★★★★ |\n| Corporate Backing | Evan You / Community | Meta (Facebook) |\n| Documentation | Excellent | Solid, but less unified |\n| Third-party Ecosystem | Growing rapidly | Massive and mature |\n\nVue has a passionate community and growing traction, especially in Asia and Europe. React, being older, has a larger ecosystem and more job listings globally.\n\n---\n\n## Performance\n\nBoth frameworks are performant enough for nearly all use cases. Vue 3’s Composition API and React’s concurrent rendering (React 18+) are modern performance features that help manage large-scale apps effectively.\n\nBenchmarks vary by test, but in real projects, architectural choices matter more than micro-benchmarks.\n\n---\n\n## Conclusion\n\nBoth Vue and React are modern, fast, and capable. Here’s a simplified way to decide:\n\n- Choose **Vue** if you want a friendly start and a cohesive ecosystem.\n- Choose **React** if you like flexibility and plan to work in teams using it professionally.\n\nIn the end, your preference might come down to syntax, philosophy, or even which tutorial you watched first.\n\nThe best way to decide? Build something small with both.\n\n---",
    #   "body_es": "## Vue vs React: Comparación Práctica para Desarrollo Frontend Moderno\n\nElegir entre **Vue.js** y **React** puede sentirse como tomar partido en una eterna batalla del frontend. Ambos son poderosos, populares y ampliamente usados en producción. Pero, ¿en qué se diferencian de forma relevante para *ti* como desarrollador?\n\nVamos a desglosarlo según preocupaciones reales: experiencia de desarrollo, curva de aprendizaje, estructura de componentes, soporte comunitario y rendimiento.\n\n---\n\n## Experiencia de Desarrollo\n\nVue es conocido por su simplicidad y elegancia. Ofrece una experiencia coherente desde el inicio gracias a herramientas oficiales como Vue Router y Vuex. Puedes montar una app funcional en minutos y sentirte productivo al instante.\n\nReact, en cambio, es más flexible y menos opinado. Armas tu propia cadena de herramientas, lo cual puede ser empoderador pero también abrumador para principiantes. La sintaxis JSX, aunque poderosa, puede requerir tiempo para apreciarla.\n\n> “Vue se siente como una caja de herramientas curada. React como una caja donde tú eliges tu propia aventura.”\n\n---\n\n## Curva de Aprendizaje\n\nSi eres nuevo en frameworks frontend, Vue tiene una curva de aprendizaje más suave. Su sintaxis de plantillas se parece al HTML y su documentación es muy amigable.\n\nReact presenta conceptos como hooks, contextos y ciclos de vida de componentes que pueden ser difíciles al principio. Sin embargo, una vez dominados, React ofrece patrones muy potentes para aplicaciones grandes.\n\n<p class=\"note\">Para nuevos desarrolladores, Vue puede resultar más intuitivo al principio, mientras que React recompensa un entendimiento más profundo con el tiempo.</p>\n\n---\n\n## Estructura de Componentes\n\nAmbos frameworks se basan en componentes, pero lo abordan de forma distinta:\n\n### Ejemplo en Vue:\n```vue\n<template>\n  <button @click=\"incrementar\">Clicado {{ conteo }} veces</button>\n</template>\n\n<script>\nexport default {\n  data() {\n    return {\n      conteo: 0\n    }\n  },\n  methods: {\n    incrementar() {\n      this.conteo++\n    }\n  }\n}\n</script>\n```\n\n### Ejemplo en React:\n```jsx\nimport { useState } from 'react';\n\nfunction Contador() {\n  const [conteo, setConteo] = useState(0);\n  return (\n    <button onClick={() => setConteo(conteo + 1)}>\n      Clicado {conteo} veces\n    </button>\n  );\n}\n```\n\nVue separa responsabilidades por secciones de archivo. React mezcla lógica y marcado usando JSX. Ambos son válidos, pero uno puede resultarte más natural.\n\n---\n\n## Comunidad y Ecosistema\n\n| Característica | Vue.js | React |\n|---------------|--------|--------|\n| Estrellas en GitHub | ★★★★☆ | ★★★★★ |\n| Soporte Corporativo | Evan You / Comunidad | Meta (Facebook) |\n| Documentación | Excelente | Sólida, menos unificada |\n| Ecosistema de terceros | En rápido crecimiento | Masivo y maduro |\n\nVue tiene una comunidad apasionada y tracción creciente, especialmente en Asia y Europa. React, al ser más antiguo, tiene un ecosistema más amplio y más ofertas de empleo a nivel global.\n\n---\n\n## Rendimiento\n\nAmbos frameworks ofrecen un rendimiento excelente para casi todos los casos. Vue 3 con la Composition API y React 18+ con renderizado concurrente permiten manejar aplicaciones grandes eficientemente.\n\nLos benchmarks varían, pero en proyectos reales, las decisiones arquitectónicas importan más que las micro-métricas.\n\n---\n\n## Conclusión\n\nVue y React son modernos, rápidos y capaces. Una forma simple de decidir:\n\n- Elige **Vue** si quieres un inicio amigable y un ecosistema coherente.\n- Elige **React** si prefieres flexibilidad y planeas trabajar en equipos que lo usan profesionalmente.\n\n¿La mejor forma de decidir? Construye algo pequeño con ambos.\n\n---"
    # }

    article_json = {
      "title_en": "Special vs General Relativity: What's the Difference?",
      "title_es": "Relatividad Especial vs General: ¿Cuál es la Diferencia?",
      "short_description_en": "Unpack the elegant ideas behind Einstein’s two theories of relativity through metaphors, real-world analogies, and engaging visuals.",
      "short_description_es": "Descubre las elegantes ideas detrás de las dos teorías de la relatividad de Einstein con metáforas, analogías y visuales cautivadoras.",
      "read_time": 8,
      "body_en": "## What Is Relativity, Really?\n\nImagine you're sitting on a train. It's moving smoothly, and you toss a ball straight up. To you, it goes up and comes down into your hand. To someone standing on the platform watching the train pass, that same ball follows a curved path. Who's right?\n\nBoth are.\n\nThis simple idea—that motion depends on your frame of reference—is the seed of Einstein's theories of relativity. But Einstein didn’t stop at trains and balls. He took this idea to its ultimate conclusion, reshaping how we think about time, space, and gravity.\n\nThere are two main flavors of relativity: **special** and **general**. Let’s explore what makes them different, and why both are so mind-bending.\n\n![einstein-theory](https://cdn.mos.cms.futurecdn.net/FrTRcvypfQJaiRwrmxsbkh-1200-80.jpg)\n\n---\n\n## Special Relativity: When Speed Changes Reality\n\nSpecial relativity came first. In 1905, Einstein introduced it to explain how the universe works when things move really fast—close to the speed of light.\n\nThe key idea? _Time and space are not fixed._\n\nTo someone zooming through space in a spaceship, clocks tick differently. A ruler might appear shorter. Events that seem simultaneous to one person may not be to another.\n\nIt sounds wild, but it’s been tested over and over. GPS satellites, for example, need to correct for these effects so your location doesn't drift.\n\n### Two Big Rules of Special Relativity:\n\n1. **The speed of light is constant** for all observers, no matter how fast they’re moving.\n2. **The laws of physics are the same** in all non-accelerating (inertial) frames.\n\nThese two principles lead to some surprising consequences—like time dilation, where fast-moving objects experience time more slowly.\n{: .note}\n\n![time-dilation](https://space-india.com/wp-content/uploads/2024/03/space-dilation.jpg)\n\n---\n\n## General Relativity: Gravity Bends Space and Time\n\nTen years later, Einstein went further. What about when objects accelerate, or when gravity comes into play?\n\nGeneral relativity is the answer. It says that **mass and energy warp the fabric of space and time**, like a bowling ball on a trampoline. Planets and stars curve spacetime, and objects move along those curves. That’s what we feel as gravity.\n\nSo instead of thinking of gravity as an invisible force pulling you down, imagine Earth bending spacetime around it—and you're just following the curves.\n\n### A Real-World Analogy:\n\n- Imagine marbles rolling on a stretched rubber sheet. Place a heavy ball in the center: smaller marbles spiral toward it. That’s the effect of mass bending spacetime.\n\n![spacetime-curvature](https://www.wtamu.edu/~cbaird/sq/images/spacetime.jpg)\n\n---\n\n## Comparing the Two Theories\n\nHere’s a quick side-by-side view:\n\n| Feature               | Special Relativity        | General Relativity               |\n|----------------------|---------------------------|----------------------------------|\n| Year Introduced      | 1905                      | 1915                             |\n| Focus                | High-speed motion         | Gravity and acceleration         |\n| Space & Time         | Flexible, relative        | Curved by mass and energy        |\n| Key Principle        | Constancy of light speed  | Gravity is curved spacetime      |\n| Everyday Evidence    | GPS timing corrections    | Gravitational lensing, black holes |\n\n---\n\n## Why It Matters\n\nRelativity isn’t just abstract theory. It shapes our understanding of the cosmos, from black holes to the Big Bang. It explains the strange bending of starlight and even powers the accuracy of your smartphone.\n\nAnd perhaps most beautifully, it reminds us that reality is more flexible—and more mysterious—than it first appears.\n\n![black-hole](https://cnewsliveenglish.com/images/gravitys-grasp-exploring-time-dilation-near-black-holes-tm-175720230331.jpg)\n\n## Conclusion: The Universe, Reimagined\n\nEinstein’s twin theories of relativity show us that time and space are not the static stage we once imagined. Instead, they are active, dynamic players in the cosmic dance.\n\nSpecial relativity teaches us to rethink motion and simultaneity. General relativity transforms gravity from a force into geometry.\n\nTwo theories, one genius, and a universe forever changed.\n",
      "body_es": "## ¿Qué es realmente la relatividad?\n\nImagina que estás sentado en un tren en movimiento. Lanzas una pelota hacia arriba. Para ti, sube y baja en línea recta. Para alguien parado en el andén viendo pasar el tren, la pelota sigue una trayectoria curva. ¿Quién tiene razón?\n\nAmbos.\n\nEsta idea simple—que el movimiento depende del punto de vista—es la semilla de las teorías de la relatividad de Einstein. Pero Einstein no se quedó en trenes y pelotas. Llevó esta idea al límite, transformando nuestra comprensión del tiempo, el espacio y la gravedad.\n\nExisten dos tipos principales de relatividad: **especial** y **general**. Exploremos qué las diferencia y por qué ambas son tan fascinantes.\n\n![einstein-theory](https://cdn.mos.cms.futurecdn.net/FrTRcvypfQJaiRwrmxsbkh-1200-80.jpg)\n\n---\n\n## Relatividad Especial: Cuando la velocidad cambia la realidad\n\nLa relatividad especial fue la primera. En 1905, Einstein la propuso para explicar cómo funciona el universo cuando las cosas se mueven muy rápido—cerca de la velocidad de la luz.\n\n¿La idea clave? _El tiempo y el espacio no son fijos._\n\nPara alguien viajando a gran velocidad en una nave espacial, los relojes se desaceleran. Las reglas cambian. Lo que para ti es \"ahora\" podría no serlo para otra persona.\n\nAunque suena extraño, se ha comprobado muchas veces. Por ejemplo, los satélites GPS corrigen estos efectos para que tu posición no se desvíe.\n\n### Dos grandes reglas de la relatividad especial:\n\n1. **La velocidad de la luz es constante** para todos, sin importar su velocidad.\n2. **Las leyes de la física son las mismas** en todos los sistemas no acelerados.\n\nEstas dos reglas llevan a consecuencias sorprendentes, como la dilatación del tiempo: los objetos en movimiento lento envejecen más rápido que los que se mueven rápido.\n{: .note}\n\n![time-dilation](https://space-india.com/wp-content/uploads/2024/03/space-dilation.jpg)\n\n---\n\n## Relatividad General: La gravedad curva el espacio y el tiempo\n\nDiez años después, Einstein dio otro paso. ¿Qué pasa cuando hay aceleración o gravedad?\n\nLa relatividad general lo explica. Afirma que **la masa y la energía deforman el tejido del espacio y el tiempo**, como una bola de boliche en un trampolín. Los planetas y estrellas curvan el espacio-tiempo, y los objetos se mueven siguiendo esas curvas. Eso es lo que sentimos como gravedad.\n\nAsí que, en lugar de pensar en la gravedad como una fuerza que te jala, imagina que la Tierra curva el espacio-tiempo a su alrededor—y tú simplemente sigues esas curvas.\n\n### Una analogía práctica:\n\n- Imagina canicas rodando sobre una sábana elástica. Si colocas una bola pesada en el centro, las canicas ruedan hacia ella. Así es como la masa curva el espacio-tiempo.\n\n![spacetime-curvature](https://www.wtamu.edu/~cbaird/sq/images/spacetime.jpg)\n\n---\n\n## Comparando las dos teorías\n\nUna vista rápida, lado a lado:\n\n| Característica        | Relatividad Especial        | Relatividad General                |\n|-----------------------|-----------------------------|------------------------------------|\n| Año de publicación    | 1905                        | 1915                               |\n| Enfoque               | Movimiento a alta velocidad | Gravedad y aceleración             |\n| Espacio y tiempo      | Flexibles, relativos        | Curvados por la masa y la energía  |\n| Principio clave       | Constancia de la luz        | La gravedad es geometría del espacio |\n| Ejemplos cotidianos   | Corrección del GPS          | Lentes gravitacionales, agujeros negros |\n\n---\n\n## ¿Por qué importa?\n\nLa relatividad no es solo teoría abstracta. Da forma a nuestra visión del cosmos, desde los agujeros negros hasta el Big Bang. Explica cómo se curva la luz de las estrellas y permite la precisión de tu celular.\n\nY lo más hermoso: nos recuerda que la realidad es más flexible—y más misteriosa—de lo que parece.\n\n![black-hole](https://cnewsliveenglish.com/images/gravitys-grasp-exploring-time-dilation-near-black-holes-tm-175720230331.jpg)\n\n## Conclusión: El universo, reinventado\n\nLas dos teorías de Einstein nos muestran que el tiempo y el espacio no son escenarios fijos. Son protagonistas activos en el drama cósmico.\n\nLa relatividad especial nos invita a repensar el movimiento. La general convierte la gravedad en una cuestión de geometría.\n\nDos teorías, un genio, y un universo transformado.\n",
      "unsplash_tags": ["relativity", "einstein", "space", "gravity", "time"]
    }

    post = Post.objects.create(
        slug=slugify(article_json['title_en']),
        title_es=article_json['title_es'],
        title_en=article_json['title_en'],
        body_es=SafeString(article_json['body_es']),
        body_en=SafeString(article_json['body_en']),
        description_es=article_json['short_description_es'],
        description_en=article_json['short_description_en'],
        category=category,
        read_time=article_json['read_time'],
    )

