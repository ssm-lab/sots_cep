package schema.pattern;

import schema.event.Event;
import java.util.*;

/**
 * Base class representing a generic pattern match (atomic or complex).
 */
public abstract class Pattern {

    /** name of the pattern (e.g., Overspeeding) */
    protected final String patternName;

    /** atomic or complex */
    protected final String patternType;

    /** aggregated confidence of the pattern match */
    protected double confidence;

    /** set of contributing source identifiers */
    protected final Set<String> sourceIds = new HashSet<>();

    /**
     * Nested event groups.
     * Each inner list corresponds to one subpattern’s contributing events.
     */
    protected final List<List<Event>> eventsNested = new ArrayList<>();

    protected Pattern(String name, String type, double confidence) {
        this.patternName = name;
        this.patternType = type;
        this.confidence = confidence;
    }

    // ---------------- Accessors ----------------

    public String getPatternName() {
        return patternName;
    }

    public String getPatternType() {
        return patternType;
    }

    public double getConfidence() {
        return confidence;
    }

    public void setConfidence(double confidence) {
        this.confidence = confidence;
    }

    public Set<String> getSourceIds() {
        return Collections.unmodifiableSet(sourceIds);
    }

    public List<List<Event>> getEventsNested() {
        return Collections.unmodifiableList(eventsNested);
    }

    /** Total number of contributing events across all nested groups. */
    public int countAllEvents() {
        return eventsNested.stream().mapToInt(List::size).sum();
    }

    /** Number of immediate subpattern groups (1 for atomic patterns). */
    public int countSubPatterns() {
        return eventsNested.size();
    }

    /** Comma-separated source IDs contributing to the pattern */
    public String getSourceIdsAsString() {
        return String.join(",", sourceIds);
    }

    @Override
    public String toString() {
        return String.format(
            "[%s | type=%s | conf=%.3f | streams=%s]",
            patternName, patternType, confidence, getSourceIdsAsString()
        );
    }
}
