package schema.pattern;

import java.util.*;
import java.util.stream.Collectors;

import schema.event.Event;

/**
 * Represents a single pattern detected directly from
 * incoming {@link schema.event.Event} streams.
 */

public class AtomicPattern extends Pattern {

    public AtomicPattern(String name,
                               List<Event> events,
                               double aggregatedConfidence) {
        super(
            name,
            "atomic",
            events,
            events.stream().map(Event::getConfidence).collect(Collectors.toList()),
            aggregatedConfidence,
            events.stream().map(Event::getOrigin).distinct().collect(Collectors.toList()),
            List.of()
        );
    }

    @Override
    public int countEvents() {
        return events.size();
    }
}
