package app;

import cep.esper.EsperCEPEngine;
import logger.PatternLogger;
import patterns.esper.EsperPatternManager;
import runtime.EventStream;

public class Main {
    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("Missing arguments, ensure you pass: <patterncfg> <runDir>");
            System.exit(1);
        }

        String patternFile = args[0];
        String runDir = args[1];

        // Initialize the engine
        EsperCEPEngine engine = new EsperCEPEngine();
        engine.initialize();

        // Initialize pattern manager
        try (PatternLogger logger = new PatternLogger(runDir)) {
            EsperPatternManager manager = new EsperPatternManager(engine, logger);
            manager.initialize(patternFile);

            // Setup event stream
            EventStream stream = new EventStream("tcp://localhost:5557", "tcp://localhost:5558");
            stream.subscribe((topic, event) -> engine.handleEvent(event), "reconstructed", "*");
            stream.subscribe((topic, event) -> engine.handleEvent(event), "groundtruth", "*");

            // Run loop
            stream.dispatch(100, false);
        }

        engine.shutdown();
    }
}