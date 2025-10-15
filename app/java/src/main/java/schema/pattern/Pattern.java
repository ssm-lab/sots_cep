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

    /** Representative stream ID for Esper joins */
    protected String streamId;

    /** Set of all contributing stream IDs (traceability) */
    protected Set<String> streamIds = new HashSet<>();

    /** Nested event groups — each sublist corresponds to one subpattern’s events */
    protected List<List<Event>> eventsNested = new ArrayList<>();

    public Pattern(String name, String type, double confidence) {
        this.patternName = name;
        this.patternType = type;
        this.confidence = confidence;
    }

    // ---------------- Getters / Setters ----------------
    public String getPatternName() { return patternName; }
    public String getPatternType() { return patternType; }
    public double getConfidence() { return confidence; }
    public void setConfidence(double confidence) { this.confidence = confidence; }

    public String getStreamId() { return streamId; }
    public void setStreamId(String streamId) { this.streamId = streamId; }

    public Set<String> getStreamIds() { return streamIds; }
    public void addStreamId(String id) { if (id != null) this.streamIds.add(id); }

    public List<List<Event>> getEventsNested() { return eventsNested; }

    /** Total number of individual events across all nested groups. */
    public int countAllEvents() {
        return eventsNested.stream().mapToInt(List::size).sum();
    }

    /** Number of direct subpattern groups (for complex patterns). */
    public int countSubPatterns() {
        return eventsNested.size();
    }

    /** Comma-separated streamIds for logging */
    public String getStreamIdsAsString() {
        return String.join(",", streamIds);
    }

    @Override
    public String toString() {
        return String.format("[%s | type=%s | conf=%.3f | streams=%s]",
                patternName, patternType, confidence, getStreamIdsAsString());
    }
}
