package app;

import cep.EsperSetup;
import patterns.PatternLoader;
import logger.PatternLogger;
import runtime.EventStream;

public class Main {
    public static void main(String[] args) throws Exception {
        EventStream eventStream = new EventStream("tcp://localhost:5557", "tcp://localhost:5558");
        EsperSetup esper = new EsperSetup();

        eventStream.subscribe((topic, event) -> {
            System.out.println("Got event from " + topic + ": " + event);
            esper.getRuntime().getEventService().sendEventBean(event, "Event");
        }, "reconstructed", "*");

        

        try (PatternLogger patternLogger = new PatternLogger("data/pattern_logs.csv")) {
            PatternLoader loader = new PatternLoader(
                    esper.getConfiguration(),
                    esper.getRuntime(),
                    eventStream,
                    patternLogger
            );

            // Load patterns from JSON file in resources
            loader.loadPatternsFromFile("patterns.json");

            // 5. Start dispatch loop (blocking)
            eventStream.dispatch(1000, false);
        }
        // PatternLogger closes automatically (try-with-resources)
    }
}
