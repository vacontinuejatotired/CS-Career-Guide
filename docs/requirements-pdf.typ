#set document(title: "$title$")
#set text(font: ("Microsoft YaHei", "Arial"), size: 10.5pt, lang: "zh")
#set page(paper: "a4", margin: (top: 16mm, bottom: 17mm, left: 18mm, right: 18mm), numbering: "1", number-align: center)
#set par(justify: false, leading: 0.7em, spacing: 0.8em)
#set heading(numbering: none)
#show heading.where(level: 1): set text(size: 13pt, fill: rgb("#18354a"))
#show heading.where(level: 2): set text(size: 11.5pt, fill: rgb("#18354a"))
#show heading.where(level: 3): set text(size: 10.5pt, fill: rgb("#18354a"))
#show heading.where(level: 2): it => {
  if it.body == [四、五人任务清单] { pagebreak() }
  it
}
#set table(inset: (x: 6pt, y: 5pt), stroke: 0.45pt + rgb("#ccd5dc"), fill: (x, y) => if y == 0 { rgb("#eaf0f4") } else { none })
#show table.cell.where(y: 0): set text(weight: "bold")

#align(center)[
  #text(size: 18pt, weight: "bold", fill: rgb("#18354a"))[$title$]
  #v(5pt)
  #text(size: 10pt, fill: rgb("#526575"))[$subtitle$]
  #v(3pt)
  #text(size: 8.5pt, fill: rgb("#697b87"))[$date$]
]
#v(5pt)
#line(length: 100%, stroke: 0.7pt + rgb("#b6c7d2"))
#v(5pt)

$body$
