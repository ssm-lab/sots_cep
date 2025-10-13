package cep;

import java.io.IOException;

import schema.event.Event;

/**
 * Handles setup of CEP Engine runtime and configuration.
 */

public interface CEPEngine {
    /** Initialize the CEP engine and prepare configuration. */
    void initialize();

    /** Handle a new incoming event. */
    void handleEvent(Event event);

    void shutdown() throws IOException;
}
