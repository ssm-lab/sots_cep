package app;

import cep.EsperSetup;
import patterns.PatternLoader;
import logger.PatternLogger;
import runtime.EventStream;

public class Main {
    public static void main(String[] args) throws Exception {
    	if (args.length < 2) {
            System.err.println("Usage: Main <patternFile> <runDir>");
            System.exit(1);
        }
    	
    	String patternFile = args.length > 0 ? args[0] : "patterns/basic_patterns.json";
        String runDir = args.length > 1 ? args[1] : "data/logs";
        
        EventStream eventStream = new EventStream("tcp://localhost:5557", "tcp://localhost:5558");
        EsperSetup esper = new EsperSetup();

        eventStream.subscribe((topic, event) -> {
            esper.getRuntime().getEventService().sendEventBean(event, "Event");
        }, "reconstructed", "*");
        
        eventStream.subscribe((topic, event) -> {
            esper.getRuntime().getEventService().sendEventBean(event, "Event");
        }, "groundtruth", "*");


        try (PatternLogger patternLogger = new PatternLogger(runDir)) {
            PatternLoader loader = new PatternLoader(
                    esper.getConfiguration(),
                    esper.getRuntime(),
                    patternLogger
            );

            loader.loadPatternsFromFile(patternFile);
            eventStream.dispatch(1000, false);
        }
    }
}
