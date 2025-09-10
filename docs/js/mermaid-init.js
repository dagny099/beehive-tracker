// Initialize Mermaid for diagram rendering
document$.subscribe(() => {
  mermaid.initialize({
    startOnLoad: true,
    theme: 'default',
    themeVariables: {
      primaryColor: '#1976d2',
      primaryTextColor: '#ffffff',
      primaryBorderColor: '#0d47a1',
      lineColor: '#333333',
      sectionBkgColor: '#f5f5f5',
      altSectionBkgColor: '#e3f2fd',
      gridColor: '#cccccc',
      secondaryColor: '#ffcc02',
      tertiaryColor: '#fff'
    },
    flowchart: {
      htmlLabels: true,
      curve: 'basis'
    },
    sequence: {
      diagramMarginX: 50,
      diagramMarginY: 10,
      actorMargin: 50,
      width: 150,
      height: 65,
      boxMargin: 10,
      boxTextMargin: 5,
      noteMargin: 10,
      messageMargin: 35,
      mirrorActors: true,
      bottomMarginAdj: 1,
      useMaxWidth: true,
      rightAngles: false,
      showSequenceNumbers: false
    }
  });
});