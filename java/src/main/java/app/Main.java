package app;

import cep.EsperSetup;
import cep.CEPManager;
import patterns.PatternLoader;
import messaging.EventStream;
import messaging.StreamClient;

public class Main {
    public static void main(String[] args) throws Exception {
        StreamClient client = new StreamClient();
        EventStream eventStream = new EventStream(client);

        EsperSetup esper = new EsperSetup();
        CEPManager cep = new CEPManager(eventStream, esper.getRuntime());

        PatternLoader loader = new PatternLoader(
        	    esper.getConfiguration(),
        	    esper.getRuntime(),
        	    eventStream
        	);

        // Load all patterns from config file
        loader.loadPatternsFromFile("patterns.json");
        // Start pipeline
        cep.start();
        eventStream.start();

        // Graceful shutdown
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            eventStream.stop();
            client.close();
        }));
    }
}
