package messaging;

import com.google.gson.Gson;
import event.Event;
import java.nio.charset.StandardCharsets;
import java.util.function.BiConsumer;
import java.util.logging.Logger;

public class StreamClient extends Client {
    private static final Logger LOG = Logger.getLogger(StreamClient.class.getName());
    private final Gson gson = new Gson();

    // Hook back to EventStream for dispatch
    private BiConsumer<String, Event> dispatcher;

    public StreamClient() {
        super();
    }

    public StreamClient(String snapshotEndpoint, String subscriberEndpoint, String publisherEndpoint) {
        super(snapshotEndpoint, subscriberEndpoint, publisherEndpoint);
    }

    public void setDispatcher(BiConsumer<String, Event> dispatcher) {
        this.dispatcher = dispatcher;
    }

    @Override
    protected void subscriberAction() {
        try {
            String topic = subscriber.recvStr();
            String payload = subscriber.recvStr();
            Event event = gson.fromJson(payload, Event.class);


            LOG.fine(() -> "[StreamClient] Received on topic " + topic + ": " + event);

            // Forward to EventStream if attached
            if (dispatcher != null) {
                dispatcher.accept(topic, event);
            }
        } catch (Exception e) {
            LOG.warning("Failed to process subscriber message: " + e.getMessage());
        }
    }
    
    public void subscribeTo(String prefix) {
        if (prefix == null || prefix.isEmpty()) {
            subscriber.subscribe(new byte[0]); // all topics
            LOG.info("[StreamClient] Subscribed to ALL topics");
        } else {
            subscriber.subscribe(prefix.getBytes(StandardCharsets.UTF_8));
            LOG.info("[StreamClient] Subscribed to prefix: " + prefix);
        }
    }


    @Override
    protected void timeoutAction() {
        LOG.fine("No events received in last interval.");
    }

    public void publish(String topic, Event event) {
        String payload = gson.toJson(event);
        publisher.sendMore(topic);
        publisher.send(payload.getBytes(StandardCharsets.UTF_8));
        LOG.fine(() -> "[StreamClient] Published on topic " + topic + ": " + event);
    }
}
