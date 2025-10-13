package schema.pattern;

import java.util.*;

/**
 * Represents a higher-level (complex) pattern composed of other patterns.
 * Each subpattern contributes its own confidence and set of events.
 * The aggregated confidence is propagated from the subpatterns.
 */
public class ComplexPattern extends Pattern {
    private final List<String> subpatternNames = new ArrayList<>();
    private final List<Double> subpatternConfidences = new ArrayList<>();

    public ComplexPattern(String name, List<Pattern> subpatterns) {
        super(name, "complex", 0.0);

        for (Pattern sub : subpatterns) {
            this.subpatternNames.add(sub.getPatternName());
            this.subpatternConfidences.add(sub.getConfidence());
            this.eventsNested.addAll(sub.getEventsNested());
        }
    }

    public List<String> getSubpatternNames() { return subpatternNames; }
    public List<Double> getSubpatternConfidences() { return subpatternConfidences; }
}
