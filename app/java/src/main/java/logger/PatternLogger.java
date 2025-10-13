package logger;

import java.io.*;
import java.nio.file.*;
import java.text.SimpleDateFormat;
import java.util.*;

import schema.pattern.Pattern;
import schema.event.Event;

/**
 * The PatternLogger handles logging of detected pattern matches
 * (both atomic and complex) into a CSV file
 */

public class PatternLogger implements AutoCloseable {
    private final PrintWriter writer;

    public PatternLogger(String runDir) throws IOException {
        Files.createDirectories(Paths.get(runDir));
        Path file = Paths.get(runDir, "patterns.csv");
        this.writer = new PrintWriter(new FileWriter(file.toFile(), false));

        writer.println("# Logger: PatternLogger | Started: " + new Date());
        writer.println("fired_at,pattern_name,pattern_type,contributing_patterns,"
                + "num_events,confidence,sources,event_ids");
    }

    public synchronized void log(Pattern record) {
        String firedAt = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS").format(new Date());

        String contributing = String.join(";", record.getContributingPatterns());
        String sources = String.join(";", record.getSources());
        String eventIds = record.getEvents().stream()
                                .map(Event::getEventId)
                                .map(Object::toString)
                                .reduce((a, b) -> a + ";" + b)
                                .orElse("");

        writer.printf("%s,%s,%s,%s,%d,%.4f,%s,%s%n",
                firedAt,
                record.getPatternName(),
                record.getPatternType(),
                contributing,
                record.countEvents(),
                record.getConfidence(),
                sources,
                eventIds);

        writer.flush();
    }

    @Override
    public void close() {
        writer.close();
    }
}
