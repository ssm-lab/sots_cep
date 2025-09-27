package runtime;
import messaging.Client;

import event.Event;

import java.util.HashMap;
import java.util.Map;
import java.util.function.BiConsumer;
import java.util.logging.Logger;

public class EventStream {
    private static final Logger LOG = Logger.getLogger(EventStream.class.getName());
    private final Map<String, Client> partitions = new HashMap<>();
    private boolean running = false;

    public EventStream(String subscriberEndpoint, String publisherEndpoint) {
        partitions.put("observed", new Client("observed", subscriberEndpoint, publisherEndpoint));
        partitions.put("reconstructed", new Client("reconstructed", subscriberEndpoint, publisherEndpoint));
        partitions.put("matched", new Client("matched", subscriberEndpoint, publisherEndpoint));
        partitions.put("late", new Client("late", subscriberEndpoint, publisherEndpoint));
        partitions.put("groundtruth", new Client("groundtruth", subscriberEndpoint, publisherEndpoint));
    }

    public void addEvent(Event event, String partition, String streamId) {
        if (!partitions.containsKey(partition)) {
            throw new IllegalArgumentException("Unknown partition: " + partition);
        }
        partitions.get(partition).publish(event, streamId);
    }

    public void subscribe(BiConsumer<String, Event> consumer, String partition, String streamId) {
        if (!partitions.containsKey(partition)) {
            throw new IllegalArgumentException("Unknown partition: " + partition);
        }
        partitions.get(partition).subscribeTo(streamId, consumer);
    }

    public void dispatch(int timeoutMs, boolean once) {
        running = true;
        while (running) {
            for (Client client : partitions.values()) {
                client.dispatch(timeoutMs);
            }
            if (once) break;
        }
    }

    public void stop() {
        LOG.info("[EventStream] Stopping dispatch loop.");
        running = false;
        partitions.values().forEach(Client::close);
    }
}
