package utils;

import schema.pattern.Pattern;
import schema.pattern.ComplexPattern;
import schema.event.Event;

import java.io.*;
import java.nio.file.*;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.stream.Collectors;

public class PatternLogger implements AutoCloseable {
    private final PrintWriter writer;
    private final long experimentStart;  // 🔹 reference timestamp

    public PatternLogger(String runDir) throws IOException {
        Files.createDirectories(Paths.get(runDir));
        Path file = Paths.get(runDir, "patterns.csv");
        this.writer = new PrintWriter(new FileWriter(file.toFile(), false));

        this.experimentStart = System.currentTimeMillis();  // 🔹 baseline for relative time

        writer.println("# Logger: PatternLogger | Started: " + new Date());
        writer.println("fired_at,fired_offset_sec,pattern_name,pattern_type,"
                + "subpatterns,subpattern_confidences,num_subpatterns,num_events,confidence,nested_event_ids");
    }

    public synchronized void log(Pattern record) {
        long now = System.currentTimeMillis();
        double offsetSec = (now - experimentStart) / 1000.0;  // 🔹 relative time since experiment start

        String firedAt = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS").format(new Date(now));

        List<String> subpatternNames = new ArrayList<>();
        List<Double> subpatternConfidences = new ArrayList<>();

        if (record instanceof ComplexPattern complex) {
            subpatternNames.addAll(complex.getSubpatternNames());
            subpatternConfidences.addAll(complex.getSubpatternConfidences());
        } else {
            subpatternNames.add(record.getPatternName());
            subpatternConfidences.add(record.getConfidence());
        }

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

        writer.printf("%s,%.3f,%s,%s,%s,%s,%d,%d,%.4f,%s%n",
                firedAt,
                offsetSec, // 🔹 new field: relative offset (seconds)
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
