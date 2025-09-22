package messaging;

import org.zeromq.ZMQ;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.UUID;
import java.util.logging.Level;
import java.util.logging.Logger;


public abstract class Client {
    private static final Logger LOG = Logger.getLogger(Client.class.getName());

    protected final UUID id = UUID.randomUUID();

    protected final ZMQ.Context context;
    protected final ZMQ.Socket snapshot;   // DEALER
    protected final ZMQ.Socket subscriber; // SUB
    protected final ZMQ.Socket publisher;  // PUSH
    protected final ZMQ.Poller poller;

    private volatile boolean running = false;

    public Client() {
        this("tcp://localhost:5556", "tcp://localhost:5557", "tcp://localhost:5558");
    }

    public Client(String snapshotEndpoint, String subscriberEndpoint, String publisherEndpoint) {
        this.context = ZMQ.context(1);

        this.snapshot = context.socket(ZMQ.DEALER);
        this.snapshot.setLinger(0);
        this.snapshot.connect(snapshotEndpoint);

        this.subscriber = context.socket(ZMQ.SUB);
        this.subscriber.setLinger(0);
        this.subscriber.connect(subscriberEndpoint);

        this.publisher = context.socket(ZMQ.PUSH);
        this.publisher.setLinger(0);
        this.publisher.connect(publisherEndpoint);

        this.poller = context.poller(1);
        this.poller.register(this.subscriber, ZMQ.Poller.POLLIN);
    }


    public void join() {
        snapshot.send("request_snapshot");
        while (!Thread.currentThread().isInterrupted()) {
            try {
                byte[] msg = snapshot.recv(0);
                if (msg == null) break;
                String s = new String(msg, StandardCharsets.UTF_8);
                LOG.fine(() -> "snapshot: " + s);
                if ("finished_snapshot".equals(s)) {
                    LOG.fine("Received snapshot");
                    break;
                }
            } catch (Exception e) {
                LOG.log(Level.FINE, "Join interrupted", e);
                return;
            }
        }
    }


    public void subscribe() {
        LOG.fine("Receiving messages");
        running = true;

        long alarmNanos = System.nanoTime() + Duration.ofSeconds(1).toNanos();

        while (running && !Thread.currentThread().isInterrupted()) {
            long now = System.nanoTime();
            long remainingMs = Math.max(0, (alarmNanos - now) / 1_000_000L);

            try {
                int rc = poller.poll((int) remainingMs);
                if (rc > 0 && poller.pollin(0)) {
                    subscriberAction();
                }

                if (System.nanoTime() >= alarmNanos) {
                    timeoutAction();
                    alarmNanos += Duration.ofSeconds(1).toNanos();
                }
            } catch (Exception e) {
                LOG.log(Level.FINE, "Subscribe loop interrupted", e);
                break;
            }
        }
        LOG.fine("Interrupted");
    }

    /** Stop the subscribe loop and close sockets/context. */
    public void close() {
        running = false;
        try { poller.unregister(subscriber); } catch (Exception ignored) {}
        safeClose(snapshot);
        safeClose(subscriber);
        safeClose(publisher);
        try { context.term(); } catch (Exception ignored) {}
    }

    private void safeClose(ZMQ.Socket s) {
        if (s != null) {
            try { s.close(); } catch (Exception ignored) {}
        }
    }

    

    protected abstract void subscriberAction();

    protected abstract void timeoutAction();
}
