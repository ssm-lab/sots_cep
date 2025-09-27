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
import event.Event;

import java.io.InputStreamReader;
import java.io.Reader;
import java.util.ArrayList;
import java.util.List;
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

        for (EPStatement stmt : deployment.getStatements()) {
            stmt.addListener((newData, oldData, s, rt) -> {
                if (newData == null || newData.length == 0) return;

                // Collect all Event objects from the match
                List<Event> matchedEvents = new ArrayList<>();
                for (String prop : newData[0].getEventType().getPropertyNames()) {
                    Object val = newData[0].get(prop);
                    if (val instanceof Event ev) {
                        matchedEvents.add(ev);
                    }
                }

                if (!matchedEvents.isEmpty()) {
                    // Partition, streamIds, eventIds
                    StringBuilder partitions = new StringBuilder();
                    StringBuilder streamIds = new StringBuilder();
                    StringBuilder eventIds = new StringBuilder();

                    for (Event ev : matchedEvents) {
                        partitions.append(ev.getOrigin()).append(";");
                        streamIds.append(ev.getStreamId()).append(";");
                        eventIds.append(ev.getEventId()).append(";");
                    }

                    String outcome = name.contains("Timeout") ? "partial" : "complete";
                    patternLogger.logPatternMatch(
                            s.getName(),
                            outcome,
                            partitions.toString(),
                            streamIds.toString(),
                            eventIds.toString()
                    );

                    LOG.info(() -> "[CEP] " + s.getName() +
                            " outcome=" + outcome +
                            " streams=" + streamIds +
                            " events=" + eventIds);
                } else {
                    LOG.warning(() -> "[CEP] " + s.getName() +
                            " fired but no Event beans found: " +
                            newData[0].getUnderlying());
                }
            });
        }
    }
}
