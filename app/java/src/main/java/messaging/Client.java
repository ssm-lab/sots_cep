package messaging;

import com.google.gson.Gson;
import com.fasterxml.jackson.databind.ObjectMapper;
import event.Event;
import org.zeromq.ZMQ;

import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.function.BiConsumer;
import java.util.logging.Level;
import java.util.logging.Logger;

public class Client {
    private static final Logger LOG = Logger.getLogger(Client.class.getName());
    private final Gson gson = new Gson();

    private final String prefix;
    private final ZMQ.Context context;
    private final ZMQ.Socket subscriber;
    private final ZMQ.Socket publisher;
    private final ZMQ.Poller poller;
    private final ObjectMapper mapper;

    // topic -> list of consumers
    private final Map<String, List<BiConsumer<String, Event>>> consumers = new HashMap<>();

    public Client(String prefix,
                  String subscriberEndpoint,
                  String publisherEndpoint) {
        this.prefix = prefix;
        this.context = ZMQ.context(1);

        this.subscriber = context.socket(ZMQ.SUB);
        this.subscriber.connect(subscriberEndpoint);

        this.publisher = context.socket(ZMQ.PUB);
        this.publisher.connect(publisherEndpoint);

        this.poller = context.poller(1);
        this.poller.register(this.subscriber, ZMQ.Poller.POLLIN);
        this.mapper = new ObjectMapper();
        
    }

    /** Publish an event to prefix.streamId */
    public void publish(Event event, String streamId) {
        String topic = prefix + "." + streamId;
        String payload = gson.toJson(event);
        publisher.sendMore(topic.getBytes(StandardCharsets.UTF_8));
        publisher.send(payload.getBytes(StandardCharsets.UTF_8));

    }

    /** Subscribe a consumer to a specific stream or all streams under prefix */
    public void subscribeTo(String streamId, BiConsumer<String, Event> consumer) {
        String topic = (streamId.equals("*")) ? prefix + "." : prefix + "." + streamId;
        subscriber.subscribe(topic.getBytes(StandardCharsets.UTF_8));
        consumers.computeIfAbsent(topic, k -> new ArrayList<>()).add(consumer);
        LOG.info(() -> "[Client-" + prefix + "] Subscribed to " + topic);
    }

    /** Dispatch one round of events (non-blocking with timeout) */
    public void dispatch(int timeoutMs) {
        try {
            int rc = poller.poll(timeoutMs);
            if (rc > 0 && poller.pollin(0)) {
                String topic = subscriber.recvStr();
                String payload = subscriber.recvStr();
//                Event event = gson.fromJson(payload, Event.class);
                Event event = this.mapper.readValue(payload, Event.class);

                // forward to all matching consumers
                consumers.forEach((subscribedTopic, handlers) -> {
                    if (topic.startsWith(subscribedTopic)) {
                        for (BiConsumer<String, Event> handler : handlers) {
                            handler.accept(topic, event);
                        }
                    }
                });
            }
        } catch (Exception e) {
            LOG.log(Level.WARNING, "[Client-" + prefix + "] Dispatch error", e);
        }
    }

    public void close() {
        try { poller.unregister(subscriber); } catch (Exception ignored) {}
        subscriber.close();
        publisher.close();
        context.term();
        LOG.info(() -> "[Client-" + prefix + "] Closed");
    }
}
