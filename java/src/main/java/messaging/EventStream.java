package messaging;

import event.Event;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Consumer;
import java.util.logging.Logger;

public class EventStream {
    private static final Logger LOG = Logger.getLogger(EventStream.class.getName());

    private final StreamClient client;

    private final Map<String, Map<String, Consumer<Event>>> subscribers = new ConcurrentHashMap<>();

    public EventStream(StreamClient client) {
        this.client = client;
        this.client.setDispatcher(this::dispatchEvent); // hook back
    }

    public void addEvent(String partition, String streamId, Event event) {
        String topic = partition + "." + streamId;
        client.publish(topic, event);
        LOG.info(() -> "[EventStream] Published " + topic + " -> " + event);
    }

    public void subscribe(String partition, String streamId, Consumer<Event> handler) {
        subscribers
            .computeIfAbsent(partition, k -> new ConcurrentHashMap<>())
            .put(streamId, handler);

        String prefix = partition + (streamId.equals("*") ? "." : "." + streamId);
        client.subscribeTo(prefix);
    }


    private void dispatchEvent(String topic, Event event) {
        String[] parts = topic.split("\\.", 2);
        if (parts.length < 2) return;
        String partition = parts[0];
        String streamId = parts[1];

        Map<String, Consumer<Event>> partitionSubs = subscribers.get(partition);
        if (partitionSubs == null) {
            LOG.fine(() -> "[EventStream] No subscribers for partition " + partition);
            return;
        }

        // Exact match
        Consumer<Event> handler = partitionSubs.get(streamId);
        if (handler != null) {
            handler.accept(event);
            return;
        }

        // Wildcard match
        Consumer<Event> wildcard = partitionSubs.get("*");
        if (wildcard != null) {
            wildcard.accept(event);
            return;
        }

        LOG.fine(() -> "[EventStream] No handler for " + topic);
    }


    public void start() {
        client.join();
        client.subscribe();
    }

    public void stop() {
        client.close();
        LOG.info("[EventStream] Stopped");
    }
}
