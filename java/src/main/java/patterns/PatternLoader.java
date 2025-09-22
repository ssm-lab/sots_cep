package patterns;

import com.espertech.esper.common.client.EPCompiled;
import com.espertech.esper.common.client.configuration.Configuration;
import com.espertech.esper.compiler.client.CompilerArguments;
import com.espertech.esper.compiler.client.EPCompiler;
import com.espertech.esper.compiler.client.EPCompilerProvider;
import com.espertech.esper.runtime.client.EPDeployment;
import com.espertech.esper.runtime.client.EPRuntime;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

import java.io.InputStreamReader;
import java.io.Reader;
import java.util.logging.Logger;

import messaging.EventStream;
import event.Event;
import messaging.StreamClient;

import java.util.HashMap;

public class PatternLoader {
    private static final Logger LOG = Logger.getLogger(PatternLoader.class.getName());

    private final EPCompiler compiler = EPCompilerProvider.getCompiler();
    private final CompilerArguments args;
    private final EPRuntime runtime;
    private final EventStream eventStream;
    private final Gson gson = new Gson();

    public PatternLoader(Configuration configuration, EPRuntime runtime, EventStream eventStream) {
        this.args = new CompilerArguments(configuration);
        this.runtime = runtime;
        this.eventStream = eventStream;
    }

    public void loadPatternsFromFile(String resourceName) throws Exception {
    	try (Reader reader = new InputStreamReader(
                getClass().getClassLoader().getResourceAsStream(resourceName))) {

            JsonArray patterns = gson.fromJson(reader, JsonArray.class);

        for (JsonElement element : patterns) {
            JsonObject pattern = element.getAsJsonObject();
            String name = pattern.get("name").getAsString();
            String epl = pattern.get("epl").getAsString();

            loadPattern(epl, name);
        }
    }
    	}

    public void loadPattern(String epl, String name) throws Exception {
        EPCompiled compiled = compiler.compile(epl, args);
        EPDeployment deployment = runtime.getDeploymentService().deploy(compiled);

        runtime.getDeploymentService().getStatement(deployment.getDeploymentId(), name)
        .addListener((newData, oldData, stmt, rt) -> {
            if (newData == null || newData.length == 0) return;

            Object underlying = newData[0].getUnderlying();
            if (!(underlying instanceof Event)) return;

            Event matched = (Event) underlying;

            // copy event
            Event outEvent = new Event();
            outEvent.stream_id = matched.stream_id;
            outEvent.timestamp = matched.timestamp;
            outEvent.datatype = matched.datatype;
            outEvent.unit = matched.unit;
            outEvent.value = matched.value;
            outEvent.observed_value = matched.observed_value;
            outEvent.imputed_value = matched.imputed_value;
            outEvent.method = matched.method;
            outEvent.confidence = matched.confidence;

            // Preserve existing extras if any
            if (matched.extras != null) {
                outEvent.extras = new HashMap<>(matched.extras);
            } else {
                outEvent.extras = new HashMap<>();
            }

            // Add/overwrite pattern metadata
            outEvent.extras.put("pattern", name);

            // publish to matched partition
            eventStream.addEvent("matched", outEvent.stream_id, outEvent);
            LOG.info(() -> "[CEP] Pattern match (" + name + ") for stream " + outEvent.stream_id);
        });
    }
}
