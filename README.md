# Twin Pigs Architecture Compiler
## Sources for the architecture diagrams
Here are the sources for the compiler. It converts a subset of the PlantUML language into GRAPHML diagrams you can open and layout using [**yEd**](https://www.yworks.com/products/yed/download).

## The Workflow
### The basics
1. Use PyCharm IDE (or maybe any other IDE based on IntelliJ IDEA) with PlantUML plugin for editing and basic syntax check (unfortunately, you will get "an explosion at a pasta factory" picture after rendering; that's why I wrote this compiler). Visual Studio Code IDE with PlantUML plugin also works, though IDEA-based IDEs are, to my mind, better.
2. Compile the resulting .puml file to GRAPHML using `puml_compiler/src/puml2graphml.py` (you may also use a binary compiler from the latest release or build it yourself; see below about the releases). Fix the errors (if any) until you get a GRAPHML file.
3. Open the GRAPHML in [yEd](https://www.yworks.com/products/yed/download). Select automated layout (`Layout->Hierarchical`), tune the oprions. Recommendations (first set everything to default, then apply): ``General->Node To Node distance"=50; "General->Layer to Layer Distance"=100, "Edges->Routing Style"="Orthogonal".``
4. Do the label placement (`Layout->Label Placement`). Recommendations (first set everything to default, then apply):``"Scope->Place Node Labels"=false; "Model->Edge Label Model"="Center Slider"; "Model->Auto Rotate"=true.``
5. Export the diagram to some graphic format if needed (though yEd is a good browser for your design: it can select the neighborhood of the desired elements and extract them as a separate diagram, it can view element's properties — look at the Data tab, it holds most of the source info, including the source code lines for the element).

### Accessing the releases
1. The releases are available [here](https://github.com/twinpigs-agile/twinpigs-design/releases).
2. Every release includes:
   - A gzipped tarball with the model sources and compiled diagrams (`samples.tar.gz`).
   - A Windows executable of the sources compiler (`puml2graphml.exe`)
   - A Linux executable of the sources compiler (`puml2graphml`)
   - Source code (a zip and a gzipped tarball)

Good luck!

## Why PlantUML? Why not Gliffy or any other WYSIWYG tool?
1. We need a detailed diagram to control all the data flows and connections between services. Data filtering and fast creation of sub-diagrams is strongly desired.
2. The diagram is huge. It is relatively easy to describe in terms of PlantUML (probably one of the easiest ways, especially if you plan to update it regularly) but not to draw manually. However, PlantUML does not help with rendering because of the diagram size.
3. The only editor I've found to support effective automatic layout of the diagrams of such size is [yEd](https://www.yworks.com/products/yed/download). So, I needed a compiler, and I have it. :-)

## Common conventions
### Arrow directions
You may use them in any way, but that's how I use them. As my main focus is to correctly reflect the data flows, the direction of an arrow depends on the direction data is sent, not on the protocol details. E.g. for HTTP and HTTPS the arrow does not say which side is the server. Bidirectional arrows (`<->`) mean that data transfer is known to be bidirectional. `->` and `<-` mean unidirectional data transfer. `--` stands for undefined direction and means the direction should be specified later. I rarely use bidire

## Info on the subset of PlantUML language supported by the compiler
PlantUML supports a lot of diagram types, a lot of objects. The PlantUML diagrams have a rather versatile syntax that is not needed in our case. Below is a brief description of the tiny subset of the PlantUML language supported by `puml2graphml` now (probably some extensions may appear in the future).

### Lower level
1. THe source files always are in UTF-8 encoding. No other encodings are supported (isn't that enough, though?).
2. A `'` symbol opens a comment that is closed automatically at the end of line. `/'` starts a comment closed by `'/` (multiline comments are allowed, the nested ones are not).
3. `@startuml` and `@enduml` should open and close the file. That 
4. `"` opens and closes a string constant. Multiline string constants are not allowed. The `"` symbols inside a line should be escaped by a backslash: `\"`. A backslash is escaped by another backslash: `\\` stands for `\`. Escaped lower latin letters work as the escapes in Python strings (`\n` for a newline, etc.). `\x**`, where `*` stands for a hex digit, means a Unicode symbol that has a code between 0 and 127 (ASCII) defined by its hex code. `\u****` (four hex digits) means a Unicode symbol with the corresponding code.
5. `{` and `}` open and close the bodies of diagram nodes.
6. The connections

### The diagram nodes (systems, groups, external services)

#### Program systems (services)
```
map SERVICE_1 {
  Team => Team name here
  Stack => Technological stack (OS, language, frameworks...) here
  Env => deployment environment description (e.g. "Google Cloud") here
  Info => General information
}

map "Service number two" as SERVICE_2  {
  Team => Team name here
  Stack => Technological stack (OS, language, frameworks...) here
  Env => deployment environment description (e.g. "Google Cloud") here
  Info => General information
}
```

`Team`, `Stack`, `Env`, `Info` are called properties and should be specified for every service. Specifying some other properties is also allowed but those four are mandatory.

#### External services
```
rectangle SOME_SERVICE {
}

rectangle ANOTHER_SERVICE as "An external service number two" {
}
```
The main idea that nothing should be put inside a `rectangle` block between `{` and `}`

#### Program system groups and categories
```
rectangle SERVICE_GROUP {
'... And here go more services or groups
}

rectangle "A service group number two" as ANOTHER_SERVICE_GROUP {
'... And here go more services or groups
}
```
The main idea that if other a `rectangle` contains other `rectangle`s or `map`s, it is treated as a group definition, a container including other services and groups.

### The edges (dataflows)
```
SERVICE_ID_1 -- SERVICE_ID_2 : data flow info [HTTPS]
SERVICE_ID_1 -> SERVICE_ID_2 : data flow info [REST/HTTPS]
SERVICE_ID_1 <-> SERVICE_ID_2 : data flow info [HTTPS]
SERVICE_ID_1 <- SERVICE_ID_2 : data flow info [REST/HTTPS]
```
As already mentioned above, bidirectional arrows (`<->`) mean that data transfer is known to be bidirectional. `->` and `<-` mean unidirectional data transfer. `--` stands for undefined direction and means the direction should be specified later.
