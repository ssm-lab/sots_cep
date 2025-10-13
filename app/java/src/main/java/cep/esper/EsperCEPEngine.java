package cep.esper;

import java.io.IOException;
import java.util.logging.Logger;

import com.espertech.esper.common.client.configuration.Configuration;
import com.espertech.esper.runtime.client.EPRuntime;
import com.espertech.esper.runtime.client.EPRuntimeProvider;

import cep.CEPEngine;
import schema.event.Event;
import schema.pattern.Pattern;

/**
 * The EsperCEPEngine handles CEP runtime setup and lifecycle management.
 * It declares base event streams ("Event") and a pattern stream ("PatternRecordStream")
 * that allows layering of atomic and complex patterns for hierarchical event detection.
 */


public class EsperCEPEngine implements CEPEngine {
    private static final Logger LOG = Logger.getLogger(EsperCEPEngine.class.getName());
    private final Configuration configuration;
    private EPRuntime runtime;

    public EsperCEPEngine() {
        configuration = new Configuration();
        configuration.getCommon().addEventType("Event", Event.class);
        configuration.getCommon().addEventType("PatternRecordStream", Pattern.class);
        LOG.info("[EsperCEPEngine] Created");
    }

    public void initialize() {
        runtime = EPRuntimeProvider.getDefaultRuntime(configuration);
        LOG.info("[EsperCEPEngine] Initialized runtime");
    }

    @Override
    public void handleEvent(Event e) {
        runtime.getEventService().sendEventBean(e, "Event");
    }

    public EPRuntime getRuntime() { return runtime; }
    public Configuration getConfiguration() { return configuration; }

	@Override
	public void shutdown() throws IOException {
		LOG.info("[EsperCEPEngine] shutting down");
		try {
			runtime.getDeploymentService().undeployAll();
			runtime.destroy();
		} catch (Exception  e) {
			LOG.warning("[EsperCEPEngine] Error during shutdown: " + e.getMessage());
		} finally {
            runtime = null;
            LOG.info("[EsperCEPEngine] Shutdown complete.");
		}
	}
}
