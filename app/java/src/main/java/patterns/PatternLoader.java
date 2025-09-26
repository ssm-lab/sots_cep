package patterns;

import com.espertech.esper.common.client.EPCompiled;
import com.espertech.esper.common.client.configuration.Configuration;
import com.espertech.esper.compiler.client.CompilerArguments;
import com.espertech.esper.compiler.client.EPCompiler;
import com.espertech.esper.compiler.client.EPCompilerProvider;
import com.espertech.esper.runtime.client.*;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

import logger.PatternLogger;

import java.io.InputStreamReader;
import java.io.Reader;
import java.util.Map;
import java.util.logging.Logger;

public class PatternLoader {
    private static final Logger LOG = Logger.getLogger(PatternLoader.class.getName());

    private final EPCompiler compiler = EPCompilerProvider.getCompiler();
    private final CompilerArguments args;
    private final EPRuntime runtime;
    private final PatternLogger patternLogger;
    private final Gson gson = new Gson();

    public PatternLoader(Configuration configuration,
                         EPRuntime runtime,
                         Object eventStream,   // unused, kept for future integration
                         PatternLogger patternLogger) {
        this.args = new CompilerArguments(configuration);
        this.runtime = runtime;
        this.patternLogger = patternLogger;
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

        // Attach listeners to ALL statements in this deployment
        for (EPStatement stmt : deployment.getStatements()) {
        	stmt.addListener((newData, oldData, s, rt) -> {
        	    if (newData == null || newData.length == 0) return;

        	    Object underlying = newData[0].getUnderlying();

        	    if (underlying instanceof Map) {
        	        @SuppressWarnings("unchecked")
        	        Map<String, Object> map = (Map<String, Object>) underlying;

        	        // Collect event IDs
        	        StringBuilder ids = new StringBuilder();
        	        for (Map.Entry<String, Object> entry : map.entrySet()) {
        	            Object v = entry.getValue();
        	            if (v instanceof com.espertech.esper.common.client.EventBean eb
        	                && eb.getUnderlying() instanceof event.Event ev) {
        	                ids.append(ev.getEventId()).append(";");
        	            }
        	        }

        	        // Log one row: patternName, allIDs
        	        patternLogger.logRaw(s.getName(), ids.toString());

        	        LOG.info(() -> "[CEP] " + s.getName() + " matched events: " + ids);
        	    } else {
        	        LOG.warning(() -> "[CEP] " + s.getName() + " unexpected payload: " + underlying);
        	    }
        	});

        }

    }
}
