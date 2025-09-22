package cep;

import com.espertech.esper.runtime.client.*;
import event.Event;
import messaging.EventStream;
import java.util.logging.Logger;

public class CEPManager {
    private static final Logger LOG = Logger.getLogger(CEPManager.class.getName());

    private final EventStream eventStream;
    private final EPRuntime runtime;

    public CEPManager(EventStream eventStream, EPRuntime runtime) {
        this.eventStream = eventStream;
        this.runtime = runtime;
    }

    public void start() {
        eventStream.subscribe("imputed", "*", this::handleEvent);

        LOG.info("[CEPManager] Subscribed to imputed partition");
    }

    private void handleEvent(Event event) {
        try {
            runtime.getEventService().sendEventBean(event, "Event"); 
        } catch (Exception e) {
            LOG.warning("[CEPManager] Failed to send event to Esper: " + e.getMessage());
        }
    }
}
