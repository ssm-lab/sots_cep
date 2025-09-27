package logger;

import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.UUID;

public class PatternLogger implements AutoCloseable {
    private final String filepath;
    private final PrintWriter writer;

    public PatternLogger(String outputDir, String baseName) throws IOException {
        Files.createDirectories(Paths.get(outputDir));

        String runId = UUID.randomUUID().toString().substring(0, 8);
        String timestamp = new SimpleDateFormat("yyyyMMdd-HHmmss").format(new Date());
        String filename = baseName + "_" + timestamp + "_" + runId + ".csv";

        this.filepath = Paths.get(outputDir, filename).toString();
        this.writer = new PrintWriter(new FileWriter(filepath, false));

        // metadata + header
        writer.println("# Logger: PatternLogger | Started: " + new Date());
        writer.println("fired_at,pattern_name,outcome,partition,stream_ids,event_ids");
    }

    public synchronized void logPatternMatch(String patternName,
                                             String outcome,
                                             String partition,
                                             String streamIds,
                                             String eventIds) {
        String firedAt = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS").format(new Date());
        writer.printf("%s,%s,%s,%s,%s,%s%n", firedAt, patternName, outcome, partition, streamIds, eventIds);
        writer.flush();
    }

    @Override
    public void close() {
        writer.close();
    }
}
