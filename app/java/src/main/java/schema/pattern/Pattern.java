package schema.pattern;

import schema.event.Event;
import java.util.*;


/**
 * Base representation of a detected pattern within the CEP layer
 */



public abstract class Pattern {
    protected String patternName;
    protected String patternType;
    protected List<Event> events;
    protected List<Double> confidences;
    public double confidence;
    protected List<String> sources;
    protected List<String> contributingPatterns;

    public Pattern(String patternName,
                         String patternType,
                         List<Event> events,
                         List<Double> confidences,
                         double confidence,
                         List<String> sources,
                         List<String> contributingPatterns) {
        this.patternName = patternName;
        this.patternType = patternType;
        this.events = events;
        this.confidences = confidences;
        this.confidence = confidence;
        this.sources = sources;
        this.contributingPatterns = contributingPatterns;
    }

    public String getPatternName() { return patternName; }
    public String getPatternType() { return patternType; }
    public List<Event> getEvents() { return events; }
    public List<Double> getConfidences() { return confidences; }
    public double getConfidence() { return confidence; }
    public List<String> getSources() { return sources; }
    public List<String> getContributingPatterns() { return contributingPatterns; }

    public abstract int countEvents();
}
