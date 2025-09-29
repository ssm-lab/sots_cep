package logger;

import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.text.SimpleDateFormat;
import java.util.Date;


public class PatternLogger implements AutoCloseable {
    private final String filepath;
    private final PrintWriter writer;

    public PatternLogger(String runDir) throws IOException {
    	Files.createDirectories(Paths.get(runDir));
    	this.filepath = Paths.get(runDir, "patterns.csv").toString();
        this.writer = new PrintWriter(new FileWriter(filepath, false));

        writer.println("# Logger: PatternLogger | Started: " + new Date());
        writer.println("fired_at,pattern_name,outcome,partition,stream_ids,event_ids,confidences");
    }


    public synchronized void logPatternMatch(String patternName,
                                             String outcome,
                                             String partition,
                                             String streamIds,
                                             String eventIds,
                                             String confidences) {
        String firedAt = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS").format(new Date());
        writer.printf("%s,%s,%s,%s,%s,%s,%s%n",
                firedAt, patternName, outcome, partition, streamIds, eventIds, confidences);
        writer.flush();
    }

    @Override
    public void close() {
        writer.close();
    }
}
