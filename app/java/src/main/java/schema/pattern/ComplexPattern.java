package schema.pattern;

import java.util.*;
import java.util.stream.Collectors;

/**
 * Represents a composite pattern formed from multiple subpatterns,
 * which may be atomic or other complex patterns.
 */

public class ComplexPattern extends Pattern {

    public ComplexPattern(String name, List<Pattern> subpatterns) {
        super(
            name,
            "complex",
            subpatterns.stream()
                       .flatMap(p -> p.getEvents().stream())
                       .collect(Collectors.toList()),
            subpatterns.stream()
                       .flatMap(p -> p.getConfidences().stream())
                       .collect(Collectors.toList()),
            0.0,  // Manager now decides confidence
            subpatterns.stream()
                       .flatMap(p -> p.getSources().stream())
                       .distinct()
                       .collect(Collectors.toList()),
            subpatterns.stream()
                       .map(Pattern::getPatternName)
                       .collect(Collectors.toList())
        );
    }

    @Override
    public int countEvents() {
        return events.size();
    }
}
