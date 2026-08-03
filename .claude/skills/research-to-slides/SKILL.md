---
name: research-to-slides
description: "Use this skill when the user wants to research a topic and turn the findings into a presentation. Trigger when the user asks to research and create slides, gives a topic with instructions like make a deck about X, generate slides on X after researching, or any request combining web research with slide generation."
---

# Research-to-Slides Skill

Research a topic online, organize findings into a structured outline, then generate a polished PPTX presentation.

## Workflow

### Phase 1: Research

For the given topic, run multiple web searches in parallel to cover different angles:

1. **Core topic** — search the topic directly for overview and key facts
2. **Latest developments** — include current year for recent news/trends
3. **Data & statistics** — search for numbers, charts, and quantitative insights
4. **Key players / comparisons** — competitors, categories, or differing viewpoints
5. **Controversies / challenges** — criticisms, limitations, or open questions (if applicable)

Execute all searches concurrently. Use English and Chinese searches if the topic is relevant to China.

For each search result, extract:
- Key facts and figures
- Notable quotes or statistics
- Dates and timelines
- Credible sources

### Phase 2: Synthesize

Create a structured outline from the research:

```
Title: [Compelling title that captures the topic]
Subtitle: [One-line summary]

Slide 1: Executive Summary — 3-4 key takeaways
Slide 2: Background & Context — why this matters now
Slide 3: Key Facts & Figures — data-driven, with stats callouts
Slide 4: Deep Dive — main analysis, trends, or mechanics
Slide 5: Key Players / Landscape — who's involved, market map
Slide 6: Challenges & Controversies — balanced perspective
Slide 7: Future Outlook — where things are heading
Slide 8: Conclusion — summary + actionable insight
```

Adjust slide count based on topic depth (minimum 6, maximum 12 slides).

### Phase 3: Write Slide Content

For each slide, write:
- **Title**: punchy, not generic
- **Body**: 3-5 bullet points or structured content. If data is available, prefer a large-number callout or comparison over plain bullets.
- **Visual direction**: what kind of visual element fits (chart type, icon category, image concept). This guidance helps the pptx skill execute better.

### Phase 4: Generate PPTX

Invoke the pptx skill to create the actual presentation. Pass:
- The full slide-by-slide content with titles and bodies
- The visual direction notes
- Color palette suggestion based on topic (choose from the pptx skill palette table)
- Font pairing suggestion

Use this prompt structure when invoking pptx:

```
Create a presentation with the following slides. Use the [palette name] color palette and [header font] / [body font] font pairing.

Slide 1: [Title] — [Subtitle]
- Content...

[repeat for all slides]

Design guidance:
- [visual direction notes]
- [chart/data visualization suggestions]
```

### Phase 5: QA

After the pptx is generated, follow the pptx skill's QA workflow:
1. Extract text with `python -m markitdown output.pptx` to verify content
2. Convert to images for visual inspection (if tools available)
3. Run the fix-and-verify loop at least once

## Quality Guidelines

- **Cite sources**: mention key sources in speaker notes or a references slide
- **Be specific**: "Grew 34% YoY to $2.8B in 2025" beats "grew significantly"
- **Stay balanced**: present multiple viewpoints, not just one side
- **Make it visual**: suggest concrete visual elements for each slide — don't leave the pptx skill guessing
- **Draft in English**: even if searching in Chinese, produce the final outline and slides in English unless the user specifies otherwise
