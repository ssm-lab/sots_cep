package logger;

import schema.pattern.Pattern;
import schema.pattern.ComplexPattern;
import schema.event.Event;

import java.io.*;
import java.nio.file.*;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Logs all detected pattern matches (atomic or complex) to a CSV file.
 * Each record includes the pattern name, type, confidence, contributing subpatterns,
 * subpattern confidences, and a nested JSON-like structure of event IDs for traceability.
 */
public class PatternLogger implements AutoCloseable {
    private final PrintWriter writer;

    public PatternLogger(String runDir) throws IOException {
        Files.createDirectories(Paths.get(runDir));
        Path file = Paths.get(runDir, "patterns.csv");
        this.writer = new PrintWriter(new FileWriter(file.toFile(), false));

        writer.println("# Logger: PatternLogger | Started: " + new Date());
        writer.println("fired_at,pattern_name,pattern_type,subpatterns,"
                + "subpattern_confidences,num_subpatterns,num_events,confidence,nested_event_ids");
    }

    /**
     * Logs a pattern match with nested event structure and subpattern confidences.
     */
    public synchronized void log(Pattern record) {
        String firedAt = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS").format(new Date());

        // Extract subpattern data
        List<String> subpatternNames = new ArrayList<>();
        List<Double> subpatternConfidences = new ArrayList<>();

        if (record instanceof ComplexPattern complex) {
            subpatternNames.addAll(complex.getSubpatternNames());
            subpatternConfidences.addAll(complex.getSubpatternConfidences());
        } else {
            subpatternNames.add(record.getPatternName());
            subpatternConfidences.add(record.getConfidence());
        }

        // Nested event IDs (one bracketed group per subpattern)
        List<String> nestedEventGroups = record.getEventsNested().stream()
                .map(inner -> inner.stream()
                        .map(Event::getEventId)
                        .filter(Objects::nonNull)
                        .collect(Collectors.joining(";", "[", "]")))
                .collect(Collectors.toList());

        String subpatternField = "[" + String.join(";", subpatternNames) + "]";
        String subConfField = "[" + subpatternConfidences.stream()
                .map(c -> String.format("%.4f", c))
                .collect(Collectors.joining(";")) + "]";
        String nestedJsonLike = "[" + String.join(";", nestedEventGroups) + "]";

        int numSub = record.countSubPatterns();
        int numEvents = record.countAllEvents();

        writer.printf("%s,%s,%s,%s,%s,%d,%d,%.4f,%s%n",
                firedAt,
                record.getPatternName(),
                record.getPatternType(),
                subpatternField,
                subConfField,
                numSub,
                numEvents,
                record.getConfidence(),
                nestedJsonLike);

        writer.flush();
    }

    @Override
    public void close() {
        writer.close();
    }
}
