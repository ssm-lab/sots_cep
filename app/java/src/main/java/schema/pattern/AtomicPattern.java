package schema.pattern;

import schema.event.Event;
import java.util.*;

/**
 * Represents a single atomic pattern match corresponding to one rule.
 * Wraps the events contributing to this detection.
 */
public class AtomicPattern extends Pattern {

    public AtomicPattern(String name, List<Event> events, double confidence) {
        super(name, "atomic", confidence);

        if (events == null || events.isEmpty()) {
            throw new IllegalArgumentException("AtomicPattern requires at least one Event");
        }

        // Store contributing events as a single nested group
        eventsNested.add(new ArrayList<>(events));

        // get the sources of the contributing events
        for (Event e : events) {
            if (e.getSrc() != null) {
                sourceIds.add(e.getSrc());
            }
        }
    }
}
