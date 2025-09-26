package logger;

import event.Event;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.time.Instant;

public class PatternLogger implements AutoCloseable {
    private final PrintWriter writer;

    public PatternLogger(String filepath) throws IOException {
        File file = new File(filepath);
        File parent = file.getParentFile();
        if (parent != null && !parent.exists()) {
            parent.mkdirs();  // make sure the directory exists
        }

        this.writer = new PrintWriter(new FileWriter(file, false), true);
        // Write header row
        writer.println("timestamp,pattern,outcome,stream_id,event_id,value,status,source");
    }

    public synchronized void logPatternMatch(String patternName, String outcome, Event event) {
        long now = Instant.now().toEpochMilli();
        String row = String.format(
                "%d,%s,%s,%s,%s,%s,%s,%s",
                now,
                patternName,
                outcome,
                safe(event.getStreamId()),
                safe(event.getEventId()),
                safe(event.getValue()),
                safe(event.getStatus()),
                safe(event.getSource())
        );
        writer.println(row);
    }

    private String safe(Object o) {
        return o == null ? "" : o.toString();
    }
    
    public void logRaw(String patternName, String eventIds) {
        writer.printf("%s,%s%n", patternName, eventIds);
        writer.flush();
    }


    @Override
    public void close() {
        writer.flush();
        writer.close();
    }
}
