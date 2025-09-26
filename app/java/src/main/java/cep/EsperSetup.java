package cep;
import event.Event;

import com.espertech.esper.common.client.configuration.Configuration;
import com.espertech.esper.runtime.client.EPRuntime;
import com.espertech.esper.runtime.client.EPRuntimeProvider;


public class EsperSetup {
    private final EPRuntime runtime;
    private final Configuration configuration;

    public EsperSetup() {
        this.configuration = new Configuration();
        configuration.getCommon().addEventType(Event.class); // Register incoming events to be of the Event Class types
        this.runtime = EPRuntimeProvider.getDefaultRuntime(configuration);
    }

    public EPRuntime getRuntime() {
        return this.runtime;
    }
    
    public Configuration getConfiguration() { 
    	return configuration; 
    }
}
