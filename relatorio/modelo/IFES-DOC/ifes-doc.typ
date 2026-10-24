// ================================================================
// lib.typ — Template Didático para Notas de Aula
// Versão: 1.0
// Autor: Prof. Dr. Sérgio Nery Simões
// IFES
// ================================================================

#import "@preview/algorithmic:1.0.0"
#import algorithmic: *
#import "@preview/codly:1.3.0": *
#import "@preview/codly-languages:0.1.1": *

// ================================================================
// 1. PALETA DE CORES
// ================================================================

// Toda a paleta deriva de color-primary.
// Para mudar o tema inteiro, altere apenas a linha abaixo

#let color-primary    = rgb("#006b52")  // <---

#let color-secondary  = color-primary.darken(10%)
#let color-dark       = color-primary.darken(60%)
#let color-table-hd   = color-primary
#let color-table-bg   = color-primary.lighten(88%)
#let color-table-alt  = color-primary.lighten(94%)
#let color-math-bg    = color-primary.lighten(92%)
#let color-code-bg    = color-primary.lighten(92%)
#let color-code-fg    = color-primary.lighten(40%)
#let color-line       = color-primary.lighten(60%)
#let color-text-soft  = color-primary.desaturate(60%).darken(20%)

// ================================================================
// 2. CALLOUT BOXES
// ================================================================

#let _callout(type, title, body) = {
  let styles = (
    info:    (label: "Informação",  color: rgb("#2980b9")),
    tip:     (label: "Dica",        color: rgb("#27ae60")),
    warning: (label: "Atenção",     color: rgb("#f39c12")),
    danger:  (label: "Cuidado",     color: rgb("#c0392b")),
    note:    (label: "Nota",        color: rgb("#8e44ad")),
    def:     (label: "Definição",   color: rgb("#534AB7")),
    example: (label: "Exemplo",     color: color-primary)
  )
  let s = styles.at(type, default: styles.info)
  let display-title = if title == none or title == "" { s.label } else { title }

  block(
    stroke: (left: 4pt + s.color),
    inset: (left: 12pt, right: 10pt, top: 8pt, bottom: 8pt),
    radius: (right: 5pt),
    fill: s.color.lighten(88%),
    width: 100%,
    breakable: true, // evita quebras de páginas em blocos longos
  )[
    #text(weight: "bold", fill: s.color.darken(20%))[#display-title] \ // Contraste WCAG aumentado
    #body
  ]
}

#let box-info(body, title: none)    = _callout("info",    title, body)
#let box-tip(body, title: none)     = _callout("tip",     title, body)
#let box-warning(body, title: none) = _callout("warning", title, body)
#let box-danger(body, title: none)  = _callout("danger",  title, body)
#let box-note(body, title: none)    = _callout("note",    title, body)
#let box-def(body, title: none)     = _callout("def",     title, body)
#let box-example(body, title: none) = _callout("example", title, body)

// ================================================================
// 3. BLOCO DE FÓRMULA MATEMÁTICA
// ================================================================

#let formula(body) = block(
  fill: color-math-bg,
  radius: 5pt,
  inset: (x: 16pt, y: 10pt),
  width: 100%,
  stroke: 0.4pt + color-line,
)[
  #set text(fill: color-primary.darken(20%))
  #align(center)[#body]
]

// ================================================================
// 4. TABELA ESTILIZADA
// ================================================================
#let styled-table(headers: (), rows: (), col-widths: auto) = {
  let n = headers.len()
  let widths = if col-widths == auto { (1fr,) * n } else { col-widths }

  table(
    columns: widths,
    fill: (_, row) => {
      if row == 0 { color-table-hd }
      else if calc.odd(row) { color-table-bg }
      else { color-table-alt }
    },
    stroke: 0.5pt + color-line,
    inset: (x: 8pt, y: 7pt),
    
    // Processamento seguro de cabeçalhos
    ..headers.map(h =>
      table.cell(align: center)[
        #text(weight: "bold", fill: white, size: 10pt)[#h]
      ]
    ),
    
    // Processamento seguro de conteúdo complexo (sem quebrar fórmulas/blocos)
    ..rows.flatten().map(cell =>
      table.cell(align: left)[
        #text(size: 9.5pt)[#cell]
      ]
    )
  )
}

// ================================================================
// 5. SETUP PRINCIPAL DO DOCUMENTO
// ================================================================

