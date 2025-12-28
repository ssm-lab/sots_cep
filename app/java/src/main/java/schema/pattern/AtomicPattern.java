package schema.pattern;

import schema.event.Event;
import java.util.*;

/**
 * Represents a single atomic pattern match corresponding to one rule (e.g. high temperature).
 * Wraps a set of raw sensor Events contributing to this match.
 */
public class AtomicPattern extends Pattern {

    public AtomicPattern(String name, List<Event> events, double confidence) {
        super(name, "atomic", confidence);

        // Store events as one nested group
        this.eventsNested.add(new ArrayList<>(events));

        // Derive representative stream ID
        if (!events.isEmpty()) {
            this.streamId = events.get(0).getSrc();
            for (Event e : events) {
                this.addStreamId(e.getSrc());
            }
        }
    }
}
