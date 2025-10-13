package schema.pattern;

import schema.event.Event;
import java.util.*;

/**
 * Base class representing a generic pattern match (atomic or complex).
 * Stores name, type, confidence, and nested event structure so that
 * downstream components can trace which events contributed to each match.
 */
public abstract class Pattern {
    protected String patternName;
    protected String patternType; // "atomic" or "complex"
    protected double confidence;

    /** Nested event groups — each sublist corresponds to one subpattern’s events */
    protected List<List<Event>> eventsNested = new ArrayList<>();

    public Pattern(String name, String type, double confidence) {
        this.patternName = name;
        this.patternType = type;
        this.confidence = confidence;
    }

    public String getPatternName() { return patternName; }
    public String getPatternType() { return patternType; }
    public double getConfidence() { return confidence; }
    public void setConfidence(double confidence) { this.confidence = confidence; }

    public List<List<Event>> getEventsNested() { return eventsNested; }

    /** Total number of individual events across all nested groups. */
    public int countAllEvents() {
        return eventsNested.stream().mapToInt(List::size).sum();
    }

    public int countSubPatterns() {
        return eventsNested.size();
    }
}
