package schema.pattern;

import java.util.*;

/**
 * Represents a composite pattern formed from multiple subpatterns.
 * Each subpattern may itself be atomic or complex.
 */
public class ComplexPattern extends Pattern {
    private List<Pattern> subPatterns;

    public ComplexPattern(String name, List<Pattern> subPatterns) {
        super(name, "complex", 0.0);
        this.subPatterns = new ArrayList<>(subPatterns);

        // Merge subpatterns’ nested events
        for (Pattern p : subPatterns) {
            this.eventsNested.addAll(p.getEventsNested());
            this.sourceIds.addAll(p.getSourceIds());
        }
    }

    public List<Pattern> getSubPatterns() {
        return subPatterns;
    }

    /** Returns names of all immediate subpatterns. */
    public List<String> getSubpatternNames() {
        List<String> names = new ArrayList<>();
        for (Pattern p : subPatterns) {
            names.add(p.getPatternName());
        }
        return names;
    }

    /** Returns confidences of all immediate subpatterns. */
    public List<Double> getSubpatternConfidences() {
        List<Double> confs = new ArrayList<>();
        for (Pattern p : subPatterns) {
            confs.add(p.getConfidence());
        }
        return confs;
    }
}
