package schema.pattern;

import schema.event.Event;
import java.util.List;

/**
 * Represents an atomic pattern that directly matches one or more base events .
 */
public class AtomicPattern extends Pattern {

    public AtomicPattern(String name, List<Event> events, double confidence) {
        super(name, "atomic", confidence);
        this.eventsNested.add(events);
    }
}