#let setup(
  title:            "Título do Documento",
  subtitle:         "Subtítulo",
  author:           "Autor",
  course:           none, // Nome da disciplina/curso
  date:             datetime.today().display("[day]/[month]/[year]"),
  affiliation:      "IFES",
  show_cover:       true,
  show_outline:     true,
  code-decorations: true, // Controle global de estilo de código
  body,
) = {

  // --- Metadados do PDF ---
  set document(title: title, author: author)
  set math.equation(numbering: "(1)")

  // --- Página ---
  set page(
    paper: "a4",
    margin: (top: 2.5cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm),
    
    header: context {
      if counter(page).get().first() > 1 {
        set text(8pt, color-text-soft)
        let header-text = if course != none { [#course | #title] } else { title }
        grid(
          columns: (1fr, 1fr),
          align(left)[#header-text],
          align(right)[#author],
        )
        line(length: 100%, stroke: 0.4pt + color-line)
      }
    },

    footer: context {
      if counter(page).get().first() > 1 {
        set align(center)
        set text(9pt, color-text-soft)
        counter(page).display("1 / 1", both: true) // Exibe "Página X / Y"
      }
    },
  )

  // --- Tipografia ---
  set text(font: "Libertinus Serif", size: 12pt, lang: "pt", region: "BR")
  set par(justify: true, leading: 0.85em, spacing: 1.0em, first-line-indent: 0em)

  // --- Hierarquia de Títulos (Unidades absolutas) ---

  set heading(numbering: "1.1.1")
  show heading: it => {
    let size-h1 = 15pt
    let scale   = 0.95
    let current-size = size-h1 * calc.pow(scale, it.level - 1)

    if it.level == 1 {
      v(0.5cm)
      block(
        fill: color-primary,
        radius: 6pt,
        inset: (x: 14pt, y: 10pt),
        width: 100%,
      )[
        #set text(fill: white, size: current-size, weight: "bold")
        #it
      ]
      v(0.4cm)
    } else {
      v(0.35cm)
      set text(size: current-size, weight: "semibold", fill: color-primary)
      it
      v(0.15cm)
    }
  }


  // --- Inicialização Condicional do Codly ---
  // (Configuração dos blocos de código)
  show: codly-init.with()
  if code-decorations {
    codly(
      languages: codly-languages,
      display-name: false,
      zebra-fill: color-primary.lighten(96%),
      stroke: 0.5pt + color-line,
      number-format: n => text(size: 8pt, fill: color-code-fg)[#n],

    )
  } else {
    codly(
      display-name: false,
      display-side-by-side: false,
      number-format: none,
      zebra-fill: none,
      stroke: 0.5pt + color-line,
    )
  }

  // --- Pseudocódigo ---
  show: style-algorithm

  // --- Geração da Capa ---
  if show_cover {
    align(center)[
      // Inclusão do logótipo institucional centralizado
      #image("logos/logo-serra-horizontal-cor.png", width: 35%)
      #v(2.5cm)
      #if course != none {
        text(size: 14pt, weight: "semibold", fill: color-secondary)[#upper(course)]
        v(0.5cm)
      }
      #v(1.5cm)
      #block(
        fill: color-primary, radius: 8pt,
        inset: (x: 20pt, y: 15pt), width: 90%,
      )[
        #set text(size: 20pt, weight: "bold", fill: white)
        #title
      ]
      #v(1.5cm)
      #text(size: 18pt, weight: "bold", fill: color-primary)[#subtitle]
      #v(1.5cm)
      #line(length: 60%, stroke: 1.5pt + color-primary)
      #v(4cm)
      #text(size: 16pt, weight: "bold", fill: color-secondary)[#author]
      #v(2.5cm)
      
      #let footer-meta = [#affiliation | #date]
      #text(size: 13pt, fill: color-secondary)[#footer-meta]
      #v(2cm)
    ]
  }


  // --- Sumário ---
  if show_outline {
    show outline.entry: it => {
      if it.level == 1 { strong(it) } else { it }
    }
    pagebreak(weak: true)
    outline(
      title: block(width: 100%, align(center)[#strong[Sumário]]),
      indent: 1.5em,
      depth: 2,
    )
    pagebreak(weak: true)
  }

  // --- Links e citações ---
  show link: set text(fill: color-secondary.darken(15%))
  show cite: set text(fill: color-secondary.darken(15%))

  // --- Blocos de código raw ---
  show raw.where(block: true): it => block(
    fill: color-code-bg,
    inset: 10pt,
    radius: 4pt,
    width: 100%,
    stroke: 0.5pt + color-line,
    text(size: 9pt, it)
  )

  // --- Tabelas ---
  show table: set text(11pt)
  show table.cell.where(y: 0): set text(weight: "bold")

  // --- Listas ---
  set enum(indent: 2.0em, body-indent: 0.8em, spacing: 0.9em)
  set list(indent: 2.0em, body-indent: 0.8em, spacing: 0.9em)


  body
}
