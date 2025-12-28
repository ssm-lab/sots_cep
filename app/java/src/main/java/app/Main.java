package app;

import cep.esper.EsperCEPEngine;
import patterns.esper.EsperPatternManager;
import runtime.EventStream;
import utils.PatternLogger;

public class Main {

    public static void main(String[] args) throws Exception {
        if (args.length < 3) {
            System.err.println("Missing arguments, ensure you pass: <patterncfg> <runDir> <logMatches>");
            System.exit(1);
        }

        String patternFile = args[0];
        String runDir = args[1];
        Boolean logMatches = Boolean.parseBoolean(args[2]);

        EsperCEPEngine engine = new EsperCEPEngine();
        engine.initialize();

        PatternLogger logger = new PatternLogger(runDir);
        EsperPatternManager manager = new EsperPatternManager(engine, logger, logMatches);
        manager.initialize(patternFile);

        EventStream stream = new EventStream("tcp://localhost:5557", "tcp://localhost:5558");
        stream.subscribe((topic, event) -> engine.handleEvent(event),"observed","*");
        stream.subscribe((topic, event) -> engine.handleEvent(event),"reconstructed","*");
        
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.out.println("[JAVA] Shutdown hook triggered — cleaning up.");
            try {
                stream.stop();
                engine.shutdown();
                logger.close();
            } catch (Exception e) {
                e.printStackTrace();
            }
        }));

        try {
            stream.dispatch(5, false);
        } finally {
            System.out.println("[JAVA] Exiting normally — closing resources.");
            try {
                stream.stop();
            } catch (Exception ignored) {}
            try {
                engine.shutdown();
            } catch (Exception ignored) {}
            try {
                logger.close();
            } catch (Exception ignored) {}
        }
    }
}
