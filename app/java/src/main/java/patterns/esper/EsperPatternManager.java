package patterns.esper;

import com.espertech.esper.common.client.EPCompiled;
import com.espertech.esper.common.client.configuration.Configuration;
import com.espertech.esper.compiler.client.*;
import com.espertech.esper.runtime.client.*;

import java.io.InputStreamReader;
import java.io.Reader;
import java.util.*;
import java.util.logging.Logger;

import cep.esper.EsperCEPEngine;
import schema.event.Event;
import schema.pattern.*;
import logger.PatternLogger;
import patterns.PatternManager;
import com.google.gson.*;



/**
 * Manages pattern lifecycle for Esper CEP — loading from JSON,
 * compiling and deploying patterns, and propagating confidence
 * between atomic and complex layers.
 */
public class EsperPatternManager extends PatternManager<EsperCEPEngine> {
    private static final Logger LOG = Logger.getLogger(EsperPatternManager.class.getName());

    private final PatternLogger patternLogger;
    private final EPCompiler compiler = EPCompilerProvider.getCompiler();
    private List<PatternDef> patterns;

    public EsperPatternManager(EsperCEPEngine engine, PatternLogger logger) {
        super(engine);
        this.patternLogger = logger;
    }

    private static class PatternDef {
        String name, epl, type;
        ConfidenceRule confidence;
        PatternDef(String n, String e, String t, ConfidenceRule c) {
            name = n; epl = e; type = t; confidence = c;
        }
    }

    private static class ConfidenceRule {
        String method;
        ConfidenceRule(String m) { method = m; }
    }

    @Override
    public void loadPatterns(String resource) throws Exception {
        Gson gson = new Gson();
        List<PatternDef> defs = new ArrayList<>();

        try (Reader reader = new InputStreamReader(
                getClass().getClassLoader().getResourceAsStream(resource))) {

            JsonArray arr = gson.fromJson(reader, JsonArray.class);
            for (JsonElement e : arr) {
                var o = e.getAsJsonObject();
                String name = o.get("name").getAsString();
                String epl = o.get("epl").getAsString();
                String type = o.has("type") ? o.get("type").getAsString() : "atomic";

                ConfidenceRule confRule = null;
                if (type.equals("complex") && o.has("confidence")) {
                    var conf = o.getAsJsonObject("confidence");
                    confRule = new ConfidenceRule(conf.get("aggregation").getAsString());
                }
                defs.add(new PatternDef(name, epl, type, confRule));
            }
        }

        this.patterns = defs;
        LOG.info("[EsperPatternManager] Loaded " + defs.size() + " patterns");
    }

    @Override
    public void deployPatterns() throws Exception {
        EPRuntime rt = engine.getRuntime();
        Configuration cfg = engine.getConfiguration();
        CompilerArguments args = new CompilerArguments(cfg);

        for (PatternDef def : patterns) {
            EPCompiled compiled = compiler.compile(def.epl, args);
            EPDeployment dep = rt.getDeploymentService().deploy(compiled);
            attachListener(def, dep, rt);
        }

        LOG.info("[EsperPatternManager] Deployed " + patterns.size() + " patterns.");
    }

    /**
     * Attaches listeners for each deployed EPL statement to propagate
     * and log pattern detections with confidence propagation.
     */
    private void attachListener(PatternDef def, EPDeployment dep, EPRuntime rt) {
        for (EPStatement stmt : dep.getStatements()) {
            stmt.addListener((newData, oldData, s, r) -> {
                if (newData == null || newData.length == 0) return;

                List<Event> baseEvents = new ArrayList<>();
                List<Pattern> subPatterns = new ArrayList<>();

                for (String prop : newData[0].getEventType().getPropertyNames()) {
                    Object v = newData[0].get(prop);
                    if (v instanceof Event e) baseEvents.add(e);
                    else if (v instanceof Pattern p) subPatterns.add(p);
                }

                Pattern record;
                if (def.type.equals("atomic")) {
                    double conf = baseEvents.stream()
                            .map(Event::getConfidence)
                            .filter(Objects::nonNull)
                            .mapToDouble(Double::doubleValue)
                            .average()
                            .orElse(1.0);
                    record = new AtomicPattern(def.name, baseEvents, conf);
                } else {
                    double conf = aggregate(
                            subPatterns.stream().map(Pattern::getConfidence).toList(),
                            def.confidence);
                    record = new ComplexPattern(def.name, subPatterns);
                    record.setConfidence(conf);
                }

                patternLogger.log(record);
                rt.getEventService().sendEventBean(record, "PatternRecordStream");
                LOG.info("[CEP] Fired " + def.type + " " + def.name +
                        " | confidence=" + record.getConfidence());
            });
        }
    }

    /**
     * Aggregates confidence values according to the selected method.
     * Supports "avg", "min", "max", and "most_recent" (most recent imputed value < 1.0).
     */
    private double aggregate(List<Double> vals, ConfidenceRule rule) {
        if (vals.isEmpty() || rule == null) return 0.0;

        return switch (rule.method) {
            case "min" -> vals.stream().mapToDouble(Double::doubleValue).min().orElse(0.0);
            case "max" -> vals.stream().mapToDouble(Double::doubleValue).max().orElse(0.0);
            case "avg" -> vals.stream().mapToDouble(Double::doubleValue).average().orElse(0.0);
            case "most_recent" -> {
                // Find the most recent imputed (confidence < 1.0) value, scanning backward
                for (int i = vals.size() - 1; i >= 0; i--) {
                    double v = vals.get(i);
                    if (v < 1.0) {
                        yield v; // Return immediately when found
                    }
                }
                // If none were imputed, fallback to the most recent value overall
                yield vals.get(vals.size() - 1);
            }
            default -> vals.get(vals.size() - 1);
        };
    }
}
